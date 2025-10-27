"""Atlassian MCP provider implementation using mcp-remote proxy."""

import shutil
from typing import Dict, List, Optional

from mcp.categories import ProviderCategory
from mcp.exceptions import ConfigurationError
from mcp.provider import MCPProvider
from mcp.transport.base import Transport
from mcp.transport.stdio import StdioTransport

from .config import AtlassianConfig


class AtlassianProvider(MCPProvider):
    """Atlassian Suite MCP provider (Jira, Confluence, Compass) via mcp-remote."""

    name = "atlassian"
    display_name = "Atlassian Suite"
    category = ProviderCategory.ENTERPRISE
    icon = "🏢"
    description = "Connect to Jira, Confluence, and Compass"
    transport_type = "stdio"  # Uses stdio via mcp-remote proxy
    requires_oauth = True  # But handled automatically by mcp-remote
    config_class = AtlassianConfig

    def __init__(self, config: Optional[Dict] = None) -> None:
        """
        Initialize Atlassian provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.config: AtlassianConfig  # Type hint for better IDE support

    async def create_transport(self) -> Transport:
        """
        Create stdio transport using npx mcp-remote.

        The mcp-remote tool:
        1. Runs as a local proxy
        2. Handles OAuth browser flow automatically
        3. Connects to Atlassian cloud via SSE
        4. Exposes stdio interface locally

        Returns:
            Configured stdio transport

        Raises:
            ConfigurationError: If npx or Node.js not available
        """
        # Check if npx is available
        if self.config.use_npx:
            if not shutil.which("npx"):
                raise ConfigurationError(
                    "npx not found. Please install Node.js v18+ to use Atlassian provider.\n"
                    "Download from: https://nodejs.org/"
                )

        # Build command
        command = self._build_command()

        # Create stdio transport
        transport = StdioTransport(command=command)
        return transport

    def _build_command(self) -> List[str]:
        """
        Build the command to run mcp-remote.

        Returns:
            Command as list of strings
        """
        if self.config.use_npx:
            command = ["npx", "-y"]

            # Add version if specified
            if self.config.mcp_remote_version:
                command.append(f"mcp-remote@{self.config.mcp_remote_version}")
            else:
                command.append("mcp-remote")

            # Add endpoint
            command.append(self.config.endpoint)
        else:
            # Direct mcp-remote command (assumes globally installed)
            command = ["mcp-remote", self.config.endpoint]

        return command

    # Convenience methods for Atlassian-specific operations

    async def search_jira_issues(
        self, jql: str, max_results: int = 50
    ) -> Dict:
        """
        Search Jira issues using JQL.

        Args:
            jql: Jira Query Language string
            max_results: Maximum number of results

        Returns:
            Search results
        """
        return await self.call_tool(
            "jira_search_issues", {"jql": jql, "maxResults": max_results}
        )

    async def get_jira_issue(self, issue_key: str) -> Dict:
        """
        Get details of a specific Jira issue.

        Args:
            issue_key: Issue key (e.g., PROJ-123)

        Returns:
            Issue details
        """
        return await self.call_tool("jira_get_issue", {"issueKey": issue_key})

    async def search_confluence_pages(self, query: str, limit: int = 25) -> Dict:
        """
        Search Confluence pages.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Search results
        """
        return await self.call_tool(
            "confluence_search", {"query": query, "limit": limit}
        )

    async def get_confluence_page(self, page_id: str) -> Dict:
        """
        Get Confluence page content.

        Args:
            page_id: Page ID

        Returns:
            Page content
        """
        return await self.call_tool("confluence_get_page", {"pageId": page_id})
