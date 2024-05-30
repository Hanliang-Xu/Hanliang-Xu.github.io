import json
import os

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from backend.json_validation import JSONValidator
from backend.validator import *

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
MAJOR_ERROR_REPORT = 'major_error_report.json'
ERROR_REPORT = 'error_report.json'
WARNING_REPORT = 'warning_report.json'
FINAL_REPORT = 'report.txt'

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)


@app.route('/')
def home():
  return "Welcome to my Flask App"


@app.route('/upload', methods=['POST'])
def upload_file():
  if 'json-file' not in request.files:
    return jsonify({"error": "No file part"}), 400
  file = request.files['json-file']
  if file.filename == '':
    return jsonify({"error": "No selected file"}), 400
  if file and file.filename.endswith('.json'):
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    data, error = read_json(filepath)
    if error:
      return jsonify({"error": error}), 400

    major_errors, errors, warnings, values = validate_json(data)

    save_json(major_errors, MAJOR_ERROR_REPORT)
    save_json(errors, ERROR_REPORT)
    save_json(warnings, WARNING_REPORT)

    if not major_errors:
      report = generate_report(values)

      # Convert the list to a single string
      report_str = "\n".join(report)
    else:
      report_str = "Major errors found, cannot generate report."

    return jsonify({
      "major_errors": major_errors,
      "errors": errors,
      "warnings": warnings,
      "report": report_str
    }), 200
  return jsonify({"error": "Invalid file type"}), 400


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


def read_json(file_path):
  try:
    with open(file_path, 'r') as file:
      data = json.load(file)
    return data, None
  except Exception as e:
    return None, f"Error reading file: {str(e)}"


def save_json(data, file_path):
  with open(file_path, 'w') as file:
    json.dump(data, file, indent=4)


def validate_json(data):
  major_error_schema = {
    "ArterialSpinLabelingType": StringValidator(
      allowed_values=["PASL", "(P)CASL", "PCASL", "CASL"]),
    "MRAcquisitionType": StringValidator(allowed_values=["2D", "3D"]),
    "PulseSequenceType": StringValidator()
  }
  required_validator_schema = {
    "BackgroundSuppression": BooleanValidator(),
    "M0Type": StringValidator(),
    "TotalAcquiredPairs": NumberValidator(min_error=0, enforce_integer=True),
    "AcquisitionVoxelSize": NumberArrayValidator(size_error=3),
    "LabelingDuration": NumberValidator(),
    "PostLabelingDelay": NumberOrNumberArrayValidator(),
    "InversionTime": NumberValidator(min_error=0),
    "BolusCutOffTechnique": StringValidator(),
    "BolusCutOffDelayTime": NumberOrNumberArrayValidator()
  }
  required_condition_schema = {
    "BackgroundSuppression": "all",
    "M0Type": "all",
    "TotalAcquiredPairs": "all",
    "AcquisitionVoxelSize": "all",
    "LabelingDuration": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "PostLabelingDelay": {"ArterialSpinLabelingType": ["PCASL", "CASL"]},
    "InversionTime": {"ArterialSpinLabelingType": "PASL"},
    "BolusCutOffTechnique": {"ArterialSpinLabelingType": "PASL"},
    "BolusCutOffDelayTime": {"ArterialSpinLabelingType": "PASL"}
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
    "LabelingSlabThickness": NumberValidator(min_error_include=0)
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
    "LabelingSlabThickness": {"ArterialSpinLabelingType": "PASL"}
  }

  validator = JSONValidator(major_error_schema, required_validator_schema,
                            required_condition_schema, recommended_validator_schema,
                            recommended_condition_schema)
  major_errors, errors, warnings, values = validator.validate(data)
  return major_errors, errors, warnings, values


