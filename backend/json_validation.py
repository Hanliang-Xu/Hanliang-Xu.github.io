import json


class JSONValidator:
  def __init__(self, major_error_schema, required_validator_schema, required_condition_schema,
               recommended_validator_schema, recommended_condition_schema):
    self.major_error_schema = major_error_schema
    self.required_validator_schema = required_validator_schema
    self.required_condition_schema = required_condition_schema
    self.recommended_validator_schema = recommended_validator_schema
    self.recommended_condition_schema = recommended_condition_schema

  def read_json(self, file_path: str):
    try:
      with open(file_path, 'r') as file:
        data = json.load(file)
      return data, None
    except Exception as e:
      return None, f"Error reading file: {str(e)}"

  def validate(self, data):
    major_errors, errors, warnings, values = {}, {}, {}, {}

    # Validate major errors first
    self.apply_schema(self.major_error_schema, data, major_errors, warnings, values, is_major=True)

    # Handle required fields
    self.apply_schema(self.required_validator_schema, data, errors, warnings, values,
                      is_required=True, condition_schema=self.required_condition_schema)
    # Handle recommended fields
    self.apply_schema(self.recommended_validator_schema, data, errors, warnings, values,
                      condition_schema=self.recommended_condition_schema)
    return major_errors, errors, warnings, values

  def apply_schema(self, validator_schema, data, errors, warnings, values,
                   is_required=False, is_major=False, condition_schema=None):
    condition_schema = condition_schema or {}
    for field, validator in validator_schema.items():
      condition = condition_schema.get(field,
                                       "all")  # Default to "all" if no specific condition is set
      if self.should_apply_validation(data, condition):
        if field not in data and (is_required or is_major):
          errors[field] = "Missing required parameter"
        elif field in data:
          error, warning = validator.validate(data[field])
          if error:
            errors[field] = error
          if warning:
            warnings[field] = warning
          values[field] = data[field]
        elif not is_required:
          values[field] = "Recommended to be specified"

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