"""
Tool Compiler

Generates Python code for tools from ToolDefinitions.
Supports multiple frameworks (Pydantic AI, LangGraph).
"""

import re
import json
from typing import Dict, Any, List
from graphflow_core.models import ToolDefinition, ToolPropertyMapping


class ToolCompiler:
    """
    Compiles ToolDefinitions into framework-specific Python code.

    Generates:
    - Tool function definitions
    - Parameter validation
    - Step instantiation and execution
    - Result extraction
    """

    def __init__(self, framework: str = "pydantic_ai"):
        """
        Initialize tool compiler.

        Args:
            framework: Target framework ('pydantic_ai' or 'langgraph')
        """
        self.framework = framework

    def compile_tool(self, tool: ToolDefinition) -> str:
        """
        Compile a single tool definition to Python code.

        Args:
            tool: Tool definition to compile

        Returns:
            Generated Python code for the tool function
        """
        if self.framework == "pydantic_ai":
            return self._compile_pydantic_ai_tool(tool)
        elif self.framework == "langgraph":
            return self._compile_langgraph_tool(tool)
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def compile_tools(self, tools: List[ToolDefinition]) -> str:
        """
        Compile multiple tool definitions.

        Args:
            tools: List of tool definitions

        Returns:
            Generated Python code for all tools
        """
        tool_codes = []
        for tool in tools:
            tool_codes.append(self.compile_tool(tool))

        return "\n\n".join(tool_codes)

    def get_tool_imports(self, tools: List[ToolDefinition]) -> List[str]:
        """
        Get required imports for compiled tools.

        Args:
            tools: List of tool definitions

        Returns:
            List of import statements
        """
        imports = set()

        # Common imports
        imports.add("from typing import Any, Dict, Optional")
        imports.add("from graphflow_core.steps.registry import StepRegistry")
        imports.add("from graphflow_core.memory import MemoryStore")

        # Framework-specific imports
        if self.framework == "pydantic_ai":
            imports.add("from pydantic_ai import RunContext")

        # Check for specific step types
        step_types = {tool.source_step_type for tool in tools}
        if any(s.startswith("http.") for s in step_types):
            imports.add("import graphflow_http")

        return sorted(imports)

    def _compile_pydantic_ai_tool(self, tool: ToolDefinition) -> str:
        """
        Generate Pydantic AI tool function.

        Pydantic AI tools are async functions decorated with @agent.tool.
        """
        lines = []

        # Generate docstring
        lines.append(f'@agent.tool')
        lines.append(f'async def {tool.name}(')
        lines.append(f'    ctx: RunContext[Dict[str, Any]],')

        # Add LLM parameters
        llm_params = tool.get_llm_parameters()
        for i, mapping in enumerate(llm_params):
            param_name = mapping.llm_parameter_name or mapping.source_property
            param_type = self._get_python_type(mapping.llm_schema)
            default = "" if mapping.required else " = None"
            comma = "," if i < len(llm_params) - 1 else ""
            lines.append(f'    {param_name}: {param_type}{default}{comma}')

        lines.append(f') -> Any:')
        lines.append(f'    """')
        lines.append(f'    {tool.description}')

        if llm_params:
            lines.append(f'')
            lines.append(f'    Args:')
            for mapping in llm_params:
                param_name = mapping.llm_parameter_name or mapping.source_property
                desc = mapping.llm_description or f"Value for {mapping.source_property}"
                lines.append(f'        {param_name}: {desc}')

        lines.append(f'    """')

        # Get memory from context
        lines.append(f'    memory = ctx.deps.get("memory")')
        lines.append(f'')

        # Build step config
        lines.append(f'    # Build step configuration')
        lines.append(f'    step_config = {{}}')

        # Add runtime parameters
        for mapping in tool.get_runtime_parameters():
            if mapping.runtime_value:
                if mapping.runtime_value.startswith("{") and mapping.runtime_value.endswith("}"):
                    # Memory binding - extract the path
                    mem_path = mapping.runtime_value[1:-1]  # Remove { and }
                    lines.append(f'    step_config["{mapping.source_property}"] = memory.read("{mem_path}")')
                else:
                    # Constant value
                    lines.append(f'    step_config["{mapping.source_property}"] = {repr(mapping.runtime_value)}')

        # Add LLM parameters
        for mapping in llm_params:
            param_name = mapping.llm_parameter_name or mapping.source_property
            lines.append(f'    step_config["{mapping.source_property}"] = {param_name}')

        lines.append(f'')

        # Create and execute step
        lines.append(f'    # Create and execute step')
        lines.append(f'    step_class = StepRegistry.get("{tool.source_step_type}")')
        lines.append(f'    step = step_class(')
        lines.append(f'        id="{tool.id}_tool",')
        lines.append(f'        config=step_config,')
        lines.append(f'        outputs={{{repr(tool.output_key)}: "{{memory.tool_result}}"}}')
        lines.append(f'    )')
        lines.append(f'')
        lines.append(f'    # Create temporary memory for tool execution')
        lines.append(f'    tool_memory = MemoryStore()')
        lines.append(f'    # Copy relevant memory values')
        lines.append(f'    for key in memory.list_keys("memory"):')
        lines.append(f'        try:')
        lines.append(f'            tool_memory.write(f"memory.{{key}}", memory.read(f"memory.{{key}}"))')
        lines.append(f'        except KeyError:')
        lines.append(f'            pass')
        lines.append(f'')
        lines.append(f'    await step.execute(tool_memory)')
        lines.append(f'')

        # Extract result
        lines.append(f'    # Extract result')
        lines.append(f'    result = tool_memory.read("memory.tool_result")')

        # Apply output transform if specified
        if tool.output_transform:
            lines.append(f'    # Apply output transform')
            lines.append(f'    result = {tool.output_transform}')

        lines.append(f'    return result')

        return "\n".join(lines)

    def _compile_langgraph_tool(self, tool: ToolDefinition) -> str:
        """
        Generate LangGraph tool function.

        LangGraph uses the @tool decorator from langchain_core.tools.
        """
        lines = []

        # Generate function signature
        lines.append(f'@tool')
        lines.append(f'async def {tool.name}(')

        # Add LLM parameters
        llm_params = tool.get_llm_parameters()
        for i, mapping in enumerate(llm_params):
            param_name = mapping.llm_parameter_name or mapping.source_property
            param_type = self._get_python_type(mapping.llm_schema)
            default = "" if mapping.required else " = None"
            comma = "," if i < len(llm_params) - 1 else ""
            lines.append(f'    {param_name}: {param_type}{default}{comma}')

        lines.append(f') -> Any:')
        lines.append(f'    """')
        lines.append(f'    {tool.description}')

        if llm_params:
            lines.append(f'')
            lines.append(f'    Args:')
            for mapping in llm_params:
                param_name = mapping.llm_parameter_name or mapping.source_property
                desc = mapping.llm_description or f"Value for {mapping.source_property}"
                lines.append(f'        {param_name}: {desc}')

        lines.append(f'    """')

        # Note: LangGraph tools need access to state/memory through different means
        lines.append(f'    # Note: Access to state must be configured at graph level')
        lines.append(f'')

        # Build step config
        lines.append(f'    # Build step configuration')
        lines.append(f'    step_config = {{}}')

        # Add runtime parameters (these would need to come from state)
        for mapping in tool.get_runtime_parameters():
            if mapping.runtime_value:
                if mapping.runtime_value.startswith("{") and mapping.runtime_value.endswith("}"):
                    lines.append(f'    # TODO: Get {mapping.source_property} from state')
                    lines.append(f'    step_config["{mapping.source_property}"] = None  # {mapping.runtime_value}')
                else:
                    lines.append(f'    step_config["{mapping.source_property}"] = {repr(mapping.runtime_value)}')

        # Add LLM parameters
        for mapping in llm_params:
            param_name = mapping.llm_parameter_name or mapping.source_property
            lines.append(f'    step_config["{mapping.source_property}"] = {param_name}')

        lines.append(f'')

        # Create and execute step
        lines.append(f'    # Create and execute step')
        lines.append(f'    step_class = StepRegistry.get("{tool.source_step_type}")')
        lines.append(f'    step = step_class(')
        lines.append(f'        id="{tool.id}_tool",')
        lines.append(f'        config=step_config,')
        lines.append(f'        outputs={{{repr(tool.output_key)}: "{{memory.tool_result}}"}}')
        lines.append(f'    )')
        lines.append(f'')
        lines.append(f'    # Create memory for step execution')
        lines.append(f'    tool_memory = MemoryStore()')
        lines.append(f'    await step.execute(tool_memory)')
        lines.append(f'')

        # Extract result
        lines.append(f'    # Extract result')
        lines.append(f'    result = tool_memory.read("memory.tool_result")')

        if tool.output_transform:
            lines.append(f'    result = {tool.output_transform}')

        lines.append(f'    return result')

        return "\n".join(lines)

    def _get_python_type(self, schema: Dict[str, Any] | None) -> str:
        """Convert JSON schema to Python type hint."""
        if not schema:
            return "Any"

        json_type = schema.get("type", "any")
        type_map = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
            "any": "Any",
        }
        return type_map.get(json_type, "Any")

    def generate_tool_registration_code(self, tools: List[ToolDefinition]) -> str:
        """
        Generate code to register all tools with an agent.

        For Pydantic AI, tools are registered via decorators.
        This generates the tools list for manual registration if needed.
        """
        lines = []
        lines.append("# Tool definitions")
        lines.append(f"TOOLS = [")

        for tool in tools:
            lines.append(f"    {tool.name},")

        lines.append(f"]")

        return "\n".join(lines)
