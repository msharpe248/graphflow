# CSV Plugin Steps Reference

Complete reference for all steps in the GraphFlow CSV plugin.

---

## Core Steps

### CSV Parse (`csv.parse`)

Parse a CSV string into a list of dictionaries (with headers) or list of lists.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | CSV string using `{memory.variable}` syntax |
| has_header | boolean | No | true | First row contains column headers |
| delimiter | string | No | "," | Field delimiter character |
| quotechar | string | No | "\"" | Character used to quote fields |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Parsed rows (list of dicts if has_header, else list of lists) |
| headers | array | Column headers (if has_header is true) |
| row_count | integer | Number of data rows |

---

### CSV Stringify (`csv.stringify`)

Convert a list of dictionaries or lists to a CSV string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of rows |
| headers | string | No | - | Column headers (inferred from dicts if not provided) |
| delimiter | string | No | "," | Field delimiter character |
| include_header | boolean | No | true | Include header row in output |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | CSV string |

---

### CSV Get Headers (`csv.get-headers`)

Extract column headers from a CSV string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | CSV string |
| delimiter | string | No | "," | Field delimiter character |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Column headers |
| count | integer | Number of columns |

---

## Conversion Steps

### CSV to JSON (`csv.to-json`)

Convert a CSV string to a JSON array of objects.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | CSV string |
| delimiter | string | No | "," | Field delimiter |
| indent | integer | No | - | JSON indentation |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | JSON array string |

---

### JSON to CSV (`csv.from-json`)

Convert a JSON array of objects to a CSV string.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | JSON array string |
| delimiter | string | No | "," | Field delimiter |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | string | CSV string |

---

## Filter & Sort Steps

### CSV Filter (`csv.filter`)

Filter rows based on column value conditions.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| column | string | Yes | - | Column name to filter on |
| operator | string | No | "eq" | Comparison operator |
| value | any | Yes | - | Value to compare against |

**Operators:**
- `eq` - Equal
- `ne` - Not equal
- `gt`, `gte` - Greater than / Greater than or equal (numeric)
- `lt`, `lte` - Less than / Less than or equal (numeric)
- `contains` - String contains
- `startswith` - String starts with
- `endswith` - String ends with

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Filtered rows |
| count | integer | Number of matching rows |

---

### CSV Sort (`csv.sort`)

Sort rows by one or more columns.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| column | string | Yes | - | Column to sort by |
| descending | boolean | No | false | Sort in descending order |
| numeric | boolean | No | false | Treat values as numbers |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Sorted rows |

---

## Column Operations

### CSV Select Columns (`csv.select-columns`)

Select and optionally reorder specific columns.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| columns | array | Yes | - | List of column names to select |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Rows with selected columns only |

---

### CSV Get Column (`csv.get-column`)

Extract all values from a single column.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| column | string | Yes | - | Column name to extract |
| unique | boolean | No | false | Return only unique values |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Column values |

---

### CSV Add Column (`csv.add-column`)

Add a new column with a constant value or copied from another column.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| column | string | Yes | - | Name for the new column |
| value | any | No | - | Constant value for all rows |
| from_column | string | No | - | Copy values from another column |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Rows with the new column |

---

### CSV Rename Columns (`csv.rename-columns`)

Rename one or more columns.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| mapping | object | Yes | - | Object mapping old names to new names |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Rows with renamed columns |

---

## Row Operations

### CSV Get Row (`csv.get-row`)

Get a specific row by its index.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| index | integer | Yes | - | Row index (0-based, negative for from end) |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | object | Row at the specified index |
| found | boolean | Whether the row was found |

---

### CSV Merge (`csv.merge`)

Merge two CSV datasets by appending rows or joining on a column.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| left | string | Yes | - | First dataset |
| right | string | Yes | - | Second dataset |
| mode | string | No | "append" | Merge mode: `append` or `join` |
| on | string | No | - | Column to join on (required for join mode) |
| join_type | string | No | "inner" | Type of join: `inner`, `left`, `right`, `outer` |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | array | Merged dataset |

---

### CSV Group By (`csv.group-by`)

Group rows by a column value.

**Config:**
| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| input | string | Yes | - | List of row dictionaries |
| column | string | Yes | - | Column to group by |

**Outputs:**
| Property | Type | Description |
|----------|------|-------------|
| output | object | Object with group keys and their rows |
| keys | array | List of unique group keys |
