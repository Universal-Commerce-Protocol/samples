from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Path
from typing import Optional
from ..storage import store


router = APIRouter()


def _require_header(name: str, value: Optional[str]) -> str:
    if not value:
        raise HTTPException(status_code=400, detail={"detail": f"Missing header: {name}", "code": "INVALID_REQUEST"})
    return value


@router.get("/orders/{id}")
async def get_order(
    order_id: str = Path(..., alias="id"),
    ucp_agent: Optional[str] = Header(None, alias="UCP-Agent"),
    request_signature: Optional[str] = Header(None, alias="request-signature"),
    request_id: Optional[str] = Header(None, alias="request-id"),
):
    _require_header("UCP-Agent", ucp_agent)
    _require_header("request-signature", request_signature)
    _require_header("request-id", request_id)

    order = store.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail={"detail": "Order not found", "code": "NOT_FOUND"})
    return order