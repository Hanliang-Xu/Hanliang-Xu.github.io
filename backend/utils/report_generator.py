from collections import Counter


def generate_report(values, combined_major_errors, combined_errors, report_line_on_M0, M0_TR,
                    global_pattern, total_acquired_pairs, slice_number):
  report_lines = []

  pld_type = handle_bolus_cutoff_technique(values, 'PLDType', combined_major_errors)
  # total_acquired_pairs = extract_value(values, "TotalAcquiredPairs", combined_errors)

  extended_pld_text = handle_pld_values(values, combined_errors, 'PostLabelingDelay', global_pattern)

  magnetic_field_strength = extract_value(values, "MagneticFieldStrength", combined_errors)
  manufacturer = extract_value(values, "Manufacturer", combined_errors)
  manufacturers_model_name = extract_and_format_unique_string_values(values,
                                                                     "ManufacturersModelName")
  asl_type = extract_value(values, "ArterialSpinLabelingType", combined_major_errors)
  mr_acq_type = extract_value(values, "MRAcquisitionType", combined_major_errors)
  pulse_seq_type = extract_value(values, "PulseSequenceType", combined_major_errors)

  if pulse_seq_type == "3Dgrase":
    pulse_seq_type = "GRASE"

  echo_time = extract_value(values, "EchoTime", combined_errors)
  repetition_time = handle_pld_values(values, combined_errors, 'RepetitionTimePreparation')

  flip_angle = extract_value(values, "FlipAngle", combined_errors)
  labeling_duration = extract_value(values, "LabelingDuration", combined_errors)

  voxel_size_1_2, voxel_size_3 = handle_voxel_size(values, combined_errors)

  bolus_cutoff_flag = handle_bolus_cutoff_flag(values, 'BolusCutOffFlag', combined_errors)
  bolus_cutoff_technique = handle_bolus_cutoff_technique(values, 'BolusCutOffTechnique',
                                                         combined_errors)
  bolus_cutoff_delay_time = handle_bolus_cutoff_delay_time(values, combined_errors)

  background_suppression = handle_bolus_cutoff_flag(values, 'BackgroundSuppression',
                                                    combined_errors)
  background_suppression_number_pulses = extract_value(values, 'BackgroundSuppressionNumberPulses',
                                                       combined_errors, report_range=True)
  background_suppression_pulse_time = extract_value(values, 'BackgroundSuppressionPulseTime',
                                                    combined_errors)

  acquisition_duration = extract_value(values, "AcquisitionDuration", combined_errors,
                                       format_duration=True)

  report_lines.append(
    f"ASL was acquired on a {magnetic_field_strength}T {manufacturer}"
    f" {manufacturers_model_name} scanner using {pld_type} {asl_type} labeling and a "
    f"{mr_acq_type} {pulse_seq_type} readout with the following parameters: "
  )

  report_lines.append(
    f"TE = {echo_time}ms, TR = {repetition_time}, "
    f"flip angle {flip_angle} degrees, "
  )
  report_lines.append(
    f"in-plane resolution {voxel_size_1_2}mm2, "
  )
  report_lines.append(
    f"{slice_number} slices with {voxel_size_3}mm thickness, "
  )

  if asl_type == 'PCASL':
    report_lines.append(
      f"labeling duration {labeling_duration}ms, "
    )
    report_lines.append(
      f"PLD {extended_pld_text}, "
    )

  if asl_type.upper() == 'PASL':
    report_lines.append(
      f"inversion time {extended_pld_text}, "
    )

    if bolus_cutoff_flag is not None:
      report_lines.append(
        f"{bolus_cutoff_flag} bolus saturation "
      )
      if bolus_cutoff_flag == "with":
        report_lines.append(
          f"using {bolus_cutoff_technique} pulse "
        )
        report_lines.append(
          f"applied {bolus_cutoff_delay_time} after the labeling, "
        )

  if background_suppression is not None:
    report_lines.append(f"{background_suppression} background suppression")
    if background_suppression_number_pulses is not None and background_suppression_number_pulses != "N/A":
      report_lines.append(
        f" with {background_suppression_number_pulses} pulses")
    if background_suppression_pulse_time is not None and background_suppression_pulse_time != "N/A":
      report_lines.append(
        f" at {format_background_suppression(background_suppression_pulse_time)} after the start of labeling")
    report_lines.append(".")

  if total_acquired_pairs == 1:
    report_lines.append(
      f" In total, {total_acquired_pairs} {global_pattern} pair was acquired"
    )
  else:
    report_lines.append(
      f" In total, {total_acquired_pairs} {global_pattern} pairs were acquired"
    )

  if acquisition_duration != "N/A":
    report_lines.append(f" in a {acquisition_duration} time.")
  else:
    report_lines.append(".")

  report_lines.append(f" {report_line_on_M0}")
  if M0_TR:
    report_lines.append(f" TR for M0 is {M0_TR}ms.")

  report_paragraph = "".join(line for line in report_lines)

  return report_paragraph


