"""Basic string manipulation steps."""
from typing import Any, Dict, List

from graphflow_core.memory import MemoryStore
from .base import BaseTextStep


class StringJoinStep(BaseTextStep):
    """Join array of strings into a single string."""

    name = "String Join"
    label = "String Join"
    description = "Join an array of strings with a separator"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-join"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input array using {memory.variable} syntax"
                },
                "separator": {
                    "type": "string",
                    "default": "",
                    "description": "String to insert between elements"
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
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of strings to join"
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
                    "description": "Joined string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_value(memory, "input")
        separator = self._get_config_value("separator", "")

        # Ensure we have a list
        if not isinstance(input_value, list):
            input_value = [input_value]

        # Convert all elements to strings and join
        result = separator.join(str(item) for item in input_value)
        self._write_output(memory, "output", result)


class StringSplitStep(BaseTextStep):
    """Split string into array."""

    name = "String Split"
    label = "String Split"
    description = "Split a string into an array using a separator"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-split"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "separator": {
                    "type": "string",
                    "default": "",
                    "description": "Separator to split on (empty = split each character)"
                },
                "max_split": {
                    "type": "integer",
                    "default": -1,
                    "description": "Maximum number of splits (-1 for unlimited)"
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
                    "description": "String to split"
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
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of string parts"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        separator = self._get_config_value("separator", "")
        max_split = self._get_config_value("max_split", -1)

        if separator == "":
            # Split each character
            result = list(input_value)
        elif max_split == -1:
            result = input_value.split(separator)
        else:
            result = input_value.split(separator, max_split)

        self._write_output(memory, "output", result)


class StringReplaceStep(BaseTextStep):
    """Replace occurrences of a substring (non-regex)."""

    name = "String Replace"
    label = "String Replace"
    description = "Replace occurrences of a substring with another string"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-replace"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "old": {
                    "type": "string",
                    "description": "Substring to find"
                },
                "new": {
                    "type": "string",
                    "default": "",
                    "description": "Replacement string"
                },
                "count": {
                    "type": "integer",
                    "default": -1,
                    "description": "Maximum replacements (-1 for all)"
                }
            },
            "required": ["input", "old"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "String to perform replacement on"
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
                    "description": "String with replacements made"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        old = self._get_config_value("old", "")
        new = self._get_config_value("new", "")
        count = self._get_config_value("count", -1)

        if count == -1:
            result = input_value.replace(old, new)
        else:
            result = input_value.replace(old, new, count)

        self._write_output(memory, "output", result)


class StringReverseStep(BaseTextStep):
    """Reverse a string."""

    name = "String Reverse"
    label = "String Reverse"
    description = "Reverse the characters in a string"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-reverse"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
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
                    "description": "String to reverse"
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
                    "description": "Reversed string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        result = input_value[::-1]
        self._write_output(memory, "output", result)


class StringRepeatStep(BaseTextStep):
    """Repeat a string N times."""

    name = "String Repeat"
    label = "String Repeat"
    description = "Repeat a string a specified number of times"

    @classmethod
    def get_type(cls) -> str:
        return "text.string-repeat"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "count": {
                    "type": "integer",
                    "default": 1,
                    "description": "Number of times to repeat"
                },
                "separator": {
                    "type": "string",
                    "default": "",
                    "description": "String to insert between repetitions"
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
                    "description": "String to repeat"
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
                    "description": "Repeated string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        count = self._get_config_value("count", 1)
        separator = self._get_config_value("separator", "")

        if count <= 0:
            result = ""
        elif separator:
            result = separator.join([input_value] * count)
        else:
            result = input_value * count

        self._write_output(memory, "output", result)
