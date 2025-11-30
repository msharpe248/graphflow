"""GraphFlow AI Plugin - LLM, Human Interaction, and MCP Steps."""

from graphflow_ai.steps import LLMStep, HumanInputStep
from graphflow_ai.mcp_step import MCPClientStep
from graphflow_ai.mcp_client import (
    mcp_session_context,
    discover_mcp_tools,
    call_mcp_tool,
    extract_mcp_result,
    MCPServerPool,
    MCPClientError,
    MCPConnectionError,
    MCPToolCallError,
)

__all__ = [
    # Steps
    "LLMStep",
    "HumanInputStep",
    "MCPClientStep",
    # MCP client utilities
    "mcp_session_context",
    "discover_mcp_tools",
    "call_mcp_tool",
    "extract_mcp_result",
    "MCPServerPool",
    "MCPClientError",
    "MCPConnectionError",
    "MCPToolCallError",
]
__version__ = "1.0.0"