def extract_value(values, key, combined_errors, report_range=False, format_duration=False):
  status, most_common_value, value_range = handle_inconsistency(values, key, combined_errors)

  if format_duration and isinstance(most_common_value, (int, float)):
    most_common_value = format_acquisition_duration(most_common_value)

  if status == "consistent":
    return most_common_value
  elif status == "inconsistent_common":
    return f"(inconsistent, {most_common_value} is the most common data)" if not report_range else f"(inconsistent, {most_common_value} is the most common data, {value_range})"
  else:
    return f"(inconsistent, no common data, {value_range})" if report_range else "(inconsistent, no common data)"


def handle_inconsistency(values, key, combined_errors):
  inconsistencies = [
    error for error in combined_errors.get(key, []) if "INCONSISTENCY" in error
  ]
  value_range = None

  if inconsistencies:
    key_values = [entry[1] for entry in values.get(key, [])]

    normalized_values = []
    for val in key_values:
      if isinstance(val, list):
        if len(val) == 1:
          normalized_values.append(val[0])
        else:
          normalized_values.append(tuple(val))
      else:
        normalized_values.append(val)

    counter = Counter(normalized_values)
    most_common_value, count = counter.most_common(1)[0]

    flattened_values = [item for sublist in normalized_values for item in
                        (sublist if isinstance(sublist, tuple) else [sublist])]
    value_range = f"Range: {min(flattened_values)}-{max(flattened_values)}"

    if count > len(normalized_values) // 2:
      return "inconsistent_common", most_common_value, value_range
    else:
      return "inconsistent_no_common", None, value_range
  else:
    first_value = values.get(key, [['N/A']])
    if first_value and isinstance(first_value[0], list) and len(first_value[0]) > 1:
      value = tuple(first_value[0])
    else:
      value = first_value[0][1] if first_value else 'N/A'

    return "consistent", value, value_range


def handle_bolus_cutoff_technique(values, key, combined_errors):
  status, technique = handle_string_inconsistency(values, key, combined_errors)
  if status == "consistent":
    return technique
  elif status == "inconsistent_common":
    return f"(inconsistent, {technique} is the most common)"
  else:
    return "(inconsistent, no common data)"


def handle_string_inconsistency(values, key, combined_errors):
  inconsistencies = [
    error for error in combined_errors.get(key, []) if "INCONSISTENCY" in error
  ]
  if inconsistencies:
    key_values = [entry[1] for entry in values.get(key, [])]
    normalized_values = [str(val) for val in key_values]
    counter = Counter(normalized_values)
    most_common_value, count = counter.most_common(1)[0]
    if count > len(normalized_values) // 2:
      return "inconsistent_common", most_common_value
    else:
      return "inconsistent_no_common", None
  else:
    first_value = values.get(key, [['N/A']])
    return "consistent", str(first_value[0][1]) if first_value else 'N/A'


def handle_voxel_size(values, combined_errors):
  status, acquisition_voxel_size, _ = handle_inconsistency(values, 'AcquisitionVoxelSize',
                                                           combined_errors)
  if status == "consistent":
    if isinstance(acquisition_voxel_size, (list, tuple)) and len(acquisition_voxel_size) >= 3:
      voxel_size_1_2 = f"{acquisition_voxel_size[0]}x{acquisition_voxel_size[1]}"
      voxel_size_3 = acquisition_voxel_size[2]
    else:
      voxel_size_1_2 = 'N/A'
      voxel_size_3 = 'N/A'
  elif status == "inconsistent_common":
    if isinstance(acquisition_voxel_size, (list, tuple)) and len(acquisition_voxel_size) >= 3:
      voxel_size_1_2 = f"(inconsistent, {acquisition_voxel_size[0]}x{acquisition_voxel_size[1]} is the most common)"
      voxel_size_3 = f"(inconsistent, {acquisition_voxel_size[2]} is the most common)"
    else:
      voxel_size_1_2 = 'N/A'
      voxel_size_3 = 'N/A'
  else:
    voxel_size_1_2 = 'N/A (inconsistent, with no common data.)'
    voxel_size_3 = 'N/A (inconsistent, with no common data.)'
  return voxel_size_1_2, voxel_size_3


