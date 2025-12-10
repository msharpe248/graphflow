"""Mixin for common memory operations in steps."""

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from graphflow_core.memory.store import MemoryStore
    from graphflow_core.memory.resolver import TemplateResolver


class MemoryMixin:
    """
    Mixin providing common memory operations for steps.

    This mixin provides a standardized way to interact with memory
    in step implementations, reducing code duplication across plugins.

    Provides:
    - _get_resolver(): Get a TemplateResolver for the memory store
    - _resolve(): Resolve a single template string
    - _resolve_dict(): Resolve all strings in a dict recursively
    - _resolve_list(): Resolve all strings in a list recursively
    - _get_value(): Get a value from memory, optionally resolving templates
    - _write_output(): Write to memory with optional namespace handling

    Example usage in a step:
        class MyStep(StepBase, MemoryMixin):
            async def execute(self, memory: MemoryStore) -> None:
                # Read and resolve a template
                url = self._resolve(self.config.get("url", ""), memory)

                # Get a value with default
                timeout = self._get_value("timeout", memory, default=30)

                # Resolve all templates in a dict
                headers = self._resolve_dict(self.config.get("headers", {}), memory)

                # Write output
                self._write_output("response", result, memory)
    """

    def _get_resolver(self, memory: "MemoryStore") -> "TemplateResolver":
        """
        Get a TemplateResolver for the given memory store.

        Args:
            memory: The MemoryStore instance

        Returns:
            TemplateResolver instance bound to the memory store
        """
        return memory.get_resolver()

    def _resolve(
        self,
        template: str,
        memory: "MemoryStore",
        *,
        allow_legacy: bool = False
    ) -> str:
        """
        Resolve a template string.

        Args:
            template: String containing {namespace.field} patterns
            memory: The MemoryStore instance
            allow_legacy: If True, also resolve {{variable}} patterns

        Returns:
            String with all bindings resolved

        Example:
            url = self._resolve("{config.api_base}/users/{memory.user_id}", memory)
        """
        return self._get_resolver(memory).resolve(template, allow_legacy=allow_legacy)

    def _resolve_dict(
        self,
        data: Dict[str, Any],
        memory: "MemoryStore",
        *,
        allow_legacy: bool = False
    ) -> Dict[str, Any]:
        """
        Resolve all template strings in a dictionary recursively.

        Args:
            data: Dictionary potentially containing template strings
            memory: The MemoryStore instance
            allow_legacy: If True, also resolve {{variable}} patterns

        Returns:
            New dictionary with all templates resolved
        """
        return self._get_resolver(memory).resolve_dict(data, allow_legacy=allow_legacy)

    def _resolve_list(
        self,
        data: list,
        memory: "MemoryStore",
        *,
        allow_legacy: bool = False
    ) -> list:
        """
        Resolve all template strings in a list recursively.

        Args:
            data: List potentially containing template strings
            memory: The MemoryStore instance
            allow_legacy: If True, also resolve {{variable}} patterns

        Returns:
            New list with all templates resolved
        """
        return self._get_resolver(memory).resolve_list(data, allow_legacy=allow_legacy)

    def _get_value(
        self,
        key: str,
        memory: "MemoryStore",
        default: Any = None,
        *,
        resolve: bool = True,
        allow_legacy: bool = False
    ) -> Any:
        """
        Get a value from memory, optionally resolving templates.

        Args:
            key: Memory key (e.g., "memory.field" or just "field")
            memory: The MemoryStore instance
            default: Default value if not found
            resolve: If True and value is a string, resolve templates
            allow_legacy: If True, also resolve {{variable}} patterns

        Returns:
            The value from memory, or default if not found

        Example:
            # Get with namespace prefix
            user_id = self._get_value("memory.user_id", memory)

            # Get with implicit memory namespace
            user_id = self._get_value("user_id", memory)

            # Get with default
            timeout = self._get_value("timeout", memory, default=30)
        """
        # Normalize key to include namespace if missing
        if '.' not in key:
            key = f"memory.{key}"

        try:
            value = memory.read(key)
            if value is None:
                return default
            if resolve and isinstance(value, str):
                return self._resolve(value, memory, allow_legacy=allow_legacy)
            return value
        except KeyError:
            return default

    def _write_output(
        self,
        key: str,
        value: Any,
        memory: "MemoryStore",
        namespace: str = "memory"
    ) -> None:
        """
        Write a value to memory.

        Args:
            key: Field name (with or without namespace prefix)
            value: Value to write
            memory: The MemoryStore instance
            namespace: Target namespace (default: "memory")
                      Used when key doesn't include namespace prefix

        Example:
            # Write with explicit namespace in key
            self._write_output("memory.response", result, memory)

            # Write with implicit namespace
            self._write_output("response", result, memory)

            # Write to outputs namespace
            self._write_output("final_result", result, memory, namespace="memory")
        """
        # Check if key already has a namespace prefix
        if '.' in key:
            parts = key.split('.')
            if parts[0] in ('memory', 'config', 'env', 'secrets'):
                # Key already has namespace prefix, use as-is
                memory.write(key, value)
                return

        # Add namespace prefix
        full_key = f"{namespace}.{key}"
        memory.write(full_key, value)

    def _has_bindings(self, template: str, memory: "MemoryStore") -> bool:
        """
        Check if a string contains any memory bindings.

        Args:
            template: String to check
            memory: The MemoryStore instance

        Returns:
            True if the string contains at least one binding pattern
        """
        return self._get_resolver(memory).has_bindings(template)

    def _extract_references(self, template: str, memory: "MemoryStore") -> set:
        """
        Extract all memory references from a template string.

        Args:
            template: String containing {namespace.field} patterns
            memory: The MemoryStore instance

        Returns:
            Set of full keys like {"memory.user_input", "secrets.api_key"}
        """
        return self._get_resolver(memory).extract_references(template)
