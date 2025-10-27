"""Core MCP client implementation."""

import uuid
from typing import Any, Dict, List, Optional

from mcp.exceptions import ProtocolError
from mcp.protocol import (
    JSONRPCRequest,
    MCPMethod,
    Prompt,
    PromptResult,
    PromptsGetParams,
    PromptsListResult,
    Resource,
    ResourceContent,
    ResourcesListResult,
    ResourcesReadParams,
    Tool,
    ToolCallResult,
    ToolsCallParams,
    ToolsListResult,
)
from mcp.transport.base import Transport


class MCPClient:
    """MCP protocol client for interacting with MCP servers."""

    def __init__(self, transport: Transport) -> None:
        """
        Initialize MCP client.

        Args:
            transport: Transport layer to use for communication
        """
        self.transport = transport
        self._request_counter = 0

    async def connect(self) -> None:
        """Establish connection to MCP server."""
        await self.transport.connect()

    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        await self.transport.disconnect()

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self._request_counter += 1
        return f"req-{self._request_counter}-{uuid.uuid4().hex[:8]}"

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC request and return result.

        Args:
            method: MCP method name
            params: Method parameters
            timeout: Optional timeout in seconds

        Returns:
            Method result

        Raises:
            ProtocolError: If request fails or returns error
        """
        request = JSONRPCRequest(
            id=self._generate_request_id(), method=method, params=params
        )

        response = await self.transport.send_request(request, timeout=timeout)

        if response.error:
            raise ProtocolError(
                f"MCP error {response.error.code}: {response.error.message}"
            )

        if response.result is None:
            raise ProtocolError(f"No result in response for {method}")

        return response.result

    # Resource Methods

    async def list_resources(self, timeout: Optional[float] = None) -> List[Resource]:
        """
        List available resources from MCP server.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            List of available resources
        """
        result = await self._send_request(MCPMethod.RESOURCES_LIST, timeout=timeout)
        resources_list = ResourcesListResult(**result)
        return resources_list.resources

    async def read_resource(
        self, uri: str, timeout: Optional[float] = None
    ) -> ResourceContent:
        """
        Read resource content from MCP server.

        Args:
            uri: Resource URI
            timeout: Optional timeout in seconds

        Returns:
            Resource content
        """
        params = ResourcesReadParams(uri=uri).model_dump()
        result = await self._send_request(
            MCPMethod.RESOURCES_READ, params=params, timeout=timeout
        )
        return ResourceContent(**result)

    # Tool Methods

    async def list_tools(self, timeout: Optional[float] = None) -> List[Tool]:
        """
        List available tools from MCP server.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            List of available tools
        """
        result = await self._send_request(MCPMethod.TOOLS_LIST, timeout=timeout)
        tools_list = ToolsListResult(**result)
        return tools_list.tools

    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> ToolCallResult:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments
            timeout: Optional timeout in seconds

        Returns:
            Tool execution result
        """
        params = ToolsCallParams(
            name=name, arguments=arguments or {}
        ).model_dump()
        result = await self._send_request(
            MCPMethod.TOOLS_CALL, params=params, timeout=timeout
        )
        return ToolCallResult(**result)

    # Prompt Methods

    async def list_prompts(self, timeout: Optional[float] = None) -> List[Prompt]:
        """
        List available prompts from MCP server.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            List of available prompts
        """
        result = await self._send_request(MCPMethod.PROMPTS_LIST, timeout=timeout)
        prompts_list = PromptsListResult(**result)
        return prompts_list.prompts

    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> PromptResult:
        """
        Get a prompt with parameters filled in.

        Args:
            name: Prompt name
            arguments: Prompt arguments
            timeout: Optional timeout in seconds

        Returns:
            Prompt result with messages
        """
        params = PromptsGetParams(
            name=name, arguments=arguments or {}
        ).model_dump()
        result = await self._send_request(
            MCPMethod.PROMPTS_GET, params=params, timeout=timeout
        )
        return PromptResult(**result)

    # Context manager support

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()
