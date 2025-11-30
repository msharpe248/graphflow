# GraphFlow CSV Plugin

CSV manipulation plugin for GraphFlow providing steps for parsing, transforming, filtering, and converting CSV data.

## Installation

```bash
pip install graphflow-plugins-csv
```

## Features

- **Parse & Stringify**: Convert between CSV strings and structured data
- **JSON Conversion**: Convert CSV to/from JSON
- **Filtering**: Filter rows by column conditions
- **Sorting**: Sort by column with numeric/string comparison
- **Column Operations**: Select, rename, add columns
- **Row Operations**: Get specific rows, merge datasets
- **Grouping**: Group rows by column values

## Available Steps

| Step | Type | Description |
|------|------|-------------|
| CSV Parse | `csv.parse` | Parse CSV string to list of dicts or lists |
| CSV Stringify | `csv.stringify` | Convert list of rows to CSV string |
| CSV Get Headers | `csv.get-headers` | Extract column headers |
| CSV to JSON | `csv.to-json` | Convert CSV to JSON array |
| JSON to CSV | `csv.from-json` | Convert JSON array to CSV |
| CSV Filter | `csv.filter` | Filter rows by conditions |
| CSV Select Columns | `csv.select-columns` | Select specific columns |
| CSV Sort | `csv.sort` | Sort rows by column |
| CSV Get Column | `csv.get-column` | Extract column as array |
| CSV Get Row | `csv.get-row` | Get row by index |
| CSV Add Column | `csv.add-column` | Add new column |
| CSV Rename Columns | `csv.rename-columns` | Rename columns |
| CSV Merge | `csv.merge` | Merge/join two datasets |
| CSV Group By | `csv.group-by` | Group rows by column |

## Usage Examples

### Parsing CSV

```yaml
steps:
  - id: parse_csv
    type: csv.parse
    config:
      input: "{memory.csv_content}"
      has_header: true
      delimiter: ","
    outputs:
      output: "{memory.rows}"
      headers: "{memory.columns}"
      row_count: "{memory.count}"
```

### Filtering Rows

```yaml
steps:
  - id: filter_active
    type: csv.filter
    config:
      input: "{memory.rows}"
      column: "status"
      operator: eq  # eq, ne, gt, gte, lt, lte, contains, startswith, endswith
      value: "active"
    outputs:
      output: "{memory.active_rows}"
      count: "{memory.active_count}"
```

### Sorting

```yaml
steps:
  - id: sort_by_score
    type: csv.sort
    config:
      input: "{memory.rows}"
      column: "score"
      numeric: true
      descending: true
    outputs:
      output: "{memory.sorted_rows}"
```

### Selecting Columns

```yaml
steps:
  - id: select_cols
    type: csv.select-columns
    config:
      input: "{memory.rows}"
      columns:
        - name
        - email
        - phone
    outputs:
      output: "{memory.contact_info}"
```

### Merging Datasets

```yaml
steps:
  # Append rows
  - id: append_data
    type: csv.merge
    config:
      left: "{memory.batch1}"
      right: "{memory.batch2}"
      mode: append
    outputs:
      output: "{memory.combined}"

  # Join on column
  - id: join_data
    type: csv.merge
    config:
      left: "{memory.users}"
      right: "{memory.orders}"
      mode: join
      on: user_id
      join_type: inner  # inner, left, right, outer
    outputs:
      output: "{memory.user_orders}"
```

### Grouping

```yaml
steps:
  - id: group_by_category
    type: csv.group-by
    config:
      input: "{memory.products}"
      column: "category"
    outputs:
      output: "{memory.by_category}"
      keys: "{memory.categories}"
```

## Dependencies

None (uses Python's built-in csv module)

## Development

Run tests:

```bash
pytest tests/ -v
```

## License

MIT
