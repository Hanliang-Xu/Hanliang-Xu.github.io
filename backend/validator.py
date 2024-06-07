class BaseValidator:
  def __init__(self):
    self.error_rules = []
    self.warning_rules = []

  def add_error_rule(self, func, error_msg):
    self.error_rules.append((func, error_msg))

  def add_warning_rule(self, func, warning_msg):
    self.warning_rules.append((func, warning_msg))

  def validate(self, value):
    for func, error_msg in self.error_rules:
      if not func(value):
        return error_msg, None
    for func, warning_msg in self.warning_rules:
      if not func(value):
        return None, warning_msg
    return None, None


class NumberValidator(BaseValidator):
  def __init__(self, min_error=None, max_error=None, min_warning=None, max_warning=None,
               min_error_include=None, max_error_include=None, enforce_integer=False):
    super().__init__()

    if enforce_integer:
      self.add_error_rule(lambda x: isinstance(x, int), "Value must be an integer")

    if min_error is not None:
      self.add_error_rule(lambda x: x > min_error, f"Value must be > {min_error}")
    if max_error is not None:
      self.add_error_rule(lambda x: x < max_error, f"Value must be < {max_error}")
    if min_error_include is not None:
      self.add_error_rule(lambda x: x >= min_error_include, f"Value must be >= {min_error_include}")
    if max_error_include is not None:
      self.add_error_rule(lambda x: x <= max_error_include, f"Value must be <= {max_error_include}")
    if min_warning is not None:
      self.add_warning_rule(lambda x: x > min_warning, f"Value is unusually low ({min_warning})")
    if max_warning is not None:
      self.add_warning_rule(lambda x: x < max_warning,
                            f"Value is unusually high ({max_warning})")


class StringValidator(BaseValidator):
  def __init__(self, allowed_values=None):
    super().__init__()
    # Convert allowed_values to lower case for case-insensitive comparison
    if allowed_values:
      # Store the allowed values as a set of lower case strings for efficient membership checking
      self.allowed_values = {value.lower() for value in allowed_values}
      self.add_error_rule(lambda x: x.lower() in self.allowed_values,
                          f"Value must be one of {allowed_values}, case-insensitive")


class NumberArrayValidator(BaseValidator):
  def __init__(self, size_error=None, min_error=None, max_error=None, min_warning=None,
               max_warning=None, min_error_include=None, check_ascending=False):
    super().__init__()

    # Validate that the array has a specific number of elements
    if size_error is not None:
      self.add_error_rule(
        lambda x: isinstance(x, list) and all(isinstance(i, (int, float)) for i in x) and len(
          x) == size_error,
        f"Array must consist of exactly {size_error} numbers")

    if min_error is not None:
      self.add_error_rule(lambda x: all(i > min_error for i in x if isinstance(i, (int, float))),
                          f"All numbers must be > {min_error}")
    if max_error is not None:
      self.add_error_rule(lambda x: all(i < max_error for i in x if isinstance(i, (int, float))),
                          f"All numbers must be < {max_error}")
    if min_error_include is not None:
      self.add_error_rule(
        lambda x: all(i >= min_error_include for i in x if isinstance(i, (int, float))),
        f"All numbers must be >= {min_error_include}")
    if min_warning is not None:
      self.add_warning_rule(
        lambda x: all(i > min_warning for i in x if isinstance(i, (int, float))),
        f"Some numbers may be unusually low ({min_warning})")
    if max_warning is not None:
      self.add_warning_rule(
        lambda x: all(i < max_warning for i in x if isinstance(i, (int, float))),
        f"Some numbers may be unusually high ({max_warning})")

    # Optionally validate that the numbers in the array are in ascending order
    if check_ascending:
      self.add_error_rule(
        lambda x: sorted(x) == x,
        "Numbers in the array are not in ascending order")


