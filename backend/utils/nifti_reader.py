import os

import nibabel as nib
from werkzeug.datastructures import FileStorage


def read_nifti_file(nifti_file, upload_folder):
  try:
    if isinstance(nifti_file, FileStorage):
      if not nifti_file.filename.endswith(('.nii', '.nii.gz')):
        return None, f"Invalid file: {nifti_file.filename}"

      nifti_filepath = os.path.join(upload_folder, nifti_file.filename)
      os.makedirs(os.path.dirname(nifti_filepath), exist_ok=True)
      nifti_file.save(nifti_filepath)
    elif isinstance(nifti_file, str):
      if not nifti_file.endswith(('.nii', '.nii.gz')):
        return None, f"Invalid file: {nifti_file}"

      nifti_filepath = nifti_file  # Assuming the file path is already valid
    else:
      return None, "Unsupported file type"

    nifti_img = nib.load(nifti_filepath)
    slice_number = nifti_img.shape[2]
    return slice_number, None
  except Exception as e:
    return None, str(e)
