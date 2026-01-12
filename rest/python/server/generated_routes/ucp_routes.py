"""Generated routes for UCP server."""

from typing import Annotated
from fastapi import APIRouter, Body, Header
import ucp_sdk.models.schemas.shopping.checkout_create_req
import ucp_sdk.models.schemas.shopping.checkout_resp
import ucp_sdk.models.schemas.shopping.checkout_update_req
import ucp_sdk.models.schemas.shopping.order
import ucp_sdk.models.schemas.shopping.payment_create_req
import ucp_sdk.models.schemas.shopping.payment_resp

router = APIRouter()


@router.post(
  "/checkout-sessions",
  response_model=ucp_sdk.models.schemas.shopping.checkout_resp.CheckoutResponse,
  status_code=201,
  operation_id="create_checkout",
  summary="Create Checkout",
)
async def create_checkout(
  body: Annotated[
    ucp_sdk.models.schemas.shopping.checkout_create_req.CheckoutCreateRequest,
    Body(...),
  ],
  authorization: str = Header(None, alias="Authorization"),
  x_api_key: str = Header(None, alias="X-API-Key"),
  request_signature: str = Header(..., alias="Request-Signature"),
  idempotency_key: str = Header(..., alias="Idempotency-Key"),
  request_id: str = Header(..., alias="Request-Id"),
  user_agent: str = Header(None, alias="User-Agent"),
  content_type: str = Header(None, alias="Content-Type"),
  accept: str = Header(None, alias="Accept"),
  accept_language: str = Header(None, alias="Accept-Language"),
  accept_encoding: str = Header(None, alias="Accept-Encoding"),
):
  """Create Checkout."""
  # TODO: Implement logic
  return {}


@router.get(
  "/checkout-sessions/{id}",
  response_model=ucp_sdk.models.schemas.shopping.checkout_resp.CheckoutResponse,
  status_code=200,
  operation_id="get_checkout",
  summary="Get Checkout",
)
async def get_checkout(
  id: str,
  authorization: str = Header(None, alias="Authorization"),
  x_api_key: str = Header(None, alias="X-API-Key"),
  request_signature: str = Header(..., alias="Request-Signature"),
  idempotency_key: str = Header(..., alias="Idempotency-Key"),
  request_id: str = Header(..., alias="Request-Id"),
  user_agent: str = Header(None, alias="User-Agent"),
  content_type: str = Header(None, alias="Content-Type"),
  accept: str = Header(None, alias="Accept"),
  accept_language: str = Header(None, alias="Accept-Language"),
  accept_encoding: str = Header(None, alias="Accept-Encoding"),
):
  """Get Checkout."""
  # TODO: Implement logic
  return {}


@router.put(
  "/checkout-sessions/{id}",
  response_model=ucp_sdk.models.schemas.shopping.checkout_resp.CheckoutResponse,
  status_code=200,
  operation_id="update_checkout",
  summary="Update Checkout",
)
async def update_checkout(
  id: str,
  body: Annotated[
    ucp_sdk.models.schemas.shopping.checkout_update_req.CheckoutUpdateRequest,
    Body(...),
  ],
  authorization: str = Header(None, alias="Authorization"),
  x_api_key: str = Header(None, alias="X-API-Key"),
  request_signature: str = Header(..., alias="Request-Signature"),
  idempotency_key: str = Header(..., alias="Idempotency-Key"),
  request_id: str = Header(..., alias="Request-Id"),
  user_agent: str = Header(None, alias="User-Agent"),
  content_type: str = Header(None, alias="Content-Type"),
  accept: str = Header(None, alias="Accept"),
  accept_language: str = Header(None, alias="Accept-Language"),
  accept_encoding: str = Header(None, alias="Accept-Encoding"),
):
  """Update Checkout."""
  # TODO: Implement logic
  return {}


@router.post(
  "/checkout-sessions/{id}/complete",
  response_model=ucp_sdk.models.schemas.shopping.checkout_resp.CheckoutResponse,
  status_code=200,
  operation_id="complete_checkout",
  summary="Complete Checkout",
)
async def complete_checkout(
  id: str,
  body: Annotated[dict, Body(...)],
  authorization: str = Header(None, alias="Authorization"),
  x_api_key: str = Header(None, alias="X-API-Key"),
  request_signature: str = Header(..., alias="Request-Signature"),
  idempotency_key: str = Header(..., alias="Idempotency-Key"),
  request_id: str = Header(..., alias="Request-Id"),
  user_agent: str = Header(None, alias="User-Agent"),
  content_type: str = Header(None, alias="Content-Type"),
  accept: str = Header(None, alias="Accept"),
  accept_language: str = Header(None, alias="Accept-Language"),
  accept_encoding: str = Header(None, alias="Accept-Encoding"),
):
  """Complete Checkout."""
  # TODO: Implement logic
  return {}


@router.post(
  "/checkout-sessions/{id}/cancel",
  response_model=ucp_sdk.models.schemas.shopping.checkout_resp.CheckoutResponse,
  status_code=200,
  operation_id="cancel_checkout",
  summary="Cancel Checkout",
)
async def cancel_checkout(
  id: str,
  authorization: str = Header(None, alias="Authorization"),
  x_api_key: str = Header(None, alias="X-API-Key"),
  request_signature: str = Header(..., alias="Request-Signature"),
  idempotency_key: str = Header(..., alias="Idempotency-Key"),
  request_id: str = Header(..., alias="Request-Id"),
  user_agent: str = Header(None, alias="User-Agent"),
  content_type: str = Header(None, alias="Content-Type"),
  accept: str = Header(None, alias="Accept"),
  accept_language: str = Header(None, alias="Accept-Language"),
  accept_encoding: str = Header(None, alias="Accept-Encoding"),
):
  """Cancel Checkout."""
  # TODO: Implement logic
  return {}


@router.post(
  "/webhooks/partners/{partner_id}/events/order",
  response_model=dict,
  status_code=200,
  operation_id="order_event_webhook",
  summary="Order Event Webhook",
)
async def order_event_webhook(
  partner_id: str,
  body: Annotated[ucp_sdk.models.schemas.shopping.order.Order, Body(...)],
  request_signature: str = Header(..., alias="Request-Signature"),
  x_api_key: str = Header(None, alias="X-API-Key"),
):
  """Order Event Webhook."""
  # TODO: Implement logic
  return {}
