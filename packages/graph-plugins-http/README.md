# GraphFlow HTTP Plugin

A comprehensive HTTP client plugin for GraphFlow, providing robust web API integration capabilities.

This is a **separate plugin package** that demonstrates the GraphFlow plugin architecture. It is discovered automatically via Python entry points and loaded by the PluginManager at runtime.

## Features

- ✅ **HTTP Methods**: GET, POST, PUT, PATCH, DELETE
- ✅ **Authentication**: Basic Auth, Bearer Token
- ✅ **Retry Logic**: Exponential backoff on failures
- ✅ **Template Support**: `{memory.variable}` syntax for memory binding
- ✅ **SSL Verification**: Configurable certificate verification
- ✅ **Redirects**: Automatic redirect following
- ✅ **Timeouts**: Configurable request timeouts
- ✅ **Response Parsing**: Automatic JSON/text/binary detection
- ✅ **URL Utilities**: Build, parse, escape, unescape
- ✅ **Data Transforms**: JSON parse/stringify, Base64 encode/decode
- ✅ **HTML Processing**: Strip tags, CSS selector parsing, link extraction, table extraction

## Installation

```bash
pip install -e packages/graph-plugins-http
```

## Quick Start

### Simple GET Request

```json
{
  "id": "fetch_data",
  "type": "http-get",
  "config": {
    "url": "https://api.example.com/users"
  },
  "outputs": {
    "response": "{memory.users_data}"
  }
}
```

### POST with JSON Body

```json
{
  "id": "create_user",
  "type": "http-post",
  "config": {
    "url": "https://api.example.com/users",
    "body": {
      "name": "{memory.user_name}",
      "email": "{memory.user_email}"
    },
    "headers": {
      "Content-Type": "application/json"
    }
  },
  "outputs": {
    "response": "{memory.created_user}"
  }
}
```

### Authenticated Request

```json
{
  "id": "protected_api",
  "type": "http-get",
  "config": {
    "url": "https://api.example.com/protected",
    "auth": {
      "type": "bearer",
      "token": "{memory.api_token}"
    }
  },
  "outputs": {
    "response": "{memory.protected_data}",
    "status_code": "{memory.status}"
  }
}
```

## Step Types

### http-get

Perform HTTP GET request to fetch data from a URL.

**Config:**
- `url` (string, required): Request URL (supports `{memory.variable}` template syntax)
- `params` (object): Query parameters as key-value pairs
- `headers` (object): Request headers as key-value pairs
- `auth` (object): Authentication configuration
  - `type`: "basic" or "bearer"
  - `username`, `password`: For basic auth
  - `token`: For bearer token auth
- `timeout` (integer, default: 30): Request timeout in seconds
- `retries` (integer, default: 2): Number of retry attempts
- `verify_ssl` (boolean, default: true): Verify SSL certificates
- `follow_redirects` (boolean, default: true): Follow HTTP redirects

**Outputs:**
- `response`: HTTP response body
- `status_code`: HTTP status code
- `headers`: Response headers

**Example:**
```json
{
  "id": "fetch_user",
  "type": "http-get",
  "config": {
    "url": "https://api.github.com/users/{memory.username}",
    "headers": {
      "Accept": "application/json",
      "User-Agent": "GraphFlow"
    }
  },
  "outputs": {
    "response": "{memory.github_user}",
    "status_code": "{memory.status}"
  }
}
```

### http-post

Perform HTTP POST request to send data to a URL.

**Config:** Same as `http-get`, plus:
- `body` (any): Request body (JSON object, string, or template)

**Outputs:** Same as `http-get`

**Example:**
```json
{
  "id": "send_webhook",
  "type": "http-post",
  "config": {
    "url": "https://api.example.com/webhooks",
    "body": {
      "event": "user.created",
      "data": "{memory.event_data}"
    },
    "headers": {
      "Content-Type": "application/json",
      "X-API-Key": "{memory.api_key}"
    }
  },
  "outputs": {
    "response": "{memory.webhook_response}"
  }
}
```

### http-put

Perform HTTP PUT request to update a resource.

**Config:** Same as `http-post`

**Outputs:** Same as `http-get`

**Example:**
```json
{
  "id": "update_user",
  "type": "http-put",
  "config": {
    "url": "https://api.example.com/users/{memory.user_id}",
    "body": {
      "name": "{memory.updated_name}",
      "email": "{memory.updated_email}"
    }
  },
  "outputs": {
    "response": "{memory.updated_user}"
  }
}
```

### http-patch

Perform HTTP PATCH request for partial updates.

