"""Text extraction and substring steps."""
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from .base import BaseTextStep


class SubstringStep(BaseTextStep):
    """Extract substring by index."""

    name = "Substring"
    label = "Substring"
    description = "Extract a portion of a string by start and end index"

    @classmethod
    def get_type(cls) -> str:
        return "text.substring"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "start": {
                    "type": "integer",
                    "default": 0,
                    "description": "Start index (0-based, supports negative)"
                },
                "end": {
                    "type": "integer",
                    "description": "End index (exclusive, supports negative). Omit for end of string."
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
                    "description": "String to extract from"
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
                    "description": "Extracted substring"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        start = self._get_config_value("start", 0)
        end = self._get_config_value("end", None)

        if end is None:
            result = input_value[start:]
        else:
            result = input_value[start:end]

        self._write_output(memory, "output", result)


class TextTruncateStep(BaseTextStep):
    """Truncate text to a maximum length."""

    name = "Text Truncate"
    label = "Text Truncate"
    description = "Truncate text to a specified length with optional suffix"

    @classmethod
    def get_type(cls) -> str:
        return "text.text-truncate"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of output string (including suffix)"
                },
                "suffix": {
                    "type": "string",
                    "default": "...",
                    "description": "Suffix to append when truncated"
                },
                "word_boundary": {
                    "type": "boolean",
                    "default": False,
                    "description": "Truncate at word boundary if possible"
                }
            },
            "required": ["input", "max_length"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "String to truncate"
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
                    "description": "Truncated string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        max_length = self._get_config_value("max_length", 100)
        suffix = self._get_config_value("suffix", "...")
        word_boundary = self._get_config_value("word_boundary", False)

        # If already short enough, return as-is
        if len(input_value) <= max_length:
            self._write_output(memory, "output", input_value)
            return

        # Calculate truncation point
        truncate_at = max_length - len(suffix)

        if truncate_at <= 0:
            # Suffix is longer than max_length, just use suffix
            result = suffix[:max_length]
        else:
            truncated = input_value[:truncate_at]

            if word_boundary:
                # Find last space before truncation point
                last_space = truncated.rfind(' ')
                if last_space > 0:
                    truncated = truncated[:last_space]

            result = truncated + suffix

        self._write_output(memory, "output", result)
