from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Header, HTTPException, Path
from ..config import settings
from ..models import (
    ApiError,
    Checkout,
    CompleteCheckoutRequest,
    CreateCheckoutRequest,
    FulfillmentOption,
)
from ..shopify_client import MockShopifyClient
from ..storage import store
from ..ucp_mappers import apply_discounts, compute_totals, product_to_ucp_item

router = APIRouter()
shopify = MockShopifyClient()


def _require_header(name: str, value: Optional[str]) -> str:
    if not value:
        raise HTTPException(status_code=400, detail={"detail": f"Missing header: {name}", "code": "INVALID_REQUEST"})
    return value


def _checkout_ucp_envelope() -> Dict[str, Any]:
    return {
        "ucp": {
            "version": settings.ucp_version,
            "capabilities": [{"name": "dev.ucp.shopping.checkout", "version": settings.ucp_version, "spec": None, "schema": None, "extends": None, "config": None}],
        }
    }


def _build_fulfillment_defaults(line_item_ids: list[str]) -> Dict[str, Any]:
    # We generate fulfillment groups/options after a destination is set (or on update)
    return {"methods": [], "available_methods": None}


def _recompute_checkout(checkout: Dict[str, Any]) -> Dict[str, Any]:
    subtotal = sum(li["item"]["price"] * li["quantity"] for li in checkout["line_items"])
    discount_amount, discounts_obj = apply_discounts(checkout.get("discounts", {}).get("codes", []), subtotal)

    fulfillment_amount = 0
    # If fulfillment selected option is exp-ship-intl => +2500
    try:
        methods = (checkout.get("fulfillment") or {}).get("methods") or []
        if methods:
            groups = (methods[0].get("groups") or [])
            if groups and groups[0].get("selected_option_id") == "exp-ship-intl":
                fulfillment_amount = 2500
    except Exception:
        pass

    checkout["totals"] = compute_totals(subtotal=subtotal, fulfillment=fulfillment_amount, discount=discount_amount)
    checkout["discounts"] = discounts_obj
    return checkout


def _ensure_groups_options(method: Dict[str, Any]) -> None:
    """
    If destinations exist, ensure groups/options exist.
    """
    if not method.get("groups"):
        method["groups"] = []

    # single group for all line items in method
    group = method["groups"][0] if method["groups"] else None
    if not group:
        group = {
            "id": f"group_{uuid.uuid4()}",
            "line_item_ids": method.get("line_item_ids") or [],
            "options": [
                {
                    "id": "std-ship",
                    "title": "Standard Shipping (Free)",
                    "description": None,
                    "carrier": None,
                    "earliest_fulfillment_time": None,
                    "latest_fulfillment_time": None,
                    "totals": [
                        {"type": "subtotal", "display_text": None, "amount": 0},
                        {"type": "total", "display_text": None, "amount": 0},
                    ],
                },
                {
                    "id": "exp-ship-intl",
                    "title": "International Express",
                    "description": None,
                    "carrier": None,
                    "earliest_fulfillment_time": None,
                    "latest_fulfillment_time": None,
                    "totals": [
                        {"type": "subtotal", "display_text": None, "amount": 2500},
                        {"type": "total", "display_text": None, "amount": 2500},
                    ],
                },
            ],
            "selected_option_id": group.get("selected_option_id") if group else None,
        }
        method["groups"] = [group]
    else:
        # make sure options exist
        if not group.get("options"):
            group["options"] = [
                {
                    "id": "std-ship",
                    "title": "Standard Shipping (Free)",
                    "description": None,
                    "carrier": None,
                    "earliest_fulfillment_time": None,
                    "latest_fulfillment_time": None,
                    "totals": [
                        {"type": "subtotal", "display_text": None, "amount": 0},
                        {"type": "total", "display_text": None, "amount": 0},
                    ],
                },
                {
                    "id": "exp-ship-intl",
                    "title": "International Express",
                    "description": None,
                    "carrier": None,
                    "earliest_fulfillment_time": None,
                    "latest_fulfillment_time": None,
                    "totals": [
                        {"type": "subtotal", "display_text": None, "amount": 2500},
                        {"type": "total", "display_text": None, "amount": 2500},
                    ],
                },
            ]


