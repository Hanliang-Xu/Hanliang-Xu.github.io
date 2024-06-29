import json
import os

from flask import current_app
from .json_validation import JSONValidator
from .nifti_reader import read_nifti_file
from .report_generator import generate_report
from .unit_conversion import convert_to_milliseconds


def validate_json_arrays(data, filenames):
  config = current_app.config

  major_error_schema = config['schemas']['major_error_schema']
  required_validator_schema = config['schemas']['required_validator_schema']
  required_condition_schema = config['schemas']['required_condition_schema']
  recommended_validator_schema = config['schemas']['recommended_validator_schema']
  recommended_condition_schema = config['schemas']['recommended_condition_schema']
  consistency_schema = config['schemas']['consistency_schema']

  json_validator = JSONValidator(major_error_schema, required_validator_schema,
                                 required_condition_schema,
                                 recommended_validator_schema, recommended_condition_schema,
                                 consistency_schema)

  # Convert all necessary values from seconds to milliseconds before validation
  for session in data:
    for key in ['EchoTime', 'RepetitionTimePreparation', 'LabelingDuration', 'BolusCutOffDelayTime',
                'BackgroundSuppressionPulseTime', "PostLabelingDelay"]:
      if key in session:
        session[key] = convert_to_milliseconds(session[key])
    session['PLDType'] = determine_pld_type(session)

  major_errors, major_errors_concise, errors, errors_concise, warnings, warnings_concise, values = json_validator.validate(
    data, filenames)

  return major_errors, major_errors_concise, errors, errors_concise, warnings, warnings_concise, values


def determine_pld_type(session):
  # Check if any of the specified keys contain arrays with different unique values
  for key in ['PostLabelingDelay', 'EchoTime', 'LabelingDuration']:
    if key in session and isinstance(session[key], list):
      unique_values = set(session[key])
      if len(unique_values) > 1:
        return "multi-PLD"
  return "single-PLD"


def handle_upload(request):
  config = current_app.config

  if 'files' not in request.files or 'filenames' not in request.form:
    return {"error": "No file part"}, 400

  files = request.files.getlist('files')
  filenames = request.form.getlist('filenames')
  nifti_file = request.files.get('nii-file')

  if not files or not filenames:
    return {"error": "No selected files or filenames"}, 400

  grouped_files, error = group_files(files, filenames, config['paths']['upload_folder'])
  if error:
    return {"error": error}, 400

  nifti_slice_number, error = read_nifti_file(nifti_file, config['paths']['upload_folder'])
  if error:
    return {"error": error, "filename": nifti_file.filename}, 400

  asl_json_filenames, asl_json_data, m0_prep_times_collection = [], [], []
  discrepancies, all_absent, bs_all_off = [], True, True

  for group in grouped_files:
    if group['asl_json'] is not None:
      asl_filename, asl_data = group['asl_json']
      asl_json_filenames.append(asl_filename)
      asl_json_data.append(asl_data)

      if asl_data.get("M0Type", []) != "Absent":
        all_absent = False
      if asl_data.get("BackgroundSuppression", []):
        bs_all_off = False

      if group['m0_json'] is not None:
        all_absent = False
        m0_filename, m0_data = group['m0_json']
        params_asl, params_m0 = extract_params(asl_data), extract_params(m0_data)
        discrepancies.extend(compare_params(params_asl, params_m0, asl_filename, m0_filename))

        m0_prep_time = m0_data.get("RepetitionTimePreparation", [])
        m0_prep_times_collection.append(m0_prep_time)

      if group['tsv'] is not None:
        all_absent = False
        if asl_data.get("M0Type", []) != "Separate":
          tsv_filename, tsv_data = group['tsv']
          m0scan_count = sum(1 for line in tsv_data if line.strip() == "m0scan")
          repetition_times = asl_data.get("RepetitionTimePreparation", [])
          if len(repetition_times) > m0scan_count:
            m0_prep_times_collection.append(repetition_times[:m0scan_count])
            asl_data["RepetitionTimePreparation"] = repetition_times[m0scan_count:]
          elif len(repetition_times) < m0scan_count:
            discrepancies.append(
              f"Error: 'RepetitionTimePreparation' array in ASL file '{asl_filename}' is shorter than the number of 'm0scan' in TSV file '{tsv_filename}'")

  M0_TR, report_line_on_M0 = determine_m0_tr_and_report(m0_prep_times_collection, all_absent,
                                                        bs_all_off, discrepancies)

  combined_major_errors, combined_major_errors_concise, combined_errors, combined_errors_concise, combined_warnings, combined_warnings_concise, combined_values = validate_json_arrays(
    asl_json_data, asl_json_filenames)

  if discrepancies:
    combined_errors.update({"m0_error": discrepancies})
    combined_errors_concise.update({"m0_error": discrepancies})

  save_json(combined_major_errors, config['paths']['major_error_report'])
  save_json(combined_errors, config['paths']['error_report'])
  save_json(combined_warnings, config['paths']['warning_report'])

  inconsistency_errors = extract_inconsistencies(combined_errors_concise)
  major_inconsistency_errors = extract_inconsistencies(combined_major_errors_concise)
  warning_inconsistency_errors = extract_inconsistencies(combined_warnings_concise)

  report = generate_report(combined_values, combined_major_errors, combined_errors,
                           report_line_on_M0, M0_TR, slice_number=nifti_slice_number)
  save_report(report, config['paths']['final_report'])

  return {
    "major_errors": combined_major_errors,
    "major_errors_concise": combined_major_errors_concise,
    "errors": combined_errors,
    "errors_concise": combined_errors_concise,
    "warnings": combined_warnings,
    "warnings_concise": combined_warnings_concise,
    "report": report,
    "nifti_slice_number": nifti_slice_number,
    "inconsistencies": "".join(inconsistency_errors),
    "major_inconsistencies": "".join(major_inconsistency_errors),
    "warning_inconsistencies": "".join(warning_inconsistency_errors)
  }, 200


