# GraphFlow XML & HTML Plugin

XML parsing and HTML manipulation utilities for GraphFlow.

## Installation

```bash
pip install -e packages/graph-plugins-xmlhtml
```

## Steps Provided

### HTML Core

| Step | Description |
|------|-------------|
| `xmlhtml.HTMLStripStep` | Remove HTML tags, leaving only text |
| `xmlhtml.HTMLParseStep` | Extract data using CSS selectors |
| `xmlhtml.HTMLFindLinksStep` | Extract all links from HTML |
| `xmlhtml.HTMLTableExtractStep` | Extract table data into structured format |

### HTML Extraction

| Step | Description |
|------|-------------|
| `xmlhtml.HTMLSelectAllStep` | Select all elements matching a CSS selector |
| `xmlhtml.HTMLAttributeExtractStep` | Extract specific attributes from elements |
| `xmlhtml.HTMLFormExtractStep` | Extract form fields and values |
| `xmlhtml.HTMLMetaExtractStep` | Extract meta tags, title, and OpenGraph data |

### HTML Transform

| Step | Description |
|------|-------------|
| `xmlhtml.HTMLToMarkdownStep` | Convert HTML to Markdown |
| `xmlhtml.HTMLCleanStep` | Sanitize HTML (remove dangerous tags) |
| `xmlhtml.XPathStep` | Query XML/HTML using XPath expressions |

### XML Operations

| Step | Description |
|------|-------------|
| `xmlhtml.XMLParseStep` | Parse XML with optional XPath extraction |
| `xmlhtml.XMLToJSONStep` | Convert XML to JSON/dict format |
| `xmlhtml.JSONToXMLStep` | Convert JSON/dict to XML |

## Examples

### HTML Strip

Remove all HTML tags and get plain text:

```json
{
  "id": "strip_1",
  "type": "xmlhtml.HTMLStripStep",
  "config": {
    "input": "{memory.html_content}",
    "separator": " ",
    "strip_whitespace": true
  },
  "outputs": {
    "output": "{memory.plain_text}"
  }
}
```

### HTML Parse with CSS Selectors

Extract data using CSS selectors:

```json
{
  "id": "parse_1",
  "type": "xmlhtml.HTMLParseStep",
  "config": {
    "input": "{memory.html_content}",
    "selectors": {
      "title": {"selector": "h1", "attribute": null, "multiple": false},
      "links": {"selector": "a", "attribute": "href", "multiple": true},
      "paragraphs": {"selector": "p", "attribute": null, "multiple": true}
    }
  },
  "outputs": {
    "output": "{memory.extracted_data}"
  }
}
```

### HTML to Markdown

Convert HTML content to Markdown:

```json
{
  "id": "to_md_1",
  "type": "xmlhtml.HTMLToMarkdownStep",
  "config": {
    "input": "{memory.html_content}",
    "heading_style": "atx",
    "bullets": "-"
  },
  "outputs": {
    "output": "{memory.markdown_content}"
  }
}
```

### Extract Meta Tags

Extract SEO and OpenGraph metadata:

```json
{
  "id": "meta_1",
  "type": "xmlhtml.HTMLMetaExtractStep",
  "config": {
    "input": "{memory.html_content}",
    "include_opengraph": true,
    "include_twitter": true,
    "include_links": true
  },
  "outputs": {
    "output": "{memory.page_metadata}"
  }
}
```

### XML Parse with XPath

Parse XML and extract data using XPath:

```json
{
  "id": "xml_1",
  "type": "xmlhtml.XMLParseStep",
  "config": {
    "input": "{memory.xml_content}",
    "xpath": "//item/title/text()",
    "namespaces": {}
  },
  "outputs": {
    "output": "{memory.titles}"
  }
}
```

### XML to JSON Conversion

```json
{
  "id": "xml_to_json_1",
  "type": "xmlhtml.XMLToJSONStep",
  "config": {
    "input": "{memory.xml_content}",
    "attr_prefix": "@",
    "cdata_key": "#text"
  },
  "outputs": {
    "output": "{memory.json_data}"
  }
}
```

### HTML Form Extraction

Extract all form fields and their values:

```json
{
  "id": "form_1",
  "type": "xmlhtml.HTMLFormExtractStep",
  "config": {
    "input": "{memory.html_content}",
    "form_selector": "form#login",
    "include_hidden": true
  },
  "outputs": {
    "output": "{memory.form_data}"
  }
}
```

## Dependencies

- `beautifulsoup4` - HTML/XML parsing
- `lxml` - Fast XML/HTML parser and XPath support
- `xmltodict` - XML to dict conversion
- `markdownify` - HTML to Markdown conversion
- `bleach` - HTML sanitization

## License

MIT
