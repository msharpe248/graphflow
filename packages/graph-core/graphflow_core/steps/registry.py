"""Step registry for managing available step types."""

from typing import Dict, Type, List, Optional, Any
from graphflow_core.steps.base import StepBase


class StepRegistry:
    """
    Global registry for step types.

    Provides registration and lookup of step classes by type identifier.
    """

    _registry: Dict[str, Type[StepBase]] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        step_type: Optional[str] = None,
        category: str = "general",
        description: str = "",
        framework_support: Optional[List[str]] = None,
        plugin: Optional[str] = None
    ):
        """
        Decorator to register a step class.

        Usage:
            @StepRegistry.register(category="control", plugin="my-plugin")
            class MyStep(StepBase):
                @classmethod
                def get_type(cls):
                    return "my_step"

        Args:
            step_type: Optional step type override (defaults to class.get_type())
            category: Category for UI organization
            description: Human-readable description
            framework_support: List of supported frameworks (None = all)
            plugin: Plugin name (for plugin steps, None for built-in)

        Returns:
            Decorator function
        """
        def decorator(step_class: Type[StepBase]) -> Type[StepBase]:
            # Get type from class if not provided
            type_id = step_type if step_type else step_class.get_type()

            if type_id in cls._registry:
                raise ValueError(f"Step type already registered: {type_id}")

            cls._registry[type_id] = step_class
            cls._metadata[type_id] = {
                "category": category,
                "description": description,
                "framework_support": framework_support or ["pydantic_ai", "langgraph"],
                "schema": step_class.get_schema(),
                "plugin": plugin or "built-in",
            }

            return step_class

        return decorator

    @classmethod
    def get(cls, step_type: str) -> Type[StepBase]:
        """
        Get step class by type identifier.

        Args:
            step_type: Step type identifier

        Returns:
            Step class

        Raises:
            KeyError: If step type not registered
        """
        if step_type not in cls._registry:
            raise KeyError(f"Unknown step type: {step_type}")
        return cls._registry[step_type]

    @classmethod
    def list_types(cls) -> List[str]:
        """
        List all registered step types.

        Returns:
            List of step type identifiers
        """
        return list(cls._registry.keys())

    @classmethod
    def list_by_category(cls) -> Dict[str, List[str]]:
        """
        List step types organized by category.

        Returns:
            Dictionary mapping categories to lists of step types
        """
        categories: Dict[str, List[str]] = {}
        for step_type, metadata in cls._metadata.items():
            category = metadata["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(step_type)
        return categories

    @classmethod
    def get_metadata(cls, step_type: str) -> Dict[str, Any]:
        """
        Get metadata for a step type.

        Args:
            step_type: Step type identifier

        Returns:
            Metadata dictionary

        Raises:
            KeyError: If step type not registered
        """
        if step_type not in cls._metadata:
            raise KeyError(f"Unknown step type: {step_type}")
        return cls._metadata[step_type].copy()

    @classmethod
    def is_registered(cls, step_type: str) -> bool:
        """Check if step type is registered."""
        return step_type in cls._registry

    @classmethod
    def supports_framework(cls, step_type: str, framework: str) -> bool:
        """
        Check if step type supports a framework.

        Args:
            step_type: Step type identifier
            framework: Framework name (e.g., "pydantic_ai", "langgraph")

        Returns:
            True if supported, False otherwise
        """
        if step_type not in cls._metadata:
            return False
        supported = cls._metadata[step_type]["framework_support"]
        return framework in supported

    @classmethod
    def register_step(
        cls,
        step_type: str,
        step_class: Type[StepBase],
        category: str = "general",
        description: str = "",
        framework_support: Optional[List[str]] = None,
        allow_override: bool = False
    ) -> None:
        """
        Programmatically register a step class.

        This method allows plugins to register steps without using decorators.
        Supports namespaced step types (e.g., "myplugin.custom_step").

        Args:
            step_type: Step type identifier (can include namespace)
            step_class: Step class to register
            category: Category for UI organization
            description: Human-readable description
            framework_support: List of supported frameworks (None = all)
            allow_override: If True, allows overriding existing registrations

        Raises:
            ValueError: If step type already registered and allow_override is False
        """
        if step_type in cls._registry and not allow_override:
            raise ValueError(f"Step type already registered: {step_type}")

        cls._registry[step_type] = step_class
        cls._metadata[step_type] = {
            "category": category,
            "description": description,
            "framework_support": framework_support or ["pydantic_ai", "langgraph"],
            "schema": step_class.get_schema(),
        }

    @classmethod
    def unregister_step(cls, step_type: str) -> bool:
        """
        Unregister a step type.

        Useful for unloading plugins or cleaning up registrations.

        Args:
            step_type: Step type identifier to unregister

        Returns:
            True if step was unregistered, False if not found
        """
        if step_type not in cls._registry:
            return False

        del cls._registry[step_type]
        if step_type in cls._metadata:
            del cls._metadata[step_type]

        return True

    @classmethod
    def list_namespaced_types(cls, namespace: str) -> List[str]:
        """
        List all step types under a specific namespace.

        Args:
            namespace: Namespace prefix (e.g., "myplugin")

        Returns:
            List of step type identifiers in the namespace
        """
        prefix = f"{namespace}."
        return [
            step_type for step_type in cls._registry.keys()
            if step_type.startswith(prefix)
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear registry (useful for testing)."""
        cls._registry.clear()
        cls._metadata.clear()
