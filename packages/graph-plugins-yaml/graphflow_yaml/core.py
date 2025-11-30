"""Core YAML manipulation steps - parse and stringify."""
import yaml
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from .base import BaseYAMLStep


class YAMLParseStep(BaseYAMLStep):
    """Parse YAML string into object."""

    name = "YAML Parse"
    label = "YAML Parse"
    description = "Parse a YAML string into a Python object/dict"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.parse"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input YAML string using {memory.variable} syntax"
                },
                "safe": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use safe loader (recommended for untrusted input)"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "YAML string to parse"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "description": "Parsed YAML object"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        yaml_string = self._get_input_string(memory, "input")
        safe = self._get_config_value("safe", True)

        try:
            if safe:
                parsed = yaml.safe_load(yaml_string)
            else:
                parsed = yaml.full_load(yaml_string)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML string: {e}")

        self._write_output(memory, "output", parsed)


class YAMLStringifyStep(BaseYAMLStep):
    """Convert object to YAML string."""

    name = "YAML Stringify"
    label = "YAML Stringify"
    description = "Convert a Python object/dict to a YAML string"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.stringify"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input object using {memory.variable} syntax"
                },
                "default_flow_style": {
                    "type": "boolean",
                    "description": "Use flow style (inline) for collections. None=auto, True=always, False=never"
                },
                "indent": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of spaces for indentation"
                },
                "sort_keys": {
                    "type": "boolean",
                    "default": False,
                    "description": "Sort dictionary keys in output"
                },
                "allow_unicode": {
                    "type": "boolean",
                    "default": True,
                    "description": "Allow unicode characters without escaping"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "description": "Object to convert to YAML"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "YAML string representation"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = self._get_input_value(memory, "input")
        default_flow_style = self._get_config_value("default_flow_style")
        indent = self._get_config_value("indent", 2)
        sort_keys = self._get_config_value("sort_keys", False)
        allow_unicode = self._get_config_value("allow_unicode", True)

        try:
            yaml_string = yaml.dump(
                obj,
                default_flow_style=default_flow_style,
                indent=indent,
                sort_keys=sort_keys,
                allow_unicode=allow_unicode
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Cannot convert object to YAML: {e}")

        self._write_output(memory, "output", yaml_string)
