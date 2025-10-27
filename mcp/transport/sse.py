"""SSE (Server-Sent Events) transport for MCP."""

import asyncio
import json
import uuid
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from httpx_sse import aconnect_sse

from mcp.exceptions import ConnectionError, TimeoutError, TransportError
from mcp.protocol import JSONRPCRequest, JSONRPCResponse
from mcp.transport.base import Transport


class SSETransport(Transport):
    """SSE transport for remote MCP servers."""

    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize SSE transport.

        Args:
            endpoint: SSE endpoint URL
            headers: Optional HTTP headers (for authentication, etc.)
        """
        super().__init__()
        self.endpoint = endpoint
        self.headers = headers or {}
        self.client: Optional[httpx.AsyncClient] = None
        self._pending_requests: Dict[str, asyncio.Future[JSONRPCResponse]] = {}
        self._listen_task: Optional[asyncio.Task[None]] = None

    async def connect(self, **kwargs: Any) -> None:
        """
        Establish SSE connection.

        Args:
            **kwargs: Additional connection parameters

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0), headers=self.headers
            )

            # Test connection with a simple request
            response = await self.client.get(self.endpoint.replace("/sse", "/health"))
            if response.status_code >= 400:
                raise ConnectionError(f"Server returned {response.status_code}")

            self.connected = True

            # Start listening for responses in background
            self._listen_task = asyncio.create_task(self._listen_loop())

        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to connect to {self.endpoint}: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error during connection: {e}")

    async def disconnect(self) -> None:
        """Close SSE connection."""
        self.connected = False

        # Cancel listen task
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        # Close client
        if self.client:
            await self.client.aclose()
            self.client = None

    async def send_request(
        self, request: JSONRPCRequest, timeout: Optional[float] = None
    ) -> JSONRPCResponse:
        """
        Send JSON-RPC request via POST and wait for response via SSE.

        Args:
            request: The JSON-RPC request
            timeout: Optional timeout in seconds

        Returns:
            The JSON-RPC response

        Raises:
            TransportError: If send fails
            TimeoutError: If request times out
        """
        if not self.connected or not self.client:
            raise TransportError("Not connected")

        # Create future for this request
        request_id = str(request.id)
        future: asyncio.Future[JSONRPCResponse] = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Send request via POST
            response = await self.client.post(
                self.endpoint.replace("/sse", "/message"),
                json=request.model_dump(mode="json", exclude_none=True),
                headers={"Content-Type": "application/json"},
            )

            if response.status_code >= 400:
                raise TransportError(f"Server returned {response.status_code}: {response.text}")

            # Wait for response from SSE stream
            timeout_duration = timeout or 60.0
            try:
                result = await asyncio.wait_for(future, timeout=timeout_duration)
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"Request {request_id} timed out after {timeout_duration}s")

        except httpx.HTTPError as e:
            raise TransportError(f"HTTP error: {e}")
        finally:
            # Clean up pending request
            self._pending_requests.pop(request_id, None)

    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Listen for server-sent events.

        Yields:
            Incoming JSON-RPC messages

        Raises:
            TransportError: If listening fails
        """
        if not self.connected or not self.client:
            raise TransportError("Not connected")

        try:
            async with aconnect_sse(
                self.client, "GET", self.endpoint, headers=self.headers
            ) as event_source:
                async for event in event_source.aiter_sse():
                    if event.data:
                        try:
                            message = json.loads(event.data)
                            yield message
                        except json.JSONDecodeError as e:
                            # Log and skip invalid JSON
                            print(f"Invalid JSON in SSE event: {e}")
                            continue

        except httpx.HTTPError as e:
            raise TransportError(f"SSE listening error: {e}")

    async def _listen_loop(self) -> None:
        """Background task to listen for responses and match them to pending requests."""
        try:
            async for message in self.listen():
                # Check if this is a response to a pending request
                if "id" in message and "result" in message or "error" in message:
                    request_id = str(message["id"])
                    future = self._pending_requests.get(request_id)
                    if future and not future.done():
                        try:
                            response = JSONRPCResponse(**message)
                            future.set_result(response)
                        except Exception as e:
                            future.set_exception(TransportError(f"Invalid response: {e}"))
        except asyncio.CancelledError:
            # Normal shutdown
            pass
        except Exception as e:
            # Log error but don't crash
            print(f"Error in SSE listen loop: {e}")
