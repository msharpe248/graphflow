"""HTML extraction step implementations."""
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="xmlhtml.HTMLSelectAllStep", category="xmlhtml", description="Select HTML elements", plugin="xmlhtml")
class HTMLSelectAllStep(StepBase):
    """Select all elements matching a CSS selector step."""

    name = "HTML Select All"
    label = "HTML Select All"
    description = "Select all elements matching a CSS selector"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.HTMLSelectAllStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector to match elements"
                },
                "extract": {
                    "type": "string",
                    "enum": ["html", "text", "outer_html"],
                    "default": "text",
                    "description": "What to extract: html (inner), text, or outer_html"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum number of elements to return"
                }
            },
            "required": ["input", "selector"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to search"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of matching elements"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of matching elements"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML select all."""
        html_content = memory.read(self.config["input"])
        selector = self.config["selector"]
        extract = self.config.get("extract", "text")
        limit = self.config.get("limit")

        soup = BeautifulSoup(str(html_content), 'lxml')
        elements = soup.select(selector)

        if limit:
            elements = elements[:limit]

        results = []
        for elem in elements:
            if extract == "html":
                results.append(elem.decode_contents())
            elif extract == "outer_html":
                results.append(str(elem))
            else:  # text
                results.append(elem.get_text().strip())

        result = {
            "elements": results,
            "count": len(results)
        }

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)


@StepRegistry.register(step_type="xmlhtml.HTMLAttributeExtractStep", category="xmlhtml", description="Extract HTML attributes", plugin="xmlhtml")
class HTMLAttributeExtractStep(StepBase):
    """Extract specific attributes from HTML elements step."""

    name = "HTML Attribute Extract"
    label = "HTML Attribute Extract"
    description = "Extract specific attributes from HTML elements"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.HTMLAttributeExtractStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector to match elements"
                },
                "attributes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attributes to extract"
                },
                "include_text": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include text content of elements"
                }
            },
            "required": ["input", "selector", "attributes"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to search"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of objects with requested attributes"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML attribute extract."""
        html_content = memory.read(self.config["input"])
        selector = self.config["selector"]
        attributes = self.config["attributes"]
        include_text = self.config.get("include_text", False)

        soup = BeautifulSoup(str(html_content), 'lxml')
        elements = soup.select(selector)

        results = []
        for elem in elements:
            item = {}
            for attr in attributes:
                item[attr] = elem.get(attr)
            if include_text:
                item["text"] = elem.get_text().strip()
            results.append(item)

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", results)


@StepRegistry.register(step_type="xmlhtml.HTMLFormExtractStep", category="xmlhtml", description="Extract HTML form data", plugin="xmlhtml")
class HTMLFormExtractStep(StepBase):
    """Extract form fields and values from HTML forms step."""

    name = "HTML Form Extract"
    label = "HTML Form Extract"
    description = "Extract form fields and values from HTML forms"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.HTMLFormExtractStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "form_selector": {
                    "type": "string",
                    "default": "form",
                    "description": "CSS selector to find form (default: first form)"
                },
                "include_hidden": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include hidden input fields"
                },
                "include_disabled": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include disabled input fields"
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
                    "description": "HTML content with form"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "form": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "method": {"type": "string"},
                        "fields": {"type": "object"}
                    },
                    "description": "Form data including action, method, and fields"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML form extract."""
        html_content = memory.read(self.config["input"])
        form_selector = self.config.get("form_selector", "form")
        include_hidden = self.config.get("include_hidden", True)
        include_disabled = self.config.get("include_disabled", False)

        soup = BeautifulSoup(str(html_content), 'lxml')
        form = soup.select_one(form_selector)

        if not form:
            result = {
                "action": None,
                "method": None,
                "fields": {}
            }
        else:
            result = {
                "action": form.get("action"),
                "method": form.get("method", "GET").upper(),
                "fields": {}
            }

            # Extract input fields
            for input_elem in form.find_all("input"):
                input_type = input_elem.get("type", "text").lower()
                name = input_elem.get("name")

                if not name:
                    continue

                # Skip hidden if not requested
                if input_type == "hidden" and not include_hidden:
                    continue

                # Skip disabled if not requested
                if input_elem.get("disabled") and not include_disabled:
                    continue

                value = input_elem.get("value", "")

                # Handle checkbox/radio
                if input_type in ("checkbox", "radio"):
                    if input_elem.get("checked"):
                        result["fields"][name] = value or "on"
                else:
                    result["fields"][name] = value

            # Extract select fields
            for select_elem in form.find_all("select"):
                name = select_elem.get("name")
                if not name:
                    continue

                if select_elem.get("disabled") and not include_disabled:
                    continue

                selected = select_elem.find("option", selected=True)
                if selected:
                    result["fields"][name] = selected.get("value", selected.get_text().strip())
                else:
                    first_option = select_elem.find("option")
                    if first_option:
                        result["fields"][name] = first_option.get("value", first_option.get_text().strip())

            # Extract textarea fields
            for textarea_elem in form.find_all("textarea"):
                name = textarea_elem.get("name")
                if not name:
                    continue

                if textarea_elem.get("disabled") and not include_disabled:
                    continue

                result["fields"][name] = textarea_elem.get_text()

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)


