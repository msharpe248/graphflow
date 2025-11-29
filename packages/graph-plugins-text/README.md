# GraphFlow Text Plugin

Text and string manipulation plugin for GraphFlow. Provides 13 steps for common string operations with zero external dependencies.

## Installation

```bash
pip install graphflow-plugins-text
```

Or install in development mode:

```bash
cd packages/graph-plugins-text
pip install -e .
```

## Quick Start

```json
{
  "id": "greet",
  "type": "text.string-format",
  "config": {
    "template": "Hello, {memory.name}! Welcome to {memory.app_name}."
  },
  "outputs": {
    "output": "{memory.greeting}"
  }
}
```

## Steps Overview

| Category | Step | Type | Description |
|----------|------|------|-------------|
| **Basic** | StringJoinStep | `text.string-join` | Join array of strings with separator |
| | StringSplitStep | `text.string-split` | Split string into array |
| | StringReplaceStep | `text.string-replace` | Replace substring occurrences |
| | StringReverseStep | `text.string-reverse` | Reverse a string |
| | StringRepeatStep | `text.string-repeat` | Repeat string N times |
| **Formatting** | StringFormatStep | `text.string-format` | Template formatting with memory values |
| | TextCaseStep | `text.text-case` | Change case (upper/lower/title/etc.) |
| | StringTrimStep | `text.string-trim` | Trim whitespace or custom chars |
| | StringPadStep | `text.string-pad` | Pad string to length |
| **Extraction** | SubstringStep | `text.substring` | Extract substring by index |
| | TextTruncateStep | `text.text-truncate` | Truncate with suffix |
| **Regex** | RegexMatchStep | `text.regex-match` | Extract regex matches |
| | RegexReplaceStep | `text.regex-replace` | Replace using regex |

## Detailed Step Reference

See [STEPS.md](STEPS.md) for complete configuration reference for each step.

## Common Patterns

### Building Dynamic Messages

```json
{
  "id": "build_message",
  "type": "text.string-format",
  "config": {
    "template": "Order #{memory.order_id} for {memory.customer_name} is {memory.status}."
  },
  "outputs": {
    "output": "{memory.message}"
  }
}
```

### Processing CSV Data

```json
[
  {
    "id": "split_line",
    "type": "text.string-split",
    "config": {
      "input": "{memory.csv_line}",
      "separator": ","
    },
    "outputs": {
      "output": "{memory.fields}"
    }
  },
  {
    "id": "join_with_tabs",
    "type": "text.string-join",
    "config": {
      "input": "{memory.fields}",
      "separator": "\t"
    },
    "outputs": {
      "output": "{memory.tsv_line}"
    }
  }
]
```

### Sanitizing User Input

```json
{
  "id": "clean_input",
  "type": "text.string-trim",
  "config": {
    "input": "{memory.user_input}",
    "mode": "both"
  },
  "outputs": {
    "output": "{memory.cleaned_input}"
  }
}
```

### Extracting Data with Regex

```json
{
  "id": "extract_email",
  "type": "text.regex-match",
  "config": {
    "input": "{memory.text}",
    "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
    "find_all": true
  },
  "outputs": {
    "output": "{memory.emails}",
    "found": "{memory.has_emails}"
  }
}
```

### Creating Summaries

```json
{
  "id": "summarize",
  "type": "text.text-truncate",
  "config": {
    "input": "{memory.article}",
    "max_length": 200,
    "suffix": "... [Read more]",
    "word_boundary": true
  },
  "outputs": {
    "output": "{memory.summary}"
  }
}
```

### Formatting Numbers

```json
{
  "id": "format_id",
  "type": "text.string-pad",
  "config": {
    "input": "{memory.id}",
    "length": 8,
    "char": "0",
    "mode": "left"
  },
  "outputs": {
    "output": "{memory.formatted_id}"
  }
}
```

## Memory Reference Syntax

All steps support the standard GraphFlow memory reference syntax:

- `{memory.variable}` - Read/write from memory namespace
- `{config.variable}` - Read from config namespace
- `{env.variable}` - Read from environment namespace
- `{secrets.variable}` - Read from secrets namespace

## Dependencies

**None** - This plugin uses only Python standard library (`re` module for regex).

## Testing

```bash
cd packages/graph-plugins-text
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
