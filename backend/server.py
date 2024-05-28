import json
import os

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

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)


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
      with open(FINAL_REPORT, 'w') as file:
        file.write(report)
    else:
      report = "Major errors found, cannot generate report."

    return jsonify({
      "major_errors": major_errors,
      "errors": errors,
      "warnings": warnings,
      "report": report
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

  # Example extraction and formatting logic (add your own parameters and conditions)
  if 'PostLabelingDelay' in values:
    pld = values['PostLabelingDelay']
    if isinstance(pld, list) and len(set(pld)) == 1:
      pld = pld[0]
    report_lines.append(f"REQ: ASL was acquired with single-PLD [{pld}]")

  if 'ArterialSpinLabelingType' in values:
    report_lines.append(f"PCASL [{values['ArterialSpinLabelingType']}] labeling")

  if 'MRAcquisitionType' in values:
    report_lines.append(
      f"a {values['MRAcquisitionType']} [{values['MRAcquisitionType']}] EPI [PulseSequenceType] readout")

  # Continue extracting and formatting other parameters...

  report = "\n".join(report_lines)
  return report


if __name__ == '__main__':
  app.run(port=5001)
