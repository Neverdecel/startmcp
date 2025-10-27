"""stdio transport for local MCP servers."""

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional

from mcp.exceptions import ConnectionError, TimeoutError, TransportError
from mcp.protocol import JSONRPCRequest, JSONRPCResponse
from mcp.transport.base import Transport


class StdioTransport(Transport):
    """stdio transport for local MCP servers running as subprocesses."""

    def __init__(self, command: List[str], cwd: Optional[str] = None) -> None:
        """
        Initialize stdio transport.

        Args:
            command: Command and arguments to start MCP server
            cwd: Optional working directory for the subprocess
        """
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.process: Optional[asyncio.subprocess.Process] = None
        self._pending_requests: Dict[str, asyncio.Future[JSONRPCResponse]] = {}
        self._listen_task: Optional[asyncio.Task[None]] = None
        self._request_lock = asyncio.Lock()

    async def connect(self, **kwargs: Any) -> None:
        """
        Start subprocess and establish stdio connection.

        Args:
            **kwargs: Additional subprocess parameters

        Raises:
            ConnectionError: If subprocess fails to start
        """
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
                **kwargs,
            )

            self.connected = True

            # Start listening for responses in background
            self._listen_task = asyncio.create_task(self._listen_loop())

        except Exception as e:
            raise ConnectionError(f"Failed to start subprocess {self.command}: {e}")

    async def disconnect(self) -> None:
        """Stop subprocess and close stdio connection."""
        self.connected = False

        # Cancel listen task
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        # Terminate process
        if self.process:
            try:
                # Close stdin first to signal graceful shutdown
                if self.process.stdin:
                    self.process.stdin.close()
                    await self.process.stdin.wait_closed()

                # Try graceful termination
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                # Force kill if termination takes too long
                try:
                    self.process.kill()
                    await asyncio.wait_for(self.process.wait(), timeout=2.0)
                except Exception:
                    pass
            except Exception:
                pass
            finally:
                self.process = None

    async def send_request(
        self, request: JSONRPCRequest, timeout: Optional[float] = None
    ) -> JSONRPCResponse:
        """
        Send JSON-RPC request via stdin and wait for response from stdout.

        Args:
            request: The JSON-RPC request
            timeout: Optional timeout in seconds

        Returns:
            The JSON-RPC response

        Raises:
            TransportError: If send fails
            TimeoutError: If request times out
        """
        if not self.connected or not self.process or not self.process.stdin:
            raise TransportError("Not connected")

        # Create future for this request
        request_id = str(request.id)
        future: asyncio.Future[JSONRPCResponse] = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Serialize and send request
            request_json = request.model_dump(mode="json", exclude_none=True)
            request_line = json.dumps(request_json) + "\n"

            # Write to stdin with lock to prevent interleaving
            async with self._request_lock:
                self.process.stdin.write(request_line.encode("utf-8"))
                await self.process.stdin.drain()

            # Wait for response
            timeout_duration = timeout or 60.0
            try:
                result = await asyncio.wait_for(future, timeout=timeout_duration)
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"Request {request_id} timed out after {timeout_duration}s")

        except Exception as e:
            if isinstance(e, (TimeoutError, TransportError)):
                raise
            raise TransportError(f"Failed to send request: {e}")
        finally:
            # Clean up pending request
            self._pending_requests.pop(request_id, None)

    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Listen for messages from stdout.

        Yields:
            Incoming JSON-RPC messages

        Raises:
            TransportError: If listening fails
        """
        if not self.connected or not self.process or not self.process.stdout:
            raise TransportError("Not connected")

        try:
            while self.connected:
                # Read line from stdout
                line_bytes = await self.process.stdout.readline()

                if not line_bytes:
                    # EOF - process has exited
                    break

                try:
                    line = line_bytes.decode("utf-8").strip()
                    if line:
                        message = json.loads(line)
                        yield message
                except json.JSONDecodeError as e:
                    # Log and skip invalid JSON
                    print(f"Invalid JSON from subprocess: {e} - Line: {line_bytes}")
                    continue
                except UnicodeDecodeError as e:
                    print(f"Invalid UTF-8 from subprocess: {e}")
                    continue

        except Exception as e:
            if self.connected:
                raise TransportError(f"Error reading from subprocess: {e}")

    async def _listen_loop(self) -> None:
        """Background task to listen for responses and match them to pending requests."""
        try:
            async for message in self.listen():
                # Check if this is a response to a pending request
                if "id" in message and ("result" in message or "error" in message):
                    request_id = str(message["id"])
                    future = self._pending_requests.get(request_id)
                    if future and not future.done():
                        try:
                            response = JSONRPCResponse(**message)
                            future.set_result(response)
                        except Exception as e:
                            future.set_exception(TransportError(f"Invalid response: {e}"))
                # Handle notifications (no id field)
                elif "method" in message and "id" not in message:
                    # This is a notification - could be logged or handled
                    pass

        except asyncio.CancelledError:
            # Normal shutdown
            pass
        except Exception as e:
            # Log error but don't crash
            print(f"Error in stdio listen loop: {e}")

    async def get_stderr(self) -> Optional[str]:
        """
        Read stderr from subprocess (for debugging).

        Returns:
            stderr content if available
        """
        if self.process and self.process.stderr:
            try:
                stderr_bytes = await asyncio.wait_for(
                    self.process.stderr.read(), timeout=0.1
                )
                return stderr_bytes.decode("utf-8")
            except asyncio.TimeoutError:
                return None
        return None
