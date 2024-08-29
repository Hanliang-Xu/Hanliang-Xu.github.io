"""
This module provides functionality to load and manage application configuration from a YAML file.

The `load_config` function reads the specified YAML configuration file, loads its contents into a
dictionary, and applies any necessary overrides using environment variables. Specifically, it checks
for the `PORT` environment variable and uses its value to override the server port defined in the
configuration file.

This setup allows the application to be configured through both a YAML file and environment variables,
which is useful in various deployment environments where environment-specific overrides are needed.
"""

import os

import yaml


def load_config(config_file):
  """
  Load the configuration from a YAML file.

  :param config_file: Path to the YAML configuration file.
  :return: Configuration dictionary.
  """
  try:
    with open(config_file, 'r') as file:
      config = yaml.safe_load(file)

      # Override with environment variables if they exist
      config['server']['port'] = int(os.getenv('PORT', config['server']['port']))

    return config
  except FileNotFoundError:
    # Raise an exception if the configuration file is not found
    raise Exception(f"Configuration file {config_file} not found.")
  except yaml.YAMLError as e:
    # Raise an exception if there is an error in parsing the YAML file
    raise Exception(f"Error parsing YAML configuration file: {str(e)}")
