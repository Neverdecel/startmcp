"""Conflict resolution and helpful error messages for MCP gateway."""

from typing import Dict, List, Optional

from mcp.aggregator import ToolAggregator


class ConflictResolver:
    """Generates helpful error messages for tool conflicts and ambiguities."""

    def __init__(self, aggregator: ToolAggregator) -> None:
        """
        Initialize conflict resolver.

        Args:
            aggregator: Tool aggregator for accessing conflict information
        """
        self.aggregator = aggregator

    def get_ambiguity_error(self, tool_name: str) -> Dict:
        """
        Generate detailed error for ambiguous tool name.

        Args:
            tool_name: Ambiguous tool name

        Returns:
            Error dict suitable for JSON-RPC error.data field
        """
        # Find all providers that have this tool
        available_variants: List[str] = []

        for cached_tool_name, provider_name in self.aggregator._provider_map.items():
            # Check if this is a namespaced version of the requested tool
            if ":" in cached_tool_name:
                _, base_name = cached_tool_name.split(":", 1)
                if base_name == tool_name:
                    available_variants.append(cached_tool_name)

        return {
            "error_type": "ambiguous_tool",
            "tool_name": tool_name,
            "message": f"Tool '{tool_name}' exists in multiple providers",
            "available_tools": available_variants,
            "suggestion": f"Please specify provider using one of: {', '.join(available_variants)}",
            "example": f"Use '{available_variants[0]}' instead of '{tool_name}'"
            if available_variants
            else None,
        }

    def get_not_found_error(self, tool_name: str) -> Dict:
        """
        Generate helpful error for tool not found.

        Args:
            tool_name: Tool name that wasn't found

        Returns:
            Error dict with suggestions
        """
        # Try to find similar tool names
        similar_tools = self._find_similar_tools(tool_name)

        return {
            "error_type": "tool_not_found",
            "tool_name": tool_name,
            "message": f"Tool '{tool_name}' not found",
            "similar_tools": similar_tools,
            "suggestion": f"Did you mean: {', '.join(similar_tools[:3])}"
            if similar_tools
            else "Use 'tools/list' to see available tools",
        }

    def _find_similar_tools(
        self, tool_name: str, max_suggestions: int = 5
    ) -> List[str]:
        """
        Find similar tool names using simple string matching.

        Args:
            tool_name: Tool name to find matches for
            max_suggestions: Maximum number of suggestions

        Returns:
            List of similar tool names
        """
        similar: List[tuple[int, str]] = []

        for cached_tool_name in self.aggregator._tool_cache.keys():
            # Calculate similarity (simple approach: substring match)
            score = 0

            # Exact substring match
            if tool_name.lower() in cached_tool_name.lower():
                score = 10

            # Word boundary match
            if any(
                word.lower() in cached_tool_name.lower()
                for word in tool_name.split("_")
            ):
                score = 5

            # Starts with same prefix
            if cached_tool_name.lower().startswith(tool_name.lower()[:3]):
                score = 3

            if score > 0:
                similar.append((score, cached_tool_name))

        # Sort by score and return top matches
        similar.sort(reverse=True, key=lambda x: x[0])
        return [name for _, name in similar[:max_suggestions]]

    def get_provider_unavailable_error(self, provider_name: str) -> Dict:
        """
        Generate error for unavailable provider.

        Args:
            provider_name: Provider name

        Returns:
            Error dict
        """
        return {
            "error_type": "provider_unavailable",
            "provider_name": provider_name,
            "message": f"Provider '{provider_name}' is not available",
            "suggestion": "Check if the provider is enabled in config.yaml and connected",
        }

    def get_conflict_summary(self) -> Dict:
        """
        Get summary of all tool conflicts.

        Returns:
            Dict with conflict information
        """
        conflicts = self.aggregator.get_conflicting_tools()

        conflict_details = {}
        for tool_name in conflicts:
            # Find all providers that have this tool
            providers = []
            for cached_tool_name, provider_name in self.aggregator._provider_map.items():
                if ":" in cached_tool_name:
                    _, base_name = cached_tool_name.split(":", 1)
                    if base_name == tool_name:
                        providers.append(provider_name)

            conflict_details[tool_name] = {
                "providers": providers,
                "namespaced_forms": [
                    f"{p}:{tool_name}" for p in providers
                ],
            }

        return {
            "total_conflicts": len(conflicts),
            "conflicts": conflict_details,
            "recommendation": "Use namespaced forms (provider:tool_name) for conflicting tools",
        }
