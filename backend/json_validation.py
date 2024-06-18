import json
from collections import defaultdict


class JSONValidator:
  def __init__(self, major_error_schema, required_validator_schema, required_condition_schema,
               recommended_validator_schema, recommended_condition_schema, consistency_schema):
    self.major_error_schema = major_error_schema
    self.required_validator_schema = required_validator_schema
    self.required_condition_schema = required_condition_schema
    self.recommended_validator_schema = recommended_validator_schema
    self.recommended_condition_schema = recommended_condition_schema
    self.consistency_schema = consistency_schema

  def read_json(self, file_path: str):
    try:
      with open(file_path, 'r') as file:
        data = json.load(file)
      return data, None
    except Exception as e:
      return None, f"Error reading file: {str(e)}"

  def validate(self, data_list, filenames):
    (combined_major_errors, combined_major_errors_concise, combined_errors, combined_errors_concise,
     combined_warnings, combined_warnings_concise, combined_values) = {}, {}, {}, {}, {}, {}, {}

    # Validate major errors first
    self.apply_schema(self.major_error_schema, data_list, combined_major_errors,
                      combined_major_errors_concise, combined_errors, combined_errors_concise,
                      combined_warnings, combined_warnings_concise, combined_values,
                      is_major=True, filenames=filenames)

    # Handle required fields
    self.apply_schema(self.required_validator_schema, data_list, combined_major_errors,
                      combined_major_errors_concise, combined_errors, combined_errors_concise,
                      combined_warnings, combined_warnings_concise, combined_values,
                      is_required=True, condition_schema=self.required_condition_schema,
                      filenames=filenames)
    # Handle recommended fields
    self.apply_schema(self.recommended_validator_schema, data_list, combined_major_errors,
                      combined_major_errors_concise, combined_errors, combined_errors_concise,
                      combined_warnings, combined_warnings_concise, combined_values,
                      condition_schema=self.recommended_condition_schema, filenames=filenames)

    return (combined_major_errors, combined_major_errors_concise, combined_errors,
            combined_errors_concise, combined_warnings, combined_warnings_concise, combined_values)

  def apply_schema(self, validator_schema, data_list, major_errors, major_errors_concise, errors,
                   errors_concise, warnings, warnings_concise, values, is_required=False,
                   is_major=False, condition_schema=None, filenames=None):
    condition_schema = condition_schema or {}
    aggregated_data = defaultdict(list)

    for field, validator in validator_schema.items():
      condition = condition_schema.get(field,
                                       "all")  # Default to "all" if no specific condition is set
      missing_files = []

      for i, data in enumerate(data_list):
        if self.should_apply_validation(data, condition):
          if field not in data and is_required:
            missing_files.append(filenames[i])
          elif field in data:
            aggregated_data[field].append((data[field], filenames[i]))

      (aggregated_major_errors, aggregated_major_errors_concise, aggregated_errors,
       aggregated_errors_concise, aggregated_warnings, aggregated_warnings_concise,
       aggregated_values) = [], [], [], [], [], [], []

      if missing_files and is_major:
        aggregated_major_errors.append({"Missing in files": missing_files})
        aggregated_major_errors_concise.append({"Missing in files": missing_files})
      elif missing_files and not is_major:
        aggregated_errors.append({"Missing in files": missing_files})
        aggregated_errors_concise.append({"Missing in files": missing_files})
      elif field in aggregated_data:
        # Consistency check
        values_to_check = aggregated_data[field]
        consistency_validator = self.consistency_schema.get(field)
        if consistency_validator:
          (consistency_major_error, consistency_major_error_concise, consistency_error,
           consistency_error_concise, consistency_warning, consistency_warning_concise)\
            = consistency_validator.validate(values_to_check)
          if consistency_major_error:
            aggregated_major_errors.append(consistency_major_error)
            aggregated_major_errors_concise.append(consistency_major_error_concise)
          if consistency_error:
            aggregated_errors.append(consistency_error)
            aggregated_errors_concise.append(consistency_error_concise)
          if consistency_warning:
            aggregated_warnings.append(consistency_warning)
            aggregated_warnings_concise.append(consistency_warning_concise)


      # Individual validation
      for value, filename in aggregated_data[field]:
        major_error, major_error_concise, error, error_concise, warning, warning_concise = (
          validator.validate(value))
        if major_error:
          aggregated_major_errors.append((filename, major_error))
          aggregated_major_errors_concise.append((filename, major_error_concise))
        if error:
          aggregated_errors.append((filename, error))
          aggregated_errors_concise.append((filename, error_concise))
        if warning:
          aggregated_warnings.append((filename, warning))
          aggregated_warnings_concise.append((filename,warning_concise))
        aggregated_values.append((filename, value))

      if aggregated_major_errors:
        major_errors[field] = aggregated_major_errors
        major_errors_concise[field] = aggregated_major_errors_concise
      if aggregated_errors:
        errors[field] = aggregated_errors
        errors_concise[field] = aggregated_errors_concise
      if aggregated_warnings:
        warnings[field] = aggregated_warnings
        warnings_concise[field] = aggregated_warnings_concise
      values[field] = aggregated_values

  def should_apply_validation(self, data, condition):
    if condition == "all":
      return True
    elif isinstance(condition, dict):
      for key, value in condition.items():
        if isinstance(value, list):
          if data.get(key) not in value:
            return False
        elif data.get(key) != value:
          return False
    return True
