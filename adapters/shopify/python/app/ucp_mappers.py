from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .models import Product


def product_to_ucp_item(p: Product) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "price": p.price,
        "image_url": p.image_url,
    }


def compute_totals(subtotal: int, fulfillment: int, discount: int) -> List[Dict[str, Any]]:
    total = max(0, subtotal + fulfillment - discount)
    out: List[Dict[str, Any]] = [
        {"type": "subtotal", "display_text": None, "amount": subtotal},
    ]
    if fulfillment:
        out.append({"type": "fulfillment", "display_text": None, "amount": fulfillment})
    if discount:
        out.append({"type": "discount", "display_text": None, "amount": discount})
    out.append({"type": "total", "display_text": None, "amount": total})
    return out


def apply_discounts(discount_codes: List[str], subtotal: int) -> Tuple[int, Dict[str, Any]]:
    """
    Very simple rule:
    - If "10OFF" is present => 10% off subtotal.
    """
    applied = []
    discount_amount = 0

    if "10OFF" in discount_codes:
        discount_amount = int(round(subtotal * 0.10))
        applied.append(
            {
                "code": "10OFF",
                "title": "10% Off",
                "amount": discount_amount,
                "automatic": False,
                "method": None,
                "priority": None,
                "allocations": [{"path": "$.totals[?(@.type=='subtotal')]", "amount": discount_amount}],
            }
        )

    return discount_amount, {"codes": discount_codes, "applied": applied}