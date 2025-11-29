# Text Plugin Step Reference

Complete configuration reference for all steps in the GraphFlow Text Plugin.

---

## Basic Operations

### StringJoinStep

**Type:** `text.string-join`

Join an array of strings into a single string with a separator.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to array (e.g., `{memory.items}`) |
| `separator` | string | No | `""` | String to insert between elements |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Joined string |

#### Example

```json
{
  "id": "join_tags",
  "type": "text.string-join",
  "config": {
    "input": "{memory.tags}",
    "separator": ", "
  },
  "outputs": {
    "output": "{memory.tag_string}"
  }
}
```

**Input:** `["apple", "banana", "cherry"]`
**Output:** `"apple, banana, cherry"`

---

### StringSplitStep

**Type:** `text.string-split`

Split a string into an array using a separator.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `separator` | string | No | `""` | Separator to split on. Empty string splits each character. |
| `max_split` | integer | No | `-1` | Maximum splits (-1 for unlimited) |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | array | Array of string parts |

#### Examples

**Split by comma:**
```json
{
  "config": {
    "input": "{memory.csv}",
    "separator": ","
  }
}
```
Input: `"a,b,c"` → Output: `["a", "b", "c"]`

**Split by character:**
```json
{
  "config": {
    "input": "{memory.word}",
    "separator": ""
  }
}
```
Input: `"hello"` → Output: `["h", "e", "l", "l", "o"]`

**Limited splits:**
```json
{
  "config": {
    "input": "{memory.path}",
    "separator": "/",
    "max_split": 2
  }
}
```
Input: `"a/b/c/d"` → Output: `["a", "b", "c/d"]`

---

### StringReplaceStep

**Type:** `text.string-replace`

Replace occurrences of a substring with another string (non-regex).

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `old` | string | Yes | - | Substring to find |
| `new` | string | No | `""` | Replacement string |
| `count` | integer | No | `-1` | Maximum replacements (-1 for all) |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | String with replacements |

#### Example

```json
{
  "id": "replace_placeholder",
  "type": "text.string-replace",
  "config": {
    "input": "{memory.template}",
    "old": "{{NAME}}",
    "new": "John"
  },
  "outputs": {
    "output": "{memory.result}"
  }
}
```

---

### StringReverseStep

**Type:** `text.string-reverse`

Reverse the characters in a string.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Reversed string |

#### Example

```json
{
  "id": "reverse",
  "type": "text.string-reverse",
  "config": {
    "input": "{memory.text}"
  },
  "outputs": {
    "output": "{memory.reversed}"
  }
}
```

Input: `"hello"` → Output: `"olleh"`

---

### StringRepeatStep

**Type:** `text.string-repeat`

Repeat a string a specified number of times.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `count` | integer | No | `1` | Number of repetitions |
| `separator` | string | No | `""` | String between repetitions |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Repeated string |

#### Examples

**Simple repeat:**
```json
{
  "config": {
    "input": "{memory.char}",
    "count": 5
  }
}
```
Input: `"ab"` → Output: `"ababababab"`

**With separator:**
```json
{
  "config": {
    "input": "{memory.word}",
    "count": 3,
    "separator": "-"
  }
}
```
Input: `"la"` → Output: `"la-la-la"`

---

## Formatting

### StringFormatStep

**Type:** `text.string-format`

Format a template string by replacing memory references with their values.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `template` | string | Yes | - | Template with `{memory.var}` placeholders |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Formatted string |

#### Example

```json
{
  "id": "format_greeting",
  "type": "text.string-format",
  "config": {
    "template": "Hello {memory.first_name} {memory.last_name}! Your order #{memory.order_id} is ready."
  },
  "outputs": {
    "output": "{memory.message}"
  }
}
```

With memory: `{first_name: "John", last_name: "Doe", order_id: 12345}`
Output: `"Hello John Doe! Your order #12345 is ready."`

---

