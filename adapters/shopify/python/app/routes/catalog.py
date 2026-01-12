from __future__ import annotations

from fastapi import APIRouter, HTTPException
from ..shopify_client import MockShopifyClient
from ..ucp_mappers import product_to_ucp_item

router = APIRouter()
shopify = MockShopifyClient()


@router.get("/products")
async def list_products():
    return {"products": [product_to_ucp_item(p) for p in shopify.list_products()]}


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    p = shopify.get_product(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product": product_to_ucp_item(p)}