from collections import Counter
from statistics import mode, median

import numpy as np


class BaseValidator:
  """
  Base class for all validators. Manages rules for major errors, errors, and warnings.
  """

  def __init__(self):
    self.major_error_rules = []
    self.error_rules = []
    self.warning_rules = []

  def add_major_error_rule(self, func, major_error_msg):
    """Adds a major error rule with a corresponding message."""
    self.major_error_rules.append((func, major_error_msg))

  def add_error_rule(self, func, error_msg):
    """Adds an error rule with a corresponding message."""
    self.error_rules.append((func, error_msg))

  def add_warning_rule(self, func, warning_msg):
    """Adds a warning rule with a corresponding message."""
    self.warning_rules.append((func, warning_msg))

  def validate(self, value):
    """Validates the value against the rules, returning the appropriate error or warning."""
    for func, major_error_msg in self.major_error_rules:
      if not func(value):
        return major_error_msg, major_error_msg, None, None, None, None
    for func, error_msg in self.error_rules:
      if not func(value):
        return None, None, error_msg, error_msg, None, None
    for func, warning_msg in self.warning_rules:
      if not func(value):
        return None, None, None, None, warning_msg, warning_msg
    return None, None, None, None, None, None


class NumberValidator(BaseValidator):
  """
  Validator for numerical values. Supports validation of ranges, integer enforcement, and warnings.
  """

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
      self.add_warning_rule(lambda x: x < max_warning, f"Value is unusually high ({max_warning})")


class StringValidator(BaseValidator):
  """
  Validator for string values. Validates against a list of allowed values, with optional major error enforcement.
  """

  def __init__(self, allowed_values=None, major_error=False):
    super().__init__()
    # Convert allowed_values to lower case for case-insensitive comparison
    if allowed_values:
      self.allowed_values = {value.lower() for value in allowed_values}
      if major_error:
        self.add_major_error_rule(lambda x: x.lower() in self.allowed_values,
                                  f"Value must be one of {allowed_values}, case-insensitive")
      else:
        self.add_error_rule(lambda x: x.lower() in self.allowed_values,
                            f"Value must be one of {allowed_values}, case-insensitive")


class NumberArrayValidator(BaseValidator):
  """
  Validator for arrays of numerical values. Supports size checks, range validation, and ascending order checks.
  """

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
  """
  Validator for single numbers or arrays of numbers. Combines the functionality of NumberValidator and NumberArrayValidator.
  """

  def __init__(self, size_error=None, min_error=None, max_error=None, min_warning=None,
               max_warning=None, min_error_include=None, check_ascending=False):
    super().__init__()
    self.number_validator = NumberValidator(
      min_error=min_error,
      max_error=max_error,
      min_warning=min_warning,
      max_warning=max_warning,
      min_error_include=min_error_include
    )
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
    """
    Validates either a single number or an array of numbers, returning appropriate messages for errors or warnings.
    """
    if isinstance(value, (int, float)):
      return self.number_validator.validate(value)
    elif isinstance(value, list):
      return self.array_validator.validate(value)
    else:
      return "Value must be a number or an array of numbers", None, None, None, None, None


class BooleanValidator(BaseValidator):
  """
  Validator for boolean values. Ensures the value is either True or False.
  """

  def __init__(self):
    super().__init__()
    self.add_error_rule(lambda x: isinstance(x, bool), "Value must be a boolean (True or False)")


