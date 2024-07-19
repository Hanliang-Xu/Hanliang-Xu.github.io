def build_alias_mapping(schema):
  alias_mapping = {}
  for key, value in schema.items():
    # Add the primary key to the mapping
    alias_mapping[key] = value
    # Add any aliases to the mapping
    if 'aliases' in value:
      for alias in value['aliases']:
        alias_mapping[alias] = key
  return alias_mapping
