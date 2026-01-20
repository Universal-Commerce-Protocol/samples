# supplier_server.py
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from demo_logger import logger

# --- UCP SDK Imports ---
from ucp_sdk.models.schemas.shopping.checkout_create_req import CheckoutCreateRequest
from ucp_sdk.models.schemas.shopping.checkout_update_req import CheckoutUpdateRequest
from ucp_sdk.models.schemas.shopping.checkout_resp import CheckoutResponse
from ucp_sdk.models.schemas.shopping.types.line_item_resp import LineItemResponse
from ucp_sdk.models.schemas.shopping.types.item_resp import ItemResponse
from ucp_sdk.models.schemas.shopping.types.total_resp import TotalResponse
from ucp_sdk.models.schemas.shopping.discount_resp import DiscountsObject, AppliedDiscount
from ucp_sdk.models.schemas.shopping.fulfillment_resp import FulfillmentResp, FulfillmentMethodResp, FulfillmentGroupResp, FulfillmentOptionResp
from ucp_sdk.models.schemas.shopping.ap2_mandate import (
    CheckoutResponseWithAp2, 
    MerchantAuthorization, 
    Ap2CheckoutResponse,
    CompleteRequestWithAp2
)

app = FastAPI()

# 1. UCP Discovery
@app.get("/.well-known/ucp")
def get_ucp_profile(request: Request):
    base_url = str(request.base_url).rstrip("/")
    logger.supplier("Received UCP Discovery Request")
    return {
        "ucp": {
            "version": "2026-01-11",
            "services": {
                "dev.ucp.shopping": {
                    "version": "2026-01-11",
                    "spec": "https://ucp.dev/specification/overview",
                    "rest": {
                        "endpoint": f"{base_url}/ucp/v1",
                        "schema": "https://ucp.dev/services/shopping/rest.openapi.json"
                    }
                }
            },
            "capabilities": [
                {"name": "dev.ucp.shopping.checkout", "version": "2026-01-11"},
                {"name": "dev.ucp.shopping.ap2_mandate", "version": "2026-01-11", "extends": "dev.ucp.shopping.checkout"},
                {"name": "dev.ucp.shopping.fulfillment", "version": "2026-01-11", "extends": "dev.ucp.shopping.checkout"},
                {"name": "dev.ucp.shopping.discount", "version": "2026-01-11", "extends": "dev.ucp.shopping.checkout"}
            ]
        },
        "inventory": {
            "widget-x": {"in_stock": True, "price": 55000} 
        }
    }

# 2. Checkout Create (Initial Intent)
@app.post("/ucp/v1/checkout-sessions", response_model=CheckoutResponseWithAp2)
def create_checkout(checkout_req: CheckoutCreateRequest):
    logger.supplier("Received Create Request. Status: INCOMPLETE (Requires Address)")
    
    # Base Price calculation
    qty = checkout_req.line_items[0].quantity
    unit_price = 55000
    subtotal = qty * unit_price
    
    response = CheckoutResponseWithAp2(
        ucp={"version": "2026-01-11", "capabilities": []},
        id="chk_123456789",
        status="incomplete",
        currency="GBP",
        messages=[{
            "type": "error",
            "code": "missing_address",
            "severity": "recoverable",
            "content": "Shipping address required to calculate tax and shipping."
        }],
        line_items=[
            LineItemResponse(
                id="li_1", quantity=qty,
                item=ItemResponse(id="widget-x", title="Industrial Widget X", price=unit_price),
                totals=[TotalResponse(type="subtotal", amount=subtotal)]
            )
        ],
        totals=[TotalResponse(type="subtotal", amount=subtotal)]
    )
    return response

# 3. Checkout Update (Negotiation: Address, Shipping, Discounts)
@app.put("/ucp/v1/checkout-sessions/{id}", response_model=CheckoutResponseWithAp2)
def update_checkout(id: str, update_req: CheckoutUpdateRequest):
    logger.supplier("Received Update Request. Calculating Tax, Shipping, Discounts...")
    
    # 1. Calculate Base
    qty = 100
    unit_price = 55000
    subtotal = qty * unit_price
    
    # 2. Apply Discounts (Logic: If code 'PARTNER_20' is present, take 20% off)
    discount_amount = 0
    applied_discounts = []
    
    if update_req.discounts and "PARTNER_20" in update_req.discounts.codes:
        discount_amount = int(subtotal * 0.20)
        applied_discounts.append(AppliedDiscount(
            code="PARTNER_20", 
            title="Strategic Partner 20% Off", 
            amount=discount_amount
        ))
        logger.supplier(f"Applying Discount: -£{discount_amount/100:.2f}")

    # 3. Apply Shipping (Logic: Flat rate industrial freight)
    shipping_cost = 5000 # £50.00
    
    # 4. Calculate Tax (10% of post-discount subtotal)
    taxable_amount = subtotal - discount_amount + shipping_cost
    tax_amount = int(taxable_amount * 0.10)
    
    final_total = taxable_amount + tax_amount

    # 5. Sign the new total (AP2)
    merchant_signature = f"eyJhbGciOiJFUzI1NiJ9..signed_total_{final_total}"

    response = CheckoutResponseWithAp2(
        ucp={"version": "2026-01-11", "capabilities": []},
        id=id,
        status="ready_for_complete",
        currency="GBP",
        line_items=[
            LineItemResponse(
                id="li_1", quantity=qty,
                item=ItemResponse(id="widget-x", title="Industrial Widget X", price=unit_price),
                totals=[TotalResponse(type="subtotal", amount=subtotal)]
            )
        ],
        fulfillment=FulfillmentResp(
            methods=[FulfillmentMethodResp(
                id="ship_1", type="shipping", line_item_ids=["li_1"],
                groups=[FulfillmentGroupResp(
                    id="grp_1", line_item_ids=["li_1"], selected_option_id="std_freight",
                    options=[FulfillmentOptionResp(id="std_freight", title="Industrial Freight", total=shipping_cost)]
                )]
            )]
        ),
        discounts=DiscountsObject(
            codes=update_req.discounts.codes if update_req.discounts else [],
            applied=applied_discounts
        ),
        totals=[
            TotalResponse(type="subtotal", amount=subtotal),
            TotalResponse(type="discount", amount=discount_amount),
            TotalResponse(type="fulfillment", amount=shipping_cost),
            TotalResponse(type="tax", amount=tax_amount),
            TotalResponse(type="total", amount=final_total)
        ],
        ap2=Ap2CheckoutResponse(
            merchant_authorization=MerchantAuthorization(root=merchant_signature)
        )
    )
    return response

# 4. Complete
@app.post("/ucp/v1/checkout-sessions/{id}/complete")
def complete_checkout(id: str, request: CompleteRequestWithAp2):
    logger.supplier(f"Processing Payment for Session {id}")
    if not request.ap2 or not request.ap2.checkout_mandate:
         logger.error("Protocol Violation: Missing AP2 Mandate")
         raise HTTPException(status_code=400, detail="Missing Mandate")
    
    mandate_token = request.ap2.checkout_mandate.root
    logger.supplier(f"Verifying AP2 Mandate Token: {mandate_token[:15]}...")
    logger.supplier("✅ Signature Valid. Dispatching Goods.")
    
    return {
        "id": id,
        "status": "completed",
        "order": {"id": "ord_999", "permalink_url": "http://order"}
    }

if __name__ == "__main__":
    print(f"\n{logger.GREEN}🏭 [SUPPLIER] Server Online at http://0.0.0.0:8000{logger.RESET}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")