def handle_pld_values(values, combined_errors, key, global_pattern=False):
  status, pld_values, _ = handle_inconsistency(values, key, combined_errors)

  def format_pld_array(pld_array):
    pld_counter = Counter(pld_array)
    if global_pattern != "deltam":
      formatted_pld = ', '.join(
        [f"{pld}ms ({count // 2} {'repeat' if (count // 2) == 1 else 'repeats'})" for pld, count in
         sorted(pld_counter.items())]
      )
    else:
      formatted_pld = ', '.join(
        [f"{pld}ms ({count} {'repeat' if count == 1 else 'repeats'})" for pld, count in
         sorted(pld_counter.items())]
      )
    return formatted_pld

  if status == "consistent":
    if isinstance(pld_values, (list, tuple)):
      unique_values = set(pld_values)
      if len(unique_values) == 1:
        extended_pld_text = f"{unique_values.pop()}ms"
      else:
        extended_pld_text = format_pld_array(pld_values)
    elif isinstance(pld_values, (int, float)):
      extended_pld_text = f"{pld_values}ms"
    else:
      extended_pld_text = 'N/A'
  elif status == "inconsistent_common":
    if isinstance(pld_values, (list, tuple)):
      unique_values = set(pld_values)
      if len(unique_values) == 1:
        extended_pld_text = f"(inconsistent, {unique_values.pop()}ms is the most common)"
      else:
        extended_pld_text = f"(inconsistent, {format_pld_array(pld_values)} is the most common)"
    elif isinstance(pld_values, (int, float)):
      extended_pld_text = f"(inconsistent, {pld_values}ms is the most common)"
    else:
      extended_pld_text = 'N/A'
  else:
    extended_pld_text = "(inconsistent, no common data)"

  return extended_pld_text


def handle_bolus_cutoff_flag(values, key, combined_errors):
  status, flag = handle_boolean_inconsistency(values, key, combined_errors)
  if status == "consistent":
    return "without" if not flag else "with"
  elif status == "inconsistent_common":
    return f"(inconsistent, {'without' if not flag else 'with'} is the most common)"
  else:
    return "(inconsistent, no common data)"


def handle_boolean_inconsistency(values, key, combined_errors):
  inconsistencies = [
    error for error in combined_errors.get(key, []) if "INCONSISTENCY" in error
  ]
  if inconsistencies:
    key_values = [entry[1] for entry in values.get(key, [])]
    normalized_values = [bool(val) for val in key_values]
    counter = Counter(normalized_values)
    most_common_value, count = counter.most_common(1)[0]
    if count > len(normalized_values) // 2:
      return "inconsistent_common", most_common_value
    else:
      return "inconsistent_no_common", None
  else:
    first_value = values.get(key, [['N/A']])
    return "consistent", bool(first_value[0][1]) if first_value else 'N/A'


def handle_bolus_cutoff_delay_time(values, combined_errors):
  status, bolus_cutoff_delay_time, _ = handle_inconsistency(values, 'BolusCutOffDelayTime',
                                                            combined_errors)
  if status == "consistent":
    if isinstance(bolus_cutoff_delay_time, (list, tuple)) and len(bolus_cutoff_delay_time) >= 2:
      return f"from {bolus_cutoff_delay_time[0]}ms to {bolus_cutoff_delay_time[len(bolus_cutoff_delay_time) - 1]}ms"
    elif isinstance(bolus_cutoff_delay_time, (list, tuple)):
      return f"at {bolus_cutoff_delay_time[0]}ms"
    else:
      return f"at {bolus_cutoff_delay_time}ms"
  elif status == "inconsistent_common":
    return f"(inconsistent, {bolus_cutoff_delay_time}ms is the most common"
  else:
    return "(inconsistent, no common data)"


def format_background_suppression(values):
  if not values:
    return ''

  if all(isinstance(val, (int, float)) for val in values):
    values = list(map(str, values))
    if len(values) == 1:
      return values[0] + 'ms'
    elif len(values) == 2:
      return 'ms and '.join(values) + 'ms'
    else:
      return 'ms, '.join(values[:-1]) + 'ms, and ' + values[-1] + 'ms'
  else:
    return values


def format_acquisition_duration(duration):
  if isinstance(duration, (int, float)):
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    return f"{minutes}:{seconds:02d}min"
  return 'N/A'


def extract_and_format_unique_string_values(values, key):
  key_values = [entry[1] for entry in values.get(key, [])]
  normalized_values = [str(val) for val in key_values]
  value_counter = Counter(normalized_values)
  sorted_unique_values = [val for val, count in value_counter.most_common()]
  formatted_values = "/".join(sorted_unique_values)
  return formatted_values


def extract_unique_values_from_array(values):
  unique_values = sorted(set(values))
  return ', '.join(map(str, unique_values))


def extract_inconsistencies(error_map):
  inconsistency_errors = []
  fields_to_remove = []

  for field, errors in error_map.items():
    for error in errors:
      if "INCONSISTENCY" in error:
        inconsistency_errors.append(f"{field}: {error.replace('INCONSISTENCY: ', '')}\n")
        errors.remove(error)

      if not errors:
        fields_to_remove.append(field)

  for field in fields_to_remove:
    del error_map[field]
  return inconsistency_errors
