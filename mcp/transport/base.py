"""Base transport interface for MCP."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, Optional

from mcp.protocol import JSONRPCRequest, JSONRPCResponse


class Transport(ABC):
    """Abstract base class for MCP transports."""

    def __init__(self) -> None:
        """Initialize transport."""
        self.connected = False

    @abstractmethod
    async def connect(self, **kwargs: Any) -> None:
        """
        Establish connection to MCP server.

        Args:
            **kwargs: Transport-specific connection parameters
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass

    @abstractmethod
    async def send_request(
        self, request: JSONRPCRequest, timeout: Optional[float] = None
    ) -> JSONRPCResponse:
        """
        Send a JSON-RPC request and wait for response.

        Args:
            request: The JSON-RPC request to send
            timeout: Optional timeout in seconds

        Returns:
            The JSON-RPC response

        Raises:
            TransportError: If send fails
            TimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Listen for incoming messages (notifications, etc).

        Yields:
            Incoming JSON-RPC messages

        Raises:
            TransportError: If listening fails
        """
        pass

    async def __aenter__(self) -> "Transport":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()
