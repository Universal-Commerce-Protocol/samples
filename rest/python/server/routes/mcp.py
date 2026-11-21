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

"""MCP (JSON-RPC 2.0) transport for the UCP shopping service.

Serves the checkout tools on the handlers the REST routes use. A
``tools/call`` request names the tool and passes its input as ``arguments``::

    {
      "name": "update_checkout",
      "arguments": {"meta": {...}, "id": "...", "checkout": {...}},
    }

``meta`` carries what REST puts in headers: ``ucp-agent`` (required) and
``idempotency-key`` (required for ``complete_checkout`` and
``cancel_checkout``).

A checkout, or a business outcome such as an out of stock item, is returned
as a JSON-RPC ``result`` with the UCP envelope in ``structuredContent``. A
JSON-RPC ``error`` is used for a call the server cannot interpret (-32602), a
reused idempotency key (-32000), an unsupported version (-32001) and a server
error (-32603).

A request that fails signature verification is rejected before it gets here,
with the same HTTP status and UCP envelope as on the REST routes.
"""

from collections.abc import Awaitable, Callable
import json
import logging
import re
from typing import Annotated, Any
import uuid

import config
import dependencies
from enums import MessageType
from exceptions import IdempotencyConflictError
from exceptions import UcpError
from exceptions import UcpErrorResponse
from exceptions import UcpMessageError
from exceptions import UcpVersionError
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import models
from pydantic import BaseModel
from pydantic import ValidationError
from routes import ucp_implementation
from services.checkout_service import CheckoutService
from ucp_sdk.models.schemas.shopping.checkout_complete_request import (
  CheckoutCompleteRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# MCP protocol revision this endpoint speaks.
MCP_PROTOCOL_VERSION = "2025-06-18"

# JSON-RPC error codes, as assigned by the UCP error registry.
_INVALID_REQUEST = -32600
_INVALID_PARAMS = -32602
_INTERNAL_ERROR = -32603
_PROTOCOL_ERROR = -32000
_DISCOVERY_ERROR = -32001

_PROFILE_RE = re.compile(r'profile="([^"]+)"')

_OBJECT = {"type": "object"}
_STRING = {"type": "string"}
_META = {
  "type": "object",
  "required": ["ucp-agent"],
  "properties": {
    "ucp-agent": {
      "type": "object",
      "required": ["profile"],
      "properties": {"profile": {"type": "string", "format": "uri"}},
    },
    "idempotency-key": _STRING,
  },
}


def _tool(
  name: str, description: str, *, with_id: bool, with_checkout: bool
) -> dict[str, Any]:
  """Describe one checkout tool for ``tools/list``."""
  properties: dict[str, Any] = {"meta": _META}
  if with_id:
    properties["id"] = _STRING
  if with_checkout:
    properties["checkout"] = _OBJECT
  return {
    "name": name,
    "description": description,
    "inputSchema": {
      "type": "object",
      "properties": properties,
      "required": list(properties),
    },
  }


# Mirrors the checkout methods of the UCP shopping OpenRPC
# (https://ucp.dev/2026-04-08/services/shopping/mcp.openrpc.json).
_TOOLS: list[dict[str, Any]] = [
  _tool(
    "create_checkout", "Create a checkout.", with_id=False, with_checkout=True
  ),
  _tool(
    "get_checkout", "Get a checkout by id.", with_id=True, with_checkout=False
  ),
  _tool(
    "update_checkout", "Update a checkout.", with_id=True, with_checkout=True
  ),
  _tool(
    "complete_checkout",
    "Complete a checkout and place the order.",
    with_id=True,
    with_checkout=True,
  ),
  _tool(
    "cancel_checkout", "Cancel a checkout.", with_id=True, with_checkout=False
  ),
]


class _RpcError(Exception):
  """A request that ends in a JSON-RPC ``error`` instead of a result."""

  def __init__(
    self,
    code: int,
    message: str,
    *,
    data: dict[str, Any] | None = None,
    status_code: int = 200,
  ):
    super().__init__(message)
    self.code = code
    self.message = message
    self.data = data
    self.status_code = status_code


def _result(request_id: Any, result: Any) -> JSONResponse:
  return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def _error(
  request_id: Any,
  code: int,
  message: str,
  *,
  data: dict[str, Any] | None = None,
  status_code: int = 200,
) -> JSONResponse:
  error: dict[str, Any] = {"code": code, "message": message}
  if data is not None:
    error["data"] = data
  return JSONResponse(
    {"jsonrpc": "2.0", "id": request_id, "error": error},
    status_code=status_code,
  )


def _invalid_params(content: str) -> _RpcError:
  return _RpcError(
    _INVALID_PARAMS,
    "Invalid params",
    data={"code": "INVALID_REQUEST", "content": content},
  )


def _parse(model: type[BaseModel], data: dict[str, Any]) -> Any:
  """Validate tool input against its request model."""
  try:
    return model(**data)
  except ValidationError as exc:
    lines = [
      f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
      for err in exc.errors()
    ]
    raise _invalid_params("\n".join(lines)) from exc


def _tool_result(payload: dict[str, Any]) -> dict[str, Any]:
  """Wrap a UCP payload as an MCP tool result."""
  return {
    "structuredContent": payload,
    "content": [{"type": "text", "text": json.dumps(payload)}],
  }


def _protocol_error(exc: UcpError) -> _RpcError | None:
  """Map a UcpError to a JSON-RPC error, or None for a business outcome.

  Decided by what failed, not by HTTP status: a payment declined for fraud is
  a 403 on REST and still a business outcome.
  """
  data = {"code": exc.code, "content": exc.message}
  if isinstance(exc, UcpVersionError):
    return _RpcError(
      _DISCOVERY_ERROR,
      "Protocol version not supported",
      data=data,
      status_code=exc.status_code,
    )
  if isinstance(exc, IdempotencyConflictError):
    return _RpcError(
      _PROTOCOL_ERROR, exc.message, data=data, status_code=exc.status_code
    )
  if exc.status_code >= 500:
    return _RpcError(
      _INTERNAL_ERROR, "Internal error", data=data, status_code=exc.status_code
    )
  return None


def _business_outcome(exc: UcpError) -> dict[str, Any]:
  """Render a UcpError as the envelope REST answers with for the same error."""
  envelope = UcpErrorResponse(
    ucp={"version": config.get_server_version(), "status": "error"},
    messages=[
      UcpMessageError(
        type=MessageType.ERROR,
        code=exc.code,
        content=exc.message,
        severity=exc.severity,
      )
    ],
  )
  return envelope.model_dump(mode="json")


class _Call:
  """The parsed arguments of one ``tools/call`` request."""

  def __init__(self, name: str, arguments: Any, request: Request):
    if not isinstance(arguments, dict):
      raise _invalid_params("arguments must be an object.")
    self.name = name
    self._arguments = arguments

    meta = arguments.get("meta")
    agent = meta.get("ucp-agent") if isinstance(meta, dict) else None
    profile = agent.get("profile") if isinstance(agent, dict) else None
    if not isinstance(profile, str) or not profile or '"' in profile:
      raise _RpcError(
        _DISCOVERY_ERROR,
        "UCP discovery failed",
        data={
          "code": "invalid_profile_url",
          "content": 'meta["ucp-agent"].profile is required.',
        },
        status_code=400,
      )
    self._meta = meta

    header = request.headers.get("ucp-agent", "")
    signer = _PROFILE_RE.search(header)
    if (
      "signature-input" in request.headers
      and signer
      and signer.group(1) != profile
    ):
      # The signature was checked against the header's profile, so the call
      # may not act for a different one.
      raise _RpcError(
        _PROTOCOL_ERROR,
        "UCP-Agent mismatch",
        data={
          "code": "signature_invalid",
          "content": (
            'meta["ucp-agent"].profile does not match the signed UCP-Agent'
            " header."
          ),
        },
        status_code=401,
      )
    # The handlers read the platform from the UCP-Agent header. Pass the
    # header itself when it names the same profile, so a version= on it is
    # negotiated as on REST.
    same = signer is not None and signer.group(1) == profile
    self.headers = dependencies.CommonHeaders(
      ucp_agent=header if same else f'profile="{profile}"',
      request_id=str(uuid.uuid4()),
    )

  @property
  def checkout_id(self) -> str:
    """The top-level ``id`` naming the checkout to act on."""
    checkout_id = self._arguments.get("id")
    if not isinstance(checkout_id, str) or not checkout_id:
      raise _invalid_params(f"id is required for {self.name}.")
    return checkout_id

  def checkout(self, *, allow_id: bool) -> dict[str, Any]:
    """Return the ``checkout`` payload."""
    checkout = self._arguments.get("checkout")
    if not isinstance(checkout, dict):
      raise _invalid_params(f"checkout is required for {self.name}.")
    if not allow_id and "id" in checkout:
      # The binding identifies the checkout by the top-level id only.
      raise _invalid_params(
        "checkout must not contain id; pass it as the top-level id."
      )
    return checkout

  def idempotency_key(self, *, required: bool) -> str:
    """Return the idempotency key, or a fresh one where none is required."""
    key = self._meta.get("idempotency-key")
    if key is None and not required:
      return str(uuid.uuid4())
    if not isinstance(key, str) or not key:
      raise _invalid_params(
        f'meta["idempotency-key"] must be a non-empty string for {self.name}.'
      )
    return key


async def _create_checkout(call: _Call, service: CheckoutService) -> Any:
  request = _parse(
    models.UnifiedCheckoutCreateRequest, call.checkout(allow_id=True)
  )
  return await ucp_implementation.create_checkout(
    request, call.headers, call.idempotency_key(required=False), service
  )


async def _get_checkout(call: _Call, service: CheckoutService) -> Any:
  return await ucp_implementation.get_checkout(
    call.checkout_id, call.headers, service
  )


async def _update_checkout(call: _Call, service: CheckoutService) -> Any:
  checkout_id = call.checkout_id
  request = _parse(
    models.UnifiedCheckoutUpdateRequest, call.checkout(allow_id=False)
  )
  return await ucp_implementation.update_checkout(
    checkout_id,
    request,
    call.headers,
    call.idempotency_key(required=False),
    service,
  )


async def _complete_checkout(call: _Call, service: CheckoutService) -> Any:
  checkout_id = call.checkout_id
  request = _parse(CheckoutCompleteRequest, call.checkout(allow_id=False))
  return await ucp_implementation.complete_checkout(
    checkout_id,
    request,
    call.headers,
    call.idempotency_key(required=True),
    service,
  )


async def _cancel_checkout(call: _Call, service: CheckoutService) -> Any:
  return await ucp_implementation.cancel_checkout(
    call.checkout_id,
    call.headers,
    call.idempotency_key(required=True),
    service,
  )


_HANDLERS: dict[str, Callable[[_Call, CheckoutService], Awaitable[Any]]] = {
  "create_checkout": _create_checkout,
  "get_checkout": _get_checkout,
  "update_checkout": _update_checkout,
  "complete_checkout": _complete_checkout,
  "cancel_checkout": _cancel_checkout,
}


async def _call_tool(
  params: Any, service: CheckoutService, request: Request
) -> dict[str, Any]:
  """Run one tool and return its MCP result."""
  if not isinstance(params, dict):
    raise _invalid_params("params must be an object.")
  name = params.get("name")
  handler = _HANDLERS.get(name) if isinstance(name, str) else None
  if handler is None:
    raise _invalid_params(f"Unknown tool: {name}")

  call = _Call(name, params.get("arguments"), request)
  try:
    await dependencies.validate_ucp_headers(call.headers.ucp_agent)
    checkout = await handler(call, service)
  except UcpError as exc:
    rpc_error = _protocol_error(exc)
    if rpc_error is not None:
      raise rpc_error from exc
    return _tool_result(_business_outcome(exc))
  return _tool_result(
    jsonable_encoder(checkout, by_alias=True, exclude_none=True)
  )


@router.post("/mcp", dependencies=[Depends(dependencies.verify_signature)])
async def mcp_endpoint(
  request: Request,
  checkout_service: Annotated[
    CheckoutService, Depends(dependencies.get_checkout_service)
  ],
) -> Response:
  """Answer ``initialize``, ``tools/list`` and ``tools/call``.

  Signature verification applies the same policy as every other inbound
  route (verify-if-present by default, required under
  ``--require_signatures``).
  """
  try:
    payload = await request.json()
  except Exception:
    return _error(None, -32700, "Parse error")
  if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
    return _error(None, _INVALID_REQUEST, "Invalid Request")

  # A request without an id is a notification: nothing to run or answer.
  if "id" not in payload:
    return Response(status_code=202)
  request_id = payload["id"]
  if isinstance(request_id, bool) or not isinstance(
    request_id, (str, int, float, type(None))
  ):
    return _error(None, _INVALID_REQUEST, "Invalid Request")

  method = payload.get("method")

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
    try:
      return _result(
        request_id,
        await _call_tool(payload.get("params"), checkout_service, request),
      )
    except _RpcError as exc:
      return _error(
        request_id,
        exc.code,
        exc.message,
        data=exc.data,
        status_code=exc.status_code,
      )
    except Exception:
      logger.exception("Unhandled error in MCP tool call")
      return _error(
        request_id, _INTERNAL_ERROR, "Internal error", status_code=500
      )

  return _error(request_id, -32601, f"Method not found: {method}")
