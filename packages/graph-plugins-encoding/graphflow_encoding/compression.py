"""Compression step implementations."""
import gzip
import re
import base64
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="encoding.GzipCompressStep", category="encoding", description="Compress with gzip", plugin="encoding")
class GzipCompressStep(StepBase):
    """Gzip compress data step."""

    name = "Gzip Compress"
    label = "Gzip Compress"
    description = "Compress data using gzip"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.GzipCompressStep"

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
                "compression_level": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 9,
                    "default": 9,
                    "description": "Compression level (0=no compression, 9=max compression)"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["base64", "bytes"],
                    "default": "base64",
                    "description": "Output format (base64 for text-safe storage, bytes for binary)"
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
                    "description": "String or bytes to compress"
                }
            },
            "required": ["data"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "compressed": {
                    "description": "Compressed data (base64 string or bytes)"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute gzip compress."""
        data = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")
        level = self.config.get("compression_level", 9)
        output_format = self.config.get("output_format", "base64")

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)

        # Compress
        compressed = gzip.compress(data_bytes, compresslevel=level)

        # Format output
        if output_format == "base64":
            result = base64.b64encode(compressed).decode('ascii')
        else:
            result = compressed

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", result)


@StepRegistry.register(step_type="encoding.GzipDecompressStep", category="encoding", description="Decompress gzip data", plugin="encoding")
class GzipDecompressStep(StepBase):
    """Gzip decompress data step."""

    name = "Gzip Decompress"
    label = "Gzip Decompress"
    description = "Decompress gzip compressed data"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.GzipDecompressStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "input_format": {
                    "type": "string",
                    "enum": ["base64", "bytes"],
                    "default": "base64",
                    "description": "Input format (base64 for text-safe, bytes for binary)"
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
                "compressed": {
                    "description": "Gzip compressed data (base64 string or bytes)"
                }
            },
            "required": ["compressed"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "decompressed": {
                    "description": "Decompressed data as string or bytes"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute gzip decompress."""
        data = memory.read(self.config["input"])
        input_format = self.config.get("input_format", "base64")
        encoding = self.config.get("encoding", "utf-8")
        as_bytes = self.config.get("as_bytes", False)

        # Convert to bytes based on input format
        if input_format == "base64":
            try:
                compressed_bytes = base64.b64decode(str(data))
            except Exception as e:
                raise ValueError(f"Invalid base64 input: {e}")
        elif isinstance(data, bytes):
            compressed_bytes = data
        else:
            raise ValueError("Input must be bytes when input_format is 'bytes'")

        # Decompress
        try:
            decompressed = gzip.decompress(compressed_bytes)
        except Exception as e:
            raise ValueError(f"Failed to decompress gzip data: {e}")

        # Convert to string unless as_bytes is True
        if as_bytes:
            result = decompressed
        else:
            try:
                result = decompressed.decode(encoding)
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
