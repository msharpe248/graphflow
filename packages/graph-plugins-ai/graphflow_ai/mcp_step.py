"""MCP Client step for connecting to MCP servers and executing tools."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry
from graphflow_core.memory.store import MemoryStore
from graphflow_core.models.tool import MCPServerConfig


@StepRegistry.register(category="ai", description="Connect to MCP server and execute a tool")
class MCPClientStep(StepBase):
    """
    MCP Client step - connect to an MCP server and execute a single tool.

    This step provides direct execution mode for MCP tools. For exposing
    MCP tools to an LLM step, use MCPTool entries in the LLM's tools array.

    Supports three transport types:
    - stdio: Local process communication (command + args)
    - sse: Server-Sent Events over HTTP
    - streamable_http: Streamable HTTP transport

    Config (all in mcp_config object):
        server.transport: str - "stdio", "sse", or "streamable_http"
        server.command: str - Command to run for stdio (e.g., "uvx", "npx")
        server.args: List[str] - Command arguments for stdio
        server.env: Dict[str, str] - Environment variables for stdio
        server.url: str - Server URL for sse/streamable_http
        server.headers: Dict[str, str] - HTTP headers for sse/streamable_http
        server.timeout: float - Connection/call timeout in seconds (default: 30)
        tool_name: str - Name of the tool to execute
        tool_args: Dict[str, Any] - Arguments for the tool (supports {memory.var} bindings)

    Outputs:
        result: The tool execution result
        error: Error message if execution failed (optional)
    """

    label = "MCP Client"
    description = "Connect to MCP server and execute a tool"
    can_be_tool = False
    tool_ineligible_reason = "MCP client manages external connections, not suitable as a tool"

    @classmethod
    def get_type(cls) -> str:
        return "mcp_client"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                # All MCP configuration in one wizard
                "mcp_config": {
                    "type": "object",
                    "description": "MCP server connection, tool selection, and arguments",
                    "x-editor": "mcp-config-wizard",
                    "properties": {
                        "server": {
                            "type": "object",
                            "properties": {
                                "transport": {"type": "string", "enum": ["stdio", "sse", "streamable_http"]},
                                "command": {"type": "string"},
                                "args": {"type": "array", "items": {"type": "string"}},
                                "env": {"type": "object"},
                                "url": {"type": "string"},
                                "headers": {"type": "object"},
                                "timeout": {"type": "number"}
                            }
                        },
                        "tool_name": {"type": "string"},
                        "tool_args": {"type": "object"}
                    }
                },
            },
            "required": []
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Memory variables referenced in tool_args using {memory.variable} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "result": {
                    "description": "Tool execution result"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if execution failed"
                }
            }
        }

    @classmethod
    def get_code_template(cls, framework: str) -> Optional[str]:
        """Return framework-specific code generation template."""
        template_dir = Path(__file__).parent / "templates" / "mcp"
        template_file = template_dir / f"{framework}.jinja"

        if template_file.exists():
            return template_file.read_text()

        return None

    @classmethod
    def get_supported_frameworks(cls) -> List[str]:
        """MCP client step supports both Pydantic AI and LangGraph."""
        return ["pydantic_ai", "langgraph"]

    def _get_mcp_config(self, memory: Optional[MemoryStore] = None) -> Dict[str, Any]:
        """Get the unified MCP configuration, resolving memory references if needed."""
        config = self.config.get("mcp_config", {})

        # If config is a memory reference string, resolve it
        if isinstance(config, str) and config.startswith("{memory.") and config.endswith("}"):
            if memory is None:
                return {"server": {}, "tool_name": "", "tool_args": {}}
            # Extract the memory path
            mem_path = config[8:-1]  # Remove "{memory." and "}"
            # Read from memory using the "memory" namespace which searches inputs/intermediate/outputs
            resolved = memory.read(f"memory.{mem_path}")
            if isinstance(resolved, dict):
                return resolved
            return {"server": {}, "tool_name": "", "tool_args": {}}

        if not isinstance(config, dict):
            return {"server": {}, "tool_name": "", "tool_args": {}}
        return config

    def _resolve_headers(self, headers: Optional[Dict[str, str]], memory: MemoryStore) -> Optional[Dict[str, str]]:
        """
        Resolve bindings in header values.

        Supports {secrets.name} and {memory.name} syntax.
        Can be used for full replacement or partial (e.g., "Bearer {secrets.API_KEY}").
        """
        if not headers:
            return headers

        secrets_pattern = re.compile(r'\{secrets\.([^}]+)\}')
        memory_pattern = re.compile(r'\{memory\.([^}]+)\}')
        resolved = {}

        for key, value in headers.items():
            if isinstance(value, str):
                result = value

                # Replace all {secrets.name} occurrences
                def replace_secret(match):
                    secret_name = match.group(1)
                    try:
                        return memory.get_secret(secret_name)
                    except Exception:
                        return match.group(0)  # Keep original if not found

                result = secrets_pattern.sub(replace_secret, result)

                # Replace all {memory.name} occurrences
                def replace_memory(match):
                    mem_path = match.group(1)
                    try:
                        mem_value = memory.read(f"memory.{mem_path}")
                        return str(mem_value) if mem_value is not None else ""
                    except Exception:
                        return match.group(0)  # Keep original if not found

                result = memory_pattern.sub(replace_memory, result)

                resolved[key] = result
            else:
                resolved[key] = value

        return resolved

    def _build_server_config(self, memory: Optional[MemoryStore] = None) -> MCPServerConfig:
        """Build MCPServerConfig from step config."""
        mcp_config = self._get_mcp_config(memory)
        server = mcp_config.get("server", {})

        # Resolve header bindings if memory is available
        headers = server.get("headers")
        if memory and headers:
            headers = self._resolve_headers(headers, memory)

        return MCPServerConfig(
            transport=server.get("transport", "stdio"),
            command=server.get("command"),
            args=server.get("args"),
            env=server.get("env"),
            url=server.get("url"),
            headers=headers,
            timeout=server.get("timeout", 30.0),
        )

    def _get_tool_config(self, memory: Optional[MemoryStore] = None) -> Dict[str, Any]:
        """Get tool configuration from mcp_config property."""
        mcp_config = self._get_mcp_config(memory)
        return {
            "tool_name": mcp_config.get("tool_name", ""),
            "tool_args": mcp_config.get("tool_args", {}),
        }

    def _resolve_tool_args(self, memory: MemoryStore) -> Dict[str, Any]:
        """
        Resolve memory bindings in tool_args.

        Supports {memory.variable} syntax for dynamic values.
        """
        tool_config = self._get_tool_config(memory)
        raw_args = tool_config.get("tool_args", {})
        if not raw_args:
            return {}

        pattern = re.compile(r'\{memory\.([^}]+)\}')
        resolved = {}

        for key, value in raw_args.items():
            if isinstance(value, str):
                match = pattern.search(value)
                if match:
                    # Full replacement if entire string is a memory ref
                    if pattern.fullmatch(value):
                        mem_path = match.group(1)
                        resolved[key] = memory.read(f"intermediate.{mem_path}")
                    else:
                        # Partial replacement for string interpolation
                        def replace_match(m):
                            mem_path = m.group(1)
                            val = memory.read(f"intermediate.{mem_path}")
                            return str(val) if val is not None else ""
                        resolved[key] = pattern.sub(replace_match, value)
                else:
                    resolved[key] = value
            else:
                resolved[key] = value

        return resolved

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute the MCP tool.

        This is the runtime execution method for testing/debugging.
        Compiled graphs will use the generated code from templates.
        """
        from graphflow_ai.mcp_client import (
            call_mcp_tool,
            MCPClientError,
        )

        tool_config = self._get_tool_config(memory)
        tool_name = tool_config.get("tool_name")
        if not tool_name:
            # Debug: show what config we received
            mcp_config = self._get_mcp_config(memory)
            raise ValueError(
                f"mcp_config.tool_name is required. "
                f"Received mcp_config keys: {list(mcp_config.keys()) if mcp_config else 'None'}. "
                f"Full step config keys: {list(self.config.keys()) if self.config else 'None'}"
            )

        # Build server config and resolve arguments
        server_config = self._build_server_config(memory)
        tool_args = self._resolve_tool_args(memory)

        try:
            # Call the MCP tool
            result = await call_mcp_tool(server_config, tool_name, tool_args)

            # Write result to output
            if "result" in self.outputs:
                output_ref = self.outputs["result"]
                match = re.search(r'\{memory\.([^}]+)\}', output_ref)
                if match:
                    memory.write(f"memory.{match.group(1)}", result)

        except MCPClientError as e:
            # Write error to output if configured
            if "error" in self.outputs:
                output_ref = self.outputs["error"]
                match = re.search(r'\{memory\.([^}]+)\}', output_ref)
                if match:
                    memory.write(f"memory.{match.group(1)}", str(e))

            # Re-raise to signal failure
            raise
