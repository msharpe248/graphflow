"""Data transformation step implementations - Base64 encoding/decoding."""
import base64
import re
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


class Base64EncodeStep(StepBase):
    """Encode data to Base64 step."""

    name = "Base64 Encode"
    label = "Base64 Encode"
    description = "Encode a string or bytes to Base64"
    category = "http"

    @classmethod
    def get_type(cls) -> str:
        return "base64-encode"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "Text encoding to use if input is string (default: utf-8)"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "description": "String or bytes to encode"
                }
            },
            "required": ["data"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base64": {
                    "type": "string",
                    "description": "Base64 encoded string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute Base64 encode."""
        data = memory.read(self.config["input_key"])
        encoding = self.config.get("encoding", "utf-8")

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            # Try to convert to string first
            data_bytes = str(data).encode(encoding)

        # Encode to Base64
        encoded = base64.b64encode(data_bytes).decode('ascii')

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", encoded)


class Base64DecodeStep(StepBase):
    """Decode Base64 data step."""

    name = "Base64 Decode"
    label = "Base64 Decode"
    description = "Decode a Base64 encoded string"
    category = "http"

    @classmethod
    def get_type(cls) -> str:
        return "base64-decode"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "Text encoding to use for output string (default: utf-8)"
                },
                "as_bytes": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return raw bytes instead of decoded string"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base64": {
                    "type": "string",
                    "description": "Base64 encoded string to decode"
                }
            },
            "required": ["base64"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "decoded": {
                    "description": "Decoded data as string or bytes"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute Base64 decode."""
        encoded = memory.read(self.config["input_key"])
        encoding = self.config.get("encoding", "utf-8")
        as_bytes = self.config.get("as_bytes", False)

        # Decode from Base64
        try:
            decoded_bytes = base64.b64decode(str(encoded))
        except Exception as e:
            raise ValueError(f"Invalid Base64 string: {e}")

        # Convert to string unless as_bytes is True
        if as_bytes:
            result = decoded_bytes
        else:
            try:
                result = decoded_bytes.decode(encoding)
            except UnicodeDecodeError as e:
                raise ValueError(f"Cannot decode bytes to string with encoding '{encoding}': {e}")

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)
