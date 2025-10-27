"""Tool and resource aggregation system for MCP gateway."""

from collections import defaultdict
from typing import Dict, List, Set

from mcp.categories import ProviderCategory
from mcp.protocol import Prompt, Resource, Tool
from mcp.provider import MCPProvider


class ToolAggregator:
    """Aggregates tools from multiple providers with conflict detection."""

    def __init__(self, providers: List[MCPProvider]) -> None:
        """
        Initialize tool aggregator.

        Args:
            providers: List of connected MCP providers
        """
        self.providers = providers
        self._tool_cache: Dict[str, Tool] = {}
        self._provider_map: Dict[str, str] = {}  # tool_name -> provider_name
        self._conflicts: Set[str] = set()  # tool names that conflict

    async def aggregate_tools(self) -> List[Tool]:
        """
        Aggregate tools from all providers with hybrid namespacing.

        Returns:
            List of tools with conflicts namespaced
        """
        # Step 1: Collect all tools from all providers
        provider_tools: Dict[str, List[Tool]] = {}

        for provider in self.providers:
            try:
                tools = await provider.list_tools()
                provider_tools[provider.name] = tools
            except Exception as e:
                # Log error but continue
                print(f"Warning: Failed to list tools from {provider.name}: {e}")
                provider_tools[provider.name] = []

        # Step 2: Detect conflicts
        tool_name_counts: Dict[str, int] = defaultdict(int)
        tool_to_providers: Dict[str, List[str]] = defaultdict(list)

        for provider_name, tools in provider_tools.items():
            for tool in tools:
                tool_name_counts[tool.name] += 1
                tool_to_providers[tool.name].append(provider_name)

        # Identify conflicts
        self._conflicts = {
            name for name, count in tool_name_counts.items() if count > 1
        }

        # Step 3: Build aggregated tool list with hybrid namespacing
        aggregated_tools: List[Tool] = []

        for provider in self.providers:
            provider_name = provider.name
            tools = provider_tools.get(provider_name, [])

            for tool in tools:
                original_name = tool.name

                # Determine if namespacing is needed
                if original_name in self._conflicts:
                    # Conflict - apply namespace
                    namespaced_name = f"{provider_name}:{original_name}"
                    namespace_reason = "conflict"
                else:
                    # No conflict - use natural name
                    namespaced_name = original_name
                    namespace_reason = None

                # Create enriched tool with metadata
                enriched_tool = Tool(
                    name=namespaced_name,
                    description=tool.description,
                    input_schema=tool.input_schema,
                    provider=provider_name,
                    category=provider.category.value if provider.category else None,
                    namespace_reason=namespace_reason,
                )

                aggregated_tools.append(enriched_tool)

                # Update mappings
                self._tool_cache[namespaced_name] = enriched_tool
                self._provider_map[namespaced_name] = provider_name

        return aggregated_tools

    def get_provider_for_tool(self, tool_name: str) -> str:
        """
        Get provider name for a given tool.

        Args:
            tool_name: Tool name (may be namespaced)

        Returns:
            Provider name

        Raises:
            KeyError: If tool not found
        """
        if tool_name in self._provider_map:
            return self._provider_map[tool_name]

        # Check if it's a natural name that has conflict
        if tool_name in self._conflicts:
            raise ValueError(
                f"Ambiguous tool name '{tool_name}'. "
                f"This tool exists in multiple providers. "
                f"Please use namespaced form: <provider>:{tool_name}"
            )

        raise KeyError(f"Tool '{tool_name}' not found")

    def get_conflicting_tools(self) -> Set[str]:
        """
        Get set of tool names that have conflicts.

        Returns:
            Set of conflicting tool names (natural names, not namespaced)
        """
        return self._conflicts.copy()

    def get_tool_info(self, tool_name: str) -> Tool:
        """
        Get tool information.

        Args:
            tool_name: Tool name (may be namespaced)

        Returns:
            Tool object

        Raises:
            KeyError: If tool not found
        """
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]

        raise KeyError(f"Tool '{tool_name}' not found")


class ResourceAggregator:
    """Aggregates resources from multiple providers with URI routing."""

    def __init__(self, providers: List[MCPProvider]) -> None:
        """
        Initialize resource aggregator.

        Args:
            providers: List of connected MCP providers
        """
        self.providers = providers
        self._provider_map: Dict[str, str] = {}  # uri_scheme -> provider_name

        # Build URI scheme mapping
        for provider in providers:
            # Use provider name as URI scheme
            self._provider_map[provider.name] = provider.name

    async def aggregate_resources(self) -> List[Resource]:
        """
        Aggregate resources from all providers with provider-prefixed URIs.

        Returns:
            List of resources with URIs prefixed by provider
        """
        aggregated_resources: List[Resource] = []

        for provider in self.providers:
            try:
                resources = await provider.list_resources()

                # Prefix URIs with provider name
                for resource in resources:
                    # Parse existing URI
                    original_uri = resource.uri

                    # Add provider prefix if not already present
                    if not original_uri.startswith(f"{provider.name}://"):
                        prefixed_uri = f"{provider.name}://{original_uri}"
                    else:
                        prefixed_uri = original_uri

                    # Create resource with prefixed URI
                    prefixed_resource = Resource(
                        uri=prefixed_uri,
                        name=resource.name,
                        description=resource.description,
                        mime_type=resource.mime_type,
                        resource_type=resource.resource_type,
                    )

                    aggregated_resources.append(prefixed_resource)

            except Exception as e:
                # Log error but continue
                print(f"Warning: Failed to list resources from {provider.name}: {e}")
                continue

        return aggregated_resources

    def get_provider_for_uri(self, uri: str) -> str:
        """
        Extract provider name from URI scheme.

        Args:
            uri: Resource URI (e.g., "atlassian://PROJ-123")

        Returns:
            Provider name

        Raises:
            ValueError: If URI format is invalid or provider not found
        """
        # Parse URI scheme
        if "://" not in uri:
            raise ValueError(f"Invalid URI format: {uri}. Expected: <provider>://<path>")

        scheme, _ = uri.split("://", 1)

        if scheme not in self._provider_map:
            raise ValueError(
                f"Unknown provider scheme '{scheme}' in URI: {uri}. "
                f"Available providers: {list(self._provider_map.keys())}"
            )

        return self._provider_map[scheme]

    def strip_provider_prefix(self, uri: str) -> str:
        """
        Remove provider prefix from URI.

        Args:
            uri: Prefixed URI (e.g., "atlassian://PROJ-123")

        Returns:
            Original URI without provider prefix
        """
        if "://" in uri:
            _, path = uri.split("://", 1)
            return path
        return uri


class PromptAggregator:
    """Aggregates prompts from multiple providers."""

    def __init__(self, providers: List[MCPProvider]) -> None:
        """
        Initialize prompt aggregator.

        Args:
            providers: List of connected MCP providers
        """
        self.providers = providers

    async def aggregate_prompts(self) -> List[Prompt]:
        """
        Aggregate prompts from all providers.

        Returns:
            List of prompts (with provider prefix if conflicts)
        """
        aggregated_prompts: List[Prompt] = []

        # Similar to tool aggregation, but simpler for now
        # TODO: Add conflict detection for prompts

        for provider in self.providers:
            try:
                prompts = await provider.list_prompts()
                aggregated_prompts.extend(prompts)
            except Exception as e:
                print(f"Warning: Failed to list prompts from {provider.name}: {e}")
                continue

        return aggregated_prompts