class NumberOrNumberArrayValidator(BaseValidator):
  def __init__(self, size_error=None, min_error=None, max_error=None, min_warning=None,
               max_warning=None, min_error_include=None, check_ascending=False):
    super().__init__()
    # Create an instance of NumberArrayValidator
    self.array_validator = NumberArrayValidator(
      size_error=size_error,
      min_error=min_error,
      max_error=max_error,
      min_warning=min_warning,
      max_warning=max_warning,
      min_error_include=min_error_include,
      check_ascending=check_ascending
    )

  def validate(self, value):
    # Convert a single number to a list if it is not already a list
    if isinstance(value, (int, float)):
      value = [value]

    # Use the existing NumberArrayValidator to perform the validation
    return self.array_validator.validate(value)


class BooleanValidator(BaseValidator):
  def __init__(self):
    super().__init__()
    self.add_error_rule(lambda x: isinstance(x, bool), "Value must be a boolean (True or False)")


class ConsistencyValidator:
  def __init__(self, type, range=None, error_variation=None, warning_variation=None):
    self.type = type
    self.range = range
    self.error_variation = error_variation
    self.warning_variation = warning_variation

  def validate(self, values_with_filenames):
    values = [value for value, _ in values_with_filenames]
    filenames = [filename for _, filename in values_with_filenames]

    if self.type == "string":
      if len(set(values)) > 1:
        return f"Inconsistent values: {list(zip(filenames, values))}", None
    elif self.type == "float":
      if self.range is not None:
        min_val, max_val = self.range
        out_of_range = [(filename, value) for value, filename in values_with_filenames if
                        value < min_val or value > max_val]
        if out_of_range:
          return f"Values out of range {self.range}: {out_of_range}", None

      # Check for allowable variation within the dataset
      dataset_min = min(values)
      dataset_max = max(values)
      if self.error_variation is not None and (dataset_max - dataset_min) > self.error_variation:
        return f"Values vary more than allowed {self.error_variation}: {list(zip(filenames, values))}", None
      elif self.warning_variation is not None and (
          dataset_max - dataset_min) > self.warning_variation:
        return None, f"Values vary slightly within {self.warning_variation}: {list(zip(filenames, values))}"
    elif self.type == "boolean":
      if not all(values) and any(values):
        return f"Inconsistent boolean values: {list(zip(filenames, values))}", None
    elif self.type == "array":
      # Check if all arrays are the same length
      first_length = len(values[0])
      for array, filename in zip(values, filenames):
        if len(array) != first_length:
          example1 = (filenames[0], values[0])
          example2 = (filename, array)
          return f"Inconsistent array lengths. Example: {example1}, {example2}", None

      # Check if all arrays are exactly the same
      first_array = values[0]
      for array, filename in zip(values, filenames):
        if array != first_array:
          example1 = (filenames[0], values[0])
          example2 = (filename, array)
          return f"Inconsistent arrays. Example: {example1}, {example2}", None

      return None, None
    elif self.type == "array_of_value_and_array":
      if all(isinstance(value, (int, float)) for value in values):
        if self.range is not None:
          min_val, max_val = self.range
          out_of_range = [(filename, value) for value, filename in values_with_filenames if
                          value < min_val or value > max_val]
          if out_of_range:
            return f"Values out of range {self.range}: {out_of_range}", None

        dataset_min = min(values)
        dataset_max = max(values)
        if self.error_variation is not None and (dataset_max - dataset_min) > self.error_variation:
          return f"Values vary more than allowed {self.error_variation}: {list(zip(filenames, values))}", None
        elif self.warning_variation is not None and (
            dataset_max - dataset_min) > self.warning_variation:
          return None, f"Values vary slightly within {self.warning_variation}: {list(zip(filenames, values))}"
      elif all(isinstance(value, list) for value in values):
        # All elements are arrays, check for consistency
        if not all(len(value) == len(values[0]) for value in values):
          return f"Inconsistent array lengths: {list(zip(filenames, values))}", None
        for i in range(len(values[0])):
          sub_values = [value[i] for value in values]
          if len(set(sub_values)) > 1:
            return f"Inconsistent values in arrays at index {i}: {list(zip(filenames, sub_values))}", None
      else:
        # Mixed values and arrays, add warning
        return None, f"Mixed values and arrays: {list(zip(filenames, values))}"

    return None, None
