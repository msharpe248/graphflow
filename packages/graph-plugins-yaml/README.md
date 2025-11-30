# GraphFlow YAML Plugin

YAML manipulation plugin for GraphFlow providing steps for parsing, serializing, validating, and converting YAML data.

## Installation

```bash
pip install graphflow-plugins-yaml
```

## Features

- **Parse & Stringify**: Convert between YAML strings and Python objects
- **Multi-Document Support**: Parse and create YAML files with multiple documents (separated by `---`)
- **Validation**: Check if strings are valid YAML syntax
- **JSON Conversion**: Convert between YAML and JSON formats
- **Deep Merge**: Combine YAML objects with configurable merge strategies
- **Path-based Access**: Get and set values using dot-notation paths

## Available Steps

| Step | Type | Description |
|------|------|-------------|
| YAML Parse | `yaml.parse` | Parse a YAML string into a Python object |
| YAML Stringify | `yaml.stringify` | Convert a Python object to a YAML string |
| YAML Parse All | `yaml.parse-all` | Parse multi-document YAML into a list |
| YAML Stringify All | `yaml.stringify-all` | Convert a list to multi-document YAML |
| YAML Validate | `yaml.validate` | Check if a string is valid YAML |
| YAML to JSON | `yaml.to-json` | Convert YAML string to JSON string |
| JSON to YAML | `yaml.from-json` | Convert JSON string to YAML string |
| YAML Merge | `yaml.merge` | Deep merge two objects |
| YAML Get | `yaml.get` | Get a value using dot-notation path |
| YAML Set | `yaml.set` | Set a value using dot-notation path |

## Usage Examples

### Parsing YAML

```yaml
steps:
  - id: parse_config
    type: yaml.parse
    config:
      input: "{memory.yaml_content}"
    outputs:
      output: "{memory.config}"
```

### Multi-Document YAML

```yaml
steps:
  # Parse multiple YAML documents
  - id: parse_k8s_manifests
    type: yaml.parse-all
    config:
      input: "{memory.manifests_yaml}"
    outputs:
      output: "{memory.manifests}"
      count: "{memory.manifest_count}"

  # Create multi-document YAML
  - id: create_manifests
    type: yaml.stringify-all
    config:
      input: "{memory.deployments}"
    outputs:
      output: "{memory.yaml_output}"
```

### YAML Validation

```yaml
steps:
  - id: validate_yaml
    type: yaml.validate
    config:
      input: "{memory.user_input}"
    outputs:
      valid: "{memory.is_valid}"
      error: "{memory.validation_error}"
```

### JSON Conversion

```yaml
steps:
  # YAML to JSON
  - id: yaml_to_json
    type: yaml.to-json
    config:
      input: "{memory.yaml_data}"
      indent: 2
    outputs:
      output: "{memory.json_data}"

  # JSON to YAML
  - id: json_to_yaml
    type: yaml.from-json
    config:
      input: "{memory.json_data}"
    outputs:
      output: "{memory.yaml_data}"
```

### Deep Merge

```yaml
steps:
  - id: merge_configs
    type: yaml.merge
    config:
      base: "{memory.default_config}"
      overlay: "{memory.user_config}"
      strategy: deep  # Options: replace, append, deep
    outputs:
      output: "{memory.final_config}"
```

## Dependencies

- pyyaml >= 6.0

## Development

Run tests:

```bash
pytest tests/ -v
```

## License

MIT