@router.post("/checkout-sessions")
async def create_checkout(
    req: CreateCheckoutRequest = Body(...),
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    request_id: Optional[str] = Header(None, alias="request-id"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
):
    _require_header("UCP-Agent", ucp_agent)
    _require_header("request-signature", request_signature)
    _require_header("request-id", request_id)
    _require_header("idempotency-key", idempotency_key)

    payload = req.model_dump(mode="json")
    try:
        existing, req_hash = store.idempotency_check_or_raise(idempotency_key, payload)
        if existing is not None:
            return existing
    except ValueError:
        raise HTTPException(status_code=409, detail={"detail": "Idempotency key reused with different parameters", "code": "IDEMPOTENCY_CONFLICT"})

    checkout_id = store.new_id()
    line_items = []
    for li in req.line_items:
        p = shopify.get_product(li.product_id)
        if not p:
            raise HTTPException(status_code=400, detail={"detail": f"Unknown product_id: {li.product_id}", "code": "INVALID_REQUEST"})
        line_item_id = store.new_id()
        item = product_to_ucp_item(p)
        line_items.append(
            {
                "id": line_item_id,
                "item": item,
                "quantity": li.quantity,
                "totals": [
                    {"type": "subtotal", "display_text": None, "amount": item["price"] * li.quantity},
                    {"type": "total", "display_text": None, "amount": item["price"] * li.quantity},
                ],
                "parent_id": None,
            }
        )

    checkout = {
        **_checkout_ucp_envelope(),
        "id": checkout_id,
        "line_items": line_items,
        "buyer": req.buyer.model_dump(mode="json") if req.buyer else None,
        "status": "ready_for_complete",
        "currency": req.currency,
        "totals": [],
        "messages": None,
        "links": [],
        "expires_at": None,
        "continue_url": None,
        "payment": {"handlers": [], "selected_instrument_id": None, "instruments": []},
        "order": None,
        "ap2": None,
        "discounts": {"codes": req.discount_codes, "applied": []},
        "fulfillment": None,
        "platform": None,
    }

    checkout["fulfillment"] = _build_fulfillment_defaults([li["id"] for li in line_items])
    checkout = _recompute_checkout(checkout)

    store.checkouts[checkout_id] = checkout
    store.put_idempotency(idempotency_key, req_hash, checkout)
    return checkout


@router.get("/checkout-sessions/{id}")
async def get_checkout(
    checkout_id: str = Path(..., alias="id"),
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    request_id: Optional[str] = Header(None, alias="request-id"),
):
    _require_header("UCP-Agent", ucp_agent)
    _require_header("request-signature", request_signature)
    _require_header("request-id", request_id)

    checkout = store.checkouts.get(checkout_id)
    if not checkout:
        raise HTTPException(status_code=404, detail={"detail": "Checkout not found", "code": "NOT_FOUND"})
    return checkout


@router.put("/checkout-sessions/{id}")
async def update_checkout(
    checkout_id: str = Path(..., alias="id"),
    body: Dict[str, Any] = Body(...),
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    request_id: Optional[str] = Header(None, alias="request-id"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
):
    _require_header("UCP-Agent", ucp_agent)
    _require_header("request-signature", request_signature)
    _require_header("request-id", request_id)
    _require_header("idempotency-key", idempotency_key)

    try:
        existing, req_hash = store.idempotency_check_or_raise(idempotency_key, body)
        if existing is not None:
            return existing
    except ValueError:
        raise HTTPException(status_code=409, detail={"detail": "Idempotency key reused with different parameters", "code": "IDEMPOTENCY_CONFLICT"})

    checkout = store.checkouts.get(checkout_id)
    if not checkout:
        raise HTTPException(status_code=404, detail={"detail": "Checkout not found", "code": "NOT_FOUND"})

    # Partial update: only fulfillment supported here
    if "fulfillment" in body and body["fulfillment"] is not None:
        checkout["fulfillment"] = body["fulfillment"]

        # Ensure groups/options if destinations exist
        methods = (checkout["fulfillment"] or {}).get("methods") or []
        if methods:
            method = methods[0]
            if method.get("destinations"):
                _ensure_groups_options(method)
            checkout["fulfillment"]["methods"] = [method]

    checkout = _recompute_checkout(checkout)
    store.checkouts[checkout_id] = checkout
    store.put_idempotency(idempotency_key, req_hash, checkout)
    return checkout


@router.post("/checkout-sessions/{id}/complete")
async def complete_checkout(
    checkout_id: str = Path(..., alias="id"),
    req: CompleteCheckoutRequest = Body(...),
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    request_id: Optional[str] = Header(None, alias="request-id"),
    idempotency_key: Optional[str] = Header(None, alias="idempotency-key"),
):
    _require_header("UCP-Agent", ucp_agent)
    _require_header("request-signature", request_signature)
    _require_header("request-id", request_id)
    _require_header("idempotency-key", idempotency_key)

    payload = req.model_dump(mode="json")
    try:
        existing, req_hash = store.idempotency_check_or_raise(idempotency_key, payload)
        if existing is not None:
            return existing
    except ValueError:
        raise HTTPException(status_code=409, detail={"detail": "Idempotency key reused with different parameters", "code": "IDEMPOTENCY_CONFLICT"})

    checkout = store.checkouts.get(checkout_id)
    if not checkout:
        raise HTTPException(status_code=404, detail={"detail": "Checkout not found", "code": "NOT_FOUND"})

    # Validate fulfillment chosen
    methods = (checkout.get("fulfillment") or {}).get("methods") or []
    if not methods:
        raise HTTPException(status_code=400, detail={"detail": "Fulfillment address and option must be selected before completion.", "code": "INVALID_REQUEST"})
    method = methods[0]
    if not method.get("selected_destination_id"):
        raise HTTPException(status_code=400, detail={"detail": "Fulfillment address and option must be selected before completion.", "code": "INVALID_REQUEST"})
    groups = method.get("groups") or []
    if not groups or not groups[0].get("selected_option_id"):
        raise HTTPException(status_code=400, detail={"detail": "Fulfillment address and option must be selected before completion.", "code": "INVALID_REQUEST"})

    # Validate payment credential
    cred = req.payment_data.credential
    if not cred or cred.type != "token":
        raise HTTPException(status_code=400, detail={"detail": "Missing credentials in instrument", "code": "INVALID_REQUEST"})
    if cred.token != "success_token":
        raise HTTPException(status_code=402, detail={"detail": "Payment authorization failed", "code": "PAYMENT_FAILED"})

    # Create order
    order_id = store.new_id()
    permalink_url = f"{settings.server_base_url}/orders/{order_id}"

    # Derive fulfillment expectation from selected option
    selected_option = groups[0]["selected_option_id"]
    option_title = "Standard Shipping (Free)" if selected_option == "std-ship" else "International Express"

    destination = None
    for d in (method.get("destinations") or []):
        if d.get("id") == method.get("selected_destination_id"):
            destination = d
            break

    expectations = [
        {
            "id": f"exp_{uuid.uuid4()}",
            "line_items": [{"id": li["id"], "quantity": li["quantity"]} for li in checkout["line_items"]],
            "method_type": method.get("type"),
            "destination": destination or {},
            "description": option_title,
            "fulfillable_on": None,
        }
    ]

    order = {
        **_checkout_ucp_envelope(),
        "id": order_id,
        "checkout_id": checkout_id,
        "permalink_url": permalink_url,
        "line_items": [
            {
                "id": li["id"],
                "item": li["item"],
                "quantity": {"total": li["quantity"], "fulfilled": 0},
                "totals": li["totals"],
                "status": "processing",
                "parent_id": None,
            }
            for li in checkout["line_items"]
        ],
        "fulfillment": {"expectations": expectations, "events": []},
        "adjustments": None,
        "totals": checkout["totals"],
    }

    store.orders[order_id] = order

    checkout["status"] = "completed"
    checkout["order"] = {"id": order_id, "permalink_url": permalink_url}
    store.checkouts[checkout_id] = checkout

    store.put_idempotency(idempotency_key, req_hash, checkout)
    return checkout