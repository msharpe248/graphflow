"""XML processing step implementations."""
import re
from typing import Any, Dict

import xmltodict
from lxml import etree

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="xmlhtml.XMLParseStep", category="xmlhtml", description="Parse XML document", plugin="xmlhtml")
class XMLParseStep(StepBase):
    """Parse XML and extract data step."""

    name = "XML Parse"
    label = "XML Parse"
    description = "Parse XML and extract data using XPath or convert to dict"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.XMLParseStep"

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
                    "description": "Optional XPath expression to extract specific data"
                },
                "namespaces": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Namespace prefix to URI mappings for XPath"
                },
                "as_dict": {
                    "type": "boolean",
                    "default": True,
                    "description": "Convert XML to dict (default: true)"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "xml": {
                    "type": "string",
                    "description": "XML string to parse"
                }
            },
            "required": ["xml"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "description": "Parsed XML data (dict, list, or string depending on options)"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute XML parse."""
        xml_content = memory.read(self.config["input"])
        xpath = self.config.get("xpath")
        namespaces = self.config.get("namespaces", {})
        as_dict = self.config.get("as_dict", True)

        try:
            # Parse XML
            root = etree.fromstring(str(xml_content).encode('utf-8'))

            if xpath:
                # Use XPath to extract data
                results = root.xpath(xpath, namespaces=namespaces)
                if isinstance(results, list):
                    # Convert elements to strings or text
                    result = []
                    for r in results:
                        if isinstance(r, etree._Element):
                            result.append(etree.tostring(r, encoding='unicode'))
                        else:
                            result.append(str(r))
                else:
                    result = results
            elif as_dict:
                # Convert entire XML to dict
                result = xmltodict.parse(str(xml_content))
            else:
                # Return normalized XML string
                result = etree.tostring(root, encoding='unicode', pretty_print=True)

        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML: {e}")

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)


@StepRegistry.register(step_type="xmlhtml.XMLToJSONStep", category="xmlhtml", description="Convert XML to JSON", plugin="xmlhtml")
class XMLToJSONStep(StepBase):
    """Convert XML to JSON/dict step."""

    name = "XML to JSON"
    label = "XML to JSON"
    description = "Convert XML to JSON/dict format"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.XMLToJSONStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "attr_prefix": {
                    "type": "string",
                    "default": "@",
                    "description": "Prefix for attribute keys (default: @)"
                },
                "cdata_key": {
                    "type": "string",
                    "default": "#text",
                    "description": "Key for CDATA/text content (default: #text)"
                },
                "force_list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tag names that should always be lists"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "xml": {
                    "type": "string",
                    "description": "XML string to convert"
                }
            },
            "required": ["xml"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "json": {
                    "type": "object",
                    "description": "XML converted to JSON/dict format"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute XML to JSON conversion."""
        xml_content = memory.read(self.config["input"])
        attr_prefix = self.config.get("attr_prefix", "@")
        cdata_key = self.config.get("cdata_key", "#text")
        force_list = self.config.get("force_list")

        try:
            # Convert XML to dict
            result = xmltodict.parse(
                str(xml_content),
                attr_prefix=attr_prefix,
                cdata_key=cdata_key,
                force_list=force_list
            )
        except Exception as e:
            raise ValueError(f"Failed to convert XML to JSON: {e}")

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)


@StepRegistry.register(step_type="xmlhtml.JSONToXMLStep", category="xmlhtml", description="Convert JSON to XML", plugin="xmlhtml")
class JSONToXMLStep(StepBase):
    """Convert JSON/dict to XML step."""

    name = "JSON to XML"
    label = "JSON to XML"
    description = "Convert JSON/dict to XML format"

    @classmethod
    def get_type(cls) -> str:
        return "xmlhtml.JSONToXMLStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "root": {
                    "type": "string",
                    "description": "Root element name (required if input is not already wrapped)"
                },
                "attr_prefix": {
                    "type": "string",
                    "default": "@",
                    "description": "Prefix for attribute keys (default: @)"
                },
                "cdata_key": {
                    "type": "string",
                    "default": "#text",
                    "description": "Key for CDATA/text content (default: #text)"
                },
                "pretty": {
                    "type": "boolean",
                    "default": True,
                    "description": "Pretty print output XML"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "json": {
                    "description": "JSON/dict to convert to XML"
                }
            },
            "required": ["json"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "xml": {
                    "type": "string",
                    "description": "JSON converted to XML string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute JSON to XML conversion."""
        data = memory.read(self.config["input"])
        root = self.config.get("root")
        attr_prefix = self.config.get("attr_prefix", "@")
        cdata_key = self.config.get("cdata_key", "#text")
        pretty = self.config.get("pretty", True)

        # Ensure data is a dict
        if not isinstance(data, dict):
            raise ValueError("Input must be a dict/object")

        # Wrap in root element if needed
        if root and len(data) != 1:
            data = {root: data}

        try:
            # Convert dict to XML
            result = xmltodict.unparse(
                data,
                pretty=pretty,
                attr_prefix=attr_prefix,
                cdata_key=cdata_key
            )
        except Exception as e:
            raise ValueError(f"Failed to convert JSON to XML: {e}")

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)
