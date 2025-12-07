"""Base64 encoding/decoding step implementations."""
import base64
import re
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="encoding.Base64EncodeStep", category="encoding", description="Encode to Base64", plugin="encoding")
class Base64EncodeStep(StepBase):
    """Encode data to Base64 step."""

    name = "Base64 Encode"
    label = "Base64 Encode"
    description = "Encode a string or bytes to Base64"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.Base64EncodeStep"

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
        data = memory.read(self.config["input"])
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


@StepRegistry.register(step_type="encoding.Base64DecodeStep", category="encoding", description="Decode from Base64", plugin="encoding")
class Base64DecodeStep(StepBase):
    """Decode Base64 data step."""

    name = "Base64 Decode"
    label = "Base64 Decode"
    description = "Decode a Base64 encoded string"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.Base64DecodeStep"

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
        encoded = memory.read(self.config["input"])
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


@StepRegistry.register(step_type="encoding.Base64URLEncodeStep", category="encoding", description="Encode to URL-safe Base64", plugin="encoding")
class Base64URLEncodeStep(StepBase):
    """URL-safe Base64 encode step."""

    name = "Base64 URL Encode"
    label = "Base64 URL Encode"
    description = "Encode to URL-safe Base64 (uses - and _ instead of + and /)"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.Base64URLEncodeStep"

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
                "base64url": {
                    "type": "string",
                    "description": "URL-safe Base64 encoded string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute URL-safe Base64 encode."""
        data = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)

        # Encode to URL-safe Base64
        encoded = base64.urlsafe_b64encode(data_bytes).decode('ascii')

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", encoded)


@StepRegistry.register(step_type="encoding.Base64URLDecodeStep", category="encoding", description="Decode from URL-safe Base64", plugin="encoding")
class Base64URLDecodeStep(StepBase):
    """URL-safe Base64 decode step."""

    name = "Base64 URL Decode"
    label = "Base64 URL Decode"
    description = "Decode a URL-safe Base64 encoded string"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.Base64URLDecodeStep"

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
                "base64url": {
                    "type": "string",
                    "description": "URL-safe Base64 encoded string to decode"
                }
            },
            "required": ["base64url"]
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
        """Execute URL-safe Base64 decode."""
        encoded = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")
        as_bytes = self.config.get("as_bytes", False)

        # Decode from URL-safe Base64
        try:
            decoded_bytes = base64.urlsafe_b64decode(str(encoded))
        except Exception as e:
            raise ValueError(f"Invalid URL-safe Base64 string: {e}")

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
