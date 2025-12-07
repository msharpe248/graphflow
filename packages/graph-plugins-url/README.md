# GraphFlow URL Plugin

URL manipulation and parsing utilities for GraphFlow.

## Installation

```bash
pip install -e packages/graph-plugins-url
```

## Steps Provided

| Step | Description |
|------|-------------|
| `url.URLEscapeStep` | URL encode a string (percent encoding) |
| `url.URLUnescapeStep` | URL decode a percent-encoded string |
| `url.URLBuildStep` | Build a URL from components (scheme, host, path, query params) |
| `url.URLParseStep` | Parse a URL into its components |

## URLEscapeStep

URL encode a string for safe use in URLs.

**Configuration:**
- `input` - Input string using `{memory.variable}` syntax
- `safe` - Characters to not encode (default: empty)

**Example:**
```json
{
  "id": "escape_1",
  "type": "url.URLEscapeStep",
  "config": {
    "input": "{memory.query_text}"
  },
  "outputs": {
    "output": "{memory.encoded_query}"
  }
}
```

## URLUnescapeStep

Decode a URL-encoded string.

**Configuration:**
- `input` - Input string using `{memory.variable}` syntax

**Example:**
```json
{
  "id": "unescape_1",
  "type": "url.URLUnescapeStep",
  "config": {
    "input": "{memory.encoded_text}"
  },
  "outputs": {
    "output": "{memory.decoded_text}"
  }
}
```

## URLBuildStep

Build a complete URL from components.

**Configuration:**
- `scheme` - URL scheme (http, https, etc.)
- `host` - Hostname
- `port` - Port number (optional)
- `path` - URL path (optional)
- `query` - Query parameters as object (optional)
- `fragment` - URL fragment (optional)

**Example:**
```json
{
  "id": "build_url_1",
  "type": "url.URLBuildStep",
  "config": {
    "scheme": "https",
    "host": "api.example.com",
    "path": "/v1/search",
    "query": {
      "q": "{memory.search_term}",
      "limit": "10"
    }
  },
  "outputs": {
    "output": "{memory.api_url}"
  }
}
```

## URLParseStep

Parse a URL into its component parts.

**Configuration:**
- `input` - URL string using `{memory.variable}` syntax

**Output:**
Returns an object with: `scheme`, `netloc`, `path`, `query`, `fragment`, `hostname`, `port`, `query_params`

**Example:**
```json
{
  "id": "parse_url_1",
  "type": "url.URLParseStep",
  "config": {
    "input": "{memory.url}"
  },
  "outputs": {
    "output": "{memory.url_parts}"
  }
}
```

## License

MIT
