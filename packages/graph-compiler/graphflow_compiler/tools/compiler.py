"""
Tool Compiler

Generates Python code for tools from ToolDefinitions and MCP tools.
Supports multiple frameworks (Pydantic AI, LangGraph).
"""

import re
import json
from typing import Dict, Any, List, Union
from graphflow_core.models import (
    ToolDefinition,
    ToolPropertyMapping,
    MCPTool,
    MCPServerConfig,
    MCPToolDefinition,
)
from graphflow_core.memory.resolver import TemplateResolver


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

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize a name to be a valid Python identifier.

        Replaces hyphens and other invalid characters with underscores.
        MCP tool names like 'resolve-library-id' become 'resolve_library_id'.

        Args:
            name: Original name (may contain hyphens, dots, etc.)

        Returns:
            Valid Python identifier
        """
        # Replace hyphens, dots, and other non-alphanumeric chars with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized

    def _generate_memory_read_code(self, value: str, indent: str = "    ") -> tuple[str, str | None]:
        """
        Generate code to read a value, resolving memory references.

        Uses TemplateResolver to detect memory binding patterns and generates
        appropriate memory.read() code.

        Args:
            value: The value which may be a memory reference like "{memory.xxx}"
            indent: Indentation for generated code

        Returns:
            Tuple of (generated_code, None) for memory refs, or (None, repr(value)) for constants
        """
        refs = TemplateResolver.find_references(value)
        if refs:
            # Get the first reference (tool configs typically have one ref per property)
            full_key = next(iter(refs))
            # Generate memory.read() with the full key (e.g., "memory.llm_1.url")
            return (f'memory.read("{full_key}")', None)
        else:
            # Not a memory reference - return as constant
            return (None, repr(value))

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
        if not tools:
            return []

        imports = set()

        # Common imports for tool execution
        imports.add("from typing import Any, Dict")
        imports.add("from graphflow_core.steps.registry import StepRegistry")

        # Framework-specific imports
        if self.framework == "pydantic_ai":
            imports.add("from pydantic_ai import RunContext")
        elif self.framework == "langgraph":
            imports.add("from langchain_core.tools import tool")

        # Check for specific step types and add plugin imports
        step_types = {tool.source_step_type for tool in tools}
        if any(s.startswith("http.") for s in step_types):
            imports.add("import graphflow_http")
        if any(s.startswith("ai.") or s == "mcp_client" for s in step_types):
            imports.add("import graphflow_ai")

        return sorted(imports)

    def _compile_pydantic_ai_tool(self, tool: ToolDefinition) -> str:
        """
        Generate Pydantic AI tool function.

        Generates a standalone async function that will be passed to Agent(tools=[...]).
        Uses RunContext for dependency injection (memory access).
        """
        lines = []

        # Generate function signature (no decorator - passed to Agent constructor)
        safe_name = self._sanitize_name(tool.name)
        lines.append(f'async def tool_{safe_name}(')
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

        # Get memory from context deps
        lines.append(f'    memory = ctx.deps["memory"]')
        lines.append(f'')

        # Build step config
        lines.append(f'    # Build step configuration')
        lines.append(f'    step_config = {{}}')

        # Add runtime parameters (memory bindings resolved at runtime)
        for mapping in tool.get_runtime_parameters():
            if mapping.runtime_value:
                mem_read, const_val = self._generate_memory_read_code(mapping.runtime_value)
                if mem_read:
                    lines.append(f'    step_config["{mapping.source_property}"] = {mem_read}')
                else:
                    lines.append(f'    step_config["{mapping.source_property}"] = {const_val}')

        # Add LLM parameters (values passed by LLM)
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
        lines.append(f'        outputs={{"{tool.output_key}": "{{memory.tool_result}}"}}')
        lines.append(f'    )')
        lines.append(f'')

        # Execute step with error handling - return errors to LLM instead of raising
        lines.append(f'    try:')
        lines.append(f'        await step.execute(memory)')
        lines.append(f'        result = memory.read("tool_result")')
        if tool.output_transform:
            lines.append(f'        # Apply output transform')
            lines.append(f'        result = {tool.output_transform}')
        lines.append(f'    except Exception as e:')
        lines.append(f'        # Return error to LLM so it can adapt')
        lines.append(f'        result = f"Error: {{type(e).__name__}}: {{str(e)}}"')
        lines.append(f'')
        lines.append(f'    return result')

        return "\n".join(lines)

    def _compile_langgraph_tool(self, tool: ToolDefinition) -> str:
        """
        Generate LangGraph tool function for use inside closure factory.

        LangGraph uses the @tool decorator from langchain_core.tools.
        Tools are generated with extra indentation to sit inside create_tools(memory).
        Memory access is via closure scope.
        """
        lines = []
        # Extra indentation since this goes inside create_tools(memory) factory
        ind = "    "

        # Generate function signature with @tool decorator
        safe_name = self._sanitize_name(tool.name)
        lines.append(f'{ind}@tool')
        lines.append(f'{ind}async def tool_{safe_name}(')

        # Add LLM parameters
        llm_params = tool.get_llm_parameters()
        for i, mapping in enumerate(llm_params):
            param_name = mapping.llm_parameter_name or mapping.source_property
            param_type = self._get_python_type(mapping.llm_schema)
            default = "" if mapping.required else " = None"
            comma = "," if i < len(llm_params) - 1 else ""
            lines.append(f'{ind}    {param_name}: {param_type}{default}{comma}')

        lines.append(f'{ind}) -> Any:')
        lines.append(f'{ind}    """')
        lines.append(f'{ind}    {tool.description}')

        if llm_params:
            lines.append(f'{ind}')
            lines.append(f'{ind}    Args:')
            for mapping in llm_params:
                param_name = mapping.llm_parameter_name or mapping.source_property
                desc = mapping.llm_description or f"Value for {mapping.source_property}"
                lines.append(f'{ind}        {param_name}: {desc}')

        lines.append(f'{ind}    """')

        # Build step config - memory accessed from closure scope
        lines.append(f'{ind}    # Build step configuration')
        lines.append(f'{ind}    step_config = {{}}')

        # Add runtime parameters (memory bindings resolved at runtime)
        for mapping in tool.get_runtime_parameters():
            if mapping.runtime_value:
                mem_read, const_val = self._generate_memory_read_code(mapping.runtime_value)
                if mem_read:
                    lines.append(f'{ind}    step_config["{mapping.source_property}"] = {mem_read}')
                else:
                    lines.append(f'{ind}    step_config["{mapping.source_property}"] = {const_val}')

        # Add LLM parameters (values passed by LLM)
        for mapping in llm_params:
            param_name = mapping.llm_parameter_name or mapping.source_property
            lines.append(f'{ind}    step_config["{mapping.source_property}"] = {param_name}')

        lines.append(f'{ind}')

        # Create and execute step
        lines.append(f'{ind}    # Create and execute step')
        lines.append(f'{ind}    step_class = StepRegistry.get("{tool.source_step_type}")')
        lines.append(f'{ind}    step = step_class(')
        lines.append(f'{ind}        id="{tool.id}_tool",')
        lines.append(f'{ind}        config=step_config,')
        lines.append(f'{ind}        outputs={{"{tool.output_key}": "{{memory.tool_result}}"}}')
        lines.append(f'{ind}    )')
        lines.append(f'{ind}')

        # Execute step with error handling - return errors to LLM instead of raising
        lines.append(f'{ind}    try:')
        lines.append(f'{ind}        await step.execute(memory)')
        lines.append(f'{ind}        result = memory.read("tool_result")')
        if tool.output_transform:
            lines.append(f'{ind}        # Apply output transform')
            lines.append(f'{ind}        result = {tool.output_transform}')
        lines.append(f'{ind}    except Exception as e:')
        lines.append(f'{ind}        # Return error to LLM so it can adapt')
        lines.append(f'{ind}        result = f"Error: {{type(e).__name__}}: {{str(e)}}"')
        lines.append(f'{ind}')
        lines.append(f'{ind}    return result')

        return "\n".join(lines)

    def compile_langgraph_tool_factory(self, tools: List[ToolDefinition]) -> str:
        """
        Generate factory function that creates tools with memory access via closure.

        This is the key pattern for LangGraph: tools are created inside a factory
        function that captures memory in the closure scope.

        Args:
            tools: List of tool definitions

        Returns:
            Generated Python code for create_tools(memory) factory function
        """
        if not tools:
            return ""

        lines = []
        lines.append('def create_tools(memory):')
        lines.append('    """Create tools with memory access via closure."""')
        lines.append('')

        # Generate each tool function (already indented)
        for tool in tools:
            lines.append(self._compile_langgraph_tool(tool))
            lines.append('')

        # Return list of tool functions
        tool_names = [f'tool_{self._sanitize_name(t.name)}' for t in tools]
        lines.append(f'    return [{", ".join(tool_names)}]')

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

    def get_tool_names(self, tools: List[ToolDefinition]) -> List[str]:
        """
        Get list of generated tool function names.

        Args:
            tools: List of tool definitions

        Returns:
            List of function names (e.g., ['tool_search', 'tool_fetch'])
        """
        return [f"tool_{self._sanitize_name(tool.name)}" for tool in tools]

    # =========================================================================
    # MCP Tool Compilation
    # =========================================================================

    def compile_mcp_tool(self, mcp_tool: MCPTool) -> str:
        """
        Compile an MCP tool to Python code.

        Args:
            mcp_tool: MCP tool definition (server config + tool definition)

        Returns:
            Generated Python code for the MCP tool function
        """
        if self.framework == "pydantic_ai":
            return self._compile_pydantic_ai_mcp_tool(mcp_tool)
        elif self.framework == "langgraph":
            return self._compile_langgraph_mcp_tool(mcp_tool)
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def compile_mcp_tools(self, mcp_tools: List[MCPTool]) -> str:
        """
        Compile multiple MCP tool definitions.

        Args:
            mcp_tools: List of MCP tool definitions

        Returns:
            Generated Python code for all MCP tools
        """
        tool_codes = []
        for mcp_tool in mcp_tools:
            tool_codes.append(self.compile_mcp_tool(mcp_tool))

        return "\n\n".join(tool_codes)

    def get_mcp_tool_imports(self, mcp_tools: List[MCPTool]) -> List[str]:
        """
        Get required imports for compiled MCP tools.

        Args:
            mcp_tools: List of MCP tool definitions

        Returns:
            List of import statements
        """
        if not mcp_tools:
            return []

        imports = set()

        # Common imports
        imports.add("from typing import Any, Dict")

        # MCP client imports
        imports.add("from pydantic_ai.mcp import MCPServerStdio, MCPServerSSE, MCPServerStreamableHTTP")

        # Framework-specific imports
        if self.framework == "pydantic_ai":
            imports.add("from pydantic_ai import RunContext")
        elif self.framework == "langgraph":
            imports.add("from langchain_core.tools import tool")

        return sorted(imports)

    def get_mcp_tool_names(self, mcp_tools: List[MCPTool]) -> List[str]:
        """
        Get list of generated MCP tool function names.

        Args:
            mcp_tools: List of MCP tool definitions

        Returns:
            List of function names
        """
        return [f"tool_{self._sanitize_name(mcp_tool.definition.name)}" for mcp_tool in mcp_tools]

    def _compile_pydantic_ai_mcp_tool(self, mcp_tool: MCPTool) -> str:
        """
        Generate Pydantic AI tool function for an MCP tool.

        Uses ctx.deps["mcp_servers"][server_key] to access the MCP server connection.
        The server should be initialized and entered before running the agent.
        """
        definition = mcp_tool.definition
        server = mcp_tool.server
        lines = []

        # Generate function signature
        safe_name = self._sanitize_name(definition.name)
        lines.append(f'async def tool_{safe_name}(')
        lines.append(f'    ctx: RunContext[Dict[str, Any]],')

        # Add LLM parameters
        llm_params = definition.get_llm_parameters()
        for i, mapping in enumerate(llm_params):
            param_name = mapping.llm_parameter_name or mapping.source_property
            param_type = self._get_python_type(mapping.llm_schema)
            default = "" if mapping.required else " = None"
            comma = "," if i < len(llm_params) - 1 else ""
            lines.append(f'    {param_name}: {param_type}{default}{comma}')

        lines.append(f') -> Any:')
        lines.append(f'    """')
        lines.append(f'    {definition.description}')

        if llm_params:
            lines.append(f'')
            lines.append(f'    Args:')
            for mapping in llm_params:
                param_name = mapping.llm_parameter_name or mapping.source_property
                desc = mapping.llm_description or f"Value for {mapping.source_property}"
                lines.append(f'        {param_name}: {desc}')

        lines.append(f'    """')
        lines.append(f'    memory = ctx.deps["memory"]')
        lines.append(f'    mcp_servers = ctx.deps.get("mcp_servers", {{}})')
        lines.append(f'')

        # Build tool arguments
        lines.append(f'    # Build MCP tool arguments')
        lines.append(f'    tool_args = {{}}')

        # Add runtime parameters
        for mapping in definition.get_runtime_parameters():
            if mapping.runtime_value:
                mem_read, const_val = self._generate_memory_read_code(mapping.runtime_value)
                if mem_read:
                    lines.append(f'    tool_args["{mapping.source_property}"] = {mem_read}')
                else:
                    lines.append(f'    tool_args["{mapping.source_property}"] = {const_val}')

        # Add LLM parameters
        for mapping in llm_params:
            param_name = mapping.llm_parameter_name or mapping.source_property
            lines.append(f'    tool_args["{mapping.source_property}"] = {param_name}')

        lines.append(f'')

        # Get MCP server and call tool
        server_key = server.get_server_key()
        lines.append(f'    # Call MCP tool')
        lines.append(f'    server_key = "{server_key}"')
        lines.append(f'    if server_key not in mcp_servers:')
        lines.append(f'        return f"Error: MCP server not available: {{server_key}}"')
        lines.append(f'')
        lines.append(f'    try:')
        lines.append(f'        mcp_server = mcp_servers[server_key]')
        lines.append(f'        result = await mcp_server.call_tool("{definition.mcp_tool_name}", tool_args)')
        lines.append(f'        # Extract text content from MCP result')
        lines.append(f'        if hasattr(result, "content") and result.content:')
        lines.append(f'            for item in result.content:')
        lines.append(f'                if hasattr(item, "text"):')
        lines.append(f'                    return item.text')
        lines.append(f'            return str(result.content[0])')
        lines.append(f'        return str(result) if result else None')
        lines.append(f'    except Exception as e:')
        lines.append(f'        return f"Error: {{type(e).__name__}}: {{str(e)}}"')

        return "\n".join(lines)

    def _compile_langgraph_mcp_tool(self, mcp_tool: MCPTool) -> str:
        """
        Generate LangGraph tool function for an MCP tool.

        Uses closure scope to access MCP servers. Generated with indentation
        to sit inside create_tools(memory, mcp_servers) factory.
        """
        definition = mcp_tool.definition
        server = mcp_tool.server
        lines = []
        ind = "    "  # Extra indentation for factory function

        # Generate function signature with @tool decorator
        safe_name = self._sanitize_name(definition.name)
        lines.append(f'{ind}@tool')
        lines.append(f'{ind}async def tool_{safe_name}(')

        # Add LLM parameters
        llm_params = definition.get_llm_parameters()
        for i, mapping in enumerate(llm_params):
            param_name = mapping.llm_parameter_name or mapping.source_property
            param_type = self._get_python_type(mapping.llm_schema)
            default = "" if mapping.required else " = None"
            comma = "," if i < len(llm_params) - 1 else ""
            lines.append(f'{ind}    {param_name}: {param_type}{default}{comma}')

        lines.append(f'{ind}) -> Any:')
        lines.append(f'{ind}    """')
        lines.append(f'{ind}    {definition.description}')

        if llm_params:
            lines.append(f'{ind}')
            lines.append(f'{ind}    Args:')
            for mapping in llm_params:
                param_name = mapping.llm_parameter_name or mapping.source_property
                desc = mapping.llm_description or f"Value for {mapping.source_property}"
                lines.append(f'{ind}        {param_name}: {desc}')

        lines.append(f'{ind}    """')

        # Build tool arguments
        lines.append(f'{ind}    # Build MCP tool arguments')
        lines.append(f'{ind}    tool_args = {{}}')

        # Add runtime parameters
        for mapping in definition.get_runtime_parameters():
            if mapping.runtime_value:
                mem_read, const_val = self._generate_memory_read_code(mapping.runtime_value)
                if mem_read:
                    lines.append(f'{ind}    tool_args["{mapping.source_property}"] = {mem_read}')
                else:
                    lines.append(f'{ind}    tool_args["{mapping.source_property}"] = {const_val}')

        # Add LLM parameters
        for mapping in llm_params:
            param_name = mapping.llm_parameter_name or mapping.source_property
            lines.append(f'{ind}    tool_args["{mapping.source_property}"] = {param_name}')

        lines.append(f'{ind}')

        # Get MCP server and call tool
        server_key = server.get_server_key()
        lines.append(f'{ind}    # Call MCP tool')
        lines.append(f'{ind}    server_key = "{server_key}"')
        lines.append(f'{ind}    if server_key not in mcp_servers:')
        lines.append(f'{ind}        return f"Error: MCP server not available: {{server_key}}"')
        lines.append(f'{ind}')
        lines.append(f'{ind}    try:')
        lines.append(f'{ind}        mcp_server = mcp_servers[server_key]')
        lines.append(f'{ind}        result = await mcp_server.call_tool("{definition.mcp_tool_name}", tool_args)')
        lines.append(f'{ind}        # Extract text content from MCP result')
        lines.append(f'{ind}        if hasattr(result, "content") and result.content:')
        lines.append(f'{ind}            for item in result.content:')
        lines.append(f'{ind}                if hasattr(item, "text"):')
        lines.append(f'{ind}                    return item.text')
        lines.append(f'{ind}            return str(result.content[0])')
        lines.append(f'{ind}        return str(result) if result else None')
        lines.append(f'{ind}    except Exception as e:')
        lines.append(f'{ind}        return f"Error: {{type(e).__name__}}: {{str(e)}}"')

        return "\n".join(lines)

    def compile_mcp_server_initialization(self, mcp_tools: List[MCPTool]) -> str:
        """
        Generate code to initialize MCP servers for a list of MCP tools.

        Groups tools by server to avoid duplicate connections.

        Args:
            mcp_tools: List of MCP tool definitions

        Returns:
            Python code to create MCP server instances
        """
        if not mcp_tools:
            return ""

        # Group by server key to avoid duplicates
        servers: Dict[str, MCPServerConfig] = {}
        for mcp_tool in mcp_tools:
            key = mcp_tool.server.get_server_key()
            if key not in servers:
                servers[key] = mcp_tool.server

        lines = []
        lines.append("# MCP Server configurations")
        lines.append("mcp_server_configs = {")

        for key, config in servers.items():
            lines.append(f'    "{key}": {{')
            lines.append(f'        "transport": "{config.transport}",')
            if config.command:
                lines.append(f'        "command": "{config.command}",')
            if config.args:
                lines.append(f'        "args": {json.dumps(config.args)},')
            if config.env:
                lines.append(f'        "env": {json.dumps(config.env)},')
            if config.url:
                lines.append(f'        "url": "{config.url}",')
            if config.headers:
                lines.append(f'        "headers": {json.dumps(config.headers)},')
            lines.append(f'        "timeout": {config.timeout},')
            lines.append(f'    }},')

        lines.append("}")
        lines.append("")
        lines.append("def create_mcp_server(config):")
        lines.append('    """Create MCP server from config dict."""')
        lines.append('    transport = config["transport"]')
        lines.append('    if transport == "stdio":')
        lines.append('        return MCPServerStdio(')
        lines.append('            command=config["command"],')
        lines.append('            args=config.get("args", []),')
        lines.append('            env=config.get("env"),')
        lines.append('            timeout=config.get("timeout", 30.0),')
        lines.append('        )')
        lines.append('    elif transport == "sse":')
        lines.append('        return MCPServerSSE(')
        lines.append('            url=config["url"],')
        lines.append('            headers=config.get("headers"),')
        lines.append('            timeout=config.get("timeout", 30.0),')
        lines.append('        )')
        lines.append('    else:  # streamable_http')
        lines.append('        return MCPServerStreamableHTTP(')
        lines.append('            url=config["url"],')
        lines.append('            headers=config.get("headers"),')
        lines.append('            timeout=config.get("timeout", 30.0),')
        lines.append('        )')

        return "\n".join(lines)

    def compile_langgraph_mcp_tool_factory(
        self,
        step_tools: List[ToolDefinition],
        mcp_tools: List[MCPTool]
    ) -> str:
        """
        Generate factory function for LangGraph that includes both step-based and MCP tools.

        Args:
            step_tools: List of step-based tool definitions
            mcp_tools: List of MCP tool definitions

        Returns:
            Generated Python code for create_tools(memory, mcp_servers) factory
        """
        if not step_tools and not mcp_tools:
            return ""

        lines = []
        lines.append('def create_tools(memory, mcp_servers=None):')
        lines.append('    """Create tools with memory and MCP server access via closure."""')
        lines.append('    if mcp_servers is None:')
        lines.append('        mcp_servers = {}')
        lines.append('')

        # Generate step-based tools
        for tool in step_tools:
            lines.append(self._compile_langgraph_tool(tool))
            lines.append('')

        # Generate MCP tools
        for mcp_tool in mcp_tools:
            lines.append(self._compile_langgraph_mcp_tool(mcp_tool))
            lines.append('')

        # Return list of all tool functions
        all_tool_names = []
        all_tool_names.extend([f'tool_{self._sanitize_name(t.name)}' for t in step_tools])
        all_tool_names.extend([f'tool_{self._sanitize_name(mt.definition.name)}' for mt in mcp_tools])

        lines.append(f'    return [{", ".join(all_tool_names)}]')

        return "\n".join(lines)
