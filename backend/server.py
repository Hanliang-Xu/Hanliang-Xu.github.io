import json
import os

import nibabel as nib
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from json_validation import JSONValidator
from validator import *

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
MAJOR_ERROR_REPORT = 'major_error_report.json'
ERROR_REPORT = 'error_report.json'
WARNING_REPORT = 'warning_report.json'
FINAL_REPORT = 'report.txt'
SECOND_TO_MILLISECOND = 1000

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)


@app.route('/')
def home():
  return "Welcome to my Flask App"


@app.route('/upload', methods=['POST'])
def upload_files():
  if 'files' not in request.files or 'filenames' not in request.form:
    return jsonify({"error": "No file part"}), 400

  files = request.files.getlist('files')
  filenames = request.form.getlist('filenames')
  nifti_file = request.files.get('nii-file')

  if not files or not filenames:
    return jsonify({"error": "No selected files or filenames"}), 400

  grouped_files = []
  current_group = {'asl_json': None, 'm0_json': None, 'tsv': None}

  # Populate grouped_files by iterating over the files once
  for file, filename in zip(files, filenames):
    if not file.filename.endswith(('.json', '.tsv')):
      return jsonify({"error": f"Invalid file: {file.filename}"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)

    data, error = read_file(filepath)
    if error:
      return jsonify({"error": error, "filename": filename}), 400

    if filename.endswith('asl.json'):
      # Start a new group if an asl.json is encountered
      if current_group['asl_json']:
        grouped_files.append(current_group)
      current_group = {'asl_json': (filename, data), 'm0_json': None, 'tsv': None}
    elif filename.endswith('m0scan.json'):
      current_group['m0_json'] = (filename, data)
    elif filename.endswith('.tsv'):
      current_group['tsv'] = (filename, data)

  # Append the last group if it contains an asl.json
  if current_group['asl_json']:
    grouped_files.append(current_group)

  if not nifti_file.filename.endswith(('.nii', '.nii.gz')):
    return jsonify({"error": f"Invalid file: {nifti_file.filename}"}), 400

  nifti_filepath = os.path.join(UPLOAD_FOLDER, nifti_file.filename)
  os.makedirs(os.path.dirname(nifti_filepath), exist_ok=True)
  nifti_file.save(nifti_filepath)

  nifti_slice_number, error = read_nifti_file(nifti_filepath)
  if error:
    return jsonify({"error": error, "filename": nifti_file.filename}), 400

  # Arrays to hold the filenames and data of asl_json files
  asl_json_filenames = []
  asl_json_data = []
  m0_prep_times_collection = []

  # Iterate over the grouped_files to extract asl_json files
  discrepancies = []
  all_absent = True
  bs_all_off = True
  for group in grouped_files:
    if group['asl_json'] is not None:
      asl_filename, asl_data = group['asl_json']
      asl_json_filenames.append(asl_filename)
      if asl_data.get("M0Type", []) != "Absent":
        all_absent = False
      if asl_data.get("BackgroundSuppression", []):
        bs_all_off = False

      if group['m0_json'] is not None:
        all_absent = False
        m0_filename, m0_data = group['m0_json']
        # Extract parameters
        params_asl = {
          "EchoTime": asl_data.get("EchoTime"),
          "FlipAngle": asl_data.get("FlipAngle"),
          "MagneticFieldStrength": asl_data.get("MagneticFieldStrength"),
          "MRAcquisitionType": asl_data.get("MRAcquisitionType"),
          "PulseSequenceType": asl_data.get("PulseSequenceType")
        }
        params_m0 = {
          "EchoTime": m0_data.get("EchoTime"),
          "FlipAngle": m0_data.get("FlipAngle"),
          "MagneticFieldStrength": m0_data.get("MagneticFieldStrength"),
          "MRAcquisitionType": m0_data.get("MRAcquisitionType"),
          "PulseSequenceType": m0_data.get("PulseSequenceType")
        }
        # Compare parameters
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
        m0_prep_time = m0_data.get("RepetitionTimePreparation", [])
        m0_prep_times_collection.append(m0_prep_time)

      if group['tsv'] is not None:
        all_absent = False
        if asl_data.get("M0Type", []) != "Separate":
          tsv_filename, tsv_data = group['tsv']
          m0scan_count = sum(1 for line in tsv_data if line.strip() == "m0scan")
          repetition_times = asl_data.get("RepetitionTimePreparation", [])
          if len(repetition_times) > m0scan_count:
            # Eliminate the same number of values from the start
            m0_prep_times_collection.append(repetition_times[:m0scan_count])
            modified_prep_times = repetition_times[m0scan_count:]
            asl_data["RepetitionTimePreparation"] = modified_prep_times
          elif len(repetition_times) < m0scan_count:
            discrepancies.append(
              f"Error: 'RepetitionTimePreparation' array in ASL file '{asl_filename}' is shorter than the number of 'm0scan' in TSV file '{tsv_filename}'"
            )
      asl_json_data.append(asl_data)


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

  # Perform validation on the combined arrays
  (combined_major_errors, combined_major_errors_concise, combined_errors, combined_errors_concise,
   combined_warnings, combined_warnings_concise, combined_values) = validate_json_arrays(
    asl_json_data, asl_json_filenames)

  if discrepancies:
    mapped_discrepancies = {"m0_error": discrepancies}
    combined_errors.update(mapped_discrepancies)
    combined_errors_concise.update(mapped_discrepancies)

  save_json(combined_major_errors, MAJOR_ERROR_REPORT)
  save_json(combined_errors, ERROR_REPORT)
  save_json(combined_warnings, WARNING_REPORT)

  inconsistency_errors = extract_inconsistencies(combined_errors_concise)
  major_inconsistency_errors = extract_inconsistencies(combined_major_errors_concise)
  warning_inconsistency_errors = extract_inconsistencies(combined_warnings_concise)

  report = generate_report(combined_values, combined_major_errors, combined_errors, report_line_on_M0, M0_TR,
                           slice_number=nifti_slice_number)

  # Ensure report is a single string
  if isinstance(report, list):
    report_str = "".join(report)  # Use space to join for a single paragraph
  else:
    report_str = str(report)

  with open(FINAL_REPORT, 'w') as report_file:
    report_file.write(report_str)

  return jsonify({
    "major_errors": combined_major_errors,
    "major_errors_concise": combined_major_errors_concise,
    "errors": combined_errors,
    "errors_concise": combined_errors_concise,
    "warnings": combined_warnings,
    "warnings_concise": combined_warnings_concise,
    "report": report_str,
    "nifti_slice_number": nifti_slice_number,
    "inconsistencies": "".join(inconsistency_errors),
    "major_inconsistencies": "".join(major_inconsistency_errors),
    "warning_inconsistencies": "".join(warning_inconsistency_errors)
  }), 200


@app.route('/download', methods=['GET'])
def download_report():
  report_type = request.args.get('type')
  if report_type == 'major_errors':
    return send_file(MAJOR_ERROR_REPORT, as_attachment=True)
  elif report_type == 'errors':
    return send_file(ERROR_REPORT, as_attachment=True)
  elif report_type == 'warnings':
    return send_file(WARNING_REPORT, as_attachment=True)
  elif report_type == 'report':
    return send_file(FINAL_REPORT, as_attachment=True)
  return jsonify({"error": "Invalid report type"}), 400


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


def save_json(data, filepath):
  with open(filepath, 'w') as file:
    json.dump(data, file, indent=2)


def read_nifti_file(filepath):
  try:
    nifti_img = nib.load(filepath)
    slice_number = nifti_img.shape[2]
    return slice_number, None
  except Exception as e:
    return None, str(e)


def determine_pld_type(session):
  # Check if any of the specified keys contain arrays with different unique values
  for key in ['PostLabelingDelay', 'EchoTime', 'LabelingDuration']:
    if key in session and isinstance(session[key], list):
      unique_values = set(session[key])
      if len(unique_values) > 1:
        return "multi-PLD"
  return "single-PLD"


def convert_to_milliseconds(values):
  """Utility function to convert seconds to milliseconds and round close values to integers."""

  def round_if_close(val, decimal_places=3):
    rounded_val = round(val, decimal_places)
    if abs(val - round(val)) < 1e-6:
      return round(val)
    return rounded_val

  def convert_value(value):
    if isinstance(value, (int, float)):
      return round_if_close(value * SECOND_TO_MILLISECOND)
    elif isinstance(value, list):
      return [round_if_close(v * SECOND_TO_MILLISECOND) for v in value]
    return value

  if isinstance(values, list):
    return [convert_value(value) for value in values]
  else:
    return convert_value(values)


def validate_json_arrays(data, filenames):
  major_error_schema = {
    "PLDType": StringValidator(allowed_values=["multi-PLD", "single-PLD"], major_error=True),
    "ArterialSpinLabelingType": StringValidator(
      allowed_values=["PASL", "(P)CASL", "PCASL", "CASL"], major_error=True),
    "MRAcquisitionType": StringValidator(allowed_values=["2D", "3D"], major_error=True),
    "PulseSequenceType": StringValidator(major_error=True)
  }
  required_validator_schema = {
    "BackgroundSuppression": BooleanValidator(),
    "M0Type": StringValidator(),
    "TotalAcquiredPairs": NumberValidator(min_error=0, enforce_integer=True),
    "AcquisitionVoxelSize": NumberArrayValidator(size_error=3),
    "LabelingDuration": NumberOrNumberArrayValidator(),
    "PostLabelingDelay": NumberOrNumberArrayValidator(),
    "BolusCutOffFlag": BooleanValidator(),
    "BolusCutOffTechnique": StringValidator(),
    "BolusCutOffDelayTime": NumberOrNumberArrayValidator(),
    "EchoTime": NumberOrNumberArrayValidator(),
    "RepetitionTimePreparation": NumberOrNumberArrayValidator(),
    "FlipAngle": NumberValidator(min_error=0, max_error_include=360),
    "MagneticFieldStrength": NumberValidator(),
    "Manufacturer": StringValidator(),
    "ManufacturersModelName": StringValidator()
  }
  required_condition_schema = {
    "BackgroundSuppression": "all",
    "M0Type": "all",
    "TotalAcquiredPairs": "all",
    "AcquisitionVoxelSize": "all",
    "LabelingDuration": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "PostLabelingDelay": {"ArterialSpinLabelingType": ["PCASL", "CASL", "PASL"]},
    "BolusCutOffFlag": {"ArterialSpinLabelingType": "PASL"},
    "BolusCutOffTechnique": {"ArterialSpinLabelingType": "PASL"},
    "BolusCutOffDelayTime": {"ArterialSpinLabelingType": "PASL"},
    "EchoTime": "all",
    "RepetitionTimePreparation": "all",
    "FlipAngle": "all",
    "MagneticFieldStrength": "all",
    "Manufacturer": "all",
    "ManufacturersModelName": "all"
  }
  recommended_validator_schema = {
    "BackgroundSuppressionNumberPulses": NumberValidator(min_error_include=0),
    "BackgroundSuppressionPulseTime": NumberArrayValidator(min_error=0),
    "LabelingLocationDescription": StringValidator(),
    "VascularCrushingVENC": NumberOrNumberArrayValidator(min_error_include=0),
    "PCASLType": StringValidator(allowed_values=["balanced", "unbalanced"]),
    "CASLType": StringValidator(allowed_values=["single-coil", "double-coil"]),
    "LabelingDistance": NumberValidator(),
    "LabelingPulseAverageGradient": NumberValidator(min_error=0),
    "LabelingPulseMaximumGradient": NumberValidator(min_error=0),
    "LabelingPulseAverageB1": NumberValidator(min_error=0),
    "LabelingPulseFlipAngle": NumberValidator(min_error=0, max_error_include=360),
    "LabelingPulseInterval": NumberValidator(min_error=0),
    "LabelingPulseDuration": NumberValidator(min_error=0),
    "PASLType": StringValidator(),
    "LabelingSlabThickness": NumberValidator(min_error_include=0),
    "AcquisitionDuration": NumberValidator()
  }
  recommended_condition_schema = {
    "BackgroundSuppressionNumberPulses": {"BackgroundSuppression": True},
    "BackgroundSuppressionPulseTime": {"BackgroundSuppression": True},
    "LabelingLocationDescription": "all",
    "VascularCrushingVENC": {"VascularCrushing": True},
    "PCASLType": {"ArterialSpinLabelingType": "PCASL"},
    "CASLType": {"ArterialSpinLabelingType": "CASL"},
    "LabelingDistance": "all",
    "LabelingPulseAverageGradient": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "LabelingPulseMaximumGradient": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "LabelingPulseAverageB1": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "LabelingPulseFlipAngle": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "LabelingPulseInterval": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "LabelingPulseDuration": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "PASLType": {"ArterialSpinLabelingType": "PASL"},
    "LabelingSlabThickness": {"ArterialSpinLabelingType": "PASL"},
    "AcquisitionDuration": "all"
  }
  consistency_schema = {
    "PLDType": ConsistencyValidator(type="string", is_major=True),
    "ArterialSpinLabelingType": ConsistencyValidator(type="string", is_major=True),
    "MRAcquisitionType": ConsistencyValidator(type="string", is_major=True),
    "PulseSequenceType": ConsistencyValidator(type="string", is_major=True),
    "EchoTime": ConsistencyValidator(type="floatOrArray", error_variation=0.1,
                                     warning_variation=0.0001),
    "RepetitionTimePreparation": ConsistencyValidator(type="floatOrArray", error_variation=10,
                                                      warning_variation=0.1),
    "LabelingDuration": ConsistencyValidator(type="floatOrArray", error_variation=10,
                                             warning_variation=0.1),
    "BackgroundSuppression": ConsistencyValidator(type="boolean"),
    "AcquisitionVoxelSize": ConsistencyValidator(type="floatOrArray", error_variation=0.1,
                                                 warning_variation=0.001),
    "FlipAngle": ConsistencyValidator(type="floatOrArray", error_variation=1,
                                      warning_variation=0.01),
    "PostLabelingDelay": ConsistencyValidator(type="floatOrArray", error_variation=10,
                                              warning_variation=0.01),
    "BolusCutOffFlag": ConsistencyValidator(type="boolean"),
    "BolusCutOffTechnique": ConsistencyValidator(type="string"),
    "BolusCutOffDelayTime": ConsistencyValidator(type="floatOrArray"),
    "BackgroundSuppressionNumberPulses": ConsistencyValidator(type="floatOrArray"),
    "BackgroundSuppressionPulseTime": ConsistencyValidator(type="floatOrArray"),
    "TotalAcquiredPairs": ConsistencyValidator(type="floatOrArray"),
    "AcquisitionDuration": ConsistencyValidator(type="floatOrArray"),
    "MagneticFieldStrength": ConsistencyValidator(type="floatOrArray"),
    "Manufacturer": ConsistencyValidator(type="string", is_major=False),
    "M0Type": ConsistencyValidator(type="string", is_major=False)
  }

  validator = JSONValidator(major_error_schema, required_validator_schema,
                            required_condition_schema, recommended_validator_schema,
                            recommended_condition_schema, consistency_schema)

  # Convert all necessary values from seconds to milliseconds before validation
  for session in data:
    for key in ['EchoTime', 'RepetitionTimePreparation', 'LabelingDuration', 'BolusCutOffDelayTime',
                'BackgroundSuppressionPulseTime', "PostLabelingDelay"]:
      if key in session:
        session[key] = convert_to_milliseconds(session[key])
    session['PLDType'] = determine_pld_type(session)

  major_errors, major_errors_concise, errors, errors_concise, warnings, warnings_concise, values \
    = validator.validate(data, filenames)
  return (major_errors, major_errors_concise, errors, errors_concise, warnings, warnings_concise,
          values)


def handle_boolean_inconsistency(values, key, combined_errors):
  inconsistencies = [
    error for error in combined_errors.get(key, []) if "INCONSISTENCY" in error
  ]
  if inconsistencies:
    key_values = [entry[1] for entry in values.get(key, [])]
    normalized_values = [bool(val) for val in key_values]
    counter = Counter(normalized_values)
    most_common_value, count = counter.most_common(1)[0]
    if count > len(normalized_values) // 2:
      return "inconsistent_common", most_common_value
    else:
      return "inconsistent_no_common", None
  else:
    first_value = values.get(key, [['N/A']])
    return "consistent", bool(first_value[0][1]) if first_value else 'N/A'


def handle_inconsistency(values, key, combined_errors):
  # Check if there are any inconsistencies for the given key
  inconsistencies = [
    error for error in combined_errors.get(key, []) if "INCONSISTENCY" in error
  ]
  value_range = None

  if inconsistencies:
    # Extract all values for the given key
    key_values = [entry[1] for entry in values.get(key, [])]

    # Normalize values (convert single element arrays to float and handle sublists)
    normalized_values = []
    for val in key_values:
      if isinstance(val, list):
        if len(val) == 1:
          normalized_values.append(val[0])
        else:
          normalized_values.append(tuple(val))
      else:
        normalized_values.append(val)

    # Determine the most common value
    counter = Counter(normalized_values)
    most_common_value, count = counter.most_common(1)[0]

    flattened_values = [item for sublist in normalized_values for item in
                        (sublist if isinstance(sublist, tuple) else [sublist])]
    value_range = f"Range: {min(flattened_values)}-{max(flattened_values)}"

    if count > len(normalized_values) // 2:
      return "inconsistent_common", most_common_value, value_range
    else:
      return "inconsistent_no_common", None, value_range
  else:
    # Return the first value if no inconsistencies found, or 'N/A' if not available
    first_value = values.get(key, [['N/A']])
    if first_value and isinstance(first_value[0], list) and len(first_value[0]) > 1:
      value = tuple(first_value[0])
    else:
      value = first_value[0][1] if first_value else 'N/A'

    return "consistent", value, value_range


def extract_value(values, key, combined_errors, report_range=False, format_duration=False):
  status, most_common_value, value_range = handle_inconsistency(values, key, combined_errors)

  if format_duration and isinstance(most_common_value, (int, float)):
    most_common_value = format_acquisition_duration(most_common_value)

  if status == "consistent":
    return most_common_value
  elif status == "inconsistent_common":
    return f"(inconsistent, {most_common_value} is the most common data)" if not report_range else f"(inconsistent, {most_common_value} is the most common data, {value_range})"
  else:
    return f"(inconsistent, no common data, {value_range})" if report_range else "(inconsistent, no common data)"


def extract_unique_values_from_array(values):
  unique_values = sorted(set(values))
  return ', '.join(map(str, unique_values))


def handle_voxel_size(values, combined_errors):
  status, acquisition_voxel_size, _ = handle_inconsistency(values, 'AcquisitionVoxelSize',
                                                           combined_errors)
  if status == "consistent":
    if isinstance(acquisition_voxel_size, (list, tuple)) and len(acquisition_voxel_size) >= 3:
      voxel_size_1_2 = f"{acquisition_voxel_size[0]}x{acquisition_voxel_size[1]}"
      voxel_size_3 = acquisition_voxel_size[2]
    else:
      voxel_size_1_2 = 'N/A'
      voxel_size_3 = 'N/A'
  elif status == "inconsistent_common":
    if isinstance(acquisition_voxel_size, (list, tuple)) and len(acquisition_voxel_size) >= 3:
      voxel_size_1_2 = f"(inconsistent, {acquisition_voxel_size[0]}x{acquisition_voxel_size[1]} is the most common)"
      voxel_size_3 = f"(inconsistent, {acquisition_voxel_size[2]} is the most common)"
    else:
      voxel_size_1_2 = 'N/A'
      voxel_size_3 = 'N/A'
  else:
    voxel_size_1_2 = 'N/A (inconsistent, with no common data.)'
    voxel_size_3 = 'N/A (inconsistent, with no common data.)'
  return voxel_size_1_2, voxel_size_3


def handle_pld_values(values, combined_errors):
  status, pld_values, _ = handle_inconsistency(values, 'PostLabelingDelay', combined_errors)

  def format_pld_array(pld_array):
    pld_counter = Counter(pld_array)
    formatted_pld = ', '.join(
      [f"{pld}ms ({count // 2} {'repeat' if (count // 2) == 1 else 'repeats'})" for pld, count in
       sorted(pld_counter.items())]
    )
    return formatted_pld

  if status == "consistent":
    if isinstance(pld_values, (list, tuple)):
      extended_pld_text = format_pld_array(pld_values)
    else:
      extended_pld_text = 'N/A'
  elif status == "inconsistent_common":
    if isinstance(pld_values, (list, tuple)):
      extended_pld_text = f"(inconsistent, {format_pld_array(pld_values)} is the most common)"
    else:
      extended_pld_text = 'N/A'
  else:
    extended_pld_text = "(inconsistent, no common data)"

  return extended_pld_text


def handle_bolus_cutoff_flag(values, key, combined_errors):
  status, flag = handle_boolean_inconsistency(values, key, combined_errors)
  if status == "consistent":
    return "without" if not flag else "with"
  elif status == "inconsistent_common":
    return f"(inconsistent, {'without' if not flag else 'with'} is the most common)"
  else:
    return "(inconsistent, no common data)"


def handle_string_inconsistency(values, key, combined_errors):
  inconsistencies = [
    error for error in combined_errors.get(key, []) if "INCONSISTENCY" in error
  ]
  if inconsistencies:
    key_values = [entry[1] for entry in values.get(key, [])]
    normalized_values = [str(val) for val in key_values]
    counter = Counter(normalized_values)
    most_common_value, count = counter.most_common(1)[0]
    if count > len(normalized_values) // 2:
      return "inconsistent_common", most_common_value
    else:
      return "inconsistent_no_common", None
  else:
    first_value = values.get(key, [['N/A']])
    return "consistent", str(first_value[0][1]) if first_value else 'N/A'


def handle_bolus_cutoff_technique(values, key, combined_errors):
  status, technique = handle_string_inconsistency(values, key, combined_errors)
  if status == "consistent":
    return technique
  elif status == "inconsistent_common":
    return f"(inconsistent, {technique} is the most common)"
  else:
    return "(inconsistent, no common data)"


def handle_bolus_cutoff_delay_time(values, combined_errors):
  status, bolus_cutoff_delay_time, _ = handle_inconsistency(values, 'BolusCutOffDelayTime',
                                                            combined_errors)
  if status == "consistent":
    if isinstance(bolus_cutoff_delay_time, (list, tuple)) and len(bolus_cutoff_delay_time) >= 2:
      return f"from {bolus_cutoff_delay_time[0]}ms to {bolus_cutoff_delay_time[len(bolus_cutoff_delay_time) - 1]}ms"
    elif isinstance(bolus_cutoff_delay_time, (list, tuple)):
      return f"at {bolus_cutoff_delay_time[0]}ms"
    else:
      return f"at {bolus_cutoff_delay_time}ms"
  elif status == "inconsistent_common":
    return f"(inconsistent, {bolus_cutoff_delay_time}ms is the most common"
  else:
    return "(inconsistent, no common data)"


def format_background_suppression(values):
  if not values:
    return ''

  if all(isinstance(val, (int, float)) for val in values):
    values = list(map(str, values))
    if len(values) == 1:
      return values[0] + 'ms'
    elif len(values) == 2:
      return 'ms and '.join(values) + 'ms'
    else:
      return 'ms, '.join(values[:-1]) + 'ms, and ' + values[-1] + 'ms'
  else:
    return values


def format_acquisition_duration(duration):
  if isinstance(duration, (int, float)):
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    return f"{minutes}:{seconds:02d}min"
  return 'N/A'


def extract_and_format_unique_string_values(values, key):
  # Extract all values for the given key
  key_values = [entry[1] for entry in values.get(key, [])]

  # Normalize values to ensure they are strings
  normalized_values = [str(val) for val in key_values]

  # Count the occurrences of each unique value
  value_counter = Counter(normalized_values)

  # Sort the unique values by frequency (highest first)
  sorted_unique_values = [val for val, count in value_counter.most_common()]

  # Join the unique values with a separator ("/")
  formatted_values = "/".join(sorted_unique_values)

  return formatted_values


def generate_report(values, combined_major_errors, combined_errors, report_line_on_M0, M0_TR, slice_number):
  report_lines = []

  pld_type = handle_bolus_cutoff_technique(values, 'PLDType', combined_major_errors)
  total_acquired_pairs = extract_value(values, "TotalAcquiredPairs", combined_errors)

  pld_value = extract_value(values, 'PostLabelingDelay', combined_errors)
  if pld_type == "multi-PLD":
    if 'inconsistent' in pld_value:
      basic_pld_text = pld_value
    else:
      basic_pld_text = extract_unique_values_from_array(values.get('PostLabelingDelay')[0][1])
    extended_pld_text = handle_pld_values(values, combined_errors)
  elif pld_type == "single-PLD":
    basic_pld_text = pld_value
    extended_pld_text = f"{pld_value}ms"
  else:
    basic_pld_text = pld_value
    extended_pld_text = pld_value

  magnetic_field_strength = extract_value(values, "MagneticFieldStrength", combined_errors)
  manufacturer = extract_value(values, "Manufacturer", combined_errors)
  manufacturers_model_name = extract_and_format_unique_string_values(values,
                                                                     "ManufacturersModelName")
  asl_type = extract_value(values, "ArterialSpinLabelingType", combined_major_errors)
  mr_acq_type = extract_value(values, "MRAcquisitionType", combined_major_errors)
  pulse_seq_type = extract_value(values, "PulseSequenceType", combined_major_errors)

  if pulse_seq_type == "3Dgrase":
    pulse_seq_type = "GRASE"

  echo_time = extract_value(values, "EchoTime", combined_errors)
  repetition_time = extract_value(values, "RepetitionTimePreparation", combined_errors)
  flip_angle = extract_value(values, "FlipAngle", combined_errors)
  labeling_duration = extract_value(values, "LabelingDuration", combined_errors)

  voxel_size_1_2, voxel_size_3 = handle_voxel_size(values, combined_errors)

  bolus_cutoff_flag = handle_bolus_cutoff_flag(values, 'BolusCutOffFlag', combined_errors)
  bolus_cutoff_technique = handle_bolus_cutoff_technique(values, 'BolusCutOffTechnique',
                                                         combined_errors)
  bolus_cutoff_delay_time = handle_bolus_cutoff_delay_time(values, combined_errors)

  background_suppression = handle_bolus_cutoff_flag(values, 'BackgroundSuppression',
                                                    combined_errors)
  background_suppression_number_pulses = extract_value(values, 'BackgroundSuppressionNumberPulses',
                                                       combined_errors, report_range=True)
  background_suppression_pulse_time = extract_value(values, 'BackgroundSuppressionPulseTime',
                                                    combined_errors)

  acquisition_duration = extract_value(values, "AcquisitionDuration", combined_errors,
                                       format_duration=True)

  # Creating the report lines
  report_lines.append(
    f"ASL was acquired with on a {magnetic_field_strength}T {manufacturer}"
    f" {manufacturers_model_name} scanner using {pld_type} {asl_type} labeling and a "
    f"{mr_acq_type} {pulse_seq_type} readout with the following parameters: "
  )

  report_lines.append(
    f"TE = {echo_time}ms, TR = {repetition_time}ms, "
    f"flip angle {flip_angle} degrees, "
  )
  report_lines.append(
    f"in-plane resolution {voxel_size_1_2}mm2, "
  )
  report_lines.append(
    f"{slice_number} slices with {voxel_size_3}mm thickness, "
  )

  # Additional lines for PCASL
  if asl_type == 'PCASL':
    report_lines.append(
      f"labeling duration {labeling_duration}ms, "
    )
    report_lines.append(
      f"PLD {extended_pld_text}, "
    )

  # Additional lines for PASL
  if asl_type.upper() == 'PASL':
    report_lines.append(
      f"inversion time {extended_pld_text}, "
    )

    if bolus_cutoff_flag is not None:
      report_lines.append(
        f"{bolus_cutoff_flag} bolus saturation "
      )
      if bolus_cutoff_flag == "with":
        report_lines.append(
          f"using {bolus_cutoff_technique} pulse "
        )
        report_lines.append(
          f"applied {bolus_cutoff_delay_time} after the labeling, "
        )

  if background_suppression is not None:
    report_lines.append(f"{background_suppression} background suppression")
    if (background_suppression_number_pulses is not None and background_suppression_number_pulses
        != "N/A"):
      report_lines.append(
        f" with {background_suppression_number_pulses} pulses")
    if (background_suppression_pulse_time is not None and background_suppression_pulse_time !=
        "N/A"):
      report_lines.append(
        f" at {format_background_suppression(background_suppression_pulse_time)} after the start of labeling")
    report_lines.append(".")

  # Additional lines for total pairs and acquisition duration
  report_lines.append(
    f" In total, {total_acquired_pairs} control-label pairs were acquired"
  )
  if acquisition_duration != "N/A":
    report_lines.append(f" in a {acquisition_duration} time.")
  else:
    report_lines.append(".")

  report_lines.append(f" {report_line_on_M0}")
  if M0_TR:
    report_lines.append(f" TR for M0 is {M0_TR}.")

  # Join the lines into a single paragraph
  report_paragraph = "".join(line for line in report_lines)

  return report_paragraph


def extract_inconsistencies(error_map):
  inconsistency_errors = []
  fields_to_remove = []

  for field, errors in error_map.items():
    for error in errors:
      if "INCONSISTENCY" in error:
        inconsistency_errors.append(f"{field}: {error.replace('INCONSISTENCY: ', '')}\n")
        errors.remove(error)  # Remove the inconsistency error from the original list

      if not errors:
        fields_to_remove.append(field)

  # Remove fields that have no errors left
  for field in fields_to_remove:
    del error_map[field]
  return inconsistency_errors


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 8000))
  app.run(host='127.0.0.1', port=port)
