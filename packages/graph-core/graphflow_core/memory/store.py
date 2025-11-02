"""Memory store implementation for graph execution."""

import os
from typing import Any, Dict, Optional
from graphflow_core.models import MemorySchema


class MemoryStore:
    """
    Runtime memory store for graph execution.

    Manages three separate namespaces:
    - inputs: Values provided at agent start
    - outputs: Final results from execution
    - intermediate: Temporary storage for step results

    Additionally handles secrets loaded from configured providers.
    """

    def __init__(self, schema: MemorySchema):
        """
        Initialize memory store with schema.

        Args:
            schema: Memory schema defining inputs, outputs, intermediate, and secrets
        """
        self.schema = schema
        self._inputs: Dict[str, Any] = {}
        self._outputs: Dict[str, Any] = {}
        self._intermediate: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}
        self._initialized = False

    def initialize_inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Initialize input values.

        Args:
            inputs: Dictionary of input values

        Raises:
            KeyError: If input key not in schema
            ValueError: If required input is missing
        """
        # Check all inputs are valid
        for key in inputs:
            if key not in self.schema.inputs:
                raise KeyError(f"Input key not in schema: {key}")

        # Check required inputs are provided
        for key, field_def in self.schema.inputs.items():
            if field_def.required and key not in inputs:
                if field_def.default is not None:
                    inputs[key] = field_def.default
                else:
                    raise ValueError(f"Required input missing: {key}")

        self._inputs = inputs.copy()
        self._initialized = True

    def read(self, key: str) -> Any:
        """
        Read value from memory.

        Searches in order: inputs, intermediate, outputs
        Supports dotted notation for nested access (e.g., "user.name")

        Args:
            key: Memory key, optionally with dotted path

        Returns:
            Value from memory

        Raises:
            KeyError: If key not found in any namespace
        """
        # Parse dotted path
        parts = key.split('.')
        base_key = parts[0]

        # Find base value
        value = None
        if base_key in self._inputs:
            value = self._inputs[base_key]
        elif base_key in self._intermediate:
            value = self._intermediate[base_key]
        elif base_key in self._outputs:
            value = self._outputs[base_key]
        else:
            raise KeyError(f"Memory key not found: {base_key}")

        # Navigate nested path
        for part in parts[1:]:
            if isinstance(value, dict):
                if part not in value:
                    raise KeyError(f"Key not found in nested object: {key}")
                value = value[part]
            else:
                raise TypeError(f"Cannot access '{part}' on non-dict value at {key}")

        return value

    def write(self, key: str, value: Any) -> None:
        """
        Write value to memory.

        Determines target namespace based on schema.
        Supports dotted notation for nested writes (creates nested dicts).

        Args:
            key: Memory key, optionally with dotted path
            value: Value to write

        Raises:
            KeyError: If base key not in schema
        """
        parts = key.split('.')
        base_key = parts[0]

        # Determine target namespace
        if base_key in self.schema.outputs:
            target = self._outputs
        elif base_key in self.schema.intermediate:
            target = self._intermediate
        else:
            raise KeyError(f"Memory key not in schema (outputs or intermediate): {base_key}")

        # Handle nested writes
        if len(parts) == 1:
            # Simple write
            target[base_key] = value
        else:
            # Nested write - ensure base exists as dict
            if base_key not in target:
                target[base_key] = {}
            elif not isinstance(target[base_key], dict):
                raise TypeError(f"Cannot write nested value: {base_key} is not a dict")

            # Navigate to nested location
            current = target[base_key]
            for part in parts[1:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    raise TypeError(f"Cannot write nested value: path {key} crosses non-dict")
                current = current[part]

            # Write final value
            current[parts[-1]] = value

    def set_input(self, key: str, value: Any) -> None:
        """
        Set input value directly (used during initialization).

        Args:
            key: Input key
            value: Value to set

        Raises:
            KeyError: If key not in inputs schema
        """
        if key not in self.schema.inputs:
            raise KeyError(f"Not an input key: {key}")
        self._inputs[key] = value

    def get_secret(self, key: str) -> str:
        """
        Get secret value, loading it if necessary.

        Args:
            key: Secret key

        Returns:
            Secret value

        Raises:
            KeyError: If secret not in schema
            ValueError: If secret cannot be loaded
        """
        if key not in self.schema.secrets:
            raise KeyError(f"Secret not in schema: {key}")

        # Load secret if not already cached
        if key not in self._secrets:
            secret_def = self.schema.secrets[key]

            if secret_def.provider == "env":
                value = os.getenv(secret_def.key)
                if value is None:
                    raise ValueError(
                        f"Environment variable not set: {secret_def.key}"
                    )
                self._secrets[key] = value
            elif secret_def.provider == "vault":
                # TODO: Implement Vault integration
                raise NotImplementedError("Vault provider not yet implemented")
            elif secret_def.provider == "aws_secrets":
                # TODO: Implement AWS Secrets Manager integration
                raise NotImplementedError("AWS Secrets Manager not yet implemented")
            else:
                raise ValueError(f"Unknown secret provider: {secret_def.provider}")

        return self._secrets[key]

    def has_key(self, key: str) -> bool:
        """Check if key exists in any namespace."""
        base_key = key.split('.')[0]
        return (
            base_key in self._inputs or
            base_key in self._intermediate or
            base_key in self._outputs
        )

    def get_all_inputs(self) -> Dict[str, Any]:
        """Get copy of all input values."""
        return self._inputs.copy()

    def get_all_outputs(self) -> Dict[str, Any]:
        """Get copy of all output values."""
        return self._outputs.copy()

    def get_all_intermediate(self) -> Dict[str, Any]:
        """Get copy of all intermediate values."""
        return self._intermediate.copy()

    def to_dict(self) -> Dict[str, Any]:
        """
        Return complete memory state as dictionary.

        Returns:
            Dictionary with 'inputs', 'outputs', and 'intermediate' keys
        """
        return {
            "inputs": self._inputs.copy(),
            "outputs": self._outputs.copy(),
            "intermediate": self._intermediate.copy(),
        }

    def clear_intermediate(self) -> None:
        """Clear all intermediate values (useful for memory management)."""
        self._intermediate.clear()

    def __repr__(self) -> str:
        return (
            f"MemoryStore(inputs={len(self._inputs)}, "
            f"outputs={len(self._outputs)}, "
            f"intermediate={len(self._intermediate)})"
        )