@StepRegistry.register(step_type="xmlhtml.HTMLMetaExtractStep", category="xmlhtml", description="Extract HTML meta tags", plugin="xmlhtml")
class HTMLMetaExtractStep(StepBase):
    """Extract meta tags, title, and OpenGraph data from HTML step."""

    name = "HTML Meta Extract"
    label = "HTML Meta Extract"
    description = "Extract meta tags, title, and OpenGraph data from HTML"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.HTMLMetaExtractStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "include_opengraph": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include OpenGraph (og:) meta tags"
                },
                "include_twitter": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include Twitter Card meta tags"
                },
                "include_links": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include link tags (canonical, alternate, etc.)"
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
                    "description": "HTML content to extract meta from"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "meta": {
                    "type": "object",
                    "description": "Extracted meta data including title, description, keywords, etc."
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML meta extract."""
        html_content = memory.read(self.config["input"])
        include_opengraph = self.config.get("include_opengraph", True)
        include_twitter = self.config.get("include_twitter", True)
        include_links = self.config.get("include_links", True)

        soup = BeautifulSoup(str(html_content), 'lxml')

        result = {
            "title": None,
            "description": None,
            "keywords": None,
            "author": None,
            "charset": None,
            "viewport": None,
            "robots": None,
        }

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            result["title"] = title_tag.get_text().strip()

        # Extract standard meta tags
        meta_mappings = {
            "description": "description",
            "keywords": "keywords",
            "author": "author",
            "viewport": "viewport",
            "robots": "robots",
        }

        for meta in soup.find_all("meta"):
            name = meta.get("name", "").lower()
            if name in meta_mappings:
                result[meta_mappings[name]] = meta.get("content")

            # Charset
            if meta.get("charset"):
                result["charset"] = meta.get("charset")
            elif meta.get("http-equiv", "").lower() == "content-type":
                content = meta.get("content", "")
                if "charset=" in content:
                    result["charset"] = content.split("charset=")[-1].strip()

        # Extract OpenGraph tags
        if include_opengraph:
            result["opengraph"] = {}
            for meta in soup.find_all("meta", property=re.compile(r'^og:')):
                prop = meta.get("property", "")[3:]  # Remove 'og:' prefix
                if prop:
                    result["opengraph"][prop] = meta.get("content")

        # Extract Twitter Card tags
        if include_twitter:
            result["twitter"] = {}
            for meta in soup.find_all("meta", attrs={"name": re.compile(r'^twitter:')}):
                name = meta.get("name", "")[8:]  # Remove 'twitter:' prefix
                if name:
                    result["twitter"][name] = meta.get("content")

        # Extract link tags
        if include_links:
            result["links"] = {}
            for link in soup.find_all("link"):
                rel = link.get("rel", [])
                if isinstance(rel, list):
                    rel = " ".join(rel)
                href = link.get("href")
                if rel and href:
                    if rel not in result["links"]:
                        result["links"][rel] = href
                    else:
                        # Handle multiple links with same rel
                        if not isinstance(result["links"][rel], list):
                            result["links"][rel] = [result["links"][rel]]
                        result["links"][rel].append(href)

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)
