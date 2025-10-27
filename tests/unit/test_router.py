"""Tests for tool and resource routing."""

import pytest

from mcp.aggregator import ResourceAggregator, ToolAggregator
from mcp.protocol import ToolCallResult
from mcp.provider import MCPProvider
from mcp.router import ResourceRouter, ToolRouter


# Mock providers (reuse from test_aggregator)
from tests.unit.test_aggregator import (
    MockProvider1,
    MockProvider2,
    providers_with_conflicts,
    providers_with_unique_tools,
)


@pytest.mark.asyncio
async def test_route_unique_tool(providers_with_unique_tools: list) -> None:
    """Test routing tool call with no conflicts."""
    aggregator = ToolAggregator(providers_with_unique_tools)
    await aggregator.aggregate_tools()

    providers_dict = {p.name: p for p in providers_with_unique_tools}
    router = ToolRouter(providers_dict, aggregator)

    # Mock call_tool to return result
    for provider in providers_with_unique_tools:
        provider.call_tool = lambda name, args: ToolCallResult(  # type: ignore
            content=[{"type": "text", "text": f"Called {name}"}]
        )

    # Route unique tool (no namespace needed)
    result = await router.route_tool_call("tool_a", {})
    assert result.content[0]["text"] == "Called tool_a"


@pytest.mark.asyncio
async def test_route_namespaced_tool(providers_with_conflicts: list) -> None:
    """Test routing namespaced tool call."""
    aggregator = ToolAggregator(providers_with_conflicts)
    await aggregator.aggregate_tools()

    providers_dict = {p.name: p for p in providers_with_conflicts}
    router = ToolRouter(providers_dict, aggregator)

    # Mock call_tool
    for provider in providers_with_conflicts:
        provider.call_tool = lambda name, args: ToolCallResult(  # type: ignore
            content=[{"type": "text", "text": f"Called on {provider.name}"}]
        )

    # Route with explicit namespace
    result = await router.route_tool_call("provider1:search", {})
    assert "provider1" in result.content[0]["text"]


@pytest.mark.asyncio
async def test_route_ambiguous_tool_error(providers_with_conflicts: list) -> None:
    """Test error when routing ambiguous tool."""
    aggregator = ToolAggregator(providers_with_conflicts)
    await aggregator.aggregate_tools()

    providers_dict = {p.name: p for p in providers_with_conflicts}
    router = ToolRouter(providers_dict, aggregator)

    # Try to route "search" without namespace - should fail
    with pytest.raises(ValueError, match="Ambiguous"):
        await router.route_tool_call("search", {})


@pytest.mark.asyncio
async def test_route_nonexistent_tool(providers_with_unique_tools: list) -> None:
    """Test error when tool doesn't exist."""
    aggregator = ToolAggregator(providers_with_unique_tools)
    await aggregator.aggregate_tools()

    providers_dict = {p.name: p for p in providers_with_unique_tools}
    router = ToolRouter(providers_dict, aggregator)

    # Try to route non-existent tool
    with pytest.raises(ValueError, match="not found"):
        await router.route_tool_call("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_resource_router() -> None:
    """Test resource routing."""
    p1 = MockProvider1()
    await p1.connect()

    # Mock read_resource
    p1.read_resource = lambda uri: {"uri": uri, "content": f"Resource {uri}"}  # type: ignore

    aggregator = ResourceAggregator([p1])
    providers_dict = {"provider1": p1}
    router = ResourceRouter(providers_dict, aggregator)

    # Route with provider prefix
    content = await router.route_resource_read("provider1://PROJ-123")
    assert "PROJ-123" in str(content)


@pytest.mark.asyncio
async def test_resource_router_invalid_uri() -> None:
    """Test error with invalid URI."""
    p1 = MockProvider1()
    aggregator = ResourceAggregator([p1])
    providers_dict = {"provider1": p1}
    router = ResourceRouter(providers_dict, aggregator)

    # Invalid URI format
    with pytest.raises(ValueError, match="Invalid"):
        await router.route_resource_read("invalid_uri")

    # Unknown provider
    with pytest.raises(ValueError, match="Invalid"):
        await router.route_resource_read("unknown://resource")
