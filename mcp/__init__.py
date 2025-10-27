"""startmcp - A flexible MCP client framework."""

__version__ = "0.1.0"

from mcp.client import MCPClient
from mcp.provider import MCPProvider

__all__ = ["MCPClient", "MCPProvider"]
