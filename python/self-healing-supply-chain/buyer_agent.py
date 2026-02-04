# buyer_agent.py
import asyncio
import requests
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

# --- 1. ADK (The Brain) ---
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

# --- 2. A2A (The Message Standard) ---
from a2a import types as a2a_types

# --- 3. AP2 (The Trust/Payment Standard) ---
from ap2.types.mandate import (
    IntentMandate, 
    PaymentMandate, 
    PaymentMandateContents
)
from ap2.types.payment_request import PaymentResponse, PaymentItem, PaymentCurrencyAmount

# --- 4. UCP (The Commerce Schema) ---
from ucp_sdk.models.schemas.shopping.checkout_create_req import CheckoutCreateRequest
from ucp_sdk.models.schemas.shopping.checkout_update_req import CheckoutUpdateRequest
from ucp_sdk.models.schemas.shopping.types.line_item_create_req import LineItemCreateRequest
from ucp_sdk.models.schemas.shopping.types.item_create_req import ItemCreateRequest
from ucp_sdk.models.schemas.shopping.payment_create_req import PaymentCreateRequest
from ucp_sdk.models.schemas.shopping.discount_create_req import DiscountsObject
from ucp_sdk.models.schemas.shopping.fulfillment_create_req import Fulfillment
from ucp_sdk.models.schemas.shopping.types.fulfillment_req import FulfillmentRequest
from ucp_sdk.models.schemas.shopping.types.fulfillment_method_create_req import FulfillmentMethodCreateRequest
from ucp_sdk.models.schemas.shopping.types.shipping_destination_req import ShippingDestinationRequest
from ucp_sdk.models.schemas.shopping.types.fulfillment_destination_req import FulfillmentDestinationRequest
from ucp_sdk.models.schemas.shopping.ap2_mandate import (
    CompleteRequestWithAp2,
    Ap2CompleteRequest,
    CheckoutMandate
)

# --- Local Helpers ---
from demo_logger import logger
from mock_db import PRODUCT_CATALOG, SPENDING_POLICY

# --- Tools ---

def check_primary_supplier(item_id: str) -> dict:
    """Checks inventory at the primary supplier."""
    logger.step("1. MONITORING INVENTORY")
    logger.agent(f"Checking primary supplier for {item_id}...")
    logger.error("Primary Supplier connection failed (503 Service Unavailable)")
    return {"status": "error", "message": "Primary Supplier Offline/OOS"}

def discover_backup_suppliers(item_id: str) -> list:
    """Queries backup suppliers using UCP Dynamic Discovery."""
    logger.step("2. UCP DISCOVERY")
    logger.agent("Initiating self-healing protocol. Scanning backup nodes...")
    
    product_data = PRODUCT_CATALOG.get(item_id)
    if not product_data:
        return []
    
    found_suppliers = []
    
    for url in product_data['backup_suppliers']:
        try:
            logger.ucp(f"GET {url}/.well-known/ucp")
            response = requests.get(f"{url}/.well-known/ucp")
            
            if response.status_code == 200:
                profile = response.json()
                
                # --- Dynamic Service Resolution ---
                services = profile.get("ucp", {}).get("services", {})
                shopping_service = services.get("dev.ucp.shopping")
                
                if not shopping_service:
                    continue
                    
                api_endpoint = shopping_service.get("rest", {}).get("endpoint")
                logger.agent(f"Discovered Commerce Endpoint: {api_endpoint}")
                
                inventory = profile.get("inventory", {}).get(item_id, {})
                if inventory.get("in_stock"):
                    price_major = inventory.get("price") / 100
                    
                    found_suppliers.append({
                        "supplier": "Supplier B",
                        "discovery_url": url,
                        "api_endpoint": api_endpoint,
                        "price": price_major,
                        "currency": "GBP"
                    })
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            
    return found_suppliers

