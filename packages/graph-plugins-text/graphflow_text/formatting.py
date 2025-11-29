"""String formatting and case manipulation steps."""
import re
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from .base import BaseTextStep


class StringFormatStep(BaseTextStep):
    """Python f-string style formatting."""

    name = "String Format"
    label = "String Format"
    description = "Format a string template with values from memory"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-format"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "template": {
                    "type": "string",
                    "description": "Template string with {memory.variable} placeholders"
                }
            },
            "required": ["template"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Variables referenced in template will be read from memory"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "Formatted string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        template = self._get_config_value("template", "")

        # Find all {namespace.variable} patterns and replace with values
        pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')

        def replace_match(match):
            namespace = match.group(1)
            field_key = match.group(2)
            full_key = f"{namespace}.{field_key}"
            try:
                value = memory.read(full_key)
                return str(value) if value is not None else ""
            except KeyError:
                return match.group(0)  # Keep original if not found

        result = pattern.sub(replace_match, template)
        self._write_output(memory, "output", result)


class TextCaseStep(BaseTextStep):
    """Change string case."""

    name = "Text Case"
    label = "Text Case"
    description = "Change the case of a string (upper, lower, title, etc.)"

    @classmethod
    def get_type(cls) -> str:
        return "text.text-case"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "case": {
                    "type": "string",
                    "enum": ["upper", "lower", "title", "capitalize", "swapcase"],
                    "default": "lower",
                    "description": "Target case transformation"
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
                    "description": "String to transform"
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
                    "description": "Case-transformed string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        case = self._get_config_value("case", "lower")

        case_methods = {
            "upper": str.upper,
            "lower": str.lower,
            "title": str.title,
            "capitalize": str.capitalize,
            "swapcase": str.swapcase,
        }

        method = case_methods.get(case, str.lower)
        result = method(input_value)
        self._write_output(memory, "output", result)


class StringTrimStep(BaseTextStep):
    """Trim whitespace from string."""

    name = "String Trim"
    label = "String Trim"
    description = "Remove whitespace or specified characters from string ends"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-trim"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "mode": {
                    "type": "string",
                    "enum": ["both", "left", "right"],
                    "default": "both",
                    "description": "Which end(s) to trim"
                },
                "chars": {
                    "type": "string",
                    "default": "",
                    "description": "Characters to trim (empty = whitespace)"
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
                    "description": "String to trim"
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
                    "description": "Trimmed string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        mode = self._get_config_value("mode", "both")
        chars = self._get_config_value("chars", "") or None  # None = whitespace

        if mode == "left":
            result = input_value.lstrip(chars)
        elif mode == "right":
            result = input_value.rstrip(chars)
        else:  # both
            result = input_value.strip(chars)

        self._write_output(memory, "output", result)


class StringPadStep(BaseTextStep):
    """Pad string to specified length."""

    name = "String Pad"
    label = "String Pad"
    description = "Pad a string to a specified length with a fill character"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-pad"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "length": {
                    "type": "integer",
                    "description": "Target length for the padded string"
                },
                "char": {
                    "type": "string",
                    "default": " ",
                    "description": "Character to pad with (default: space)"
                },
                "mode": {
                    "type": "string",
                    "enum": ["left", "right", "center"],
                    "default": "left",
                    "description": "Where to add padding"
                }
            },
            "required": ["input", "length"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "String to pad"
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
                    "description": "Padded string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        length = self._get_config_value("length", 0)
        char = self._get_config_value("char", " ")
        mode = self._get_config_value("mode", "left")

        # Ensure char is a single character
        if len(char) != 1:
            char = char[0] if char else " "

        if mode == "left":
            result = input_value.rjust(length, char)  # rjust pads on left
        elif mode == "right":
            result = input_value.ljust(length, char)  # ljust pads on right
        else:  # center
            result = input_value.center(length, char)

        self._write_output(memory, "output", result)
