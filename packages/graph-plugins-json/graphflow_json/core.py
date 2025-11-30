"""Core JSON manipulation steps - parse and stringify."""
import json
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from .base import BaseJSONStep


class JSONParseStep(BaseJSONStep):
    """Parse JSON string into object."""

    name = "JSON Parse"
    label = "JSON Parse"
    description = "Parse a JSON string into a Python object/dict"

    @classmethod
    def get_type(cls) -> str:
        return "json.parse"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON string using {memory.variable} syntax"
                },
                "strict": {
                    "type": "boolean",
                    "default": True,
                    "description": "If false, allows trailing commas and comments"
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
                    "description": "JSON string to parse"
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
                    "description": "Parsed JSON object"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        json_string = self._get_input_string(memory, "input")

        try:
            parsed = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")

        self._write_output(memory, "output", parsed)


class JSONStringifyStep(BaseJSONStep):
    """Convert object to JSON string."""

    name = "JSON Stringify"
    label = "JSON Stringify"
    description = "Convert a Python object/dict to a JSON string"

    @classmethod
    def get_type(cls) -> str:
        return "json.stringify"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input object using {memory.variable} syntax"
                },
                "indent": {
                    "type": "integer",
                    "description": "Number of spaces for indentation (optional, for pretty printing)"
                },
                "sort_keys": {
                    "type": "boolean",
                    "default": False,
                    "description": "Sort dictionary keys in output"
                },
                "ensure_ascii": {
                    "type": "boolean",
                    "default": True,
                    "description": "Escape non-ASCII characters"
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
                    "description": "Object to convert to JSON"
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
                    "description": "JSON string representation"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = self._get_input_value(memory, "input")
        indent = self._get_config_value("indent")
        sort_keys = self._get_config_value("sort_keys", False)
        ensure_ascii = self._get_config_value("ensure_ascii", True)

        try:
            json_string = json.dumps(
                obj,
                indent=indent,
                sort_keys=sort_keys,
                ensure_ascii=ensure_ascii
            )
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot convert object to JSON: {e}")

        self._write_output(memory, "output", json_string)
