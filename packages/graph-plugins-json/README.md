# GraphFlow JSON Plugin

JSON manipulation plugin for GraphFlow providing steps for parsing, querying, transforming, and validating JSON data.

## Installation

```bash
pip install graphflow-plugins-json
```

Or install with development dependencies:

```bash
pip install graphflow-plugins-json[dev]
```

## Features

- **Parse & Stringify**: Convert between JSON strings and Python objects
- **JSONPath Queries**: Extract data using JSONPath expressions
- **Deep Merge**: Combine JSON objects with configurable merge strategies
- **Schema Validation**: Validate JSON against JSON Schema
- **Path-based Access**: Get and set values using dot-notation paths
- **Object Inspection**: Extract keys and values from JSON objects

## Available Steps

| Step | Type | Description |
|------|------|-------------|
| JSON Parse | `json.parse` | Parse a JSON string into a Python object |
| JSON Stringify | `json.stringify` | Convert a Python object to a JSON string |
| JSON Path | `json.path` | Extract values using JSONPath expressions |
| JSON Merge | `json.merge` | Deep merge multiple JSON objects |
| JSON Schema Validate | `json.schema-validate` | Validate JSON against a JSON Schema |
| JSON Get | `json.get` | Get a value using dot-notation path |
| JSON Set | `json.set` | Set a value using dot-notation path |
| JSON Keys | `json.keys` | Get all keys from a JSON object |
| JSON Values | `json.values` | Get all values from a JSON object |

## Usage Examples

### Parsing JSON

```yaml
steps:
  - id: parse_response
    type: json.parse
    config:
      input: "{memory.api_response}"
    outputs:
      output: "{memory.data}"
```

### JSONPath Query

```yaml
steps:
  - id: extract_authors
    type: json.path
    config:
      input: "{memory.book_data}"
      expression: "$.store.book[*].author"
    outputs:
      output: "{memory.authors}"
      found: "{memory.has_authors}"
```

### Deep Merge

```yaml
steps:
  - id: merge_configs
    type: json.merge
    config:
      base: "{memory.default_config}"
      overlay: "{memory.user_config}"
      strategy: deep  # Options: replace, append, deep
    outputs:
      output: "{memory.final_config}"
```

### Schema Validation

```yaml
steps:
  - id: validate_user
    type: json.schema-validate
    config:
      input: "{memory.user_data}"
      schema:
        type: object
        properties:
          name:
            type: string
          email:
            type: string
            format: email
        required:
          - name
          - email
    outputs:
      valid: "{memory.is_valid}"
      errors: "{memory.validation_errors}"
```

### Get/Set Values

```yaml
steps:
  - id: get_user_name
    type: json.get
    config:
      input: "{memory.user}"
      path: "profile.name"
      default: "Anonymous"
    outputs:
      output: "{memory.user_name}"
      found: "{memory.name_found}"

  - id: update_user
    type: json.set
    config:
      input: "{memory.user}"
      path: "profile.updated_at"
      value: "{memory.timestamp}"
    outputs:
      output: "{memory.updated_user}"
```

## Dependencies

- jsonpath-ng >= 1.5.0
- jsonschema >= 4.0.0

## Development

Run tests:

```bash
pytest tests/ -v
```

## License

MIT
