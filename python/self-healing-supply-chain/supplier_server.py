# supplier_server.py
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from demo_logger import logger

# --- UCP SDK Imports ---
from ucp_sdk.models.schemas.shopping.checkout_create_req import CheckoutCreateRequest
from ucp_sdk.models.schemas.shopping.checkout_resp import CheckoutResponse
from ucp_sdk.models.schemas.shopping.types.line_item_resp import LineItemResponse
from ucp_sdk.models.schemas.shopping.types.item_resp import ItemResponse
from ucp_sdk.models.schemas.shopping.types.total_resp import TotalResponse
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
                {"name": "dev.ucp.shopping.ap2_mandate", "version": "2026-01-11", "extends": "dev.ucp.shopping.checkout"}
            ]
        },
        "inventory": {
            "widget-x": {"in_stock": True, "price": 55000} 
        }
    }

# 2. Checkout
@app.post("/ucp/v1/checkout-sessions", response_model=CheckoutResponseWithAp2)
def create_checkout(checkout_req: CheckoutCreateRequest):
    logger.supplier("Received Valid UCP Checkout Request")
    
    # Simulate AP2 Signing
    merchant_signature = "eyJhbGciOiJFUzI1NiJ9..signed_by_merchant_private_key"
    
    response = CheckoutResponseWithAp2(
        ucp={"version": "2026-01-11", "capabilities": []},
        id="chk_123456789",
        status="ready_for_complete",
        currency="GBP",
        links=[],
        payment={"handlers": [], "instruments": []},
        line_items=[
            LineItemResponse(
                id="li_1",
                quantity=100,
                item=ItemResponse(
                    id="widget-x",
                    title="Industrial Widget X",
                    price=55000 
                ),
                totals=[TotalResponse(type="total", amount=5500000)]
            )
        ],
        totals=[TotalResponse(type="total", amount=5500000)],
        ap2=Ap2CheckoutResponse(
            merchant_authorization=MerchantAuthorization(root=merchant_signature)
        )
    )
    logger.supplier(f"Created Session {response.id} with AP2 Sig")
    return response

# 3. Complete
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
    # Add a visible print statement so you know it's alive
    print(f"\n{logger.GREEN}🏭 [SUPPLIER] Server Online at http://0.0.0.0:8000{logger.RESET}")
    print(f"{logger.GREEN}🏭 [SUPPLIER] Waiting for UCP Discovery requests...{logger.RESET}\n")
    
    # Change log_level to "info" if you want to see standard Uvicorn logs, 
    # or keep "error" to rely solely on our custom logger.
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")