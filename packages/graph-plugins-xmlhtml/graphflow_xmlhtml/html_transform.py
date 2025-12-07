"""HTML transformation step implementations."""
import re
from typing import Any, Dict, List

import bleach
from bs4 import BeautifulSoup
from lxml import etree
from markdownify import markdownify as md

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="xmlhtml.HTMLToMarkdownStep", category="xmlhtml", description="Convert HTML to Markdown", plugin="xmlhtml")
class HTMLToMarkdownStep(StepBase):
    """Convert HTML content to Markdown format step."""

    name = "HTML to Markdown"
    label = "HTML to Markdown"
    description = "Convert HTML content to Markdown format"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.HTMLToMarkdownStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "heading_style": {
                    "type": "string",
                    "enum": ["atx", "atx_closed", "setext"],
                    "default": "atx",
                    "description": "Heading style: atx (#), atx_closed (# ... #), setext (underline)"
                },
                "bullets": {
                    "type": "string",
                    "default": "-",
                    "description": "Character to use for bullet points (-, *, +)"
                },
                "code_language": {
                    "type": "string",
                    "default": "",
                    "description": "Default language for code blocks"
                },
                "strip_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to strip (remove content entirely)"
                },
                "convert_as_inline": {
                    "type": "boolean",
                    "default": False,
                    "description": "Convert block elements as inline"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to convert"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "markdown": {
                    "type": "string",
                    "description": "Converted Markdown content"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML to Markdown conversion."""
        html_content = memory.read(self.config["input"])
        heading_style = self.config.get("heading_style", "atx")
        bullets = self.config.get("bullets", "-")
        code_language = self.config.get("code_language", "")
        strip_tags = self.config.get("strip_tags", [])
        convert_as_inline = self.config.get("convert_as_inline", False)

        # Convert to markdown
        result = md(
            str(html_content),
            heading_style=heading_style,
            bullets=bullets,
            code_language=code_language,
            strip=strip_tags if strip_tags else None,
            convert_as_inline=convert_as_inline
        )

        # Clean up extra whitespace
        result = re.sub(r'\n{3,}', '\n\n', result).strip()

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)


@StepRegistry.register(step_type="xmlhtml.HTMLCleanStep", category="xmlhtml", description="Sanitize HTML content", plugin="xmlhtml")
class HTMLCleanStep(StepBase):
    """Sanitize HTML by removing dangerous tags and attributes step."""

    name = "HTML Clean"
    label = "HTML Clean"
    description = "Sanitize HTML by removing dangerous tags and attributes"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.HTMLCleanStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "allowed_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to allow (default: basic safe tags)"
                },
                "allowed_attributes": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "description": "Attributes to allow per tag (e.g., {'a': ['href']})"
                },
                "strip": {
                    "type": "boolean",
                    "default": True,
                    "description": "Strip disallowed tags (true) or escape them (false)"
                },
                "strip_comments": {
                    "type": "boolean",
                    "default": True,
                    "description": "Strip HTML comments"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to sanitize"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "Sanitized HTML content"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML clean."""
        html_content = memory.read(self.config["input"])

        # Default safe tags
        default_tags = [
            'a', 'abbr', 'acronym', 'address', 'b', 'big', 'blockquote',
            'br', 'center', 'cite', 'code', 'col', 'colgroup', 'dd',
            'del', 'dfn', 'dir', 'div', 'dl', 'dt', 'em', 'font',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
            'ins', 'kbd', 'li', 'ol', 'p', 'pre', 'q', 's', 'samp',
            'small', 'span', 'strike', 'strong', 'sub', 'sup', 'table',
            'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'tt', 'u', 'ul', 'var'
        ]

        # Default safe attributes
        default_attributes = {
            'a': ['href', 'title'],
            'abbr': ['title'],
            'acronym': ['title'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'table': ['border', 'cellpadding', 'cellspacing'],
            '*': ['class', 'id']
        }

        allowed_tags = self.config.get("allowed_tags", default_tags)
        allowed_attributes = self.config.get("allowed_attributes", default_attributes)
        strip = self.config.get("strip", True)
        strip_comments = self.config.get("strip_comments", True)

        # Clean HTML with bleach
        result = bleach.clean(
            str(html_content),
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=strip,
            strip_comments=strip_comments
        )

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)


@StepRegistry.register(step_type="xmlhtml.XPathStep", category="xmlhtml", description="Query with XPath", plugin="xmlhtml")
class XPathStep(StepBase):
    """Query XML/HTML using XPath expressions step."""

    name = "XPath Query"
    label = "XPath Query"
    description = "Query XML/HTML using XPath expressions"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.XPathStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "xpath": {
                    "type": "string",
                    "description": "XPath expression to evaluate"
                },
                "namespaces": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Namespace prefix to URI mappings"
                },
                "mode": {
                    "type": "string",
                    "enum": ["xml", "html"],
                    "default": "html",
                    "description": "Parse mode: xml for strict XML, html for HTML"
                },
                "extract": {
                    "type": "string",
                    "enum": ["text", "html", "string", "all"],
                    "default": "text",
                    "description": "What to extract from results"
                },
                "first_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return only the first match"
                }
            },
            "required": ["input", "xpath"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "XML or HTML content to query"
                }
            },
            "required": ["content"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "results": {
                    "description": "XPath query results (list or single value)"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of matches"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute XPath query."""
        content = memory.read(self.config["input"])
        xpath_expr = self.config["xpath"]
        namespaces = self.config.get("namespaces", {})
        mode = self.config.get("mode", "html")
        extract = self.config.get("extract", "text")
        first_only = self.config.get("first_only", False)

        try:
            # Parse content
            if mode == "html":
                parser = etree.HTMLParser()
                tree = etree.fromstring(str(content).encode('utf-8'), parser)
            else:
                tree = etree.fromstring(str(content).encode('utf-8'))

            # Execute XPath
            results = tree.xpath(xpath_expr, namespaces=namespaces)

            # Process results
            processed = []
            for r in results:
                if isinstance(r, etree._Element):
                    if extract == "html":
                        processed.append(etree.tostring(r, encoding='unicode'))
                    elif extract == "text":
                        text = etree.tostring(r, method='text', encoding='unicode')
                        processed.append(text.strip() if text else "")
                    elif extract == "string":
                        processed.append(etree.tostring(r, encoding='unicode', method='text'))
                    else:  # all
                        processed.append({
                            "tag": r.tag,
                            "text": r.text,
                            "tail": r.tail,
                            "attrib": dict(r.attrib),
                            "html": etree.tostring(r, encoding='unicode')
                        })
                elif isinstance(r, etree._ElementUnicodeResult):
                    processed.append(str(r))
                else:
                    processed.append(r)

            # Return single or multiple results
            if first_only:
                final_result = processed[0] if processed else None
            else:
                final_result = processed

            result = {
                "results": final_result,
                "count": len(results)
            }

        except etree.XPathEvalError as e:
            raise ValueError(f"Invalid XPath expression: {e}")
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML/HTML content: {e}")

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)