def generate_report(values):
  report_lines = []

  # Check and process PostLabelingDelay
  if 'PostLabelingDelay' in values:
    pld = values['PostLabelingDelay']
    if isinstance(pld, list):
      if len(set(pld)) == 1:
        pld_text = f"single-PLD [{pld[0]}]"
        pld_value = pld[0]
      else:
        # Split long lists into multiple lines
        pld_text = "multi-PLD [\n"
        for i, val in enumerate(pld):
          if i > 0 and i % 10 == 0:
            pld_text += "\n"
          pld_text += f"{val}, "
        pld_text = pld_text.rstrip(", ") + "\n]"
        pld_value = ', '.join(map(str, pld))
    else:
      pld_text = f"single-PLD {pld}"
      pld_value = pld
  else:
    pld_text = "missing-PLD"
    pld_value = 'N/A'

  # Additional parameters
  asl_type = values.get('ArterialSpinLabelingType', 'N/A')
  mr_acq_type = values.get('MRAcquisitionType', 'N/A')
  pulse_seq_type = values.get('PulseSequenceType', 'N/A')
  echo_time = values.get('EchoTime', 'N/A')
  repetition_time = values.get('RepetitionTimePreparation', 'N/A')
  flip_angle = values.get('FlipAngle', 'N/A')

  # Extract voxel sizes safely
  acquisition_voxel_size = values.get('AcquisitionVoxelSize', ['N/A', 'N/A', 'N/A'])
  if isinstance(acquisition_voxel_size, list) and len(acquisition_voxel_size) >= 3:
    voxel_size_1_2 = f"{acquisition_voxel_size[0]}x{acquisition_voxel_size[1]}"
    voxel_size_3 = acquisition_voxel_size[2]
  else:
    voxel_size_1_2 = 'N/A'
    voxel_size_3 = 'N/A'

  labeling_duration = values.get('LabelingDuration', 'N/A')
  inversion_time = values.get('InversionTime', 'N/A')
  bolus_cutoff_flag = values.get('BolusCutOffFlag', 'N/A')
  bolus_cutoff_technique = values.get('BolusCutOffTechnique', 'N/A')
  bolus_cutoff_delay_time = values.get('BolusCutOffDelayTime', 'N/A')
  background_suppression = values.get('BackgroundSuppression', 'N/A')
  background_suppression_number_pulses = values.get('BackgroundSuppressionNumberPulses', 'N/A')
  background_suppression_pulse_time = values.get('BackgroundSuppressionPulseTime', 'N/A')
  total_acquired_pairs = values.get('TotalAcquiredPairs', 'N/A')
  acquisition_duration = values.get('AcquisitionDuration', 'N/A')

  # Convert acquisition duration from seconds to minutes and seconds
  if isinstance(acquisition_duration, (int, float)):
    minutes = int(acquisition_duration // 60)
    seconds = int(acquisition_duration % 60)
    acquisition_duration_str = f"{minutes}:{seconds:02d}min"
  else:
    acquisition_duration_str = 'N/A'

  # Creating the report lines
  report_lines.append(
    f"REQ: ASL was acquired with {pld_text} {asl_type} labeling and a "
    f"{mr_acq_type} {pulse_seq_type} readout with the following parameters:"
  )
  report_lines.append("")

  report_lines.append(
    f"REQ: TE {echo_time} ms, TR {repetition_time} ms, flip angle {flip_angle} degrees"
  )
  report_lines.append(
    f"REQ: in-plane resolution {voxel_size_1_2} mm2,"
  )
  report_lines.append(
    f"REQ: (TODO: number of slices) slices with {voxel_size_3} mm thickness,"
  )

  # Additional lines for PCASL
  if asl_type == 'PCASL':
    report_lines.append("")
    report_lines.append(
      f"REQ-PCASL: labeling duration {labeling_duration} ms,"
    )
    report_lines.append(
      f"REQ-PCASL: PLD {pld_value} ms,"
    )

  # Additional lines for PASL
  if asl_type.upper() == 'PASL':
    report_lines.append("")
    report_lines.append(
      f"REQ-PASL: inversion time {inversion_time} ms,"
    )
    if bolus_cutoff_flag is not None:
      if bolus_cutoff_flag:
        report_lines.append(
          f"REQ-PASL: with bolus saturation"
        )
        report_lines.append(
          f"REC-PASL: using {bolus_cutoff_technique} pulse"
        )
        report_lines.append(
          f"REC-PASL: applied at {bolus_cutoff_delay_time} ms after the labeling,"
        )
      else:
        report_lines.append(
          f"REQ-PASL: without bolus saturation"
        )

  report_lines.append("")
  # Additional lines for Background Suppression
  if background_suppression is not None:
    if background_suppression:
      report_lines.append(
        f"REQ: with background suppression"
      )
      report_lines.append(
        f"REC: with {background_suppression_number_pulses} pulses"
      )
      report_lines.append(
        f"REC: at {background_suppression_pulse_time} ms after the start of labeling."
      )
    else:
      report_lines.append(
        f"REQ: without background suppression"
      )

  report_lines.append("")
  # Additional lines for total pairs and acquisition duration
  report_lines.append(
    f"REQ: In total, {total_acquired_pairs} control-label pairs were acquired"
  )
  report_lines.append(
    f"REC: in a {acquisition_duration_str} time."
  )

  return report_lines


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 8000))
  app.run(host='127.0.0.1', port=port)
