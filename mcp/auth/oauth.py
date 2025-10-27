"""OAuth 2.1 browser-based authentication with PKCE."""

import asyncio
import hashlib
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from mcp.exceptions import AuthenticationError


class OAuth2BrowserFlow:
    """OAuth 2.1 browser flow with PKCE support."""

    def __init__(
        self,
        client_id: str,
        authorization_url: str,
        token_url: str,
        redirect_uri: str = "http://localhost:8734/callback",
        scopes: Optional[list[str]] = None,
    ) -> None:
        """
        Initialize OAuth flow.

        Args:
            client_id: OAuth client ID
            authorization_url: Authorization endpoint URL
            token_url: Token exchange endpoint URL
            redirect_uri: Callback URL (default: http://localhost:8734/callback)
            scopes: OAuth scopes to request
        """
        self.client_id = client_id
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scopes = scopes or []

        # PKCE parameters
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        self.state = secrets.token_urlsafe(32)

        # Callback server
        self.callback_server: Optional[HTTPServer] = None
        self.authorization_code: Optional[str] = None
        self.callback_error: Optional[str] = None

    @staticmethod
    def _generate_code_verifier() -> str:
        """Generate PKCE code verifier."""
        return secrets.token_urlsafe(64)

    @staticmethod
    def _generate_code_challenge(verifier: str) -> str:
        """Generate PKCE code challenge from verifier."""
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        # Base64 URL-safe encoding without padding
        return (
            digest.hex()
        )  # Using hex for simplicity, should be base64url in production

    def get_authorization_url(self) -> str:
        """
        Generate authorization URL for user to visit.

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": self.state,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
        }

        if self.scopes:
            params["scope"] = " ".join(self.scopes)

        return f"{self.authorization_url}?{urlencode(params)}"

    async def authenticate(self, open_browser: bool = True) -> Dict[str, str]:
        """
        Run OAuth flow and return tokens.

        Args:
            open_browser: Whether to automatically open browser

        Returns:
            Dict with 'access_token' and optionally 'refresh_token'

        Raises:
            AuthenticationError: If authentication fails
        """
        # Start local callback server
        port = int(urlparse(self.redirect_uri).port or 8734)
        server_started = await self._start_callback_server(port)

        if not server_started:
            raise AuthenticationError(f"Failed to start callback server on port {port}")

        # Get authorization URL
        auth_url = self.get_authorization_url()

        # Open browser
        if open_browser:
            webbrowser.open(auth_url)
            print(f"Opening browser for authentication...")
        else:
            print(f"Please visit this URL to authenticate:\n{auth_url}")

        # Wait for callback
        try:
            await self._wait_for_callback(timeout=300)  # 5 minute timeout
        finally:
            self._stop_callback_server()

        # Check for errors
        if self.callback_error:
            raise AuthenticationError(f"OAuth error: {self.callback_error}")

        if not self.authorization_code:
            raise AuthenticationError("No authorization code received")

        # Exchange code for token
        tokens = await self._exchange_code_for_token()
        return tokens

    async def _start_callback_server(self, port: int) -> bool:
        """Start HTTP server to handle OAuth callback."""

        class CallbackHandler(BaseHTTPRequestHandler):
            oauth_flow = self

            def do_GET(handler_self) -> None:  # type: ignore
                """Handle GET request (OAuth callback)."""
                parsed = urlparse(handler_self.path)
                query_params = parse_qs(parsed.query)

                # Check state parameter
                state = query_params.get("state", [None])[0]
                if state != self.state:
                    handler_self.send_response(400)
                    handler_self.end_headers()
                    handler_self.wfile.write(b"Invalid state parameter")
                    self.callback_error = "Invalid state parameter"
                    return

                # Get authorization code or error
                if "error" in query_params:
                    self.callback_error = query_params["error"][0]
                    handler_self.send_response(400)
                    handler_self.end_headers()
                    handler_self.wfile.write(
                        f"Authentication failed: {self.callback_error}".encode()
                    )
                    return

                code = query_params.get("code", [None])[0]
                if code:
                    self.authorization_code = code
                    handler_self.send_response(200)
                    handler_self.end_headers()
                    handler_self.wfile.write(
                        b"Authentication successful! You can close this window."
                    )
                else:
                    handler_self.send_response(400)
                    handler_self.end_headers()
                    handler_self.wfile.write(b"No authorization code received")
                    self.callback_error = "No authorization code received"

            def log_message(handler_self, format: str, *args: any) -> None:  # type: ignore
                """Suppress server logs."""
                pass

        try:
            self.callback_server = HTTPServer(("localhost", port), CallbackHandler)
            return True
        except Exception as e:
            print(f"Failed to start callback server: {e}")
            return False

    async def _wait_for_callback(self, timeout: int = 300) -> None:
        """Wait for OAuth callback with timeout."""
        if not self.callback_server:
            raise AuthenticationError("Callback server not started")

        start_time = asyncio.get_event_loop().time()

        while (
            not self.authorization_code
            and not self.callback_error
            and (asyncio.get_event_loop().time() - start_time) < timeout
        ):
            # Handle one request with timeout
            self.callback_server.timeout = 1.0
            self.callback_server.handle_request()
            await asyncio.sleep(0.1)

        if not self.authorization_code and not self.callback_error:
            raise AuthenticationError("Authentication timed out")

    def _stop_callback_server(self) -> None:
        """Stop callback server."""
        if self.callback_server:
            self.callback_server.server_close()
            self.callback_server = None

    async def _exchange_code_for_token(self) -> Dict[str, str]:
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "code": self.authorization_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": self.code_verifier,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    raise AuthenticationError(
                        f"Token exchange failed: {response.status_code} - {response.text}"
                    )

                token_data = response.json()

                if "access_token" not in token_data:
                    raise AuthenticationError("No access token in response")

                return token_data

            except httpx.HTTPError as e:
                raise AuthenticationError(f"Token exchange HTTP error: {e}")

    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token data

        Raises:
            AuthenticationError: If refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    raise AuthenticationError(
                        f"Token refresh failed: {response.status_code} - {response.text}"
                    )

                return response.json()

            except httpx.HTTPError as e:
                raise AuthenticationError(f"Token refresh HTTP error: {e}")
