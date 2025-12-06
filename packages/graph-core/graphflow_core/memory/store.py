"""Memory store implementation for graph execution."""

import os
from typing import Any, Dict, Optional
from graphflow_core.models import MemorySchema

# Global runtime config registry
# This is populated by the runtime executor before agent execution
# Allows config namespace to redirect to runtime config without circular dependency
_RUNTIME_CONFIG: Dict[str, Any] = {}


class MemoryStore:
    """
    Runtime memory store for graph execution.

    Manages six separate namespaces:
    - memory.* (inputs/intermediate/outputs): User inputs and step results
    - config.*: System configuration (read-only)
    - env.*: Environment variables (read/write)
    - secrets.*: Sensitive values from secret providers

    Supports namespaced syntax: {memory.field}, {config.field}, {env.field}, {secrets.field}
    """

    def __init__(self, schema: MemorySchema):
        """
        Initialize memory store with schema.

        Args:
            schema: Memory schema defining all namespaces
        """
        self.schema = schema
        self._inputs: Dict[str, Any] = {}
        self._outputs: Dict[str, Any] = {}
        self._intermediate: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}
        # Note: config is NOT stored, it proxies to global _RUNTIME_CONFIG
        # Note: environment is NOT stored, it proxies directly to os.environ
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
            ValueError: If required input is missing

        Note:
            Extra inputs not in the schema are accepted and stored.
            This allows passing dynamic data that prompts can reference.
        """
        # Apply defaults and check required inputs for schema-defined inputs
        for key, field_def in self.schema.inputs.items():
            if key not in inputs:
                # Apply default if available
                if field_def.default is not None:
                    inputs[key] = field_def.default
                # Check if required
                elif field_def.required:
                    raise ValueError(f"Required input missing: {key}")

        # Accept all inputs (both schema-defined and extra dynamic inputs)
        self._inputs = inputs.copy()
        self._initialized = True

    def read(self, key: str) -> Any:
        """
        Read value from memory.

        Supports both legacy format and namespaced format:
        - Legacy: "field_name" (searches inputs → intermediate → outputs)
        - Namespaced: "memory.field", "config.field", "env.field", "secrets.field"

        Args:
            key: Memory key

        Returns:
            Value from memory

        Raises:
            KeyError: If key not found in any namespace
        """
        # Check if namespaced
        if "." in key:
            namespace, field_key = key.split(".", 1)

            if namespace == "memory":
                # Search in memory namespaces
                if field_key in self._inputs:
                    return self._inputs[field_key]
                elif field_key in self._intermediate:
                    return self._intermediate[field_key]
                elif field_key in self._outputs:
                    return self._outputs[field_key]
                else:
                    # Return empty string for missing keys (graceful handling)
                    # This allows generated code to work even with incomplete schemas
                    return ""

            elif namespace == "config":
                # Proxy to global runtime config
                if field_key in _RUNTIME_CONFIG:
                    return _RUNTIME_CONFIG[field_key]
                else:
                    raise KeyError(f"Config key not found: {field_key}")

            elif namespace == "env":
                # Proxy to os.environ - get the actual env var name from schema
                if field_key in self.schema.environment:
                    env_var_name = self.schema.environment[field_key].key
                    value = os.getenv(env_var_name)
                    if value is None:
                        raise KeyError(f"Environment variable not set: {env_var_name}")
                    return value
                else:
                    raise KeyError(f"Environment key not in schema: {field_key}")

            elif namespace == "secrets":
                return self.get_secret(field_key)

            else:
                raise KeyError(f"Unknown namespace: {namespace}")

        else:
            # Legacy format: search in order
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

        Supports both legacy format and namespaced format:
        - Legacy: "field_name" (writes to outputs or intermediate)
        - Namespaced: "memory.field", "env.field", "secrets.field"

        Note: Config namespace is read-only and cannot be written to.

        Args:
            key: Memory key
            value: Value to write

        Raises:
            KeyError: If key not in schema
            ValueError: If attempting to write to read-only namespace
        """
        # Check if namespaced
        if "." in key:
            namespace, field_key = key.split(".", 1)

            if namespace == "memory":
                # Write to memory namespaces
                if field_key in self.schema.outputs:
                    self._outputs[field_key] = value
                elif field_key in self.schema.intermediate:
                    self._intermediate[field_key] = value
                else:
                    raise KeyError(f"Memory key not in schema: {field_key}")

            elif namespace == "config":
                raise ValueError("Config namespace is read-only")

            elif namespace == "env":
                # Steps can create/update environment variables at runtime
                # Proxy to os.environ - get the actual env var name from schema
                if field_key in self.schema.environment:
                    env_var_name = self.schema.environment[field_key].key
                    os.environ[env_var_name] = str(value)
                else:
                    raise KeyError(f"Environment key not in schema: {field_key}")

            elif namespace == "secrets":
                # Steps can create/update secrets at runtime
                self._secrets[field_key] = str(value)

            else:
                raise KeyError(f"Unknown namespace: {namespace}")

        else:
            # Legacy format
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

    def populate_config(self, config_values: Dict[str, Any]) -> None:
        """
        Populate configuration values into global runtime config.

        Called by runtime to set system configuration values like:
        - cwd: Current working directory
        - runtime_url: Runtime API URL
        - ui_url: Builder URL
        - runtime_id: Runtime instance ID

        Like environment variables, config is stored globally and shared
        across all MemoryStore instances. This allows runtime to manage
        config centrally without schema restrictions.

        Args:
            config_values: Dictionary of config key -> value
        """
        global _RUNTIME_CONFIG
        _RUNTIME_CONFIG.update(config_values)

    def set_config(self, key: str, value: Any) -> None:
        """
        Set a single configuration value.

        Args:
            key: Config key
            value: Value to set
        """
        global _RUNTIME_CONFIG
        _RUNTIME_CONFIG[key] = value

    def populate_environment(self, env_filter: Optional[list] = None) -> None:
        """
        Validate environment variables are available.

        Note: Environment namespace proxies directly to os.environ,
        so this method just validates that required vars exist.

        Args:
            env_filter: Optional list of schema keys to validate (for filtering).
                       If None, validates all env vars defined in schema.
        """
        import logging

        for schema_key, env_def in self.schema.environment.items():
            # Check whitelist if provided
            if env_filter is not None and schema_key not in env_filter:
                continue

            env_var_name = env_def.key
            value = os.getenv(env_var_name)

            if value is None and env_def.required:
                # Log warning but don't fail (per plan requirements)
                logging.warning(f"Required environment variable not set: {env_var_name}")

    def validate_references(self) -> list:
        """
        Validate that all required config/env/secrets exist.

        Returns:
            List of warning messages for missing values
        """
        warnings = []

        # Check config (from global runtime config)
        for key in self.schema.config:
            if key not in _RUNTIME_CONFIG:
                warnings.append(f"Config value not set: {key}")

        # Check environment (proxy to os.environ)
        for schema_key, env_def in self.schema.environment.items():
            if env_def.required and os.getenv(env_def.key) is None:
                warnings.append(f"Required environment variable not set: {env_def.key}")

        # Check secrets
        for key, secret_def in self.schema.secrets.items():
            try:
                # Try to resolve secret (will use cached value if already loaded)
                if secret_def.provider == "env":
                    value = os.getenv(secret_def.key)
                    if value is None:
                        warnings.append(f"Secret not available (env var not set): {secret_def.key}")
            except Exception as e:
                warnings.append(f"Secret resolution failed for {key}: {str(e)}")

        return warnings

    def has_key(self, key: str) -> bool:
        """Check if key exists in any namespace.

        Supports both legacy format and namespaced format:
        - Legacy: "field_name" (checks inputs → intermediate → outputs)
        - Namespaced: "memory.field", "config.field", "env.field", "secrets.field"
        """
        # Check if namespaced
        if "." in key:
            namespace, field_key = key.split(".", 1)

            if namespace == "memory":
                return (
                    field_key in self._inputs or
                    field_key in self._intermediate or
                    field_key in self._outputs
                )
            elif namespace == "config":
                return field_key in _RUNTIME_CONFIG
            elif namespace == "env":
                if field_key in self.schema.environment:
                    env_var_name = self.schema.environment[field_key].key
                    return os.getenv(env_var_name) is not None
                return False
            elif namespace == "secrets":
                return field_key in self.schema.secrets
            else:
                return False

        # Legacy format: check memory namespaces
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

    def get_all_config(self) -> Dict[str, Any]:
        """
        Get copy of all config values from global runtime config.

        Like environment, config redirects to a global registry rather than
        storing values locally. This allows runtime to manage config centrally.
        """
        return _RUNTIME_CONFIG.copy()

    def get_all_environment(self) -> Dict[str, Any]:
        """
        Get all environment variables from os.environ.

        Returns all env vars, not just ones defined in schema.
        This allows runtime visibility of the full environment.
        """
        return dict(os.environ)

    def to_dict(self) -> Dict[str, Any]:
        """
        Return complete memory state as dictionary.

        Returns:
            Dictionary with all namespaces
        """
        return {
            "memory": {
                "inputs": self._inputs.copy(),
                "outputs": self._outputs.copy(),
                "intermediate": self._intermediate.copy(),
            },
            "config": self.get_all_config(),  # Read from global runtime config
            "environment": self.get_all_environment(),  # Read from os.environ
            "secrets": {k: "<exists>" for k in self._secrets.keys()},  # Don't expose values
        }

    def clear_intermediate(self) -> None:
        """Clear all intermediate values (useful for memory management)."""
        self._intermediate.clear()

    def __repr__(self) -> str:
        return (
            f"MemoryStore(inputs={len(self._inputs)}, "
            f"outputs={len(self._outputs)}, "
            f"intermediate={len(self._intermediate)}, "
            f"config={len(_RUNTIME_CONFIG)}, "
            f"env={len(self.schema.environment)}, "
            f"secrets={len(self._secrets)})"
        )
