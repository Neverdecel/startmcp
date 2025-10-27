"""Tool and resource routing for MCP gateway."""

from typing import Any, Dict, List, Optional

from mcp.aggregator import ResourceAggregator, ToolAggregator
from mcp.protocol import ToolCallResult
from mcp.provider import MCPProvider


class ToolRouter:
    """Routes tool calls to appropriate providers."""

    def __init__(
        self, providers: Dict[str, MCPProvider], aggregator: ToolAggregator
    ) -> None:
        """
        Initialize tool router.

        Args:
            providers: Dict mapping provider name to provider instance
            aggregator: Tool aggregator for looking up provider mappings
        """
        self.providers = providers
        self.aggregator = aggregator

    async def route_tool_call(
        self, tool_name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> ToolCallResult:
        """
        Route tool call to appropriate provider.

        Args:
            tool_name: Tool name (may be namespaced like "provider:tool")
            arguments: Tool arguments

        Returns:
            Tool call result

        Raises:
            ValueError: If tool is ambiguous or not found
            RuntimeError: If provider is not available
        """
        # Parse tool name to extract provider
        provider_name, actual_tool_name = self._parse_tool_name(tool_name)

        # Get provider
        if provider_name not in self.providers:
            raise RuntimeError(
                f"Provider '{provider_name}' not available or not connected"
            )

        provider = self.providers[provider_name]

        # Call tool on provider
        result = await provider.call_tool(actual_tool_name, arguments)

        return result

    def _parse_tool_name(self, tool_name: str) -> tuple[str, str]:
        """
        Parse tool name to extract provider and actual tool name.

        Args:
            tool_name: Tool name (may be "provider:tool" or just "tool")

        Returns:
            Tuple of (provider_name, actual_tool_name)

        Raises:
            ValueError: If tool name is ambiguous or invalid
        """
        # Check if explicitly namespaced
        if ":" in tool_name:
            parts = tool_name.split(":", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid namespaced tool name: {tool_name}")

            provider_name = parts[0]
            actual_tool_name = parts[1]

            # Verify this tool exists
            try:
                expected_provider = self.aggregator.get_provider_for_tool(tool_name)
                if expected_provider != provider_name:
                    raise ValueError(
                        f"Tool '{tool_name}' does not belong to provider '{provider_name}'"
                    )
            except KeyError:
                raise ValueError(f"Tool '{tool_name}' not found")

            return provider_name, actual_tool_name

        # Not namespaced - look up in aggregator
        try:
            provider_name = self.aggregator.get_provider_for_tool(tool_name)
            return provider_name, tool_name

        except ValueError as e:
            # Ambiguous tool name
            raise ValueError(str(e))

        except KeyError:
            # Tool not found
            raise ValueError(
                f"Tool '{tool_name}' not found. "
                f"Use 'tools/list' to see available tools."
            )


class ResourceRouter:
    """Routes resource operations to appropriate providers."""

    def __init__(
        self, providers: Dict[str, MCPProvider], aggregator: ResourceAggregator
    ) -> None:
        """
        Initialize resource router.

        Args:
            providers: Dict mapping provider name to provider instance
            aggregator: Resource aggregator for URI parsing
        """
        self.providers = providers
        self.aggregator = aggregator

    async def route_resource_read(self, uri: str) -> Any:
        """
        Route resource read to appropriate provider.

        Args:
            uri: Resource URI (must be provider-prefixed, e.g., "atlassian://PROJ-123")

        Returns:
            Resource content

        Raises:
            ValueError: If URI is invalid
            RuntimeError: If provider is not available
        """
        # Extract provider from URI
        try:
            provider_name = self.aggregator.get_provider_for_uri(uri)
        except ValueError as e:
            raise ValueError(f"Invalid resource URI: {e}")

        # Get provider
        if provider_name not in self.providers:
            raise RuntimeError(
                f"Provider '{provider_name}' not available or not connected"
            )

        provider = self.providers[provider_name]

        # Strip provider prefix to get original URI
        original_uri = self.aggregator.strip_provider_prefix(uri)

        # Read resource from provider
        content = await provider.read_resource(original_uri)

        return content