class ConsistencyValidator(BaseValidator):
  """
  Validates the consistency of values across multiple datasets.
  Supports strings, booleans, floats, and arrays, with options for error and warning variations.
  """

  def __init__(self, validation_type, is_major=False, error_variation=None, warning_variation=None):
    """
    Initializes the validator with specific rules for consistency checking.
    """
    super().__init__()
    self.validation_type = validation_type
    self.is_major = is_major
    self.error_variation = error_variation
    self.warning_variation = warning_variation

  def validate(self, values_with_filenames):
    """
    Validates the provided values based on their type, returning error or warning messages for inconsistencies.
    """
    values = [value for value, _ in values_with_filenames]
    filenames = [filename for _, filename in values_with_filenames]
    if self.validation_type == "string":
      if len(set(values)) > 1:
        counts = Counter(values)
        summary = []
        summary_concise = []
        for value, count in counts.items():
          files_with_value = [filenames[i] for i, v in enumerate(values) if v == value]
          summary.append(f"'{value}' ({count}): {files_with_value}")
          summary_concise.append(f"'{value}'")
        summary_str = "; ".join(summary)
        summary_str_concise = ", ".join(summary_concise)
        if self.is_major:
          return f"INCONSISTENCY: {summary_str}", f"INCONSISTENCY: {summary_str_concise}", None, None, None, None
        else:
          return None, None, f"INCONSISTENCY: {summary_str}", f"INCONSISTENCY: {summary_str_concise}", None, None

    elif self.validation_type == "boolean":
      if not all(values) and any(values):
        counts = Counter(values)
        summary = []
        summary_concise = []
        for value, count in counts.items():
          files_with_value = [filenames[i] for i, v in enumerate(values) if v == value]
          summary.append(f"'{value}' ({count}): {files_with_value}")
          summary_concise.append(f"'{value}'")
        summary_str = "; ".join(summary)
        summary_str_concise = ", ".join(summary_concise)
        return None, None, f"INCONSISTENCY: {summary_str}", f"INCONSISTENCY: {summary_str_concise}", None, None

    elif self.validation_type == "floatOrArray":
      all_floats = all(isinstance(value, (int, float)) for value in values)
      all_arrays = all(isinstance(value, list) for value in values)
      mixed_values = not (all_floats or all_arrays)

      if all_floats:
        summary = self.calculate_summary(values, filenames)
        if self.error_variation is not None:
          dataset_min = min(values)
          dataset_max = max(values)
          if (dataset_max - dataset_min) > self.error_variation:
            return None, None, (
              f"INCONSISTENCY: Values vary more than allowed {self.error_variation}. {summary}"), (
              f"INCONSISTENCY: Values ({dataset_min}, {dataset_max}) vary more than the allowed variation {self.error_variation}."), None, None
          elif (self.warning_variation is not None and (
              dataset_max - dataset_min) > self.warning_variation):
            return None, None, None, None, (
              f"INCONSISTENCY: Values vary slightly within {self.error_variation}. {summary}"), (
              f"INCONSISTENCY: Values ({dataset_min}, {dataset_max}) vary slightly within the allowed variation {self.error_variation}.")
        elif self.error_variation is None and self.warning_variation is None:
          dataset_min = min(values)
          dataset_max = max(values)
          if len(set(values)) > 1:
            return (None, None, f"INCONSISTENCY: Values vary. {summary}",
                    f"INCONSISTENCY: Values vary. The range is ({dataset_min}, {dataset_max}).",
                    None, None)
      elif mixed_values:
        arrays_with_multiple_elements = [value for value in values if
                                         isinstance(value, list) and len(value) > 1]
        arrays_with_single_element = [value for value in values if
                                      isinstance(value, list) and len(value) == 1]
        float_values = [value for value in values if isinstance(value, (int, float))]

        if arrays_with_multiple_elements:
          single_value_sessions = [filenames[i] for i, v in enumerate(values) if
                                   isinstance(v, (int, float)) or (
                                       isinstance(v, list) and len(v) == 1)]
          array_sessions = [filenames[i] for i, v in enumerate(values) if
                            isinstance(v, list) and len(v) > 1]

          single_value_count = len(single_value_sessions)
          array_session_count = len(array_sessions)

          summary = (
            f"Single value sessions ({single_value_count}): {single_value_sessions}, "
            f"Array sessions ({array_session_count}): {array_sessions}"
          )
          return None, None, f"INCONSISTENCY: Mixed single values and arrays. {summary}", (
            f"INCONSISTENCY: Mixed single values and arrays."), None, None

        elif arrays_with_single_element and float_values:
          single_elements = [value[0] for value in arrays_with_single_element]
          combined_values = float_values + single_elements
          summary = self.calculate_summary(combined_values, filenames)
          dataset_min = min(combined_values)
          dataset_max = max(combined_values)
          if self.error_variation is not None and (
              dataset_max - dataset_min) > self.error_variation:
            return None, None, (
              f"INCONSISTENCY: Values vary more than allowed {self.error_variation}. {summary}"), (
              f"INCONSISTENCY: Values ({dataset_min}-{dataset_max}) vary more than allowed"
              f" {self.error_variation}."), None, None
          elif self.warning_variation is not None and (
              dataset_max - dataset_min) > self.warning_variation:
            return None, None, None, None, (
              f"INCONSISTENCY: Values vary slightly within {self.error_variation}. {summary}"), (
              f"INCONSISTENCY: Values ({dataset_min}-{dataset_max}) vary slightly within"
              f" {self.error_variation}.")
          elif self.error_variation is None and self.warning_variation is None:
            dataset_min = min(combined_values)
            dataset_max = max(combined_values)
            if len(set(combined_values)) > 1:
              return (None, None, f"INCONSISTENCY: Values vary. {summary}",
                      f"INCONSISTENCY: Values vary. The range is ({dataset_min}-{dataset_max})",
                      None, None)

      elif all_arrays:
        array_lengths = [len(array) for array in values]
        unique_lengths = set(array_lengths)

        if len(unique_lengths) > 1:
          length_files = {
            length: [filenames[i] for i in range(len(values)) if len(values[i]) == length] for
            length in unique_lengths}
          summary = f"Unique lengths: {length_files}"
          return (None, None, f"INCONSISTENCY: Inconsistent array lengths. {summary}",
                  f"INCONSISTENCY: Inconsistent array lengths.", None, None)
        else:
          first_length = len(values[0])
          for i in range(first_length):
            sub_values = [value[i] for value in values]
            array_min = min(sub_values)
            array_max = max(sub_values)
            if self.error_variation is not None and (array_max - array_min) > self.error_variation:
              return (None, None, (f"INCONSISTENCY: Values in arrays vary more than allowed"
                                   f" {self.error_variation} at index {i}. Values:"
                                   f" {list(zip(filenames, sub_values))}"),
                      f"INCONSISTENCY: Values in arrays vary more than allowed"
                      f" {self.error_variation} at index {i} ({array_min}-{array_max}).",
                      None, None)
            elif self.warning_variation is not None and (
                array_max - array_min) > self.warning_variation:
              return None, None, None, None, (
                f"INCONSISTENCY: Values in arrays vary slightly within"
                f" {self.error_variation} at index {i}. Values:"
                f" {list(zip(filenames, sub_values))}"), (f"INCONSISTENCY: Values in arrays vary"
                                                          f" slightly within"
                                                          f" {self.error_variation} at index"
                                                          f" {i} ({array_min}-{array_max}).")
            elif self.error_variation is None and self.warning_variation is None:
              array_min = min(sub_values)
              array_max = max(sub_values)
              if len(set(sub_values)) > 1:
                return None, None, (
                  f"INCONSISTENCY: Index {i} of arrays vary. Values:"
                  f" {list(zip(filenames, sub_values))}"), (f"INCONSISTENCY: Index {i} of arrays"
                                                            f"vary. The range is ({array_min}-"
                                                            f"{array_max})"), None, None
    return None, None, None, None, None, None

  def calculate_summary(self, values, filenames):
    """
    Generates a statistical summary of the dataset including mode, median, range, and identification of outliers.
    """
    try:
      mode_value = mode(values)
    except:
      mode_value = "No unique mode"

    median_value = median(values)
    dataset_min = min(values)
    dataset_max = max(values)
    range_value = (dataset_min, dataset_max)
    percentile_25 = np.percentile(values, 25)
    percentile_75 = np.percentile(values, 75)
    IQR = percentile_75 - percentile_25

    # Identifying outliers (values outside the 25-75 percentile range)
    outliers = [value for value in values if
                value < percentile_25 - 1.5 * IQR or value > percentile_75 + 1.5 * IQR]
    outliers_files = [filenames[i] for i, v in enumerate(values) if v in outliers]

    summary = (
      f"Mode: {mode_value}, "
      f"Median: {median_value}, "
      f"Range: {range_value}, "
      f"25-75 Percentile: ({percentile_25}, {percentile_75}), "
      f"Outliers: {list(zip(outliers_files, outliers))}"
    )

    return summary
