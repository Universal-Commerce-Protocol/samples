from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ucp_shopify_adapter_mock")

ADAPTER_BASE_URL = os.getenv("ADAPTER_BASE_URL", "http://127.0.0.1:8183").rstrip("/")
DEFAULT_UCP_AGENT = os.getenv("UCP_AGENT", "profile=https://agent.example/profile")
DEFAULT_SIGNATURE = os.getenv("REQUEST_SIGNATURE", "test")


def _headers(idempotency_key: Optional[str] = None, simulation_secret: Optional[str] = None) -> Dict[str, str]:
    h = {
        "UCP-Agent": DEFAULT_UCP_AGENT,
        "request-signature": DEFAULT_SIGNATURE,
        "request-id": str(uuid.uuid4()),
    }
    if idempotency_key:
        h["idempotency-key"] = idempotency_key
    if simulation_secret:
        h["Simulation-Secret"] = simulation_secret
    return h


async def _request(method: str, path: str, *, json: Any = None, headers: Optional[Dict[str, str]] = None) -> Any:
    url = f"{ADAPTER_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.request(method, url, json=json, headers=headers)
        try:
            data = r.json()
        except Exception:
            data = r.text
        return {"status_code": r.status_code, "body": data}


@mcp.tool()
async def discovery_profile() -> Any:
    """Fetch the discovery profile from the adapter."""
    return await _request("GET", "/.well-known/ucp", headers=_headers())


@mcp.tool()
async def list_products() -> Any:
    """List products."""
    return await _request("GET", "/products", headers=_headers())


@mcp.tool()
async def get_product(product_id: str) -> Any:
    """Get a product."""
    return await _request("GET", f"/products/{product_id}", headers=_headers())


@mcp.tool()
async def create_checkout(
    product_id: str,
    quantity: int = 1,
    currency: str = "USD",
    discount_code: Optional[str] = None,
    full_name: str = "John Doe",
    email: str = "john.doe@example.com",
    idempotency_key: Optional[str] = None,
) -> Any:
    """Create a checkout session."""
    payload: Dict[str, Any] = {
        "buyer": {"full_name": full_name, "email": email},
        "currency": currency,
        "line_items": [{"product_id": product_id, "quantity": quantity}],
        "discount_codes": ([discount_code] if discount_code else []),
    }
    idem = idempotency_key or str(uuid.uuid4())
    return await _request("POST", "/checkout-sessions", json=payload, headers=_headers(idem))


@mcp.tool()
async def set_shipping(
    checkout_id: str,
    line_item_id: str,
    selected_option_id: str = "std-ship",
    full_name: str = "John Doe",
    street_address: str = "10 Downing St",
    address_locality: str = "London",
    address_region: str = "London",
    address_country: str = "GB",
    postal_code: str = "SW1A 2AA",
    phone_number: str = "+447000000000",
    idempotency_key: Optional[str] = None,
) -> Any:
    """Set shipping destination + select option."""
    payload: Dict[str, Any] = {
        "id": checkout_id,
        "fulfillment": {
            "methods": [
                {
                    "type": "shipping",
                    "line_item_ids": [line_item_id],
                    "destinations": [
                        {
                            "id": "dest_1",
                            "street_address": street_address,
                            "address_locality": address_locality,
                            "address_region": address_region,
                            "address_country": address_country,
                            "postal_code": postal_code,
                            "full_name": full_name,
                            "phone_number": phone_number,
                        }
                    ],
                    "selected_destination_id": "dest_1",
                    "groups": [{"selected_option_id": selected_option_id}],
                }
            ]
        },
    }
    idem = idempotency_key or str(uuid.uuid4())
    return await _request("PUT", f"/checkout-sessions/{checkout_id}", json=payload, headers=_headers(idem))


@mcp.tool()
async def complete_checkout(
    checkout_id: str,
    token: str = "success_token",
    idempotency_key: Optional[str] = None,
) -> Any:
    """Complete checkout using mock payment token."""
    payload: Dict[str, Any] = {
        "payment_data": {
            "id": "pi_test_1",
            "handler_id": "mock_payment_handler",
            "type": "card",
            "brand": "VISA",
            "last_digits": "1111",
            "credential": {"type": "token", "token": token},
        },
        "risk_signals": {},
    }
    idem = idempotency_key or str(uuid.uuid4())
    return await _request("POST", f"/checkout-sessions/{checkout_id}/complete", json=payload, headers=_headers(idem))


@mcp.tool()
async def get_order(order_id: str) -> Any:
    """Fetch an order."""
    return await _request("GET", f"/orders/{order_id}", headers=_headers())


@mcp.tool()
async def simulate_shipping(order_id: str, simulation_secret: str = "letmein") -> Any:
    """Append a shipped event (requires Simulation-Secret)."""
    return await _request(
        "POST",
        f"/testing/simulate-shipping/{order_id}",
        json={},
        headers=_headers(simulation_secret=simulation_secret),
    )


def run() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()