#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Minimal MCP (JSON-RPC 2.0) transport for the UCP shopping service.

The discovery profile advertises an ``mcp`` transport at ``<endpoint>/mcp``, but
the server otherwise only implements REST, so spec-conformant MCP clients fail
discovery with an HTTP 404 on that endpoint.

This module adds the minimum needed for capability discovery to succeed over
MCP: it answers ``initialize`` and ``tools/list`` (advertising the shopping
methods from the UCP shopping OpenRPC). Executing tools (``tools/call``) by
bridging to the REST checkout handlers is intentionally left as a follow-up.
"""

from typing import Any

import config
import dependencies
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.responses import JSONResponse

router = APIRouter()

# MCP protocol revision this endpoint speaks.
MCP_PROTOCOL_VERSION = "2025-06-18"

_OBJECT = {"type": "object"}
_STRING = {"type": "string"}

# Shopping methods exposed over MCP, mirroring the UCP shopping OpenRPC
# (https://ucp.dev/2026-04-08/services/shopping/openrpc.json).
_TOOLS: list[dict[str, Any]] = [
  {
    "name": "create_checkout",
    "description": "Create a checkout.",
    "inputSchema": {
      "type": "object",
      "properties": {"meta": _OBJECT, "checkout": _OBJECT},
      "required": ["meta", "checkout"],
    },
  },
  {
    "name": "get_checkout",
    "description": "Get a checkout by id.",
    "inputSchema": {
      "type": "object",
      "properties": {"meta": _OBJECT, "id": _STRING},
      "required": ["meta", "id"],
    },
  },
  {
    "name": "update_checkout",
    "description": "Update a checkout.",
    "inputSchema": {
      "type": "object",
      "properties": {"meta": _OBJECT, "id": _STRING, "checkout": _OBJECT},
      "required": ["meta", "id", "checkout"],
    },
  },
  {
    "name": "complete_checkout",
    "description": "Complete a checkout and place the order.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "meta": _OBJECT,
        "id": _STRING,
        "checkout": _OBJECT,
        "idempotency_key": _STRING,
      },
      "required": ["meta", "id", "checkout", "idempotency_key"],
    },
  },
  {
    "name": "cancel_checkout",
    "description": "Cancel a checkout.",
    "inputSchema": {
      "type": "object",
      "properties": {"meta": _OBJECT, "id": _STRING},
      "required": ["meta", "id"],
    },
  },
]


def _result(request_id: Any, result: Any) -> JSONResponse:
  return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def _error(request_id: Any, code: int, message: str) -> JSONResponse:
  return JSONResponse(
    {
      "jsonrpc": "2.0",
      "id": request_id,
      "error": {"code": code, "message": message},
    }
  )


@router.post("/mcp", dependencies=[Depends(dependencies.verify_signature)])
async def mcp_endpoint(request: Request) -> Response:
  """Minimal MCP (JSON-RPC 2.0) endpoint for capability discovery.

  Answers ``initialize`` and ``tools/list`` so MCP clients can complete
  discovery. ``tools/call`` is not yet bridged to the REST checkout handlers.

  Signature verification applies the same policy as every other inbound
  route (verify-if-present by default, required under
  ``--require_signatures``) so that bridging ``tools/call`` later cannot
  silently open an unsigned transport into the checkout handlers.
  """
  try:
    payload = await request.json()
  except Exception:
    return _error(None, -32700, "Parse error")

  method = payload.get("method")
  request_id = payload.get("id")

  # JSON-RPC notifications (no id), e.g. notifications/initialized.
  if (
    request_id is None
    and isinstance(method, str)
    and method.startswith("notifications/")
  ):
    return Response(status_code=202)

  if method == "initialize":
    return _result(
      request_id,
      {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {
          "name": "ucp-shopping-sample",
          "version": config.get_server_version(),
        },
      },
    )

  if method == "tools/list":
    return _result(request_id, {"tools": _TOOLS})

  if method == "tools/call":
    return _error(
      request_id,
      -32000,
      "tools/call is not yet implemented on this sample's MCP endpoint; use the"
      " REST transport for checkout operations.",
    )

  return _error(request_id, -32601, f"Method not found: {method}")
