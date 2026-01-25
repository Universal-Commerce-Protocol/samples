from __future__ import annotations

import datetime
import uuid
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Path
from ..config import settings
from ..storage import store

router = APIRouter()


def _require_header(name: str, value: Optional[str]) -> str:
    if not value:
        raise HTTPException(status_code=400, detail={"detail": f"Missing header: {name}", "code": "INVALID_REQUEST"})
    return value


@router.post("/testing/simulate-shipping/{id}")
async def simulate_shipping(
    order_id: str = Path(..., alias="id"),
    simulation_secret: Optional[str] = Header(None, alias="Simulation-Secret"),
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    request_id: Optional[str] = Header(None, alias="request-id"),
):
    _require_header("UCP-Agent", ucp_agent)
    _require_header("request-signature", request_signature)
    _require_header("request-id", request_id)

    if simulation_secret != settings.simulation_secret:
        raise HTTPException(status_code=403, detail={"detail": "Invalid Simulation-Secret", "code": "FORBIDDEN"})

    order = store.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail={"detail": "Order not found", "code": "NOT_FOUND"})

    if "fulfillment" not in order or order["fulfillment"] is None:
        order["fulfillment"] = {"expectations": [], "events": []}
    if "events" not in order["fulfillment"] or order["fulfillment"]["events"] is None:
        order["fulfillment"]["events"] = []

    order["fulfillment"]["events"].append(
        {
            "id": f"evt_{uuid.uuid4()}",
            "type": "shipped",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    )

    store.orders[order_id] = order
    return {"status": "shipped"}