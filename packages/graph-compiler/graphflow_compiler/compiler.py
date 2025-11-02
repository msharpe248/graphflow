"""Main compiler interface and registry."""

from typing import Dict, Type
from graphflow_core.models import GraphDefinition
from graphflow_compiler.base import CodeGenerator


class CompilerRegistry:
    """Registry for code generators."""

    _generators: Dict[str, Type[CodeGenerator]] = {}

    @classmethod
    def register(cls, framework: str, generator_class: Type[CodeGenerator]) -> None:
        """
        Register a code generator for a framework.

        Args:
            framework: Framework identifier (e.g., 'pydantic_ai', 'langgraph')
            generator_class: Generator class
        """
        cls._generators[framework] = generator_class

    @classmethod
    def get(cls, framework: str) -> Type[CodeGenerator]:
        """
        Get generator class for framework.

        Args:
            framework: Framework identifier

        Returns:
            Generator class

        Raises:
            KeyError: If framework not registered
        """
        if framework not in cls._generators:
            raise KeyError(
                f"Unknown framework: {framework}. "
                f"Available: {', '.join(cls._generators.keys())}"
            )
        return cls._generators[framework]

    @classmethod
    def list_frameworks(cls) -> list[str]:
        """List all registered frameworks."""
        return list(cls._generators.keys())


def compile_graph(
    graph: GraphDefinition,
    framework: str = "pydantic_ai",
    standalone: bool = True
) -> str:
    """
    Compile graph definition to Python code.

    Args:
        graph: Graph definition to compile
        framework: Target framework ('pydantic_ai' or 'langgraph')
        standalone: If True, include CLI/FastAPI wrappers

    Returns:
        Generated Python code

    Raises:
        KeyError: If framework not registered
        ValueError: If graph is invalid

    Example:
        >>> from graphflow_core import GraphDefinition
        >>> graph = GraphDefinition.model_validate_json(json_str)
        >>> code = compile_graph(graph, framework="pydantic_ai")
        >>> with open("agent.py", "w") as f:
        ...     f.write(code)
    """
    generator_class = CompilerRegistry.get(framework)
    generator = generator_class()
    return generator.generate(graph, standalone=standalone)
