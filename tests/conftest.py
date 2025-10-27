"""Pytest configuration and fixtures."""

import asyncio
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator

import pytest
from pydantic import BaseModel

from mcp.client import MCPClient
from mcp.config import Config
from mcp.provider import MCPProvider, ProviderConfig
from mcp.transport.base import Transport


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock Transport for testing


class MockTransport(Transport):
    """Mock transport for testing."""

    def __init__(self) -> None:
        """Initialize mock transport."""
        super().__init__()
        self.sent_requests: list[Dict[str, Any]] = []
        self.responses: list[Dict[str, Any]] = []

    async def connect(self, **kwargs: Any) -> None:
        """Mock connect."""
        self.connected = True

    async def disconnect(self) -> None:
        """Mock disconnect."""
        self.connected = False

    async def send_request(
        self, request: Any, timeout: float | None = None
    ) -> Any:
        """Mock send request."""
        from mcp.protocol import JSONRPCResponse

        self.sent_requests.append(request.model_dump())

        # Return mock response
        if self.responses:
            response_data = self.responses.pop(0)
        else:
            response_data = {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {"success": True},
            }

        return JSONRPCResponse(**response_data)

    async def listen(self) -> Any:
        """Mock listen."""
        if False:
            yield {}

    def add_response(self, response: Dict[str, Any]) -> None:
        """Add a mock response."""
        self.responses.append(response)


@pytest.fixture
def mock_transport() -> MockTransport:
    """Provide mock transport."""
    return MockTransport()


# Mock Provider for testing


class MockProviderConfig(ProviderConfig):
    """Mock provider configuration."""

    api_key: str = "test_key"


class MockProvider(MCPProvider):
    """Mock provider for testing."""

    name = "mock"
    display_name = "Mock Provider"
    description = "Test provider"
    transport_type = "stdio"
    requires_oauth = False
    config_class = MockProviderConfig

    async def create_transport(self) -> Transport:
        """Create mock transport."""
        return MockTransport()


@pytest.fixture
def mock_provider() -> MockProvider:
    """Provide mock provider."""
    return MockProvider({"api_key": "test_key"})


@pytest.fixture
async def connected_mock_provider(
    mock_provider: MockProvider,
) -> AsyncGenerator[MockProvider, None]:
    """Provide connected mock provider."""
    await mock_provider.connect()
    yield mock_provider
    await mock_provider.disconnect()


# Configuration fixtures


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_config() -> Config:
    """Provide sample configuration."""
    return Config(
        enabled_providers=["mock", "test"],
        provider_settings={
            "mock": {"api_key": "test_key"},
            "test": {"endpoint": "http://localhost:8080"},
        },
    )


# Client fixtures


@pytest.fixture
async def mock_client(
    mock_transport: MockTransport,
) -> AsyncGenerator[MCPClient, None]:
    """Provide mock MCP client."""
    client = MCPClient(mock_transport)
    await client.connect()
    yield client
    await client.disconnect()
