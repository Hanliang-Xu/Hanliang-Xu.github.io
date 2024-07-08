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
    raise Exception(f"Configuration file {config_file} not found.")
  except yaml.YAMLError as e:
    raise Exception(f"Error parsing YAML configuration file: {str(e)}")
