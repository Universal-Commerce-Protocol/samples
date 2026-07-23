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

"""FastAPI dependencies for the UCP server.

This module contains dependency injection logic for FastAPI endpoints,
including:
- Header validation (UCP-Agent, Idempotency-Key, Request-Signature).
- Service instantiation (CheckoutService, FulfillmentService).
- Database session management (Products and Transactions DBs).
- Request signature verification for webhooks.
"""

import re
from collections.abc import AsyncGenerator
from typing import Annotated

import config
import db
from exceptions import UcpErrorDetail
from exceptions import UcpErrorDetailItem
from exceptions import UcpVersionError
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from pydantic import BaseModel
from services.checkout_service import CheckoutService
from services.fulfillment_service import FulfillmentService
from sqlalchemy.ext.asyncio import AsyncSession
from ucp_version import parse_ucp_version


class CommonHeaders(BaseModel):
  """Common headers used in UCP requests."""

  x_api_key: str | None = None
  ucp_agent: str
  request_signature: str
  request_id: str


async def common_headers(
  x_api_key: str | None = Header(None),
  ucp_agent: str = Header(...),
  request_signature: str = Header(...),
  request_id: str = Header(...),
) -> CommonHeaders:
  """Extract and validate common headers."""
  await validate_ucp_headers(ucp_agent)
  return CommonHeaders(
    x_api_key=x_api_key,
    ucp_agent=ucp_agent,
    request_signature=request_signature,
    request_id=request_id,
  )


async def validate_ucp_headers(ucp_agent: str):
  """Validate UCP headers and version negotiation."""
  server_version = config.get_server_version()
  try:
    server_date = parse_ucp_version(server_version)
  except UcpVersionError as exc:
    raise HTTPException(status_code=500, detail=exc.to_detail().model_dump()) from exc

  # Default to server version if UCP-Agent omits version=.
  agent_version = server_version
  agent_date = server_date

  # Use regex to extract version more robustly.
  # We look for 'version=' either at the start or after a semicolon,
  # allowing for whitespace.
  # Matches: version="2026-01-23" or version=2026-01-23
  match = re.search(
    r"(?:^|;)\s*version=(?:\"([^\"]+)\"|([^;]+))", ucp_agent, re.IGNORECASE
  )
  if match:
    # Group 1 is quoted value, Group 2 is unquoted value
    agent_version = (match.group(1) or match.group(2)).strip()
    try:
      agent_date = parse_ucp_version(agent_version)
    except UcpVersionError as exc:
      raise HTTPException(status_code=400, detail=exc.to_detail().model_dump()) from exc

  if agent_date > server_date:
    raise HTTPException(
      status_code=400,
      detail=UcpErrorDetail(
        errors=[
          UcpErrorDetailItem(
            code="VERSION_UNSUPPORTED",
            message=(
              f"Version {agent_version} is not supported. This merchant"
              f" implements version {server_version}."
            ),
            severity="critical",
          )
        ]
      ).model_dump(),
    )


async def idempotency_header(
  idempotency_key: str = Header(...),
) -> str:
  """Extract the Idempotency-Key header."""
  return idempotency_key


async def verify_signature(
  request_signature: str = Header(..., alias="Request-Signature"),
) -> None:
  """Verify the request signature.

  Note: This is a placeholder implementation that bypasses validation if the
  signature is "test". A real implementation would verify the HMAC-SHA256
  signature of the request body.

  Args:
    request_signature: The signature header from the platform.

  """
  # In tests, we might want to bypass validation if signature is "test"
  if request_signature == "test":
    return
  # In sample implementation, we don't enforce signature validation
  # as we don't share secrets with clients.
  return


async def verify_simulation_secret(
  simulation_secret: str | None = Header(None, alias="Simulation-Secret"),
) -> None:
  """Verify the secret for simulation endpoints."""
  expected_secret = config.FLAGS.simulation_secret
  if not expected_secret:
    raise HTTPException(
      status_code=500, detail="Simulation secret not configured"
    )

  if not simulation_secret or simulation_secret != expected_secret:
    raise HTTPException(status_code=403, detail="Invalid Simulation Secret")


def get_fulfillment_service() -> FulfillmentService:
  """Dependency provider for FulfillmentService."""
  return FulfillmentService()


async def get_products_db() -> AsyncGenerator[AsyncSession, None]:
  """Dependency provider for Products DB session."""
  async with db.manager.products_session_factory() as session:
    yield session


async def get_transactions_db() -> AsyncGenerator[AsyncSession, None]:
  """Dependency provider for Transactions DB session."""
  async with db.manager.transactions_session_factory() as session:
    yield session


def get_checkout_service(
  request: Request,
  fulfillment_service: Annotated[
    FulfillmentService, Depends(get_fulfillment_service)
  ],
  products_session: Annotated[AsyncSession, Depends(get_products_db)],
  transactions_session: Annotated[AsyncSession, Depends(get_transactions_db)],
) -> CheckoutService:
  """Dependency provider for CheckoutService."""
  return CheckoutService(
    fulfillment_service,
    products_session,
    transactions_session,
    str(request.base_url),
  )
