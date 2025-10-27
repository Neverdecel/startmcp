"""Configuration for Atlassian provider."""

from typing import Optional

from pydantic import BaseModel, Field


class AtlassianConfig(BaseModel):
    """Configuration for Atlassian provider."""

    # mcp-remote proxy settings
    endpoint: str = Field(
        default="https://mcp.atlassian.com/v1/sse",
        description="Atlassian MCP remote endpoint",
    )
    use_npx: bool = Field(
        default=True,
        description="Use npx to run mcp-remote (recommended)",
    )
    mcp_remote_version: Optional[str] = Field(
        default=None,
        description="Specific mcp-remote version (e.g., '0.1.13'), uses latest if None",
    )

    # Atlassian-specific settings
    default_project: Optional[str] = Field(
        default=None, description="Default Jira project key"
    )
    cloud_id: Optional[str] = Field(default=None, description="Atlassian cloud ID")

    # Connection settings
    timeout: int = Field(default=30, description="Request timeout in seconds")

    # Authentication is handled automatically by mcp-remote via browser OAuth
    # No manual credentials needed!
