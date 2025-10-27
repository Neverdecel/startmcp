"""Tests for MCP client."""

import pytest

from mcp.client import MCPClient
from mcp.exceptions import ProtocolError
from mcp.protocol import Resource


@pytest.mark.asyncio
async def test_client_connection(mock_client: MCPClient) -> None:
    """Test client connection."""
    assert mock_client.transport.connected


@pytest.mark.asyncio
async def test_list_resources(mock_client: MCPClient, mock_transport: any) -> None:
    """Test listing resources."""
    # Set up mock response
    mock_transport.add_response(
        {
            "jsonrpc": "2.0",
            "id": "test",
            "result": {
                "resources": [
                    {
                        "uri": "test://resource1",
                        "name": "Resource 1",
                        "resource_type": "text",
                    }
                ]
            },
        }
    )

    resources = await mock_client.list_resources()

    assert len(resources) == 1
    assert resources[0].uri == "test://resource1"
    assert isinstance(resources[0], Resource)


@pytest.mark.asyncio
async def test_call_tool(mock_client: MCPClient, mock_transport: any) -> None:
    """Test calling a tool."""
    # Set up mock response
    mock_transport.add_response(
        {
            "jsonrpc": "2.0",
            "id": "test",
            "result": {
                "content": [{"type": "text", "text": "Tool executed"}],
                "is_error": False,
            },
        }
    )

    result = await mock_client.call_tool(
        "test_tool", {"arg1": "value1"}
    )

    assert result.is_error is False
    assert len(result.content) == 1


@pytest.mark.asyncio
async def test_protocol_error(mock_client: MCPClient, mock_transport: any) -> None:
    """Test protocol error handling."""
    # Set up error response
    mock_transport.add_response(
        {
            "jsonrpc": "2.0",
            "id": "test",
            "error": {"code": -32600, "message": "Invalid Request"},
        }
    )

    with pytest.raises(ProtocolError, match="MCP error -32600"):
        await mock_client.list_resources()


@pytest.mark.asyncio
async def test_request_id_generation(mock_client: MCPClient) -> None:
    """Test that request IDs are unique."""
    id1 = mock_client._generate_request_id()
    id2 = mock_client._generate_request_id()

    assert id1 != id2
    assert id1.startswith("req-")
    assert id2.startswith("req-")
