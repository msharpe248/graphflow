"""Centralized template resolution for memory bindings."""

import re
from typing import Any, Dict, List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from graphflow_core.memory.store import MemoryStore


class TemplateResolver:
    """
    Resolves template strings containing memory bindings.

    Supports patterns:
    - {memory.field} - reads from memory (inputs/intermediate/outputs)
    - {config.field} - reads system configuration
    - {env.field} - reads environment variables
    - {secrets.field} - reads secret values
    - {{variable}} - legacy SQL-style templates (deprecated)

    Example usage:
        resolver = TemplateResolver(memory)
        result = resolver.resolve("Hello, {memory.user_name}!")
        config = resolver.resolve_dict({"url": "{config.api_base}/users"})
    """

    # Standard pattern for all namespaces
    # Matches: {memory.field}, {config.field}, {env.field}, {secrets.field}
    # Field names can include dots for nested paths: {memory.user.name}
    STANDARD_PATTERN = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')

    # Legacy pattern for backwards compatibility (e.g., DBQueryStep SQL templates)
    # Matches: {{variable}}
    LEGACY_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    def __init__(self, memory: "MemoryStore"):
        """
        Initialize the resolver with a memory store.

        Args:
            memory: The MemoryStore instance to read values from
        """
        self.memory = memory

    def resolve(self, template: str, *, allow_legacy: bool = False) -> str:
        """
        Resolve all memory bindings in a template string.

        Args:
            template: String containing {namespace.field} patterns
            allow_legacy: If True, also resolve {{variable}} patterns

        Returns:
            String with all patterns replaced by actual values.
            Missing keys are left as empty strings.

        Example:
            >>> resolver.resolve("Hello {memory.name}!")
            "Hello Alice!"
            >>> resolver.resolve("Value: {memory.missing}")
            "Value: "
        """
        if not template:
            return ""

        result = template

        # Resolve standard patterns
        for match in self.STANDARD_PATTERN.finditer(template):
            namespace, field = match.groups()
            full_key = f"{namespace}.{field}"
            try:
                value = self.memory.read(full_key)
                if value is not None:
                    result = result.replace(match.group(0), str(value))
                else:
                    # Replace with empty string for None values
                    result = result.replace(match.group(0), "")
            except KeyError:
                # Replace with empty string for missing keys
                result = result.replace(match.group(0), "")

        # Resolve legacy patterns if enabled
        if allow_legacy:
            result = self._resolve_legacy(result)

        return result

    def resolve_dict(
        self,
        data: Dict[str, Any],
        *,
        allow_legacy: bool = False
    ) -> Dict[str, Any]:
        """
        Recursively resolve all string values in a dictionary.

        Args:
            data: Dictionary potentially containing template strings
            allow_legacy: If True, also resolve {{variable}} patterns

        Returns:
            New dictionary with all template strings resolved

        Example:
            >>> resolver.resolve_dict({
            ...     "url": "{config.api_base}/users/{memory.user_id}",
            ...     "headers": {"Auth": "Bearer {secrets.token}"}
            ... })
            {
                "url": "https://api.example.com/users/123",
                "headers": {"Auth": "Bearer sk-abc123"}
            }
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.resolve(value, allow_legacy=allow_legacy)
            elif isinstance(value, dict):
                result[key] = self.resolve_dict(value, allow_legacy=allow_legacy)
            elif isinstance(value, list):
                result[key] = self.resolve_list(value, allow_legacy=allow_legacy)
            else:
                result[key] = value
        return result

    def resolve_list(
        self,
        data: List[Any],
        *,
        allow_legacy: bool = False
    ) -> List[Any]:
        """
        Recursively resolve all string values in a list.

        Args:
            data: List potentially containing template strings
            allow_legacy: If True, also resolve {{variable}} patterns

        Returns:
            New list with all template strings resolved
        """
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self.resolve(item, allow_legacy=allow_legacy))
            elif isinstance(item, dict):
                result.append(self.resolve_dict(item, allow_legacy=allow_legacy))
            elif isinstance(item, list):
                result.append(self.resolve_list(item, allow_legacy=allow_legacy))
            else:
                result.append(item)
        return result

    def extract_references(self, template: str) -> Set[str]:
        """
        Extract all memory references from a template.

        Useful for static analysis and validation.

        Args:
            template: String containing {namespace.field} patterns

        Returns:
            Set of full keys like {"memory.user_input", "secrets.api_key"}

        Example:
            >>> resolver.extract_references("Hello {memory.name}, your key is {secrets.key}")
            {"memory.name", "secrets.key"}
        """
        refs = set()
        if not template:
            return refs

        for match in self.STANDARD_PATTERN.finditer(template):
            namespace, field = match.groups()
            refs.add(f"{namespace}.{field}")
        return refs

    def extract_references_from_dict(self, data: Dict[str, Any]) -> Set[str]:
        """
        Recursively extract all memory references from a dictionary.

        Args:
            data: Dictionary potentially containing template strings

        Returns:
            Set of all memory references found
        """
        refs = set()
        for value in data.values():
            if isinstance(value, str):
                refs.update(self.extract_references(value))
            elif isinstance(value, dict):
                refs.update(self.extract_references_from_dict(value))
            elif isinstance(value, list):
                refs.update(self.extract_references_from_list(value))
        return refs

    def extract_references_from_list(self, data: List[Any]) -> Set[str]:
        """
        Recursively extract all memory references from a list.

        Args:
            data: List potentially containing template strings

        Returns:
            Set of all memory references found
        """
        refs = set()
        for item in data:
            if isinstance(item, str):
                refs.update(self.extract_references(item))
            elif isinstance(item, dict):
                refs.update(self.extract_references_from_dict(item))
            elif isinstance(item, list):
                refs.update(self.extract_references_from_list(item))
        return refs

    def _resolve_legacy(self, template: str) -> str:
        """
        Resolve legacy {{variable}} patterns for backwards compatibility.

        Legacy patterns search in order: inputs -> intermediate -> outputs

        Args:
            template: String containing {{variable}} patterns

        Returns:
            String with legacy patterns resolved
        """
        for match in self.LEGACY_PATTERN.finditer(template):
            var_name = match.group(1)
            # Try memory namespace (searches inputs -> intermediate -> outputs)
            try:
                value = self.memory.read(f"memory.{var_name}")
                if value is not None:
                    template = template.replace(match.group(0), str(value))
            except KeyError:
                # Leave pattern as-is if not found
                pass
        return template

    def has_bindings(self, template: str) -> bool:
        """
        Check if a string contains any memory bindings.

        Args:
            template: String to check

        Returns:
            True if the string contains at least one binding pattern
        """
        if not template:
            return False
        return bool(self.STANDARD_PATTERN.search(template))

    def has_legacy_bindings(self, template: str) -> bool:
        """
        Check if a string contains legacy {{variable}} bindings.

        Args:
            template: String to check

        Returns:
            True if the string contains at least one legacy binding pattern
        """
        if not template:
            return False
        return bool(self.LEGACY_PATTERN.search(template))

    # =========================================================================
    # Static methods for compile-time analysis (no MemoryStore required)
    # =========================================================================

    @classmethod
    def find_references(cls, template: str) -> Set[str]:
        """
        Extract all memory references from a template (static method).

        This is the static version of extract_references(), useful for
        compile-time static analysis when no MemoryStore is available.

        Args:
            template: String containing {namespace.field} patterns

        Returns:
            Set of full keys like {"memory.user_input", "secrets.api_key"}

        Example:
            >>> TemplateResolver.find_references("Hello {memory.name}!")
            {"memory.name"}
        """
        refs = set()
        if not template:
            return refs

        for match in cls.STANDARD_PATTERN.finditer(template):
            namespace, field = match.groups()
            refs.add(f"{namespace}.{field}")
        return refs

    @classmethod
    def find_references_in_dict(cls, data: Dict[str, Any]) -> Set[str]:
        """
        Recursively extract all memory references from a dictionary (static method).

        Useful for compile-time analysis of step configurations.

        Args:
            data: Dictionary potentially containing template strings

        Returns:
            Set of all memory references found
        """
        refs = set()
        for value in data.values():
            if isinstance(value, str):
                refs.update(cls.find_references(value))
            elif isinstance(value, dict):
                refs.update(cls.find_references_in_dict(value))
            elif isinstance(value, list):
                refs.update(cls.find_references_in_list(value))
        return refs

    @classmethod
    def find_references_in_list(cls, data: List[Any]) -> Set[str]:
        """
        Recursively extract all memory references from a list (static method).

        Args:
            data: List potentially containing template strings

        Returns:
            Set of all memory references found
        """
        refs = set()
        for item in data:
            if isinstance(item, str):
                refs.update(cls.find_references(item))
            elif isinstance(item, dict):
                refs.update(cls.find_references_in_dict(item))
            elif isinstance(item, list):
                refs.update(cls.find_references_in_list(item))
        return refs

    @classmethod
    def contains_bindings(cls, template: str) -> bool:
        """
        Check if a string contains any memory bindings (static method).

        Args:
            template: String to check

        Returns:
            True if the string contains at least one binding pattern
        """
        if not template:
            return False
        return bool(cls.STANDARD_PATTERN.search(template))