### TextCaseStep

**Type:** `text.text-case`

Change the case of a string.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `case` | string | No | `"lower"` | One of: `upper`, `lower`, `title`, `capitalize`, `swapcase` |

#### Case Options

| Case | Description | Example |
|------|-------------|---------|
| `upper` | All uppercase | `"hello world"` → `"HELLO WORLD"` |
| `lower` | All lowercase | `"HELLO WORLD"` → `"hello world"` |
| `title` | Title Case | `"hello world"` → `"Hello World"` |
| `capitalize` | First char upper | `"hello world"` → `"Hello world"` |
| `swapcase` | Swap upper/lower | `"Hello World"` → `"hELLO wORLD"` |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Case-transformed string |

#### Example

```json
{
  "id": "to_title",
  "type": "text.text-case",
  "config": {
    "input": "{memory.name}",
    "case": "title"
  },
  "outputs": {
    "output": "{memory.formatted_name}"
  }
}
```

---

### StringTrimStep

**Type:** `text.string-trim`

Remove whitespace or specified characters from string ends.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `mode` | string | No | `"both"` | One of: `both`, `left`, `right` |
| `chars` | string | No | `""` | Characters to trim (empty = whitespace) |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Trimmed string |

#### Examples

**Trim whitespace:**
```json
{
  "config": {
    "input": "{memory.text}",
    "mode": "both"
  }
}
```
Input: `"  hello  "` → Output: `"hello"`

**Trim specific characters:**
```json
{
  "config": {
    "input": "{memory.text}",
    "mode": "both",
    "chars": "x-"
  }
}
```
Input: `"--xx-hello-xx--"` → Output: `"hello"`

---

### StringPadStep

**Type:** `text.string-pad`

Pad a string to a specified length.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `length` | integer | Yes | - | Target length |
| `char` | string | No | `" "` | Padding character |
| `mode` | string | No | `"left"` | One of: `left`, `right`, `center` |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Padded string |

#### Examples

**Zero-pad number:**
```json
{
  "config": {
    "input": "{memory.num}",
    "length": 5,
    "char": "0",
    "mode": "left"
  }
}
```
Input: `"42"` → Output: `"00042"`

**Center text:**
```json
{
  "config": {
    "input": "{memory.title}",
    "length": 20,
    "char": "=",
    "mode": "center"
  }
}
```
Input: `"Title"` → Output: `"=======Title========"`

---

## Extraction

### SubstringStep

**Type:** `text.substring`

Extract a portion of a string by index.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `start` | integer | No | `0` | Start index (0-based, supports negative) |
| `end` | integer | No | - | End index (exclusive, supports negative). Omit for end of string. |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Extracted substring |

#### Examples

**First 5 characters:**
```json
{
  "config": {
    "input": "{memory.text}",
    "start": 0,
    "end": 5
  }
}
```
Input: `"hello world"` → Output: `"hello"`

**Last 5 characters:**
```json
{
  "config": {
    "input": "{memory.text}",
    "start": -5
  }
}
```
Input: `"hello world"` → Output: `"world"`

**Middle portion:**
```json
{
  "config": {
    "input": "{memory.text}",
    "start": 6,
    "end": -1
  }
}
```
Input: `"hello world!"` → Output: `"world"`

---

### TextTruncateStep

**Type:** `text.text-truncate`

Truncate text to a maximum length with optional suffix.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `max_length` | integer | Yes | - | Maximum output length (including suffix) |
| `suffix` | string | No | `"..."` | Suffix when truncated |
| `word_boundary` | boolean | No | `false` | Truncate at word boundary if possible |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | Truncated string |

#### Examples

**Simple truncate:**
```json
{
  "config": {
    "input": "{memory.text}",
    "max_length": 20,
    "suffix": "..."
  }
}
```
Input: `"This is a very long sentence"` → Output: `"This is a very lo..."`

