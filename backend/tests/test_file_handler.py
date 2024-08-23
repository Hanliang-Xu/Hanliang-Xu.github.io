import json
import os
from io import BytesIO

import pytest
from flask import Flask

from backend.routes import upload_routes, download_routes, home_routes
from backend.utils.config_loader import load_config


@pytest.fixture
def app():
  app = Flask(__name__)
  from flask_cors import CORS
  CORS(app)

  config = load_config('../config.yaml')
  app.config.update(config)

  app.register_blueprint(home_routes.home_bp)
  app.register_blueprint(upload_routes.upload_bp)
  app.register_blueprint(download_routes.download_bp)

  yield app


@pytest.fixture
def client(app):
  return app.test_client()


def load_test_case(test_case_folder):
  # Load the input files
  files_folder = os.path.join(test_case_folder, 'perf')
  data = load_test_files(files_folder)

  # Load the expected response
  expected_response_file = os.path.join(test_case_folder, 'expected_response.json')
  with open(expected_response_file, 'r') as f:
    expected_response = json.load(f)

  return data, expected_response


def load_test_files(folder_path):
  relevant_files = find_relevant_files(folder_path)
  nii_file = find_nii_file(folder_path)
  data = {}

  if nii_file:
    with open(os.path.join(folder_path, nii_file), 'rb') as f:
      data['nii-file'] = (BytesIO(f.read()), nii_file)

  for file_name in relevant_files:
    with open(os.path.join(folder_path, file_name), 'rb') as f:
      data.setdefault('files', []).append((BytesIO(f.read()), file_name))
      data.setdefault('filenames', []).append(file_name)

  dicom_files = [f for f in os.listdir(folder_path) if f.endswith('.dcm')]
  for dicom_file in dicom_files:
    with open(os.path.join(folder_path, dicom_file), 'rb') as f:
      data.setdefault('dcm-files', []).append((BytesIO(f.read()), dicom_file))

  return data


def find_relevant_files(folder_path):
  relevant_files = []

  # Step 1: Find all files ending with '_asl.json'
  asl_files = [item for item in os.listdir(folder_path) if item.endswith('_asl.json')]

  # Step 2: For each found '_asl.json' file, find and add relevant files with the same base name
  for asl_file in asl_files:
    relevant_files.append(asl_file)
    base_name = asl_file.replace('_asl.json', '')

    m0scan_file = f"{base_name}_m0scan.json"
    aslcontext_file = f"{base_name}_aslcontext.tsv"

    # Check if these files exist in the folder and add them to the list
    if m0scan_file in os.listdir(folder_path):
      relevant_files.append(m0scan_file)
    if aslcontext_file in os.listdir(folder_path):
      relevant_files.append(aslcontext_file)

  return relevant_files


def find_nii_file(folder_path):
  folder_items = os.listdir(folder_path)
  for item in folder_items:
    if item.endswith('asl.nii.gz') or item.endswith('asl.nii'):
      return item
  return None


### Step 3: **Parametrize the Test Cases**
@pytest.mark.parametrize("test_case_folder", [
  'PCASL_with_BS_time',
  'PASL_1',
  'PCASL_no_BS_time',
  'flip_angle_differ_by_more_than_1',
  'inconsistent_vascular_crushing',
  'vascular_crushing_VENC_test',
  'inconsistent_but_with_common_data',
  'multi_pld_differ_in_length',
  'multi_pld_differ_in_value',
  'string_difference',
  'number_of_pulse_difference_range',
  'extended_report_test_1',
  'extended_report_test_2',
  'extended_report_test_3',
  'warning_Echo_Time_0.1ms',
  'warning_voxel_size',
  'major_error_pcasl_3d',
  'm0_without_error_separate'
])
def test_handle_upload_cases(client, app, test_case_folder):
  # Path to the test case folder
  folder_path = os.path.join(os.path.dirname(__file__), 'test_data', test_case_folder)

  # Load test case data and expected response
  data, expected_response = load_test_case(folder_path)

  # Simulate a POST request to the /upload route with the loaded files
  with app.test_client() as client:
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    response_data = response.get_json()

    # Assertions to check that the response matches the expected output
    assert response_data == expected_response

  # Clean up any files that may have been created during the test
  upload_folder = app.config['paths']['upload_folder']
  if os.path.exists(upload_folder):
    for file_name in os.listdir(upload_folder):
      file_path = os.path.join(upload_folder, file_name)
      if os.path.isfile(file_path):
        os.unlink(file_path)
    os.rmdir(upload_folder)