def group_files(files, filenames, upload_folder):
  grouped_files = []
  current_group = {'asl_json': None, 'm0_json': None, 'tsv': None}

  for file, filename in zip(files, filenames):
    if not filename.endswith(('.json', '.tsv')):
      return None, f"Invalid file: {filename}"

    filepath = os.path.join(upload_folder, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)

    data, error = read_file(filepath)
    if error:
      return None, error

    if filename.endswith('asl.json'):
      if current_group['asl_json']:
        grouped_files.append(current_group)
      current_group = {'asl_json': (filename, data), 'm0_json': None, 'tsv': None}
    elif filename.endswith('m0scan.json'):
      current_group['m0_json'] = (filename, data)
    elif filename.endswith('.tsv'):
      current_group['tsv'] = (filename, data)

  if current_group['asl_json']:
    grouped_files.append(current_group)

  return grouped_files, None


def read_file(file_path):
  try:
    if file_path.endswith('.json'):
      with open(file_path, 'r') as file:
        data = json.load(file)
      return data, None
    elif file_path.endswith('.tsv'):
      with open(file_path, 'r') as file:
        lines = file.readlines()
      header = lines[0].strip()
      if header != 'volume_type':
        return None, "Invalid TSV header, not \"volume_type\""
      data = [line.strip() for line in lines[1:]]
      return data, None
    else:
      return None, "Unsupported file format"
  except Exception as e:
    return None, f"Error reading file: {str(e)}"


def extract_params(data):
  return {
    "EchoTime": data.get("EchoTime"),
    "FlipAngle": data.get("FlipAngle"),
    "MagneticFieldStrength": data.get("MagneticFieldStrength"),
    "MRAcquisitionType": data.get("MRAcquisitionType"),
    "PulseSequenceType": data.get("PulseSequenceType")
  }


def compare_params(params_asl, params_m0, asl_filename, m0_filename):
  discrepancies = []
  for param, asl_value in params_asl.items():
    m0_value = params_m0.get(param)
    if isinstance(asl_value, float) and isinstance(m0_value, float):
      tolerance = 1e-6
      if abs(asl_value - m0_value) > tolerance:
        discrepancies.append(
          f"Discrepancy in '{param}' for ASL file '{asl_filename}' and M0 file '{m0_filename}': ASL value = {asl_value}, M0 value = {m0_value}")
    else:
      if asl_value != m0_value:
        discrepancies.append(
          f"Discrepancy in '{param}' for ASL file '{asl_filename}' and M0 file '{m0_filename}': ASL value = {asl_value}, M0 value = {m0_value}")
  return discrepancies


def determine_m0_tr_and_report(m0_prep_times_collection, all_absent, bs_all_off, discrepancies):
  M0_TR = None
  if m0_prep_times_collection:
    if all(x == m0_prep_times_collection[0] for x in m0_prep_times_collection):
      M0_TR = m0_prep_times_collection[0]
    else:
      discrepancies.append("Different \"RepetitionTimePreparation\" parameters for M0")

  if all_absent and bs_all_off:
    report_line_on_M0 = "No m0-scan was acquired, a control image without background suppression was used for M0 estimation."
  elif all_absent and not bs_all_off:
    report_line_on_M0 = "No m0-scan was acquired, but there doesn't always exist a control image without background suppression."
  else:
    if not discrepancies:
      report_line_on_M0 = "M0 was acquired with the same readout and without background suppression."
    else:
      report_line_on_M0 = "There is inconsistency in parameters between M0 and ASL scans."
  return M0_TR, report_line_on_M0


def save_json(data, filepath):
  with open(filepath, 'w') as file:
    json.dump(data, file, indent=2)


def save_report(report, filepath):
  with open(filepath, 'w') as file:
    file.write(report)


def extract_inconsistencies(error_map):
  inconsistency_errors = []
  fields_to_remove = []

  for field, errors in error_map.items():
    for error in errors:
      if "INCONSISTENCY" in error:
        inconsistency_errors.append(f"{field}: {error.replace('INCONSISTENCY: ', '')}\n")
        errors.remove(error)

    if not errors:
      fields_to_remove.append(field)

  for field in fields_to_remove:
    del error_map[field]
  return inconsistency_errors
