"""MCP (Model Context Protocol) client utilities.

This module provides utilities for connecting to MCP servers and discovering/calling tools.
It supports three transport types:
- stdio: Local process communication
- sse: Server-Sent Events over HTTP
- streamable_http: Streamable HTTP transport

Uses the raw MCP SDK for direct tool calls.
"""

from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
import asyncio
import os

from graphflow_core.models.tool import MCPServerConfig


class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class MCPConnectionError(MCPClientError):
    """Raised when connection to MCP server fails."""
    pass


class MCPToolCallError(MCPClientError):
    """Raised when a tool call fails."""
    pass


@asynccontextmanager
async def mcp_session_context(config: MCPServerConfig):
    """
    Context manager for MCP server connection using raw MCP SDK.

    Usage:
        async with mcp_session_context(config) as session:
            tools = await session.list_tools()
            result = await session.call_tool("tool_name", {"arg": "value"})

    Args:
        config: MCPServerConfig with transport type and connection details

    Yields:
        Connected ClientSession instance
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        raise MCPConnectionError(
            "mcp package is required for MCP support. "
            "Install with: pip install mcp"
        )

    if config.transport == "stdio":
        if not config.command:
            raise MCPConnectionError("command is required for stdio transport")

        server_params = StdioServerParameters(
            command=config.command,
            args=config.args or [],
            env={**os.environ, **(config.env or {})},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
        except Exception as e:
            raise MCPConnectionError(f"Failed to connect to MCP server: {e}") from e

    elif config.transport == "sse":
        if not config.url:
            raise MCPConnectionError("url is required for SSE transport")

        try:
            from mcp.client.sse import sse_client
        except ImportError:
            raise MCPConnectionError(
                "SSE transport requires additional MCP components"
            )

        try:
            async with sse_client(
                url=config.url,
                headers=config.headers or {},
                timeout=config.timeout or 30.0,
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
        except Exception as e:
            raise MCPConnectionError(f"Failed to connect to MCP server: {e}") from e

    elif config.transport == "streamable_http":
        if not config.url:
            raise MCPConnectionError("url is required for streamable_http transport")

        try:
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError:
            raise MCPConnectionError(
                "streamable_http transport requires MCP with HTTP support"
            )

        try:
            async with streamablehttp_client(
                url=config.url,
                headers=config.headers or {},
                timeout=config.timeout or 30.0,
            ) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
        except Exception as e:
            raise MCPConnectionError(f"Failed to connect to MCP server: {e}") from e

    else:
        raise MCPConnectionError(f"Unknown transport type: {config.transport}")


async def discover_mcp_tools(config: MCPServerConfig) -> Dict[str, Any]:
    """
    Connect to an MCP server and discover available tools.

    Args:
        config: MCPServerConfig with transport type and connection details

    Returns:
        Dict containing:
            - success: bool
            - server_info: Dict with name, version (if available)
            - tools: List of tool definitions with name, description, input_schema
            - error: Optional error message

    Example response:
        {
            "success": True,
            "server_info": {"name": "mcp-server-fetch", "version": "1.0.0"},
            "tools": [
                {
                    "name": "fetch",
                    "description": "Fetch URL content",
                    "input_schema": {...}
                }
            ]
        }
    """
    try:
        async with mcp_session_context(config) as session:
            # Get tools from server
            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools if hasattr(tools_result, 'tools') else tools_result

            # Extract server info if available
            server_info = {}

            # Convert tools to serializable format
            tools = []
            for tool in mcp_tools:
                tool_def = {
                    "name": tool.name,
                    "description": getattr(tool, 'description', None) or "",
                }
                # Handle input schema - can be inputSchema or input_schema
                input_schema = getattr(tool, 'inputSchema', None) or getattr(tool, 'input_schema', None)
                if input_schema:
                    # Convert to dict if it's a Pydantic model or similar
                    if hasattr(input_schema, 'model_dump'):
                        tool_def["input_schema"] = input_schema.model_dump()
                    elif hasattr(input_schema, 'dict'):
                        tool_def["input_schema"] = input_schema.dict()
                    elif isinstance(input_schema, dict):
                        tool_def["input_schema"] = input_schema
                    else:
                        tool_def["input_schema"] = {}
                else:
                    tool_def["input_schema"] = {}

                tools.append(tool_def)

            return {
                "success": True,
                "server_info": server_info,
                "tools": tools,
                "error": None,
            }

    except MCPConnectionError as e:
        return {
            "success": False,
            "server_info": {},
            "tools": [],
            "error": str(e),
        }
    except Exception as e:
        return {
            "success": False,
            "server_info": {},
            "tools": [],
            "error": f"Discovery failed: {type(e).__name__}: {str(e)}",
        }


async def call_mcp_tool(
    config: MCPServerConfig,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Any:
    """
    Connect to an MCP server and call a specific tool.

    This creates a new connection for each call. For multiple calls
    to the same server, use mcp_session_context() directly.

    Args:
        config: MCPServerConfig with transport type and connection details
        tool_name: Name of the tool to call
        arguments: Arguments to pass to the tool

    Returns:
        Tool result (extracted text content or raw result)

    Raises:
        MCPToolCallError: If the tool call fails
    """
    try:
        async with mcp_session_context(config) as session:
            result = await session.call_tool(tool_name, arguments)
            return extract_mcp_result(result)
    except MCPConnectionError:
        raise
    except Exception as e:
        raise MCPToolCallError(
            f"Tool call '{tool_name}' failed: {type(e).__name__}: {str(e)}"
        ) from e


def extract_mcp_result(result: Any) -> Any:
    """
    Extract usable content from an MCP tool result.

    MCP tool results can contain various content types (text, images, etc.).
    This function extracts the most useful representation.

    Args:
        result: Raw MCP tool result

    Returns:
        Extracted content (string for text, or raw content for other types)
    """
    # Handle None result
    if result is None:
        return None

    # If result has content attribute (standard MCP response)
    if hasattr(result, 'content'):
        content = result.content
        if not content:
            return None

        # Extract text from first text content block
        for item in content:
            if hasattr(item, 'text'):
                return item.text
            elif hasattr(item, 'type') and item.type == 'text':
                return getattr(item, 'text', str(item))

        # Return first content item as fallback
        first_item = content[0]
        if hasattr(first_item, 'text'):
            return first_item.text
        return str(first_item)

    # Handle string result directly
    if isinstance(result, str):
        return result

    # Handle dict result
    if isinstance(result, dict):
        return result

    # Fallback: convert to string
    return str(result)


class MCPServerPool:
    """
    Manages a pool of MCP server connections.

    Used to share connections across multiple tool calls within
    the same LLM step execution.
    """

    def __init__(self):
        self._sessions: Dict[str, Any] = {}
        self._configs: Dict[str, MCPServerConfig] = {}
        self._contexts: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, config: MCPServerConfig):
        """
        Get an existing session or create a new one.

        Args:
            config: MCPServerConfig for the server

        Returns:
            Connected ClientSession instance
        """
        key = config.get_server_key()

        async with self._lock:
            if key not in self._sessions:
                # Create and enter the context
                ctx = mcp_session_context(config)
                session = await ctx.__aenter__()
                self._sessions[key] = session
                self._contexts[key] = ctx
                self._configs[key] = config

            return self._sessions[key]

    async def close_all(self):
        """Close all server connections in the pool."""
        async with self._lock:
            for key, ctx in list(self._contexts.items()):
                try:
                    await ctx.__aexit__(None, None, None)
                except Exception:
                    pass  # Ignore errors on cleanup
            self._sessions.clear()
            self._contexts.clear()
            self._configs.clear()

    @asynccontextmanager
    async def managed_pool(self):
        """
        Context manager that ensures all connections are closed.

        Usage:
            async with pool.managed_pool():
                session1 = await pool.get_or_create(config1)
                session2 = await pool.get_or_create(config2)
                # Use sessions...
            # All connections automatically closed
        """
        try:
            yield self
        finally:
            await self.close_all()
