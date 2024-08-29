SECOND_TO_MILLISECOND = 1000


# Function to convert time values from seconds to milliseconds.
# This utility function takes a single value or a list of values, converts them from seconds to milliseconds,
# and rounds the result to an integer if it is close enough to an integer value (within a small tolerance).
# The function handles both individual numeric values (int or float) and lists of such values.
def convert_to_milliseconds(values):
  """Utility function to convert seconds to milliseconds and round close values to integers."""

  def round_if_close(val, decimal_places=3):
    rounded_val = round(val, decimal_places)
    if abs(val - round(val)) < 1e-6:
      return round(val)
    return rounded_val

  def convert_value(value):
    if isinstance(value, (int, float)):
      return round_if_close(value * SECOND_TO_MILLISECOND)
    elif isinstance(value, list):
      return [round_if_close(v * SECOND_TO_MILLISECOND) for v in value]
    return value

  if isinstance(values, list):
    return [convert_value(value) for value in values]
  else:
    return convert_value(values)
