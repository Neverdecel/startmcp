"""Custom exceptions for startmcp."""


class MCPError(Exception):
    """Base exception for all MCP errors."""

    pass


class TransportError(MCPError):
    """Error in transport layer."""

    pass


class ProtocolError(MCPError):
    """Error in MCP protocol handling."""

    pass


class AuthenticationError(MCPError):
    """Error during authentication."""

    pass


class ProviderError(MCPError):
    """Error from a provider."""

    pass


class ConfigurationError(MCPError):
    """Error in configuration."""

    pass


class TimeoutError(MCPError):
    """Operation timed out."""

    pass


class ConnectionError(TransportError):
    """Failed to connect to MCP server."""

    pass
