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

        # Initialize all intermediate and output fields with defaults or zero values
        for key, field_def in schema.intermediate.items():
            if field_def.default is not None:
                self._intermediate[key] = field_def.default
            else:
                self._intermediate[key] = self._get_zero_value(field_def.type)

        for key, field_def in schema.outputs.items():
            if field_def.default is not None:
                self._outputs[key] = field_def.default
            else:
                self._outputs[key] = self._get_zero_value(field_def.type)

    def _get_zero_value(self, field_type: str) -> Any:
        """Get the zero value for a field type."""
        zero_values = {
            'string': '',
            'number': 0,
            'boolean': False,
            'object': {},
            'array': [],
            'any': None,
        }
        return zero_values.get(field_type, None)

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

        # Apply defaults and check required inputs
        for key, field_def in self.schema.inputs.items():
            if key not in inputs:
                # Apply default if available
                if field_def.default is not None:
                    inputs[key] = field_def.default
                # Check if required
                elif field_def.required:
                    raise ValueError(f"Required input missing: {key}")

        self._inputs = inputs.copy()
        self._initialized = True

    def read(self, key: str) -> Any:
        """
        Read value from memory.

        Searches in order: inputs, intermediate, outputs

        Args:
            key: Memory key (exact match, no nested navigation)

        Returns:
            Value from memory

        Raises:
            KeyError: If key not found in any namespace
        """
        # Find value in namespaces (exact key match)
        if key in self._inputs:
            return self._inputs[key]
        elif key in self._intermediate:
            return self._intermediate[key]
        elif key in self._outputs:
            return self._outputs[key]
        else:
            raise KeyError(f"Memory key not found: {key}")

    def write(self, key: str, value: Any) -> None:
        """
        Write value to memory.

        Determines target namespace based on schema.

        Args:
            key: Memory key (exact match, no nested navigation)
            value: Value to write

        Raises:
            KeyError: If key not in schema
        """
        # Determine target namespace (exact key match)
        if key in self.schema.outputs:
            self._outputs[key] = value
        elif key in self.schema.intermediate:
            self._intermediate[key] = value
        else:
            raise KeyError(f"Memory key not in schema (outputs or intermediate): {key}")

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
        return (
            key in self._inputs or
            key in self._intermediate or
            key in self._outputs
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
