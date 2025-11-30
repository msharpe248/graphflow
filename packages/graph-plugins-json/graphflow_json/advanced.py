"""Advanced JSON manipulation steps - path queries, merge, schema validation."""
import json
import copy
from typing import Any, Dict, List, Optional, Union

from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError
import jsonschema
from jsonschema import ValidationError, SchemaError

from graphflow_core.memory import MemoryStore
from .base import BaseJSONStep


class JSONPathStep(BaseJSONStep):
    """Extract values using JSONPath expressions."""

    name = "JSON Path"
    label = "JSON Path"
    description = "Extract values from JSON using JSONPath expressions"

    @classmethod
    def get_type(cls) -> str:
        return "json.path"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON object using {memory.variable} syntax"
                },
                "expression": {
                    "type": "string",
                    "description": "JSONPath expression (e.g., '$.store.book[*].author')"
                },
                "first_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return only the first match instead of all matches"
                }
            },
            "required": ["input", "expression"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "description": "JSON object to query"
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
                    "description": "Extracted value(s)"
                },
                "found": {
                    "type": "boolean",
                    "description": "Whether any matches were found"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = self._get_input_value(memory, "input")
        expression = self._get_config_value("expression", "$")
        first_only = self._get_config_value("first_only", False)

        try:
            jsonpath_expr = jsonpath_parse(expression)
        except JsonPathParserError as e:
            raise ValueError(f"Invalid JSONPath expression: {e}")

        matches = jsonpath_expr.find(obj)

        if matches:
            if first_only:
                result = matches[0].value
            else:
                result = [match.value for match in matches]
            found = True
        else:
            result = None if first_only else []
            found = False

        self._write_output(memory, "output", result)
        self._write_output(memory, "found", found)


class JSONMergeStep(BaseJSONStep):
    """Deep merge multiple JSON objects."""

    name = "JSON Merge"
    label = "JSON Merge"
    description = "Deep merge multiple JSON objects into one"

    @classmethod
    def get_type(cls) -> str:
        return "json.merge"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base": {
                    "type": "string",
                    "description": "Base object using {memory.variable} syntax"
                },
                "overlay": {
                    "type": "string",
                    "description": "Object to merge on top using {memory.variable} syntax"
                },
                "strategy": {
                    "type": "string",
                    "enum": ["replace", "append", "deep"],
                    "default": "deep",
                    "description": "Merge strategy: replace (overwrite), append (arrays), deep (recursive)"
                }
            },
            "required": ["base", "overlay"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base": {
                    "type": "object",
                    "description": "Base JSON object"
                },
                "overlay": {
                    "type": "object",
                    "description": "Object to merge on top"
                }
            },
            "required": ["base", "overlay"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "object",
                    "description": "Merged JSON object"
                }
            }
        }

    def _deep_merge(self, base: Any, overlay: Any, strategy: str) -> Any:
        """Recursively merge two objects."""
        if strategy == "replace":
            return copy.deepcopy(overlay)

        if isinstance(base, dict) and isinstance(overlay, dict):
            result = copy.deepcopy(base)
            for key, value in overlay.items():
                if key in result:
                    result[key] = self._deep_merge(result[key], value, strategy)
                else:
                    result[key] = copy.deepcopy(value)
            return result

        if isinstance(base, list) and isinstance(overlay, list):
            if strategy == "append":
                return copy.deepcopy(base) + copy.deepcopy(overlay)
            else:
                return copy.deepcopy(overlay)

        return copy.deepcopy(overlay)

    async def execute(self, memory: MemoryStore) -> None:
        base = self._get_input_value(memory, "base")
        overlay = self._get_input_value(memory, "overlay")
        strategy = self._get_config_value("strategy", "deep")

        result = self._deep_merge(base, overlay, strategy)
        self._write_output(memory, "output", result)


