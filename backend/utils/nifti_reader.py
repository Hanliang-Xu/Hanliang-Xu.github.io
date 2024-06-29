import os

import nibabel as nib


def read_nifti_file(nifti_file, upload_folder):
  try:
    if not nifti_file.filename.endswith(('.nii', '.nii.gz')):
      return None, f"Invalid file: {nifti_file.filename}"

    nifti_filepath = os.path.join(upload_folder, nifti_file.filename)
    os.makedirs(os.path.dirname(nifti_filepath), exist_ok=True)
    nifti_file.save(nifti_filepath)

    nifti_img = nib.load(nifti_filepath)
    slice_number = nifti_img.shape[2]
    return slice_number, None
  except Exception as e:
    return None, str(e)