**Config:** Same as `http-post`

**Outputs:** Same as `http-get`

**Example:**
```json
{
  "id": "patch_user",
  "type": "http-patch",
  "config": {
    "url": "https://api.example.com/users/{memory.user_id}",
    "body": {
      "email": "{memory.new_email}"
    }
  },
  "outputs": {
    "response": "{memory.patched_user}"
  }
}
```

### http-delete

Perform HTTP DELETE request to remove a resource.

**Config:** Same as `http-get`

**Outputs:** Same as `http-get`

**Example:**
```json
{
  "id": "delete_user",
  "type": "http-delete",
  "config": {
    "url": "https://api.example.com/users/{memory.user_id}"
  },
  "outputs": {
    "response": "{memory.delete_response}",
    "status_code": "{memory.status}"
  }
}
```

---

## URL Utility Steps

### url-escape

URL encode a string for safe use in URLs.

**Config:**
- `input` (string, required): Value to encode (supports `{memory.variable}` syntax)
- `safe` (string, optional): Characters that should not be encoded (default: empty)

**Outputs:**
- `output`: URL encoded string

**Example:**
```json
{
  "id": "encode_param",
  "type": "url-escape",
  "config": {
    "input": "{memory.user_input}",
    "safe": "/"
  },
  "outputs": {
    "output": "{memory.encoded_input}"
  }
}
```

### url-unescape

URL decode a percent-encoded string.

**Config:**
- `input` (string, required): URL encoded string to decode

**Outputs:**
- `output`: Decoded string

**Example:**
```json
{
  "id": "decode_param",
  "type": "url-unescape",
  "config": {
    "input": "{memory.encoded_param}"
  },
  "outputs": {
    "output": "{memory.decoded_param}"
  }
}
```

### url-build

Construct a URL from components.

**Config:**
- `scheme` (string, default: "https"): URL scheme (http, https, etc.)
- `host` (string, required): Hostname (e.g., api.example.com)
- `port` (integer, optional): Port number
- `path` (string, default: ""): URL path (e.g., /api/users)
- `params` (object, optional): Query parameters as key-value pairs
- `fragment` (string, optional): URL fragment/anchor

**Outputs:**
- `output`: Constructed URL string

**Example:**
```json
{
  "id": "build_api_url",
  "type": "url-build",
  "config": {
    "scheme": "https",
    "host": "api.example.com",
    "path": "/v1/search",
    "params": {
      "q": "{memory.search_query}",
      "limit": "10"
    }
  },
  "outputs": {
    "output": "{memory.api_url}"
  }
}
```

### url-parse

Extract components from a URL.

**Config:**
- `input` (string, required): URL to parse

**Outputs:**
- `output`: Object with fields:
  - `scheme`: URL scheme (http, https, etc.)
  - `netloc`: Full network location (host:port)
  - `host`: Hostname only
  - `port`: Port number (if present)
  - `path`: URL path
  - `params`: Query parameters as object
  - `query`: Raw query string
  - `fragment`: URL fragment/anchor

**Example:**
```json
{
  "id": "parse_url",
  "type": "url-parse",
  "config": {
    "input": "{memory.full_url}"
  },
  "outputs": {
    "output": "{memory.url_components}"
  }
}
```

---

## Data Transformation Steps

### json-parse

Parse a JSON string into a Python object/dict.

**Config:**
- `input` (string, required): JSON string to parse

**Outputs:**
- `output`: Parsed object/dict

**Example:**
```json
{
  "id": "parse_json",
  "type": "json-parse",
  "config": {
    "input": "{memory.json_response}"
  },
  "outputs": {
    "output": "{memory.parsed_data}"
  }
}
```

### json-stringify

Convert a Python object/dict to a JSON string.

**Config:**
- `input` (any, required): Object to convert to JSON
- `indent` (integer, optional): Number of spaces for indentation (for pretty printing)
- `sort_keys` (boolean, default: false): Sort dictionary keys in output

**Outputs:**
- `output`: JSON string

**Example:**
```json
{
  "id": "stringify_object",
  "type": "json-stringify",
  "config": {
    "input": "{memory.data_object}",
    "indent": 2,
    "sort_keys": true
  },
  "outputs": {
    "output": "{memory.json_string}"
  }
}
```

### base64-encode

Encode a string or bytes to Base64.

**Config:**
- `input` (string, required): Data to encode
- `encoding` (string, default: "utf-8"): Text encoding to use if input is string

**Outputs:**
- `output`: Base64 encoded string