**Word boundary:**
```json
{
  "config": {
    "input": "{memory.text}",
    "max_length": 20,
    "suffix": "...",
    "word_boundary": true
  }
}
```
Input: `"This is a very long sentence"` → Output: `"This is a very..."`

---

## Regex

### RegexMatchStep

**Type:** `text.regex-match`

Extract matches from a string using a regular expression.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `pattern` | string | Yes | - | Regular expression pattern |
| `flags` | string | No | `""` | Regex flags: `i`=ignorecase, `m`=multiline, `s`=dotall |
| `find_all` | boolean | No | `false` | Find all matches (true) or just first (false) |
| `groups` | boolean | No | `false` | Return captured groups instead of full match |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string/array/null | Match result(s) |
| `found` | boolean | Whether any match was found |

#### Examples

**Find first match:**
```json
{
  "config": {
    "input": "{memory.text}",
    "pattern": "\\d+"
  },
  "outputs": {
    "output": "{memory.first_number}",
    "found": "{memory.has_number}"
  }
}
```
Input: `"Order 123 and 456"` → Output: `"123"`, found: `true`

**Find all matches:**
```json
{
  "config": {
    "input": "{memory.text}",
    "pattern": "\\d+",
    "find_all": true
  },
  "outputs": {
    "output": "{memory.numbers}"
  }
}
```
Input: `"Order 123 and 456"` → Output: `["123", "456"]`

**Extract groups:**
```json
{
  "config": {
    "input": "{memory.text}",
    "pattern": "(\\w+)@(\\w+\\.\\w+)",
    "groups": true
  },
  "outputs": {
    "output": "{memory.email_parts}"
  }
}
```
Input: `"Contact: john@example.com"` → Output: `["john", "example.com"]`

**Case insensitive:**
```json
{
  "config": {
    "input": "{memory.text}",
    "pattern": "error",
    "flags": "i",
    "find_all": true
  }
}
```
Input: `"Error: ERROR found"` → Output: `["Error", "ERROR"]`

---

### RegexReplaceStep

**Type:** `text.regex-replace`

Replace text matching a regex pattern.

#### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `input` | string | Yes | - | Memory reference to string |
| `pattern` | string | Yes | - | Regular expression pattern |
| `replacement` | string | No | `""` | Replacement string (supports `\1`, `\2` for groups) |
| `flags` | string | No | `""` | Regex flags: `i`=ignorecase, `m`=multiline, `s`=dotall |
| `count` | integer | No | `0` | Max replacements (0 = all) |

#### Outputs

| Name | Type | Description |
|------|------|-------------|
| `output` | string | String with replacements |
| `count` | integer | Number of replacements made |

#### Examples

**Remove all digits:**
```json
{
  "config": {
    "input": "{memory.text}",
    "pattern": "\\d+",
    "replacement": ""
  }
}
```
Input: `"abc123def456"` → Output: `"abcdef"`

**Mask sensitive data:**
```json
{
  "config": {
    "input": "{memory.text}",
    "pattern": "\\d{4}-\\d{4}-\\d{4}-(\\d{4})",
    "replacement": "****-****-****-\\1"
  }
}
```
Input: `"Card: 1234-5678-9012-3456"` → Output: `"Card: ****-****-****-3456"`

**Swap first/last name:**
```json
{
  "config": {
    "input": "{memory.name}",
    "pattern": "(\\w+) (\\w+)",
    "replacement": "\\2, \\1"
  }
}
```
Input: `"John Doe"` → Output: `"Doe, John"`

**Limited replacements:**
```json
{
  "config": {
    "input": "{memory.text}",
    "pattern": "a",
    "replacement": "X",
    "count": 2
  }
}
```
Input: `"banana"` → Output: `"bXnXna"`, count: `2`

---

## All Steps Can Be Used as LLM Tools

All steps in this plugin have `can_be_tool = True`, meaning they can be exposed to LLM steps as callable tools during agent execution.
