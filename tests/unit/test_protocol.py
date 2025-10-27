"""Tests for MCP protocol models."""

import pytest
from pydantic import ValidationError

from mcp.protocol import (
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    Resource,
    ResourceType,
    Tool,
    ToolParameter,
)


def test_jsonrpc_request() -> None:
    """Test JSONRPCRequest model."""
    request = JSONRPCRequest(
        id="test-1", method="resources/list", params={"limit": 10}
    )

    assert request.jsonrpc == "2.0"
    assert request.id == "test-1"
    assert request.method == "resources/list"
    assert request.params == {"limit": 10}


def test_jsonrpc_response_success() -> None:
    """Test successful JSONRPCResponse."""
    response = JSONRPCResponse(
        id="test-1", result={"resources": [{"uri": "test://resource"}]}
    )

    assert response.jsonrpc == "2.0"
    assert response.id == "test-1"
    assert response.result is not None
    assert response.error is None


def test_jsonrpc_response_error() -> None:
    """Test error JSONRPCResponse."""
    error = JSONRPCError(code=-32600, message="Invalid Request")
    response = JSONRPCResponse(id="test-1", error=error)

    assert response.jsonrpc == "2.0"
    assert response.id == "test-1"
    assert response.result is None
    assert response.error is not None
    assert response.error.code == -32600


def test_resource_model() -> None:
    """Test Resource model."""
    resource = Resource(
        uri="jira://PROJ-123",
        name="PROJ-123",
        description="Test issue",
        mime_type="application/json",
        resource_type=ResourceType.TEXT,
    )

    assert resource.uri == "jira://PROJ-123"
    assert resource.resource_type == ResourceType.TEXT


def test_tool_model() -> None:
    """Test Tool model."""
    tool = Tool(
        name="search_issues",
        description="Search Jira issues",
        input_schema={
            "type": "object",
            "properties": {
                "jql": {"type": "string", "description": "JQL query"},
                "maxResults": {"type": "integer", "default": 50},
            },
            "required": ["jql"],
        },
    )

    assert tool.name == "search_issues"
    assert "jql" in tool.input_schema["properties"]
    assert tool.input_schema["required"] == ["jql"]


def test_jsonrpc_version_validation() -> None:
    """Test that JSON-RPC version must be 2.0."""
    with pytest.raises(ValidationError):
        JSONRPCRequest(
            jsonrpc="1.0",  # type: ignore
            id="test-1",
            method="test",
        )