**Example:**
```json
{
  "id": "encode_text",
  "type": "base64-encode",
  "config": {
    "input": "{memory.plain_text}"
  },
  "outputs": {
    "output": "{memory.encoded_text}"
  }
}
```

### base64-decode

Decode a Base64 encoded string.

**Config:**
- `input` (string, required): Base64 encoded string to decode
- `encoding` (string, default: "utf-8"): Text encoding to use for output string
- `as_bytes` (boolean, default: false): Return raw bytes instead of decoded string

**Outputs:**
- `output`: Decoded data

**Example:**
```json
{
  "id": "decode_text",
  "type": "base64-decode",
  "config": {
    "input": "{memory.encoded_data}"
  },
  "outputs": {
    "output": "{memory.decoded_text}"
  }
}
```

---

## HTML Processing Steps

### html-strip

Remove HTML tags from content, leaving only plain text.

**Config:**
- `input` (string, required): HTML content to strip
- `separator` (string, default: " "): Separator to use between text elements
- `strip_whitespace` (boolean, default: true): Remove excess whitespace from output

**Outputs:**
- `output`: Plain text

**Example:**
```json
{
  "id": "strip_html",
  "type": "html-strip",
  "config": {
    "input": "{memory.html_response}",
    "separator": " ",
    "strip_whitespace": true
  },
  "outputs": {
    "output": "{memory.plain_text}"
  }
}
```

### html-parse

Extract data from HTML using CSS selectors (powered by BeautifulSoup).

**Config:**
- `input` (string, required): HTML content to parse
- `selectors` (object, required): CSS selectors to extract data. Each key maps to a selector config with:
  - `selector` (string): CSS selector to find element(s)
  - `attribute` (string, optional): Extract attribute value instead of text
  - `multiple` (boolean, default: false): Find all matches instead of just first
- `parser` (string, default: "lxml"): HTML parser to use (lxml, html.parser, html5lib)

**Outputs:**
- `output`: Extracted data as object

**Example:**
```json
{
  "id": "parse_html",
  "type": "html-parse",
  "config": {
    "input": "{memory.html_page}",
    "selectors": {
      "title": {"selector": "h1"},
      "description": {"selector": "meta[name='description']", "attribute": "content"},
      "articles": {"selector": "article h2", "multiple": true},
      "first_link": {"selector": "a", "attribute": "href"}
    }
  },
  "outputs": {
    "output": "{memory.extracted_data}"
  }
}
```

### html-find-links

Extract all links (URLs) from HTML content.

**Config:**
- `input` (string, required): HTML content
- `absolute_only` (boolean, default: false): Only return absolute URLs (starting with http/https)
- `unique` (boolean, default: true): Remove duplicate URLs

**Outputs:**
- `output`: List of links

**Example:**
```json
{
  "id": "extract_links",
  "type": "html-find-links",
  "config": {
    "input": "{memory.webpage_html}",
    "absolute_only": true,
    "unique": true
  },
  "outputs": {
    "output": "{memory.all_links}"
  }
}
```

### html-table-extract

Extract data from HTML tables into structured format.

**Config:**
- `input` (string, required): HTML content with tables
- `table_selector` (string, default: "table"): CSS selector to find table
- `headers` (boolean, default: true): First row contains headers (creates dict rows)
- `skip_rows` (integer, default: 0): Number of rows to skip at start

**Outputs:**
- `output`: Extracted table data (array of dicts when headers=true, array of arrays when headers=false)

**Example:**
```json
{
  "id": "extract_table",
  "type": "html-table-extract",
  "config": {
    "input": "{memory.html_with_table}",
    "table_selector": "table.data-table",
    "headers": true,
    "skip_rows": 0
  },
  "outputs": {
    "output": "{memory.table_data}"
  }
}
```

---

## Authentication

### Basic Auth

```json
{
  "auth": {
    "type": "basic",
    "username": "{memory.api_username}",
    "password": "{memory.api_password}"
  }
}
```

### Bearer Token

```json
{
  "auth": {
    "type": "bearer",
    "token": "{memory.api_token}"
  }
}
```

## Template Syntax

All string values support `{memory.variable}` template syntax for memory binding:

```json
{
  "url": "https://api.example.com/users/{memory.user_id}/posts/{memory.post_id}",
  "headers": {
    "Authorization": "Bearer {memory.token}",
    "X-User-ID": "{memory.user_id}"
  },
  "body": {
    "title": "{memory.post_title}",
    "content": "{memory.post_content}"
  }
}
```

Nested memory access with dot notation:

```json
{
  "url": "https://api.example.com/{memory.api.endpoint}/{memory.resource.id}"
}
```

