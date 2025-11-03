# HTTP Plugin Package - Implementation Plan

## Overview
A comprehensive HTTP client plugin for GraphFlow, providing robust web API integration capabilities.

## Package Structure
```
packages/graph-plugins-http/
├── README.md                          # User documentation
├── IMPLEMENTATION_PLAN.md             # This file
├── setup.py                           # Package installation
├── pyproject.toml                     # Modern Python packaging
├── graphflow_http/
│   ├── __init__.py                   # Plugin registration
│   ├── base.py                       # Base HTTP step with shared logic
│   ├── request.py                    # HTTP request steps (GET, POST, etc.)
│   ├── url.py                        # URL manipulation steps
│   ├── data.py                       # Data transformation steps
│   └── html.py                       # HTML processing steps
└── tests/
    ├── test_request.py
    ├── test_url.py
    ├── test_data.py
    └── test_html.py
```

## Steps to Implement

### 1. HTTP Request Steps (request.py)
- **http-get** - GET requests with query parameters
  - Config: url, params, headers, auth, timeout, verify_ssl, follow_redirects
  - Outputs: response_body, status_code, headers, cookies

- **http-post** - POST requests with body
  - Config: url, body, params, headers, auth, timeout, content_type
  - Outputs: response_body, status_code, headers

- **http-put** - PUT requests
  - Config: Same as POST

- **http-patch** - PATCH requests
  - Config: Same as POST

- **http-delete** - DELETE requests
  - Config: url, params, headers, auth, timeout

### 2. URL Manipulation Steps (url.py)
- **url-build** - Construct URLs from components
  - Config: scheme, host, port, path, query_params
  - Outputs: url

- **url-parse** - Extract components from URL
  - Config: url
  - Outputs: scheme, host, port, path, query_params, fragment

- **url-escape** - URL encode strings
  - Config: text, safe_chars
  - Outputs: encoded_text

### 3. Data Transformation Steps (data.py)
- **json-parse** - Parse JSON strings
  - Config: json_string
  - Outputs: parsed_object

- **json-stringify** - Convert objects to JSON
  - Config: object, indent, sort_keys
  - Outputs: json_string

- **base64-encode** - Encode data to base64
  - Config: data
  - Outputs: encoded_data

- **base64-decode** - Decode base64 data
  - Config: encoded_data
  - Outputs: decoded_data

### 4. HTML Processing Steps (html.py)
- **html-strip** - Remove HTML tags
  - Config: html_content, keep_tags (optional)
  - Outputs: text

- **html-parse** - Extract data from HTML
  - Config: html_content, css_selector
  - Outputs: matched_elements

## Features

### Base HTTP Client Features (base.py)
- ✅ HTTP/HTTPS support
- ✅ Custom headers
- ✅ Query parameters
- ✅ Request timeout
- ✅ Retry logic with exponential backoff
- ✅ SSL certificate verification toggle
- ✅ Authentication (Basic, Bearer token)
- ✅ Cookie handling
- ✅ Follow redirects
- ✅ Automatic content-type detection
- ✅ Response status code handling
- ✅ Binary data support

### Error Handling
- Network errors (connection timeout, DNS failure)
- HTTP errors (4xx, 5xx status codes)
- Parsing errors (invalid JSON, malformed HTML)
- Configuration errors (invalid URLs, missing required fields)

### Memory Integration
- All inputs support memory binding: `{memory.field}`
- Template variable substitution in URLs, headers, body
- Outputs written to configurable memory locations

## Dependencies
```
httpx>=0.24.0           # Modern async HTTP client
beautifulsoup4>=4.12.0  # HTML parsing
lxml>=4.9.0             # XML/HTML parser
python-dateutil>=2.8.0  # Date parsing
```

## Plugin Registration
```python
from graphflow_core.plugins.base import PluginBase

class HTTPPlugin(PluginBase):
    name = "http"
    version = "1.0.0"
    description = "HTTP client and web utilities"

    def get_step_types(self):
        return {
            'http-get': HTTPGetStep,
            'http-post': HTTPPostStep,
            'http-put': HTTPPutStep,
            'http-patch': HTTPPatchStep,
            'http-delete': HTTPDeleteStep,
            'url-build': URLBuildStep,
            'url-parse': URLParseStep,
            'url-escape': URLEscapeStep,
            'json-parse': JSONParseStep,
            'json-stringify': JSONStringifyStep,
            'base64-encode': Base64EncodeStep,
            'base64-decode': Base64DecodeStep,
            'html-strip': HTMLStripStep,
            'html-parse': HTMLParseStep,
        }
```

## Testing Strategy
1. Unit tests for each step
2. Integration tests with mock HTTP server
3. Error handling tests
4. Memory binding tests
5. Template substitution tests

## Documentation Requirements
1. README.md with:
   - Installation instructions
   - Quick start examples
   - All step types with config schemas
   - Common use cases
   - Authentication examples
   - Error handling guide

2. Inline docstrings for all classes and methods

3. Example graphs:
   - Simple HTTP GET
   - REST API workflow (CRUD operations)
   - Web scraping pipeline
   - API integration with auth

## Migration Plan
1. Keep existing `HTTPStep` in `graph-core/steps/llm.py` for backward compatibility
2. Mark it as deprecated
3. Add migration guide in documentation
4. Eventually remove in v2.0.0

## Implementation Phases

### Phase 1: Core HTTP Steps ✅
- [ ] Package setup (setup.py, pyproject.toml)
- [ ] Base HTTP client with shared logic
- [ ] http-get, http-post, http-put, http-patch, http-delete
- [ ] Basic tests
- [ ] README with examples

### Phase 2: URL & Data Steps ✅
- [ ] URL manipulation steps (build, parse, escape)
- [ ] JSON steps (parse, stringify)
- [ ] Base64 steps (encode, decode)
- [ ] Tests for all steps

### Phase 3: HTML Processing ✅
- [ ] html-strip step
- [ ] html-parse step with CSS selectors
- [ ] Tests

### Phase 4: Advanced Features ✅
- [ ] Retry logic with exponential backoff
- [ ] Cookie jar management
- [ ] Session persistence
- [ ] Request/response middleware hooks

### Phase 5: Documentation & Examples ✅
- [ ] Complete README
- [ ] Example graphs
- [ ] API documentation
- [ ] Migration guide

## Notes
- This plugin serves as a reference implementation for future plugins
- Focus on code quality, documentation, and testability
- Use type hints throughout
- Follow GraphFlow step conventions
- Ensure all memory bindings work correctly
