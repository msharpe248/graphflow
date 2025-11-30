# YAML Plugin Steps Reference

Complete reference for all steps in the GraphFlow YAML plugin.

---

## Core Steps

### YAML Parse (`yaml.parse`)

Parse a YAML string into a Python object/dict.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input YAML string using `{memory.variable}` syntax |
| safe | boolean | No | true | Use safe loader (recommended for untrusted input) |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | any | Parsed YAML object |

---

### YAML Stringify (`yaml.stringify`)

Convert a Python object/dict to a YAML string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input object using `{memory.variable}` syntax |
| default_flow_style | boolean | No | - | Use flow style (inline) for collections |
| indent | integer | No | 2 | Number of spaces for indentation |
| sort_keys | boolean | No | false | Sort dictionary keys in output |
| allow_unicode | boolean | No | true | Allow unicode characters without escaping |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | YAML string representation |

---

## Multi-Document Steps

### YAML Parse All (`yaml.parse-all`)

Parse a multi-document YAML string (documents separated by `---`) into a list of objects.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input multi-document YAML string |
| safe | boolean | No | true | Use safe loader |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | List of parsed YAML documents |
| count | integer | Number of documents parsed |

**Example:**
```yaml
- id: parse_k8s
  type: yaml.parse-all
  config:
    input: "{memory.manifests}"
  outputs:
    output: "{memory.docs}"
    count: "{memory.doc_count}"
```

---

### YAML Stringify All (`yaml.stringify-all`)

Convert a list of objects to a multi-document YAML string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input list of objects |
| indent | integer | No | 2 | Number of spaces for indentation |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | Multi-document YAML string |

---

## Validation Steps

### YAML Validate (`yaml.validate`)

Check if a string is valid YAML syntax.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input YAML string to validate |
| strict | boolean | No | false | Raise error on invalid YAML |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| valid | boolean | Whether the YAML is valid |
| error | string | Error message if invalid |

---

## Conversion Steps

### YAML to JSON (`yaml.to-json`)

Convert a YAML string to a JSON string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input YAML string |
| indent | integer | No | - | Number of spaces for JSON indentation |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | JSON string representation |

---

### JSON to YAML (`yaml.from-json`)

Convert a JSON string to a YAML string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input JSON string |
| indent | integer | No | 2 | Number of spaces for YAML indentation |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | YAML string representation |

---

## Transform Steps

### YAML Merge (`yaml.merge`)

Deep merge two objects.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| base | string | Yes | - | Base object using `{memory.variable}` syntax |
| overlay | string | Yes | - | Object to merge on top |
| strategy | string | No | deep | Merge strategy: `replace`, `append`, `deep` |

**Merge Strategies:**
- `replace` - Overlay completely replaces base
- `append` - Arrays are concatenated, objects are merged
- `deep` - Recursively merge objects, arrays are replaced

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | object | Merged object |

---

## Access Steps

### YAML Get (`yaml.get`)

Get a value from an object using a dot-notation path.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input object |
| path | string | Yes | - | Dot-notation path (e.g., `user.address.city`) |
| default | any | No | - | Default value if path not found |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | any | Value at the path |
| found | boolean | Whether the path was found |

---

### YAML Set (`yaml.set`)

Set a value in an object using a dot-notation path.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | Input object |
| path | string | Yes | - | Dot-notation path |
| value | string | Yes | - | Value to set |
| create_path | boolean | No | true | Create intermediate objects if missing |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | object | Modified object |
