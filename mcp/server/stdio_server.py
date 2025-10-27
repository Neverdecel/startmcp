"""stdio-based MCP server for local connections."""

import asyncio
import json
import sys
from typing import Any, Callable, Dict, Optional

from mcp.exceptions import ProtocolError
from mcp.protocol import JSONRPCError, JSONRPCRequest, JSONRPCResponse
from mcp.server.base import MCPServer


class StdioMCPServer(MCPServer):
    """MCP server that communicates via stdin/stdout."""

    def __init__(self) -> None:
        """Initialize stdio MCP server."""
        super().__init__()
        self._read_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the stdio server (begin reading from stdin)."""
        self.running = True
        self._read_task = asyncio.create_task(self._read_loop())

        # Log to stderr (stdout is for JSON-RPC)
        sys.stderr.write("MCP server started on stdio\n")
        sys.stderr.flush()

    async def stop(self) -> None:
        """Stop the stdio server."""
        self.running = False

        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        sys.stderr.write("MCP server stopped\n")
        sys.stderr.flush()

    async def _read_loop(self) -> None:
        """Read loop for stdin."""
        try:
            while self.running:
                # Read line from stdin
                try:
                    # Use asyncio to read from stdin
                    loop = asyncio.get_event_loop()
                    line = await loop.run_in_executor(None, sys.stdin.readline)

                    if not line:
                        # EOF - client disconnected
                        break

                    line = line.strip()
                    if not line:
                        continue

                    # Parse JSON-RPC request
                    try:
                        request_data = json.loads(line)
                        request = JSONRPCRequest(**request_data)

                        # Handle request
                        response = await self.handle_request(request)

                        # Send response
                        await self._send_response(response)

                    except json.JSONDecodeError as e:
                        # Invalid JSON - send error
                        error_response = JSONRPCResponse(
                            id="unknown",
                            error=JSONRPCError(
                                code=-32700,
                                message=f"Parse error: {e}",
                            ),
                        )
                        await self._send_response(error_response)

                    except Exception as e:
                        # Request handling error
                        error_response = JSONRPCResponse(
                            id=request.id if "request" in locals() else "unknown",
                            error=JSONRPCError(
                                code=-32603,
                                message=f"Internal error: {e}",
                            ),
                        )
                        await self._send_response(error_response)

                except Exception as e:
                    sys.stderr.write(f"Error in read loop: {e}\n")
                    sys.stderr.flush()
                    break

        except asyncio.CancelledError:
            # Normal shutdown
            pass

    async def _send_response(self, response: JSONRPCResponse) -> None:
        """
        Send JSON-RPC response to stdout.

        Args:
            response: JSON-RPC response to send
        """
        response_json = response.model_dump(mode="json", exclude_none=True)
        response_line = json.dumps(response_json) + "\n"

        # Write to stdout
        sys.stdout.write(response_line)
        sys.stdout.flush()

    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """
        Handle incoming JSON-RPC request.

        Args:
            request: JSON-RPC request

        Returns:
            JSON-RPC response
        """
        method = request.method

        # Check if handler exists
        if method not in self.handlers:
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=-32601,
                    message=f"Method not found: {method}",
                ),
            )

        # Call handler
        try:
            handler = self.handlers[method]
            result = await handler(request.params or {})

            return JSONRPCResponse(
                id=request.id,
                result=result,
            )

        except Exception as e:
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=-32000,
                    message=str(e),
                    data={"type": type(e).__name__},
                ),
            )