def check_governance_and_approve(supplier_price: float, item_id: str, quantity: int = 100) -> dict:
    """Checks price variance and creates AP2 Intent Mandate."""
    logger.step("3. AP2 GOVERNANCE & INTENT")
    
    product = PRODUCT_CATALOG.get(item_id)
    std_price = product['standard_price']
    total_cost = supplier_price * quantity
    variance = (supplier_price - std_price) / std_price
    
    logger.ap2(f"Checking Price: £{supplier_price:.2f} (Std: £{std_price:.2f})")
    logger.ap2(f"Total Cost: £{total_cost:.2f}")
    logger.ap2(f"Variance: {variance:.1%}")

    # [AP2 Protocol] Creating the Intent Mandate
    intent = IntentMandate(
        natural_language_description=f"Purchase {quantity} x {item_id} for supply chain resilience",
        user_cart_confirmation_required=True,
        intent_expiry=(datetime.now() + timedelta(hours=1)).isoformat()
    )

    if variance <= SPENDING_POLICY['max_variance']:
        logger.ap2("✅ Variance within policy limits. Approved.")
        return {"approved": True, "mandate": intent.model_dump(), "type": "auto"}
    else:
        logger.ap2("⚠️ Policy Check Failed. Requesting Human Sign-off.")
        # We use standard input here for simplicity in this demo flow
        input(f"[ADMIN] Sign off on £{total_cost:.2f} (Unit: £{supplier_price:.2f} vs Std: £{std_price:.2f}, {variance:.1%} variance)? (Press Enter): ")
        return {"approved": True, "mandate": intent.model_dump(), "type": "manual"}

def execute_ucp_transaction(api_endpoint: str, item_id: str, price: float, mandate_type: str) -> dict:
    """Executes the transaction using UCP schemas and AP2 Payment Mandates."""
    logger.step("4. UCP TRANSACTION & AP2 PAYMENT")

    # [UCP Protocol] 1. Create Checkout (Initial Intent)
    logger.ucp("Building UCP Checkout Request (Initial)...")
    ucp_req = CheckoutCreateRequest(
        currency="GBP",
        line_items=[
            LineItemCreateRequest(
                quantity=100,
                item=ItemCreateRequest(id=item_id)
            )
        ],
        payment=PaymentCreateRequest()
    )
    
    target_url = f"{api_endpoint}/checkout-sessions"
    logger.ucp(f"POST {target_url}", ucp_req)
    
    res = requests.post(target_url, json=ucp_req.model_dump(mode='json', exclude_none=True))
    checkout_data = res.json()
    
    # [UCP Protocol] 2. Negotiation Loop (Update)
    # The server returned 'incomplete' because we need shipping/tax/discounts
    if checkout_data.get('status') == 'incomplete':
        logger.agent("Checkout Incomplete. Negotiating capabilities (Discount + Shipping)...")
        
        update_req = CheckoutUpdateRequest(
            id=checkout_data['id'],
            # Re-transmit required state
            currency=checkout_data['currency'],
            line_items=[{
                "id": li['id'],
                "quantity": li['quantity'],
                "item": {"id": li['item']['id']}
            } for li in checkout_data['line_items']],
            payment={"instruments": []}, 
            # Apply our corporate discount code
            discounts=DiscountsObject(codes=["PARTNER_20"]),
            # Provide shipping destination
            fulfillment=Fulfillment(
                root=FulfillmentRequest(
                    methods=[FulfillmentMethodCreateRequest(
                        line_item_ids=[checkout_data['line_items'][0]['id']],
                        type="shipping",
                        destinations=[FulfillmentDestinationRequest(
                            root=ShippingDestinationRequest(postal_code="SW1A 1AA", address_country="GB")
                        )]
                    )]
                )
            )
        )
        
        update_url = f"{target_url}/{checkout_data['id']}"
        logger.ucp(f"PUT {update_url} (Adding 'PARTNER_20' code + Address)", update_req)
        
        res = requests.put(update_url, json=update_req.model_dump(mode='json', exclude_none=True))
        checkout_data = res.json()

    # Calculate final totals from the negotiated checkout
    final_total_major = next((t['amount'] for t in checkout_data['totals'] if t['type'] == 'total'), 0) / 100
    logger.agent(f"Final Negotiated Price: £{final_total_major:.2f} (Includes Tax, Shipping & Discounts)")

    # [AP2 Protocol] 3. Construct Payment Mandate (The Trust Proof)
    logger.ap2("Constructing AP2 Payment Mandate on FINAL total...")
    
    payment_payload = PaymentMandate(
        payment_mandate_contents=PaymentMandateContents(
            payment_mandate_id="pm_unique_123",
            payment_details_id=checkout_data['id'],
            payment_details_total=PaymentItem(
                label="Total",
                # Using the final negotiated total from the server
                amount=PaymentCurrencyAmount(currency="GBP", value=int(final_total_major * 100))
            ),
            payment_response=PaymentResponse(
                request_id="req_1",
                method_name="corporate_p_card"
            ),
            merchant_agent="supplier_b_agent"
        ),
        user_authorization="eyJhbGciOiJFUzI1NiJ9..signed_by_user_private_key" 
    )
    
    # [UCP Protocol] 4. Complete Checkout (Embedding AP2)
    logger.ucp("Finalizing UCP Transaction...")
    
    complete_req = CompleteRequestWithAp2(
        ap2=Ap2CompleteRequest(
            checkout_mandate=CheckoutMandate(root=payment_payload.user_authorization)
        )
    )
    
    complete_url = f"{target_url}/{checkout_data['id']}/complete"
    logger.ucp(f"POST {complete_url}", complete_req)

    final_res = requests.post(
        complete_url, 
        json=complete_req.model_dump(mode='json', exclude_none=True)
    )
    
    logger.step("5. RESULT")
    logger.ucp("Transaction Finalized:", final_res.json())
    
    return final_res.json()

