"""Integration tests for MCP Gateway."""

import pytest

from mcp.config import Config
from mcp.gateway import MCPGateway
from mcp.protocol import Tool


@pytest.mark.asyncio
async def test_gateway_initialization(tmp_path) -> None:
    """Test gateway initialization with config."""
    # Create minimal config
    config = Config(
        enabled_providers=[],  # No providers for this test
        provider_settings={},
    )

    gateway = MCPGateway(config)

    # Should initialize without error (but no providers)
    assert gateway.config == config
    assert gateway.providers == {}


@pytest.mark.asyncio
async def test_gateway_tools_list_empty() -> None:
    """Test tools/list with no providers."""
    config = Config(enabled_providers=[], provider_settings={})
    gateway = MCPGateway(config)

    # Mock empty provider list
    gateway.tool_aggregator = None
    gateway._tools_cache = []

    result = await gateway.handle_tools_list({})

    assert "tools" in result
    assert result["tools"] == []


@pytest.mark.asyncio
async def test_gateway_tools_call_error() -> None:
    """Test tools/call with missing tool name."""
    from mcp.exceptions import ProtocolError

    config = Config(enabled_providers=[], provider_settings={})
    gateway = MCPGateway(config)

    # Should raise error for missing tool name
    with pytest.raises(ProtocolError, match="Tool name required"):
        await gateway.handle_tools_call({})


@pytest.mark.asyncio
async def test_gateway_resources_list_empty() -> None:
    """Test resources/list with no providers."""
    config = Config(enabled_providers=[], provider_settings={})
    gateway = MCPGateway(config)

    gateway.resource_aggregator = None
    gateway._resources_cache = []

    result = await gateway.handle_resources_list({})

    assert "resources" in result
    assert result["resources"] == []


@pytest.mark.asyncio
async def test_gateway_resources_read_error() -> None:
    """Test resources/read with missing URI."""
    from mcp.exceptions import ProtocolError

    config = Config(enabled_providers=[], provider_settings={})
    gateway = MCPGateway(config)

    # Should raise error for missing URI
    with pytest.raises(ProtocolError, match="Resource URI required"):
        await gateway.handle_resources_read({})


# Note: Full integration tests with real providers would require
# setting up actual MCP servers, which is beyond unit testing scope.
# These tests verify the gateway's error handling and basic structure.
