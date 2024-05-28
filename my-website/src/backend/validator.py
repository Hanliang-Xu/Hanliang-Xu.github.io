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
