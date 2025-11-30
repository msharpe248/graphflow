# JSON Plugin Steps Reference

Complete reference for all steps in the GraphFlow JSON plugin.

---

## Core Steps

### JSON Parse (`json.parse`)

Parse a JSON string into a Python object/dict.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON string using `{memory.variable}` syntax |
| strict | boolean | No | true | If false, allows trailing commas and comments |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | any | Parsed JSON object |

**Example:**
```yaml
- id: parse_json
  type: json.parse
  config:
    input: "{memory.json_string}"
  outputs:
    output: "{memory.parsed}"
```

---

### JSON Stringify (`json.stringify`)

Convert a Python object/dict to a JSON string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input object using `{memory.variable}` syntax |
| indent | integer | No | - | Number of spaces for indentation (pretty printing) |
| sort_keys | boolean | No | false | Sort dictionary keys in output |
| ensure_ascii | boolean | No | true | Escape non-ASCII characters |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | JSON string representation |

**Example:**
```yaml
- id: stringify_json
  type: json.stringify
  config:
    input: "{memory.data}"
    indent: 2
    sort_keys: true
  outputs:
    output: "{memory.json_string}"
```

---

## Query Steps

### JSON Path (`json.path`)

Extract values from JSON using JSONPath expressions.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON object using `{memory.variable}` syntax |
| expression | string | Yes | - | JSONPath expression (e.g., `$.store.book[*].author`) |
| first_only | boolean | No | false | Return only the first match instead of all matches |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | any | Extracted value(s) - single value if first_only, array otherwise |
| found | boolean | Whether any matches were found |

**Example:**
```yaml
- id: query_path
  type: json.path
  config:
    input: "{memory.data}"
    expression: "$.users[*].email"
  outputs:
    output: "{memory.emails}"
    found: "{memory.has_emails}"
```

**JSONPath Examples:**
- `$.store.book[*].author` - All authors of all books
- `$..author` - All authors anywhere in the document
- `$.store.book[0]` - First book
- `$.store.book[-1]` - Last book
- `$.store.book[0,1]` - First two books
- `$.store.book[:2]` - Books from index 0 to 1

---

### JSON Get (`json.get`)

Get a value from a JSON object using a dot-notation path.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON object using `{memory.variable}` syntax |
| path | string | Yes | - | Dot-notation path (e.g., `user.address.city`) |
| default | any | No | - | Default value if path not found |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | any | Value at the path |
| found | boolean | Whether the path was found |

**Path Syntax:**
- `user.name` - Access nested property
- `items.0` - Access array by index
- `items[0].name` - Bracket notation for arrays

**Example:**
```yaml
- id: get_value
  type: json.get
  config:
    input: "{memory.config}"
    path: "database.host"
    default: "localhost"
  outputs:
    output: "{memory.db_host}"
    found: "{memory.host_configured}"
```

---

### JSON Set (`json.set`)

Set a value in a JSON object using a dot-notation path.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON object using `{memory.variable}` syntax |
| path | string | Yes | - | Dot-notation path (e.g., `user.address.city`) |
| value | string | Yes | - | Value to set using `{memory.variable}` syntax or literal |
| create_path | boolean | No | true | Create intermediate objects/arrays if they don't exist |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | object | Modified JSON object |

**Example:**
```yaml
- id: set_value
  type: json.set
  config:
    input: "{memory.user}"
    path: "profile.updated_at"
    value: "{memory.timestamp}"
  outputs:
    output: "{memory.updated_user}"
```

---

## Transform Steps

### JSON Merge (`json.merge`)

Deep merge multiple JSON objects into one.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| base | string | Yes | - | Base object using `{memory.variable}` syntax |
| overlay | string | Yes | - | Object to merge on top using `{memory.variable}` syntax |
| strategy | string | No | deep | Merge strategy: `replace`, `append`, `deep` |

**Merge Strategies:**
- `replace` - Overlay completely replaces base
- `append` - Arrays are concatenated, objects are merged
- `deep` - Recursively merge objects, arrays are replaced

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | object | Merged JSON object |

**Example:**
```yaml
- id: merge_configs
  type: json.merge
  config:
    base: "{memory.defaults}"
    overlay: "{memory.overrides}"
    strategy: deep
  outputs:
    output: "{memory.config}"
```

---

## Validation Steps

### JSON Schema Validate (`json.schema-validate`)

Validate a JSON object against a JSON Schema.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON object using `{memory.variable}` syntax |
| schema | object | Yes | - | JSON Schema to validate against |
| strict | boolean | No | false | Raise error on validation failure |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| valid | boolean | Whether the JSON is valid |
| errors | array | List of validation error messages |

**Example:**
```yaml
- id: validate
  type: json.schema-validate
  config:
    input: "{memory.data}"
    schema:
      type: object
      properties:
        name:
          type: string
          minLength: 1
        age:
          type: integer
          minimum: 0
      required:
        - name
  outputs:
    valid: "{memory.is_valid}"
    errors: "{memory.errors}"
```

---

## Inspection Steps

### JSON Keys (`json.keys`)

Get all keys from a JSON object.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON object using `{memory.variable}` syntax |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Array of keys |

**Example:**
```yaml
- id: get_keys
  type: json.keys
  config:
    input: "{memory.obj}"
  outputs:
    output: "{memory.keys}"
```

---

### JSON Values (`json.values`)

Get all values from a JSON object.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON object using `{memory.variable}` syntax |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Array of values |

**Example:**
```yaml
- id: get_values
  type: json.values
  config:
    input: "{memory.obj}"
  outputs:
    output: "{memory.values}"
```