## Error Handling

The plugin handles various error scenarios:

- **Network Errors**: Connection timeouts, DNS failures → Automatic retry with exponential backoff
- **HTTP Errors**: 4xx/5xx status codes → Raises exception after retries
- **SSL Errors**: Certificate verification failures → Can be disabled with `verify_ssl: false`
- **Timeout**: Request exceeds timeout → Automatic retry

## Examples

### REST API CRUD Workflow

```json
{
  "steps": [
    {
      "id": "create",
      "type": "http-post",
      "config": {
        "url": "https://api.example.com/items",
        "body": {"name": "{memory.item_name}"}
      },
      "outputs": {
        "response": "{memory.created_item}"
      }
    },
    {
      "id": "read",
      "type": "http-get",
      "config": {
        "url": "https://api.example.com/items/{memory.created_item.id}"
      },
      "outputs": {
        "response": "{memory.item_data}"
      }
    },
    {
      "id": "update",
      "type": "http-put",
      "config": {
        "url": "https://api.example.com/items/{memory.created_item.id}",
        "body": {"name": "{memory.updated_name}"}
      },
      "outputs": {
        "response": "{memory.updated_item}"
      }
    },
    {
      "id": "delete",
      "type": "http-delete",
      "config": {
        "url": "https://api.example.com/items/{memory.created_item.id}"
      },
      "outputs": {
        "response": "{memory.delete_result}"
      }
    }
  ]
}
```

### API with Retry Logic

```json
{
  "id": "resilient_fetch",
  "type": "http-get",
  "config": {
    "url": "https://flaky-api.example.com/data",
    "timeout": 60,
    "retries": 5
  },
  "outputs": {
    "response": "{memory.data}"
  }
}
```

### File Download

```json
{
  "id": "download_file",
  "type": "http-get",
  "config": {
    "url": "https://example.com/files/document.pdf"
  },
  "outputs": {
    "response": "{memory.file_content}"
  }
}
```

## Plugin Registration

The plugin is automatically discovered via Python entry points when installed. GraphFlow's PluginLoader finds all packages that declare the `graphflow.plugins` entry point.

**Step Type Naming**: When loaded by the PluginManager, step types are namespaced with the plugin name:
- `http.HTTPGetStep`
- `http.HTTPPostStep`
- `http.HTTPPutStep`
- `http.HTTPPatchStep`
- `http.HTTPDeleteStep`

**Usage in Code**:

```python
from graphflow_core.plugins.manager import PluginManager

# Create plugin manager and discover all installed plugins
manager = PluginManager()
plugins = manager.discover_and_load()

# The HTTP plugin is now loaded with all its steps registered
# Steps can be referenced by their namespaced types (e.g., "http.HTTPGetStep")
```

**Direct Import** (for testing or custom registration):

```python
from graphflow_http import HTTPGetStep, HTTPPostStep, HTTPPutStep, HTTPPatchStep, HTTPDeleteStep

# All step classes are available for direct instantiation
step = HTTPGetStep(
    id="fetch_api",
    config={"url": "https://api.example.com"},
    outputs={"response": "{memory.data}"}
)
```

## Development

### Running Tests

```bash
cd packages/graph-plugins-http
pytest tests/
```

### Code Quality

```bash
# Format code
black graphflow_http/

# Type checking
mypy graphflow_http/
```

## Roadmap

- [x] Phase 1: Core HTTP Steps (GET, POST, PUT, PATCH, DELETE)
- [x] Phase 2: URL & Data Steps
  - [x] url-build - Construct URLs from components
  - [x] url-parse - Extract components from URL
  - [x] url-escape - URL encode strings
  - [x] url-unescape - URL decode strings
  - [x] json-parse - Parse JSON strings
  - [x] json-stringify - Convert objects to JSON
  - [x] base64-encode / base64-decode
- [x] Phase 3: HTML Processing
  - [x] html-strip - Remove HTML tags
  - [x] html-parse - Extract data with CSS selectors
  - [x] html-find-links - Extract all links from HTML
  - [x] html-table-extract - Extract data from HTML tables
- [x] Phase 4: Memory Reference Refactor
  - [x] Unified `{memory.variable}` syntax throughout
  - [x] Removed `*_key` config fields in favor of outputs object
  - [x] Consistent input/output patterns across all steps
- [ ] Phase 5: Advanced Features
  - [ ] Cookie jar management
  - [ ] Session persistence
  - [ ] Request/response middleware

## License

MIT

## Contributing

Contributions welcome! This plugin serves as a reference implementation for GraphFlow plugins.
