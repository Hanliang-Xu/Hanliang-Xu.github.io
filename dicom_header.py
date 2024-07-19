import pydicom

# Function to save the CSA Series Header Info to a text file
def save_csa_header_to_text_file(csa_header_bytes, file_path):
    try:
        csa_header_str = csa_header_bytes.decode('latin1')
        with open(file_path, 'w') as file:
            file.write(csa_header_str)
        print(f"CSA Series Header Info saved to {file_path}")
    except UnicodeDecodeError as e:
        print(f"Error decoding CSA Series Header Info: {e}")

# Replace 'path_to_dicom_file' with the actual path to your DICOM file
dicom_file_path = '/Users/leonslaptop/Desktop/GSoC/dcm_qa_asl/In/pCASL3Dve/20_jw_tgse_PCASL_singleShot_6PLDs_8Averages/0001.dcm'
dicom_data = pydicom.dcmread(dicom_file_path)

# Access the private tag (0029, 1020)
private_tag = dicom_data.get((0x0029, 0x1020), None)

if private_tag is not None:
    csa_series_header_info = private_tag.value
    print(f"CSA Series Header Info: {csa_series_header_info[:100]}...")  # Print the first 100 bytes as a preview
    output_text_file_path = '20_jw_tgse_PCASL_singleShot_6PLDs_8Averages.txt'
    save_csa_header_to_text_file(csa_series_header_info, output_text_file_path)
else:
    print("Tag (0029, 1020) not found in the DICOM file.")
