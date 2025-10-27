# Creating Custom Providers

This guide explains how to create custom MCP providers for startmcp.

## Provider Structure

Create a new provider directory:

```
provider_mcps/<category>/<provider_name>/
├── __init__.py           # Package marker
├── provider.py           # Provider implementation
└── config.py             # Configuration model (optional)
```

## Basic Provider

### 1. Define Configuration (Optional)

```python
# provider_mcps/custom/my_provider/config.py
from pydantic import BaseModel, Field

class MyProviderConfig(BaseModel):
    """Configuration for My Provider."""

    api_key: str = Field(description="API key for authentication")
    endpoint: str = Field(
        default="https://api.example.com",
        description="API endpoint"
    )
    timeout: int = Field(default=30, description="Request timeout")
```

### 2. Implement Provider

```python
# provider_mcps/custom/my_provider/provider.py
from typing import Optional, Dict
from mcp.provider import MCPProvider
from mcp.categories import ProviderCategory
from mcp.transport.base import Transport
from mcp.transport.sse import SSETransport
from .config import MyProviderConfig

class MyProvider(MCPProvider):
    """My Custom Provider for XYZ service."""

    # Metadata
    name = "my_provider"              # Unique identifier
    display_name = "My Provider"       # Human-readable name
    category = ProviderCategory.CUSTOM # Category for wizard
    icon = "🔧"                        # Emoji icon
    description = "Connect to XYZ service"
    transport_type = "sse"             # or "stdio"
    requires_oauth = False             # True if OAuth needed
    config_class = MyProviderConfig    # Configuration class

    async def create_transport(self) -> Transport:
        """Create and configure transport for this provider."""
        return SSETransport(
            url=self.config.endpoint,
            headers={"Authorization": f"Bearer {self.config.api_key}"}
        )
```

## SSE Provider Example

For providers with HTTP/SSE endpoints:

```python
from mcp.transport.sse import SSETransport

class MySSEProvider(MCPProvider):
    transport_type = "sse"

    async def create_transport(self) -> Transport:
        return SSETransport(
            url="https://api.example.com/mcp/sse",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "X-Custom-Header": "value"
            }
        )
```

## stdio Provider Example

For providers that run as subprocesses:

```python
from mcp.transport.stdio import StdioTransport

class MyStdioProvider(MCPProvider):
    transport_type = "stdio"

    async def create_transport(self) -> Transport:
        command = ["my-mcp-server", "--port", "8080"]
        return StdioTransport(command=command)
```

## OAuth Provider Example

For providers requiring OAuth:

```python
class MyOAuthProvider(MCPProvider):
    requires_oauth = True

    async def authenticate(self) -> Dict[str, str]:
        """
        Run OAuth flow and return tokens.

        Returns:
            Dict with access_token, refresh_token, etc.
        """
        from mcp.auth.oauth import OAuth2Client

        client = OAuth2Client(
            client_id=self.config.client_id,
            auth_url="https://example.com/oauth/authorize",
            token_url="https://example.com/oauth/token",
            redirect_uri="http://localhost:8000/callback"
        )

        return await client.authenticate()
```

## Provider Categories

Choose the appropriate category:

```python
from mcp.categories import ProviderCategory

ProviderCategory.ENTERPRISE  # Atlassian, Salesforce, etc.
ProviderCategory.DEV_TOOLS   # GitHub, GitLab, etc.
ProviderCategory.DATA        # Databases, data warehouses
ProviderCategory.CLOUD       # AWS, GCP, Azure
ProviderCategory.WEB         # Web scraping, APIs
ProviderCategory.CUSTOM      # Custom/other providers
```

## Convenience Methods (Optional)

Add provider-specific helper methods:

```python
class MyProvider(MCPProvider):
    # ... base implementation ...

    async def search(self, query: str, limit: int = 10):
        """Search using this provider."""
        return await self.call_tool(
            "search",
            {"query": query, "limit": limit}
        )

    async def get_item(self, item_id: str):
        """Get item by ID."""
        return await self.call_tool(
            "get_item",
            {"id": item_id}
        )
```

## Testing Your Provider

Create tests in `tests/unit/test_my_provider.py`:

```python
import pytest
from provider_mcps.custom.my_provider.provider import MyProvider

@pytest.mark.asyncio
async def test_provider_connection():
    """Test provider can connect."""
    provider = MyProvider({"api_key": "test_key"})

    async with provider:
        tools = await provider.list_tools()
        assert len(tools) > 0

@pytest.mark.asyncio
async def test_search():
    """Test search functionality."""
    provider = MyProvider({"api_key": "test_key"})

    async with provider:
        results = await provider.search("test query")
        assert results is not None
```

## Registration

Providers are auto-discovered by the registry. No manual registration needed!

The registry scans `provider_mcps/` and loads all classes that:
1. Inherit from `MCPProvider`
2. Have a `name` attribute
3. Are in a file named `provider.py`

## Configuration in Wizard

When users run `mcp init`, your provider will appear in the category you specified:

```
? Select providers to enable:

🔧 Custom
  [ ] My Provider - Connect to XYZ service
```

If `requires_oauth = True`, the wizard will automatically run the OAuth flow.

## Best Practices

1. **Use descriptive names**: `display_name` should be clear
2. **Validate configuration**: Use Pydantic models with validation
3. **Handle errors gracefully**: Catch and wrap transport errors
4. **Add docstrings**: Document what the provider does
5. **Test thoroughly**: Test connection, tools, and resources
6. **Follow conventions**: Use standard MCP patterns

## Example: Complete Provider

See the Atlassian provider for a complete example:
- `provider_mcps/enterprise/atlassian/provider.py`
- `provider_mcps/enterprise/atlassian/config.py`

## Need Help?

- Check existing providers in `provider_mcps/`
- Read the [Architecture Overview](../architecture/overview.md)
- Open a [GitHub Discussion](https://github.com/yourusername/startmcp/discussions)
