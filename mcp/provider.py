"""Base provider class for MCP providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from mcp.categories import ProviderCategory
from mcp.client import MCPClient
from mcp.protocol import Prompt, Resource, Tool
from mcp.transport.base import Transport


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    enabled: bool = True


class MCPProvider(ABC):
    """Abstract base class for MCP providers."""

    # Metadata (to be overridden by subclasses)
    name: str = ""  # Unique identifier (e.g., "atlassian")
    display_name: str = ""  # Human-readable name (e.g., "Atlassian Suite")
    category: ProviderCategory = ProviderCategory.CUSTOM
    icon: str = "📦"  # Emoji icon
    description: str = ""
    transport_type: str = "sse"  # "sse" or "stdio"
    requires_oauth: bool = False
    config_class: Type[ProviderConfig] = ProviderConfig

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize provider.

        Args:
            config: Provider-specific configuration
        """
        self.config = self.config_class(**(config or {}))
        self.transport: Optional[Transport] = None
        self.client: Optional[MCPClient] = None
        self._connected = False

    @abstractmethod
    async def create_transport(self) -> Transport:
        """
        Create and configure transport for this provider.

        Returns:
            Configured transport instance
        """
        pass

    async def connect(self) -> None:
        """Initialize connection to MCP server."""
        self.transport = await self.create_transport()
        self.client = MCPClient(self.transport)
        await self.client.connect()
        self._connected = True

    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        if self.client:
            await self.client.disconnect()
            self.client = None
        self.transport = None
        self._connected = False

    @property
    def connected(self) -> bool:
        """Check if provider is connected."""
        return self._connected

    # MCP Protocol Methods (delegates to client)

    async def list_resources(self) -> List[Resource]:
        """List available resources from this provider."""
        if not self.client:
            raise RuntimeError("Provider not connected")
        return await self.client.list_resources()

    async def read_resource(self, uri: str) -> Any:
        """Read resource content."""
        if not self.client:
            raise RuntimeError("Provider not connected")
        return await self.client.read_resource(uri)

    async def list_tools(self) -> List[Tool]:
        """List available tools from this provider."""
        if not self.client:
            raise RuntimeError("Provider not connected")
        return await self.client.list_tools()

    async def call_tool(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call a tool."""
        if not self.client:
            raise RuntimeError("Provider not connected")
        return await self.client.call_tool(name, arguments)

    async def list_prompts(self) -> List[Prompt]:
        """List available prompts from this provider."""
        if not self.client:
            raise RuntimeError("Provider not connected")
        return await self.client.list_prompts()

    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get a prompt with parameters."""
        if not self.client:
            raise RuntimeError("Provider not connected")
        return await self.client.get_prompt(name, arguments)

    # Health & Validation

    async def health_check(self) -> bool:
        """
        Check if provider is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.connected:
                await self.connect()
            # Try listing resources as a health check
            await self.list_resources()
            return True
        except Exception:
            return False

    async def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate using Pydantic model
            self.config_class(**self.config.model_dump())
            return True
        except Exception:
            return False

    # Context manager support

    async def __aenter__(self) -> "MCPProvider":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(name='{self.name}', connected={self.connected})>"
