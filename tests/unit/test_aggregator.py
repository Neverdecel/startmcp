"""Tests for tool and resource aggregation."""

import pytest

from mcp.aggregator import ResourceAggregator, ToolAggregator
from mcp.categories import ProviderCategory
from mcp.protocol import Resource, ResourceType, Tool
from mcp.provider import MCPProvider, ProviderConfig
from mcp.transport.base import Transport


# Mock providers for testing


class MockProvider1(MCPProvider):
    """First mock provider."""

    name = "provider1"
    display_name = "Provider 1"
    category = ProviderCategory.ENTERPRISE
    transport_type = "stdio"

    async def create_transport(self) -> Transport:
        from tests.conftest import MockTransport

        return MockTransport()


class MockProvider2(MCPProvider):
    """Second mock provider."""

    name = "provider2"
    display_name = "Provider 2"
    category = ProviderCategory.DEV_TOOLS
    transport_type = "stdio"

    async def create_transport(self) -> Transport:
        from tests.conftest import MockTransport

        return MockTransport()


@pytest.fixture
async def providers_with_unique_tools() -> list[MCPProvider]:
    """Providers with unique tool names (no conflicts)."""
    p1 = MockProvider1()
    p2 = MockProvider2()

    await p1.connect()
    await p2.connect()

    # Mock tool lists
    p1.client._send_request = lambda *args, **kwargs: {  # type: ignore
        "tools": [
            {"name": "tool_a", "description": "Tool A", "input_schema": {}},
            {"name": "tool_b", "description": "Tool B", "input_schema": {}},
        ]
    }

    p2.client._send_request = lambda *args, **kwargs: {  # type: ignore
        "tools": [
            {"name": "tool_c", "description": "Tool C", "input_schema": {}},
            {"name": "tool_d", "description": "Tool D", "input_schema": {}},
        ]
    }

    return [p1, p2]


@pytest.fixture
async def providers_with_conflicts() -> list[MCPProvider]:
    """Providers with conflicting tool names."""
    p1 = MockProvider1()
    p2 = MockProvider2()

    await p1.connect()
    await p2.connect()

    # Both have "search" tool - conflict!
    p1.client._send_request = lambda *args, **kwargs: {  # type: ignore
        "tools": [
            {"name": "search", "description": "Search P1", "input_schema": {}},
            {"name": "unique_p1", "description": "Unique to P1", "input_schema": {}},
        ]
    }

    p2.client._send_request = lambda *args, **kwargs: {  # type: ignore
        "tools": [
            {"name": "search", "description": "Search P2", "input_schema": {}},
            {"name": "unique_p2", "description": "Unique to P2", "input_schema": {}},
        ]
    }

    return [p1, p2]


@pytest.mark.asyncio
async def test_aggregate_unique_tools(providers_with_unique_tools: list) -> None:
    """Test aggregating tools with no conflicts."""
    aggregator = ToolAggregator(providers_with_unique_tools)

    tools = await aggregator.aggregate_tools()

    assert len(tools) == 4
    tool_names = [t.name for t in tools]

    # All tools should have natural names (no namespace prefix)
    assert "tool_a" in tool_names
    assert "tool_b" in tool_names
    assert "tool_c" in tool_names
    assert "tool_d" in tool_names

    # Check metadata
    for tool in tools:
        assert tool.provider in ["provider1", "provider2"]
        assert tool.category in ["enterprise", "dev_tools"]
        assert tool.namespace_reason is None  # No conflicts


@pytest.mark.asyncio
async def test_aggregate_conflicting_tools(providers_with_conflicts: list) -> None:
    """Test aggregating tools with conflicts."""
    aggregator = ToolAggregator(providers_with_conflicts)

    tools = await aggregator.aggregate_tools()

    assert len(tools) == 4
    tool_names = [t.name for t in tools]

    # Conflicting tools should be namespaced
    assert "provider1:search" in tool_names
    assert "provider2:search" in tool_names

    # Unique tools should NOT be namespaced
    assert "unique_p1" in tool_names
    assert "unique_p2" in tool_names

    # Check conflict detection
    conflicts = aggregator.get_conflicting_tools()
    assert "search" in conflicts
    assert "unique_p1" not in conflicts


@pytest.mark.asyncio
async def test_get_provider_for_tool(providers_with_conflicts: list) -> None:
    """Test looking up provider for a tool."""
    aggregator = ToolAggregator(providers_with_conflicts)
    await aggregator.aggregate_tools()

    # Unique tools - can find without namespace
    assert aggregator.get_provider_for_tool("unique_p1") == "provider1"
    assert aggregator.get_provider_for_tool("unique_p2") == "provider2"

    # Conflicting tools - must use namespace
    assert aggregator.get_provider_for_tool("provider1:search") == "provider1"
    assert aggregator.get_provider_for_tool("provider2:search") == "provider2"

    # Ambiguous - should raise ValueError
    with pytest.raises(ValueError, match="Ambiguous"):
        aggregator.get_provider_for_tool("search")


@pytest.mark.asyncio
async def test_resource_aggregator() -> None:
    """Test resource aggregation with URI prefixing."""
    p1 = MockProvider1()
    await p1.connect()

    # Mock resource list
    p1.client._send_request = lambda *args, **kwargs: {  # type: ignore
        "resources": [
            {
                "uri": "PROJ-123",
                "name": "Issue 123",
                "resource_type": "text",
            }
        ]
    }

    aggregator = ResourceAggregator([p1])
    resources = await aggregator.aggregate_resources()

    assert len(resources) == 1
    assert resources[0].uri == "provider1://PROJ-123"  # Prefixed!


@pytest.mark.asyncio
async def test_resource_uri_routing() -> None:
    """Test URI-based provider routing."""
    p1 = MockProvider1()
    p2 = MockProvider2()

    aggregator = ResourceAggregator([p1, p2])

    # Test routing
    assert aggregator.get_provider_for_uri("provider1://resource") == "provider1"
    assert aggregator.get_provider_for_uri("provider2://resource") == "provider2"

    # Test URI stripping
    assert aggregator.strip_provider_prefix("provider1://PROJ-123") == "PROJ-123"

    # Invalid URIs
    with pytest.raises(ValueError, match="Invalid URI"):
        aggregator.get_provider_for_uri("invalid_uri_no_scheme")

    with pytest.raises(ValueError, match="Unknown provider"):
        aggregator.get_provider_for_uri("unknown://resource")
