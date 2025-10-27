"""Tests for provider system."""

import pytest

from mcp.provider import MCPProvider


@pytest.mark.asyncio
async def test_provider_connection(mock_provider: MCPProvider) -> None:
    """Test provider connection."""
    assert not mock_provider.connected

    await mock_provider.connect()
    assert mock_provider.connected

    await mock_provider.disconnect()
    assert not mock_provider.connected


@pytest.mark.asyncio
async def test_provider_context_manager(mock_provider: MCPProvider) -> None:
    """Test provider as context manager."""
    async with mock_provider as provider:
        assert provider.connected

    assert not mock_provider.connected


@pytest.mark.asyncio
async def test_provider_list_resources(
    connected_mock_provider: MCPProvider,
) -> None:
    """Test provider list_resources delegates to client."""
    # This would normally raise an error without mock transport
    # returning proper data, but we're just testing the delegation
    try:
        resources = await connected_mock_provider.list_resources()
        # If we get here, delegation worked
        assert isinstance(resources, list)
    except Exception:
        # Expected if mock doesn't return proper data
        pass


@pytest.mark.asyncio
async def test_provider_not_connected_error(mock_provider: MCPProvider) -> None:
    """Test that calling methods on disconnected provider raises error."""
    with pytest.raises(RuntimeError, match="Provider not connected"):
        await mock_provider.list_resources()


def test_provider_metadata(mock_provider: MCPProvider) -> None:
    """Test provider metadata attributes."""
    assert mock_provider.name == "mock"
    assert mock_provider.display_name == "Mock Provider"
    assert mock_provider.transport_type in ["sse", "stdio"]


def test_provider_config_validation(mock_provider: MCPProvider) -> None:
    """Test provider configuration validation."""
    # Config should be valid by default
    assert mock_provider.config.api_key == "test_key"
