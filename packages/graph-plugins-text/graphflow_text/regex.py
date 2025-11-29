"""Regex matching and replacement steps."""
import re
from typing import Any, Dict, List, Optional, Union

from graphflow_core.memory import MemoryStore
from .base import BaseTextStep


class RegexMatchStep(BaseTextStep):
    """Extract regex matches from string."""

    name = "Regex Match"
    label = "Regex Match"
    description = "Extract matches from a string using a regular expression"

    @classmethod
    def get_type(cls) -> str:
        return "text.regex-match"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern"
                },
                "flags": {
                    "type": "string",
                    "default": "",
                    "description": "Regex flags: i=ignorecase, m=multiline, s=dotall"
                },
                "find_all": {
                    "type": "boolean",
                    "default": False,
                    "description": "Find all matches (True) or just first (False)"
                },
                "groups": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return captured groups instead of full match"
                }
            },
            "required": ["input", "pattern"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "String to search"
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
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "null"}
                    ],
                    "description": "Match result(s) or null if no match"
                },
                "found": {
                    "type": "boolean",
                    "description": "Whether a match was found"
                }
            }
        }

    def _parse_flags(self, flags_str: str) -> int:
        """Convert flag string to re flags."""
        flags = 0
        if 'i' in flags_str.lower():
            flags |= re.IGNORECASE
        if 'm' in flags_str.lower():
            flags |= re.MULTILINE
        if 's' in flags_str.lower():
            flags |= re.DOTALL
        return flags

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        pattern = self._get_config_value("pattern", "")
        flags_str = self._get_config_value("flags", "")
        find_all = self._get_config_value("find_all", False)
        return_groups = self._get_config_value("groups", False)

        flags = self._parse_flags(flags_str)
        compiled = re.compile(pattern, flags)

        if find_all:
            matches = compiled.findall(input_value)
            if matches:
                # findall returns groups if they exist, otherwise full matches
                result = matches
                found = True
            else:
                result = []
                found = False
        else:
            match = compiled.search(input_value)
            if match:
                if return_groups and match.groups():
                    # Return captured groups as list
                    result = list(match.groups())
                else:
                    result = match.group(0)
                found = True
            else:
                result = None
                found = False

        self._write_output(memory, "output", result)
        self._write_output(memory, "found", found)


class RegexReplaceStep(BaseTextStep):
    """Replace using regex pattern."""

    name = "Regex Replace"
    label = "Regex Replace"
    description = "Replace text matching a regex pattern"

    @classmethod
    def get_type(cls) -> str:
        return "text.regex-replace"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input string using {memory.variable} syntax"
                },
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern to match"
                },
                "replacement": {
                    "type": "string",
                    "default": "",
                    "description": "Replacement string (supports \\1, \\2 for groups)"
                },
                "flags": {
                    "type": "string",
                    "default": "",
                    "description": "Regex flags: i=ignorecase, m=multiline, s=dotall"
                },
                "count": {
                    "type": "integer",
                    "default": 0,
                    "description": "Max replacements (0 = all)"
                }
            },
            "required": ["input", "pattern"]
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
                },
                "count": {
                    "type": "integer",
                    "description": "Number of replacements made"
                }
            }
        }

    def _parse_flags(self, flags_str: str) -> int:
        """Convert flag string to re flags."""
        flags = 0
        if 'i' in flags_str.lower():
            flags |= re.IGNORECASE
        if 'm' in flags_str.lower():
            flags |= re.MULTILINE
        if 's' in flags_str.lower():
            flags |= re.DOTALL
        return flags

    async def execute(self, memory: MemoryStore) -> None:
        input_value = self._get_input_string(memory, "input")
        pattern = self._get_config_value("pattern", "")
        replacement = self._get_config_value("replacement", "")
        flags_str = self._get_config_value("flags", "")
        count = self._get_config_value("count", 0)

        flags = self._parse_flags(flags_str)
        compiled = re.compile(pattern, flags)

        result, num_replacements = compiled.subn(replacement, input_value, count=count)

        self._write_output(memory, "output", result)
        self._write_output(memory, "count", num_replacements)
