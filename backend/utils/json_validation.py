import json
from collections import defaultdict

from .validators import NumberValidator, StringValidator, BooleanValidator, NumberArrayValidator, \
  NumberOrNumberArrayValidator, ConsistencyValidator


def create_validators_from_schema(schema):
  validator_classes = {
    'NumberValidator': NumberValidator,
    'StringValidator': StringValidator,
    'BooleanValidator': BooleanValidator,
    'NumberArrayValidator': NumberArrayValidator,
    'NumberOrNumberArrayValidator': NumberOrNumberArrayValidator,
    'ConsistencyValidator': ConsistencyValidator
  }

  validators = {}
  for key, spec in schema.items():
    spec_type = spec['type']
    validator_class = validator_classes[spec_type]

    # Handle ConsistencyValidator separately
    if spec_type == 'ConsistencyValidator':
      validation_type = spec['validation_type']
      is_major = spec.get('is_major', False)
      error_variation = spec.get('error_variation')
      warning_variation = spec.get('warning_variation')
      validators[key] = validator_class(validation_type, is_major=is_major,
                                        error_variation=error_variation,
                                        warning_variation=warning_variation)

    # Handle NumberValidator
    elif spec_type == 'NumberValidator':
      validators[key] = validator_class(
        min_error=spec.get('min_error'),
        max_error=spec.get('max_error'),
        min_warning=spec.get('min_warning'),
        max_warning=spec.get('max_warning'),
        min_error_include=spec.get('min_error_include'),
        max_error_include=spec.get('max_error_include'),
        enforce_integer=spec.get('enforce_integer', False)
      )

    # Handle StringValidator
    elif spec_type == 'StringValidator':
      validators[key] = validator_class(
        allowed_values=spec.get('allowed_values'),
        major_error=spec.get('major_error', False)
      )

    # Handle BooleanValidator
    elif spec_type == 'BooleanValidator':
      validators[key] = validator_class()

    # Handle NumberArrayValidator
    elif spec_type == 'NumberArrayValidator':
      validators[key] = validator_class(
        size_error=spec.get('size_error'),
        min_error=spec.get('min_error'),
        max_error=spec.get('max_error'),
        min_warning=spec.get('min_warning'),
        max_warning=spec.get('max_warning'),
        min_error_include=spec.get('min_error_include'),
        check_ascending=spec.get('check_ascending', False)
      )

    # Handle NumberOrNumberArrayValidator
    elif spec_type == 'NumberOrNumberArrayValidator':
      validators[key] = validator_class(
        size_error=spec.get('size_error'),
        min_error=spec.get('min_error'),
        max_error=spec.get('max_error'),
        min_warning=spec.get('min_warning'),
        max_warning=spec.get('max_warning'),
        min_error_include=spec.get('min_error_include'),
        check_ascending=spec.get('check_ascending', False)
      )

    # Default handling for any other validator classes
    else:
      validators[key] = validator_class(**spec)

  return validators


class JSONValidator:
  def __init__(self, major_error_schema, required_validator_schema, required_condition_schema,
               recommended_validator_schema, recommended_condition_schema, consistency_schema):
    self.major_error_schema = create_validators_from_schema(major_error_schema)
    self.required_validator_schema = create_validators_from_schema(required_validator_schema)
    self.required_condition_schema = required_condition_schema
    self.recommended_validator_schema = create_validators_from_schema(recommended_validator_schema)
    self.recommended_condition_schema = recommended_condition_schema
    self.consistency_schema = create_validators_from_schema(consistency_schema)

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

    self.apply_schema(self.major_error_schema, data_list, combined_major_errors,
                      combined_major_errors_concise, combined_errors, combined_errors_concise,
                      combined_warnings, combined_warnings_concise, combined_values,
                      is_major=True, filenames=filenames)

    self.apply_schema(self.required_validator_schema, data_list, combined_major_errors,
                      combined_major_errors_concise, combined_errors, combined_errors_concise,
                      combined_warnings, combined_warnings_concise, combined_values,
                      is_required=True, condition_schema=self.required_condition_schema,
                      filenames=filenames)

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
      condition = condition_schema.get(field, "all")
      missing_files = []

      for i, data in enumerate(data_list):
        if self.should_apply_validation(data, condition):
          if field not in data and (is_major or is_required):
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
        values_to_check = aggregated_data[field]
        consistency_validator = self.consistency_schema.get(field)
        if consistency_validator:
          (consistency_major_error, consistency_major_error_concise, consistency_error,
           consistency_error_concise, consistency_warning, consistency_warning_concise) \
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

        def append_error(aggregation, error_message, filename):
          found = False
          for error_entry in aggregation:
            if error_message in error_entry:
              error_entry[error_message].append(filename)
              found = True
              break
          if not found:
            aggregation.append({error_message: [filename]})

        for value, filename in aggregated_data[field]:
          major_error, major_error_concise, error, error_concise, warning, warning_concise = validator.validate(
            value)

          if major_error:
            append_error(aggregated_major_errors, major_error, filename)
            append_error(aggregated_major_errors_concise, major_error_concise, filename)
          if error:
            append_error(aggregated_errors, error, filename)
            append_error(aggregated_errors_concise, error_concise, filename)
          if warning:
            append_error(aggregated_warnings, warning, filename)
            append_error(aggregated_warnings_concise, warning_concise, filename)
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
