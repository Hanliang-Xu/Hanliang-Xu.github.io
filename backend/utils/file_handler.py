import csv
import json
import os
from io import StringIO

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


def analyze_volume_types(volume_types):
  first_non_m0type = next((vt for vt in volume_types if vt in {'control', 'label', 'deltam'}), None)
  pattern = None
  control_label_pairs = 0
  label_control_pairs = 0
  deltam_count = 0
  if first_non_m0type == 'control':
    pattern = 'control-label'
  elif first_non_m0type == 'label':
    pattern = 'label-control'
  elif first_non_m0type == 'deltam':
    pattern = 'deltam'
    deltam_count = volume_types.count('deltam')
    return pattern, deltam_count
  i = 0
  while i < len(volume_types):
    if volume_types[i] == 'control' and i + 1 < len(volume_types) and volume_types[
      i + 1] == 'label':
      control_label_pairs += 1
      i += 2
    elif volume_types[i] == 'label' and i + 1 < len(volume_types) and volume_types[
      i + 1] == 'control':
      label_control_pairs += 1
      i += 2
    else:
      i += 1
  print(pattern)
  if pattern == 'control-label':
    return pattern, control_label_pairs
  else:
    return pattern, label_control_pairs


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
  errors, warnings, all_absent, bs_all_off = [], [], True, True
  global_pattern = None

  for group in grouped_files:
    if group['asl_json'] is not None:
      asl_filename, asl_data = group['asl_json']
      asl_json_filenames.append(asl_filename)
      asl_json_data.append(asl_data)

      m0_type = asl_data.get("M0Type")
      if m0_type != "Absent":
        all_absent = False
      if asl_data.get("BackgroundSuppression", []):
        bs_all_off = False
  # Convert all necessary values from seconds to milliseconds before validation
  for session in asl_json_data:
    for key in ['EchoTime', 'RepetitionTimePreparation', 'LabelingDuration',
                'BolusCutOffDelayTime', 'BackgroundSuppressionPulseTime', "PostLabelingDelay"]:
      if key in session:
        session[key] = convert_to_milliseconds(session[key])
    session['PLDType'] = determine_pld_type(session)

  (combined_major_errors, combined_major_errors_concise, combined_errors, combined_errors_concise,
   combined_warnings, combined_warnings_concise, combined_values) = validate_json_arrays(
    asl_json_data, asl_json_filenames)

  for i, group in enumerate(grouped_files):
    if group['asl_json'] is not None:
      asl_filename = asl_json_filenames[i]
      asl_data = asl_json_data[i]
      m0_type = asl_data.get("M0Type")

      if group['m0_json'] is not None:
        m0_filename, m0_data = group['m0_json']
        for key in ['EchoTime', 'RepetitionTimePreparation']:
          if key in m0_data:
            m0_data[key] = convert_to_milliseconds(m0_data[key])
        if m0_type == "Absent":
          errors.append(
            f"Error: M0 type specified as 'Absent' for '{asl_filename}', but"
            f" '{m0_filename}' is present")
        elif m0_type == "Included":
          errors.append(
            f"Error: M0 type specified as 'Included' for '{asl_filename}', but"
            f" '{m0_filename}' is present")
        params_asl, params_m0 = extract_params(asl_data), extract_params(m0_data)
        errors.extend(compare_params(params_asl, params_m0, asl_filename, m0_filename)[0])
        warnings.extend(compare_params(params_asl, params_m0, asl_filename, m0_filename)[1])

        m0_prep_time = m0_data.get("RepetitionTimePreparation", [])
        m0_prep_times_collection.append(m0_prep_time)
      else:
        if m0_type == "Separate":
          errors.append(
            f"Error: M0 type specified as 'Separate' for '{asl_filename}', but"
            f" m0scan.json is not provided.")

      if group['tsv'] is not None:
        tsv_filename, tsv_data = group['tsv']
        m0scan_count = sum(1 for line in tsv_data if line.strip() == "m0scan")
        volume_types = [line.strip() for line in tsv_data if line.strip()]
        pattern, total_acquired_pairs = analyze_volume_types(volume_types)
        if global_pattern is None:
          global_pattern = pattern
        elif global_pattern != pattern:
          global_pattern = "control-label (there's no consistent control-label or label-control order)"
        if m0scan_count > 0:
          if m0_type == "Absent":
            errors.append(
              f"Error: m0 type is specified as 'Absent' for '{asl_filename}', but"
              f" '{tsv_filename}' contains m0scan.")
          elif m0_type == "Separate":
            errors.append(
              f"Error: m0 type is specified as 'Separate' for '{asl_filename}', but"
              f" '{tsv_filename}' contains m0scan.")
          else:
            repetition_times = asl_data.get("RepetitionTimePreparation", [])

            if not isinstance(repetition_times, list):
              repetition_times = [repetition_times]
            repetition_times_max = max(repetition_times)
            repetition_times_min = min(repetition_times)

            if len(repetition_times) > m0scan_count:
              m0_prep_times_collection.append(repetition_times[0])
              asl_data["RepetitionTimePreparation"] = repetition_times[m0scan_count:]
            elif (repetition_times_max - repetition_times_min) < 10e-5:
              m0_prep_times_collection.append(repetition_times[0])
              asl_data["RepetitionTimePreparation"] = repetition_times[0]
            elif len(repetition_times) < m0scan_count:
              errors.append(
                f"Error: 'RepetitionTimePreparation' array in ASL file '{asl_filename}' is shorter"
                f" than the number of 'm0scan' in TSV file '{tsv_filename}'")
        else:
          if group['m0_json'] is None and asl_data.get("BackgroundSuppression") and asl_data.get(
              "BackgroundSuppression"):
            if asl_data.get("BackgroundSuppressionPulseTime"):
              warnings.append(f"For {asl_filename}, no M0 is provided and BS pulses with known"
                              f" timings are on. BS-pulse efficiency has to be calculated to"
                              f" enable absolute quantification.")
            else:
              warnings.append(f"For {asl_filename}, no M0 is provided and BS pulses with unknown"
                              f" timings are on, only a relative quantification is possible.")
      else:
        errors.append(f"Error: 'aslcontext.tsv' is missing for {asl_filename}")

  M0_TR, report_line_on_M0 = determine_m0_tr_and_report(m0_prep_times_collection, all_absent,
                                                        bs_all_off, errors, m0_type)

  if errors:
    combined_errors.update({"m0_error": errors})
    combined_errors_concise.update({"m0_error": errors})
  if warnings:
    combined_warnings.update({"m0_warning": warnings})
    combined_warnings_concise.update({"m0_warning": warnings})

  save_json(combined_major_errors, config['paths']['major_error_report'])
  save_json(combined_errors, config['paths']['error_report'])
  save_json(combined_warnings, config['paths']['warning_report'])

  inconsistency_errors = extract_inconsistencies(combined_errors_concise)
  major_inconsistency_errors = extract_inconsistencies(combined_major_errors_concise)
  warning_inconsistency_errors = extract_inconsistencies(combined_warnings_concise)

  report = generate_report(combined_values, combined_major_errors, combined_errors,
                           report_line_on_M0, M0_TR, global_pattern, total_acquired_pairs,
                           slice_number=nifti_slice_number)
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
  config = current_app.config
  consistency_schema = config['schemas']['consistency_schema']

  errors = []
  warnings = []
  for param, asl_value in params_asl.items():
    m0_value = params_m0.get(param)
    schema = consistency_schema.get(param)

    if not schema:
      continue

    validation_type = schema.get('validation_type')
    warning_variation = schema.get('warning_variation', 1e-5)
    error_variation = schema.get('error_variation', 1e-4)

    if validation_type == "string":
      if asl_value != m0_value:
        errors.append(
          f"Discrepancy in '{param}' for ASL file '{asl_filename}' and M0 file '{m0_filename}': "
          f"ASL value = {asl_value}, M0 value = {m0_value}")
    elif validation_type == "floatOrArray":
      if isinstance(asl_value, float) and isinstance(m0_value, float):
        difference = abs(asl_value - m0_value)
        if difference > error_variation:
          errors.append(
            f"ERROR: Discrepancy in '{param}' for ASL file '{asl_filename}' and M0 file '{m0_filename}': "
            f"ASL value = {asl_value}, M0 value = {m0_value}, difference = {difference}, exceeds error threshold {error_variation}")
        elif difference > warning_variation:
          warnings.append(
            f"WARNING: Discrepancy in '{param}' for ASL file '{asl_filename}' and M0 file '{m0_filename}': "
            f"ASL value = {asl_value}, M0 value = {m0_value}, difference = {difference}, exceeds warning threshold {warning_variation}")
  return errors, warnings


def determine_m0_tr_and_report(m0_prep_times_collection, all_absent, bs_all_off, discrepancies,
                               m0_type):
  M0_TR = None
  if m0_type == "Estimate":
    return M0_TR, "A single M0 scaling value is provided for CBF quantification"
  if m0_prep_times_collection:
    if all(abs(x - m0_prep_times_collection[0]) < 1e-5 for x in m0_prep_times_collection):
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
