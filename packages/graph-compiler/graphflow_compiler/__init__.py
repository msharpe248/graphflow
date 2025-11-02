"""GraphFlow Compiler - Transpile graphs to executable Python code."""

from graphflow_compiler.compiler import compile_graph, CompilerRegistry
from graphflow_compiler.generators.pydantic_ai import PydanticAIGenerator
from graphflow_compiler.generators.langgraph import LangGraphGenerator

# Register built-in generators
CompilerRegistry.register("pydantic_ai", PydanticAIGenerator)
CompilerRegistry.register("langgraph", LangGraphGenerator)

__version__ = "0.1.0"

__all__ = [
    "compile_graph",
    "CompilerRegistry",
    "PydanticAIGenerator",
    "LangGraphGenerator",
]
