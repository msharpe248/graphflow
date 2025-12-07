"""Hash computation step implementations."""
import hashlib
import re
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="encoding.MD5HashStep", category="encoding", description="Compute MD5 hash", plugin="encoding")
class MD5HashStep(StepBase):
    """Compute MD5 hash step."""

    name = "MD5 Hash"
    label = "MD5 Hash"
    description = "Compute MD5 hash of input data"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.MD5HashStep"

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
                    "description": "String or bytes to hash"
                }
            },
            "required": ["data"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hash": {
                    "type": "string",
                    "description": "MD5 hash as hexadecimal string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute MD5 hash."""
        data = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)

        # Compute hash
        hash_result = hashlib.md5(data_bytes).hexdigest()

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", hash_result)


@StepRegistry.register(step_type="encoding.SHA1HashStep", category="encoding", description="Compute SHA1 hash", plugin="encoding")
class SHA1HashStep(StepBase):
    """Compute SHA1 hash step."""

    name = "SHA1 Hash"
    label = "SHA1 Hash"
    description = "Compute SHA1 hash of input data"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.SHA1HashStep"

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
                    "description": "String or bytes to hash"
                }
            },
            "required": ["data"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hash": {
                    "type": "string",
                    "description": "SHA1 hash as hexadecimal string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute SHA1 hash."""
        data = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)

        # Compute hash
        hash_result = hashlib.sha1(data_bytes).hexdigest()

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", hash_result)


@StepRegistry.register(step_type="encoding.SHA256HashStep", category="encoding", description="Compute SHA256 hash", plugin="encoding")
class SHA256HashStep(StepBase):
    """Compute SHA256 hash step."""

    name = "SHA256 Hash"
    label = "SHA256 Hash"
    description = "Compute SHA256 hash of input data"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.SHA256HashStep"

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
                    "description": "String or bytes to hash"
                }
            },
            "required": ["data"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hash": {
                    "type": "string",
                    "description": "SHA256 hash as hexadecimal string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute SHA256 hash."""
        data = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)

        # Compute hash
        hash_result = hashlib.sha256(data_bytes).hexdigest()

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", hash_result)


@StepRegistry.register(step_type="encoding.SHA512HashStep", category="encoding", description="Compute SHA512 hash", plugin="encoding")
class SHA512HashStep(StepBase):
    """Compute SHA512 hash step."""

    name = "SHA512 Hash"
    label = "SHA512 Hash"
    description = "Compute SHA512 hash of input data"

    @classmethod
    def get_type(cls) -> str:
        return "encoding.SHA512HashStep"

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
                    "description": "String or bytes to hash"
                }
            },
            "required": ["data"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hash": {
                    "type": "string",
                    "description": "SHA512 hash as hexadecimal string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute SHA512 hash."""
        data = memory.read(self.config["input"])
        encoding = self.config.get("encoding", "utf-8")

        # Convert to bytes if string
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)

        # Compute hash
        hash_result = hashlib.sha512(data_bytes).hexdigest()

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                memory.write(f"{namespace}.{field_key}", hash_result)