class JSONSchemaValidateStep(BaseJSONStep):
    """Validate JSON against a JSON Schema."""

    name = "JSON Schema Validate"
    label = "JSON Schema Validate"
    description = "Validate a JSON object against a JSON Schema"

    @classmethod
    def get_type(cls) -> str:
        return "json.schema-validate"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON object using {memory.variable} syntax"
                },
                "schema": {
                    "type": "object",
                    "description": "JSON Schema to validate against",
                    "x-editor": "json"
                },
                "strict": {
                    "type": "boolean",
                    "default": False,
                    "description": "Raise error on validation failure (otherwise returns false)"
                }
            },
            "required": ["input", "schema"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "description": "JSON object to validate"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "valid": {
                    "type": "boolean",
                    "description": "Whether the JSON is valid"
                },
                "errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of validation error messages"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = self._get_input_value(memory, "input")
        schema = self._get_config_value("schema", {})
        strict = self._get_config_value("strict", False)

        errors = []
        valid = True

        try:
            jsonschema.validate(instance=obj, schema=schema)
        except ValidationError as e:
            valid = False
            errors.append(str(e.message))
        except SchemaError as e:
            raise ValueError(f"Invalid JSON Schema: {e.message}")

        if strict and not valid:
            raise ValueError(f"JSON validation failed: {'; '.join(errors)}")

        self._write_output(memory, "valid", valid)
        self._write_output(memory, "errors", errors)


class JSONGetStep(BaseJSONStep):
    """Get a value from JSON by key/path."""

    name = "JSON Get"
    label = "JSON Get"
    description = "Get a value from a JSON object using a dot-notation path"

    @classmethod
    def get_type(cls) -> str:
        return "json.get"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON object using {memory.variable} syntax"
                },
                "path": {
                    "type": "string",
                    "description": "Dot-notation path (e.g., 'user.address.city')"
                },
                "default": {
                    "description": "Default value if path not found"
                }
            },
            "required": ["input", "path"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "object",
                    "description": "JSON object to get value from"
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
                    "description": "Value at the path"
                },
                "found": {
                    "type": "boolean",
                    "description": "Whether the path was found"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = self._get_input_value(memory, "input")
        path = self._get_config_value("path", "")
        default = self._get_config_value("default")

        # Navigate the path
        current = obj
        found = True
        parts = path.split('.') if path else []

        for part in parts:
            # Handle array index notation like "items[0]"
            if '[' in part and part.endswith(']'):
                key = part[:part.index('[')]
                index = int(part[part.index('[') + 1:-1])
                if isinstance(current, dict) and key in current:
                    current = current[key]
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        found = False
                        break
                else:
                    found = False
                    break
            elif isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        found = False
                        break
                except ValueError:
                    found = False
                    break
            else:
                found = False
                break

        result = current if found else default
        self._write_output(memory, "output", result)
        self._write_output(memory, "found", found)


class JSONSetStep(BaseJSONStep):
    """Set a value in JSON by key/path."""

    name = "JSON Set"
    label = "JSON Set"
    description = "Set a value in a JSON object using a dot-notation path"

    @classmethod
    def get_type(cls) -> str:
        return "json.set"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON object using {memory.variable} syntax"
                },
                "path": {
                    "type": "string",
                    "description": "Dot-notation path (e.g., 'user.address.city')"
                },
                "value": {
                    "type": "string",
                    "description": "Value to set using {memory.variable} syntax or literal"
                },
                "create_path": {
                    "type": "boolean",
                    "default": True,
                    "description": "Create intermediate objects/arrays if they don't exist"
                }
            },
            "required": ["input", "path", "value"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "object",
                    "description": "JSON object to modify"
                },
                "value": {
                    "description": "Value to set"
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
                    "type": "object",
                    "description": "Modified JSON object"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = copy.deepcopy(self._get_input_value(memory, "input"))
        path = self._get_config_value("path", "")
        create_path = self._get_config_value("create_path", True)

        # Get value - check if it's a memory reference
        value_config = self._get_config_value("value")
        if isinstance(value_config, str) and self._memory_pattern.search(value_config):
            match = self._memory_pattern.search(value_config)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                value = memory.read(f"{namespace}.{field_key}")
            else:
                value = value_config
        else:
            value = value_config

        # Navigate and set
        current = obj
        parts = path.split('.') if path else []

        for i, part in enumerate(parts[:-1]):
            if isinstance(current, dict):
                if part not in current:
                    if create_path:
                        # Peek at next part to decide dict vs list
                        next_part = parts[i + 1]
                        try:
                            int(next_part)
                            current[part] = []
                        except ValueError:
                            current[part] = {}
                    else:
                        raise ValueError(f"Path not found: {'.'.join(parts[:i + 1])}")
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    while len(current) <= idx:
                        current.append({})
                    current = current[idx]
                except ValueError:
                    raise ValueError(f"Cannot use string key '{part}' on array")

        # Set the final value
        if parts:
            final_key = parts[-1]
            if isinstance(current, dict):
                current[final_key] = value
            elif isinstance(current, list):
                try:
                    idx = int(final_key)
                    while len(current) <= idx:
                        current.append(None)
                    current[idx] = value
                except ValueError:
                    raise ValueError(f"Cannot use string key '{final_key}' on array")

        self._write_output(memory, "output", obj)


class JSONKeysStep(BaseJSONStep):
    """Get all keys from a JSON object."""

    name = "JSON Keys"
    label = "JSON Keys"
    description = "Get all keys from a JSON object"

    @classmethod
    def get_type(cls) -> str:
        return "json.keys"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON object using {memory.variable} syntax"
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
                    "type": "object",
                    "description": "JSON object to get keys from"
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
                    "description": "Array of keys"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = self._get_input_value(memory, "input")

        if not isinstance(obj, dict):
            raise ValueError("Input must be a JSON object (dict)")

        keys = list(obj.keys())
        self._write_output(memory, "output", keys)


class JSONValuesStep(BaseJSONStep):
    """Get all values from a JSON object."""

    name = "JSON Values"
    label = "JSON Values"
    description = "Get all values from a JSON object"

    @classmethod
    def get_type(cls) -> str:
        return "json.values"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON object using {memory.variable} syntax"
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
                    "type": "object",
                    "description": "JSON object to get values from"
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
                    "description": "Array of values"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        obj = self._get_input_value(memory, "input")

        if not isinstance(obj, dict):
            raise ValueError("Input must be a JSON object (dict)")

        values = list(obj.values())
        self._write_output(memory, "output", values)