# --- Agent Definition ---
agent = Agent(
    name="SelfHealingSupplyChainBot",
    model="gemini-3-flash-preview",
    instruction="""
    You are a Supply Chain Agent utilizing UCP and AP2 protocols.
    1. Check primary supplier.
    2. If down, Discover UCP backup suppliers.
    3. Generate AP2 Intent Mandate and check governance.
    4. Execute UCP Checkout negotiation (address/discount) and AP2 Payment Mandate.
    """,
    tools=[check_primary_supplier, discover_backup_suppliers, check_governance_and_approve, execute_ucp_transaction]
)

# --- Interactive Mode Logic ---

class InventoryManager:
    def __init__(self, initial_stock=100, threshold=20):
        self.inventory = initial_stock
        self.threshold = threshold

    def sell(self, amount):
        if amount > self.inventory:
            print(f"❌ Not enough stock! Current: {self.inventory}")
            return False
        self.inventory -= amount
        return True

    def restock(self, amount):
        self.inventory += amount
        print(f"📦 Restocked {amount} units. New Level: {self.inventory}")

    def is_critical(self):
        return self.inventory < self.threshold

async def trigger_restock_flow():
    print(f"\n{logger.RED}⚠ CRITICAL INVENTORY ALERT! Initiating Autonomous Restock Protocol...{logger.RESET}")
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, session_service=session_service, app_name="demo")
    
    session = await session_service.create_session(
        app_name="demo", 
        user_id="user"
    )
    
    # [A2A Protocol] Using strict types for user input
    user_msg = genai_types.Content(parts=[genai_types.Part(text="Check inventory for widget-x.")], role="user")
    
    async for event in runner.run_async(session_id=session.id, user_id="user", new_message=user_msg):
        pass
    
    return True # Assume success for demo flow

async def main():
    manager = InventoryManager(initial_stock=100, threshold=20)
    
    print("\n--- INTERACTIVE SUPPLY CHAIN DEMO ---")
    print(f"Initial Inventory: {manager.inventory}")
    print(f"Restock Threshold: < {manager.threshold}")
    print("-------------------------------------")

    while True:
        print(f"\n📊 Current Inventory: {logger.BOLD}{manager.inventory}{logger.RESET}")
        
        try:
            user_input = await asyncio.to_thread(input, "🛒 Enter units sold (or 'q' to quit): ")
            
            if user_input.lower() == 'q':
                break
                
            try:
                sold_amount = int(user_input)
            except ValueError:
                print("❌ Please enter a valid number.")
                continue

            if manager.sell(sold_amount):
                if manager.is_critical():
                    success = await trigger_restock_flow()
                    if success:
                        manager.restock(100)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    asyncio.run(main())