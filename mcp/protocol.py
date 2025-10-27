"""MCP Protocol models based on JSON-RPC 2.0 and Model Context Protocol specification."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# JSON-RPC 2.0 Base Models


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request."""

    jsonrpc: Literal["2.0"] = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response."""

    jsonrpc: Literal["2.0"] = "2.0"
    id: Union[str, int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[JSONRPCError] = None


class JSONRPCNotification(BaseModel):
    """JSON-RPC 2.0 notification (no response expected)."""

    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None


# MCP Protocol Models


class ResourceType(str, Enum):
    """Types of MCP resources."""

    TEXT = "text"
    BINARY = "binary"
    IMAGE = "image"


class Resource(BaseModel):
    """MCP resource metadata."""

    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    resource_type: ResourceType = ResourceType.TEXT


class ResourceContent(BaseModel):
    """Content of an MCP resource."""

    uri: str
    mime_type: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[bytes] = None


class ToolParameter(BaseModel):
    """Parameter definition for a tool."""

    name: str
    description: str
    type: str = Field(description="JSON Schema type (string, number, boolean, etc.)")
    required: bool = False
    default: Optional[Any] = None


class Tool(BaseModel):
    """MCP tool definition."""

    model_config = {"populate_by_name": True}

    name: str
    description: str
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        alias="inputSchema",
        description="JSON Schema for tool input parameters"
    )

    # Gateway metadata (for aggregated server mode)
    provider: Optional[str] = Field(
        default=None, description="Provider that owns this tool (e.g., 'atlassian')"
    )
    category: Optional[str] = Field(
        default=None, description="Tool category (e.g., 'enterprise', 'dev_tools')"
    )
    namespace_reason: Optional[str] = Field(
        default=None,
        description="Why tool was namespaced: 'conflict' if name collision, None if natural name"
    )


class ToolCallResult(BaseModel):
    """Result of calling a tool."""

    content: List[Dict[str, Any]]
    is_error: bool = False


class PromptParameter(BaseModel):
    """Parameter for a prompt template."""

    name: str
    description: str
    required: bool = False


class Prompt(BaseModel):
    """MCP prompt template."""

    name: str
    description: str
    parameters: List[PromptParameter] = Field(default_factory=list)


class PromptMessage(BaseModel):
    """A message in a prompt."""

    role: Literal["user", "assistant", "system"]
    content: str


class PromptResult(BaseModel):
    """Result of getting a prompt."""

    messages: List[PromptMessage]
    description: Optional[str] = None


# MCP Method Names (as constants)


class MCPMethod:
    """MCP protocol method names."""

    # Initialization
    INITIALIZE = "initialize"

    # Resources
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"

    # Tools
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # Prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

    # Notifications
    NOTIFICATION_PROGRESS = "notifications/progress"
    NOTIFICATION_CANCELLED = "notifications/cancelled"


# Request/Response specific models


class InitializeParams(BaseModel):
    """Parameters for initialize request."""

    protocol_version: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    client_info: Dict[str, str] = Field(default_factory=dict)


class InitializeResult(BaseModel):
    """Result of initialize request."""

    protocol_version: str
    capabilities: Dict[str, Any]
    server_info: Dict[str, str]


class ResourcesListResult(BaseModel):
    """Result of resources/list."""

    resources: List[Resource]


class ResourcesReadParams(BaseModel):
    """Parameters for resources/read."""

    uri: str


class ToolsListResult(BaseModel):
    """Result of tools/list."""

    tools: List[Tool]


class ToolsCallParams(BaseModel):
    """Parameters for tools/call."""

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class PromptsListResult(BaseModel):
    """Result of prompts/list."""

    prompts: List[Prompt]


class PromptsGetParams(BaseModel):
    """Parameters for prompts/get."""

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


# Server capabilities


class ServerCapabilities(BaseModel):
    """Capabilities advertised by an MCP server."""

    resources: bool = False
    tools: bool = False
    prompts: bool = False
    logging: bool = False
