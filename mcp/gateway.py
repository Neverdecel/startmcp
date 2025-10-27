"""MCP Gateway - orchestrates providers and acts as unified MCP server."""

import sys
from typing import Any, Dict, List, Optional

from mcp.aggregator import PromptAggregator, ResourceAggregator, ToolAggregator
from mcp.config import Config
from mcp.conflict_resolver import ConflictResolver
from mcp.exceptions import ProtocolError, ProviderError
from mcp.protocol import (
    JSONRPCError,
    Prompt,
    PromptResult,
    Resource,
    ResourceContent,
    Tool,
    ToolCallResult,
)
from mcp.provider import MCPProvider
from mcp.registry import get_registry
from mcp.router import ResourceRouter, ToolRouter
from mcp.server.base import MCPServer


class MCPGateway:
    """
    MCP Gateway - aggregates multiple MCP providers into a single MCP server.

    Acts as both an MCP server (for AI assistants) and an MCP client (to backend providers).
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize MCP gateway.

        Args:
            config: Configuration with enabled providers
        """
        self.config = config
        self.providers: Dict[str, MCPProvider] = {}
        self.registry = get_registry()

        # Aggregators
        self.tool_aggregator: Optional[ToolAggregator] = None
        self.resource_aggregator: Optional[ResourceAggregator] = None
        self.prompt_aggregator: Optional[PromptAggregator] = None

        # Routers
        self.tool_router: Optional[ToolRouter] = None
        self.resource_router: Optional[ResourceRouter] = None

        # Conflict resolver
        self.conflict_resolver: Optional[ConflictResolver] = None

        # Cached aggregated data
        self._tools_cache: Optional[List[Tool]] = None
        self._resources_cache: Optional[List[Resource]] = None
        self._prompts_cache: Optional[List[Prompt]] = None

    async def start(self) -> None:
        """Initialize gateway and connect to all providers."""
        sys.stderr.write("Starting MCP Gateway...\n")

        # Discover providers
        self.registry.discover_providers()

        # Connect to enabled providers
        for provider_name in self.config.enabled_providers:
            sys.stderr.write(f"Connecting to provider: {provider_name}\n")

            try:
                # Get provider config
                provider_config = self.config.get_provider_config(provider_name)

                # Create provider instance
                provider = self.registry.create_provider(provider_name, provider_config)

                # Connect
                await provider.connect()

                # Store
                self.providers[provider_name] = provider

                sys.stderr.write(f"✓ Connected to {provider_name}\n")

            except Exception as e:
                sys.stderr.write(
                    f"✗ Failed to connect to {provider_name}: {e}\n"
                )
                # Continue with other providers
                continue

        if not self.providers:
            raise RuntimeError("No providers connected. Check configuration.")

        # Initialize aggregators
        provider_list = list(self.providers.values())
        self.tool_aggregator = ToolAggregator(provider_list)
        self.resource_aggregator = ResourceAggregator(provider_list)
        self.prompt_aggregator = PromptAggregator(provider_list)

        # Initialize routers
        self.tool_router = ToolRouter(self.providers, self.tool_aggregator)
        self.resource_router = ResourceRouter(self.providers, self.resource_aggregator)

        # Initialize conflict resolver
        self.conflict_resolver = ConflictResolver(self.tool_aggregator)

        # Pre-aggregate data
        sys.stderr.write("Aggregating tools and resources...\n")
        await self._refresh_aggregations()

        sys.stderr.write(
            f"✓ Gateway started with {len(self.providers)} providers\n"
        )
        sys.stderr.write(
            f"  Tools: {len(self._tools_cache or [])}\n"
        )
        sys.stderr.write(
            f"  Resources: {len(self._resources_cache or [])}\n"
        )

        # Show conflicts if any
        if self.tool_aggregator:
            conflicts = self.tool_aggregator.get_conflicting_tools()
            if conflicts:
                sys.stderr.write(
                    f"  ⚠ Tool conflicts detected: {len(conflicts)} tools have namespace prefix\n"
                )

    async def stop(self) -> None:
        """Disconnect from all providers."""
        sys.stderr.write("Stopping MCP Gateway...\n")

        for provider_name, provider in self.providers.items():
            try:
                await provider.disconnect()
                sys.stderr.write(f"✓ Disconnected from {provider_name}\n")
            except Exception as e:
                sys.stderr.write(
                    f"✗ Error disconnecting from {provider_name}: {e}\n"
                )

        self.providers.clear()
        sys.stderr.write("Gateway stopped\n")

    async def _refresh_aggregations(self) -> None:
        """Refresh aggregated tools, resources, and prompts."""
        if self.tool_aggregator:
            self._tools_cache = await self.tool_aggregator.aggregate_tools()

        if self.resource_aggregator:
            self._resources_cache = await self.resource_aggregator.aggregate_resources()

        if self.prompt_aggregator:
            self._prompts_cache = await self.prompt_aggregator.aggregate_prompts()

    # MCP Protocol Handler Methods

    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/list request.

        Args:
            params: Request parameters (unused)

        Returns:
            Dict with tools list
        """
        if self._tools_cache is None:
            await self._refresh_aggregations()

        return {
            "tools": [
                tool.model_dump(mode="json", exclude_none=True)
                for tool in (self._tools_cache or [])
            ]
        }

    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/call request.

        Args:
            params: Request parameters with 'name' and 'arguments'

        Returns:
            Dict with tool call result
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ProtocolError("Tool name required")

        if not self.tool_router or not self.conflict_resolver:
            raise RuntimeError("Gateway not initialized")

        try:
            # Route tool call
            result = await self.tool_router.route_tool_call(tool_name, arguments)

            return result.model_dump(mode="json", exclude_none=True)

        except ValueError as e:
            # Check if it's an ambiguity error
            if "ambiguous" in str(e).lower() or "multiple providers" in str(e).lower():
                # Generate helpful error
                error_data = self.conflict_resolver.get_ambiguity_error(tool_name)
                raise ProtocolError(str(e)) from e

            # Tool not found
            error_data = self.conflict_resolver.get_not_found_error(tool_name)
            raise ProtocolError(str(e)) from e

        except RuntimeError as e:
            # Provider unavailable
            raise ProviderError(str(e)) from e

    async def handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle resources/list request.

        Args:
            params: Request parameters (unused)

        Returns:
            Dict with resources list
        """
        if self._resources_cache is None:
            await self._refresh_aggregations()

        return {
            "resources": [
                resource.model_dump(mode="json", exclude_none=True)
                for resource in (self._resources_cache or [])
            ]
        }

    async def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle resources/read request.

        Args:
            params: Request parameters with 'uri'

        Returns:
            Dict with resource content
        """
        uri = params.get("uri")

        if not uri:
            raise ProtocolError("Resource URI required")

        if not self.resource_router:
            raise RuntimeError("Gateway not initialized")

        try:
            # Route resource read
            content = await self.resource_router.route_resource_read(uri)

            # Return content (already a ResourceContent object)
            return content.model_dump(mode="json", exclude_none=True)

        except ValueError as e:
            raise ProtocolError(str(e)) from e

        except RuntimeError as e:
            raise ProviderError(str(e)) from e

    async def handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle prompts/list request.

        Args:
            params: Request parameters (unused)

        Returns:
            Dict with prompts list
        """
        if self._prompts_cache is None:
            await self._refresh_aggregations()

        return {
            "prompts": [
                prompt.model_dump(mode="json", exclude_none=True)
                for prompt in (self._prompts_cache or [])
            ]
        }

    async def handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle prompts/get request.

        Args:
            params: Request parameters with 'name' and 'arguments'

        Returns:
            Dict with prompt result
        """
        # TODO: Implement prompt routing similar to tools
        raise NotImplementedError("Prompt routing not yet implemented")

    def register_handlers(self, server: MCPServer) -> None:
        """
        Register all gateway handlers with an MCP server.

        Args:
            server: MCP server to register handlers with
        """
        server.register_handler("tools/list", self.handle_tools_list)
        server.register_handler("tools/call", self.handle_tools_call)
        server.register_handler("resources/list", self.handle_resources_list)
        server.register_handler("resources/read", self.handle_resources_read)
        server.register_handler("prompts/list", self.handle_prompts_list)
        server.register_handler("prompts/get", self.handle_prompts_get)

    # Context manager support

    async def __aenter__(self) -> "MCPGateway":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()
