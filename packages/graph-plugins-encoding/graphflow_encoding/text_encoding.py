"""Hex encoding/decoding step implementations."""
import re
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="encoding.HexEncodeStep", category="encoding", description="Encode to hexadecimal", plugin="encoding")
class HexEncodeStep(StepBase):
    """Encode data to hexadecimal step."""

    name = "Hex Encode"
    label = "Hex Encode"
    description = "Encode a string or bytes to hexadecimal"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.HexEncodeStep"

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
                },
                "uppercase": {
                    "type": "boolean",
                    "default": False,
                    "description": "Use uppercase hex characters (default: lowercase)"
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
                "hex": {
                    "type": "string",
                    "description": "Hexadecimal encoded string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute hex encode."""
        data = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")
        uppercase = self.config.get("uppercase", False)

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)

        # Encode to hex
        encoded = data_bytes.hex()
        if uppercase:
            encoded = encoded.upper()

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", encoded)


@StepRegistry.register(step_type="encoding.HexDecodeStep", category="encoding", description="Decode from hexadecimal", plugin="encoding")
class HexDecodeStep(StepBase):
    """Decode hexadecimal data step."""

    name = "Hex Decode"
    label = "Hex Decode"
    description = "Decode a hexadecimal encoded string"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.HexDecodeStep"

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
                "hex": {
                    "type": "string",
                    "description": "Hexadecimal encoded string to decode"
                }
            },
            "required": ["hex"]
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
        """Execute hex decode."""
        encoded = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")
        as_bytes = self.config.get("as_bytes", False)

        # Decode from hex
        try:
            decoded_bytes = bytes.fromhex(str(encoded))
        except ValueError as e:
            raise ValueError(f"Invalid hexadecimal string: {e}")

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
