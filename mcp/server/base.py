"""Base MCP server interface."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from mcp.protocol import JSONRPCRequest, JSONRPCResponse


class MCPServer(ABC):
    """Abstract base class for MCP servers."""

    def __init__(self) -> None:
        """Initialize MCP server."""
        self.running = False
        self.handlers: Dict[str, Callable] = {}

    @abstractmethod
    async def start(self) -> None:
        """Start the MCP server."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the MCP server."""
        pass

    @abstractmethod
    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """
        Handle incoming JSON-RPC request.

        Args:
            request: JSON-RPC request

        Returns:
            JSON-RPC response
        """
        pass

    def register_handler(self, method: str, handler: Callable) -> None:
        """
        Register a method handler.

        Args:
            method: MCP method name (e.g., "tools/list")
            handler: Async callable that handles the method
        """
        self.handlers[method] = handler

    async def __aenter__(self) -> "MCPServer":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()
