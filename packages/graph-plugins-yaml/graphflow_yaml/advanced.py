"""Advanced YAML manipulation steps - multi-doc, validation, conversion."""
import json
import yaml
import copy
from typing import Any, Dict, List

from graphflow_core.memory import MemoryStore
from .base import BaseYAMLStep


class YAMLParseAllStep(BaseYAMLStep):
    """Parse multi-document YAML into list of objects."""

    name = "YAML Parse All"
    label = "YAML Parse All"
    description = "Parse a multi-document YAML string (documents separated by ---) into a list of objects"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.parse-all"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input YAML string with multiple documents using {memory.variable} syntax"
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
                    "description": "Multi-document YAML string to parse"
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
                    "description": "List of parsed YAML documents"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of documents parsed"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        yaml_string = self._get_input_string(memory, "input")
        safe = self._get_config_value("safe", True)

        try:
            if safe:
                documents = list(yaml.safe_load_all(yaml_string))
            else:
                documents = list(yaml.full_load_all(yaml_string))
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML string: {e}")

        self._write_output(memory, "output", documents)
        self._write_output(memory, "count", len(documents))


class YAMLValidateStep(BaseYAMLStep):
    """Validate YAML syntax."""

    name = "YAML Validate"
    label = "YAML Validate"
    description = "Check if a string is valid YAML syntax"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.validate"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input YAML string using {memory.variable} syntax"
                },
                "strict": {
                    "type": "boolean",
                    "default": False,
                    "description": "Raise error on invalid YAML (otherwise returns false)"
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
                    "description": "YAML string to validate"
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
                    "description": "Whether the YAML is valid"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if invalid"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        yaml_string = self._get_input_string(memory, "input")
        strict = self._get_config_value("strict", False)

        valid = True
        error = None

        try:
            yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            valid = False
            error = str(e)

        if strict and not valid:
            raise ValueError(f"Invalid YAML: {error}")

        self._write_output(memory, "valid", valid)
        self._write_output(memory, "error", error)


class YAMLToJSONStep(BaseYAMLStep):
    """Convert YAML to JSON string."""

    name = "YAML to JSON"
    label = "YAML to JSON"
    description = "Convert a YAML string to a JSON string"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.to-json"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input YAML string using {memory.variable} syntax"
                },
                "indent": {
                    "type": "integer",
                    "description": "Number of spaces for JSON indentation (optional)"
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
                    "description": "YAML string to convert"
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
        yaml_string = self._get_input_string(memory, "input")
        indent = self._get_config_value("indent")

        try:
            obj = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML string: {e}")

        try:
            json_string = json.dumps(obj, indent=indent)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot convert to JSON: {e}")

        self._write_output(memory, "output", json_string)


class JSONToYAMLStep(BaseYAMLStep):
    """Convert JSON string to YAML."""

    name = "JSON to YAML"
    label = "JSON to YAML"
    description = "Convert a JSON string to a YAML string"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.from-json"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON string using {memory.variable} syntax"
                },
                "indent": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of spaces for YAML indentation"
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
                    "description": "JSON string to convert"
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
        json_string = self._get_input_string(memory, "input")
        indent = self._get_config_value("indent", 2)

        try:
            obj = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")

        try:
            yaml_string = yaml.dump(obj, indent=indent, allow_unicode=True)
        except yaml.YAMLError as e:
            raise ValueError(f"Cannot convert to YAML: {e}")

        self._write_output(memory, "output", yaml_string)


class YAMLMergeStep(BaseYAMLStep):
    """Deep merge multiple YAML objects."""

    name = "YAML Merge"
    label = "YAML Merge"
    description = "Deep merge multiple YAML/dict objects into one"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.merge"

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
                    "description": "Base object"
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
                    "description": "Merged object"
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


class YAMLStringifyAllStep(BaseYAMLStep):
    """Convert list of objects to multi-document YAML string."""

    name = "YAML Stringify All"
    label = "YAML Stringify All"
    description = "Convert a list of objects to a multi-document YAML string (separated by ---)"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.stringify-all"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input list of objects using {memory.variable} syntax"
                },
                "indent": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of spaces for indentation"
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
                    "description": "List of objects to convert to YAML documents"
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
                    "description": "Multi-document YAML string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        documents = self._get_input_value(memory, "input")
        indent = self._get_config_value("indent", 2)

        if not isinstance(documents, list):
            documents = [documents]

        try:
            yaml_string = yaml.dump_all(
                documents,
                indent=indent,
                allow_unicode=True,
                explicit_start=True
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Cannot convert objects to YAML: {e}")

        self._write_output(memory, "output", yaml_string)


class YAMLGetStep(BaseYAMLStep):
    """Get a value from YAML/dict by key/path."""

    name = "YAML Get"
    label = "YAML Get"
    description = "Get a value from an object using a dot-notation path"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.get"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input object using {memory.variable} syntax"
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
                    "description": "Object to get value from"
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


class YAMLSetStep(BaseYAMLStep):
    """Set a value in YAML/dict by key/path."""

    name = "YAML Set"
    label = "YAML Set"
    description = "Set a value in an object using a dot-notation path"

    @classmethod
    def get_type(cls) -> str:
        return "yaml.set"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input object using {memory.variable} syntax"
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
                    "description": "Create intermediate objects if they don't exist"
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
                    "description": "Object to modify"
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
                    "description": "Modified object"
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
