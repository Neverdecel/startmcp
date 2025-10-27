"""API key authentication."""

from typing import Dict, Optional


class APIKeyAuth:
    """Simple API key authentication."""

    def __init__(
        self, api_key: str, header_name: str = "Authorization", prefix: str = "Bearer"
    ) -> None:
        """
        Initialize API key authentication.

        Args:
            api_key: The API key
            header_name: HTTP header name (default: Authorization)
            prefix: Prefix for the header value (default: Bearer)
        """
        self.api_key = api_key
        self.header_name = header_name
        self.prefix = prefix

    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for authentication.

        Returns:
            Dict of headers
        """
        if self.prefix:
            value = f"{self.prefix} {self.api_key}"
        else:
            value = self.api_key

        return {self.header_name: value}


class TokenStore:
    """Simple token storage (in-memory)."""

    def __init__(self) -> None:
        """Initialize token store."""
        self._tokens: Dict[str, Dict[str, str]] = {}

    def store(self, provider: str, tokens: Dict[str, str]) -> None:
        """
        Store tokens for a provider.

        Args:
            provider: Provider name
            tokens: Token data
        """
        self._tokens[provider] = tokens

    def get(self, provider: str) -> Optional[Dict[str, str]]:
        """
        Get tokens for a provider.

        Args:
            provider: Provider name

        Returns:
            Token data or None
        """
        return self._tokens.get(provider)

    def remove(self, provider: str) -> None:
        """
        Remove tokens for a provider.

        Args:
            provider: Provider name
        """
        self._tokens.pop(provider, None)

    def clear(self) -> None:
        """Clear all stored tokens."""
        self._tokens.clear()


# Global token store instance
_global_token_store = TokenStore()


def get_token_store() -> TokenStore:
    """Get the global token store."""
    return _global_token_store
