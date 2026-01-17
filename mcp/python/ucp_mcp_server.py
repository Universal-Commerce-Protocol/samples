#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
UCP MCP Server - Model Context Protocol implementation for Universal Commerce Protocol.

This module implements an MCP server that exposes UCP shopping capabilities as tools
and resources. It enables AI agents to interact with UCP-compliant merchants through
a standardized protocol, supporting operations like:

- Product discovery and catalog browsing
- Checkout session management
- Payment processing
- Order tracking

The server can operate in two modes:
1. Standalone mode with mock data for testing/development
2. Connected mode proxying to a real UCP REST server

Usage:
    # Run with stdio transport (for LLM integration):
    uv run ucp-mcp-server

    # Run with streamable HTTP transport (for web clients):
    uv run ucp-mcp-server --transport http --port 8000
"""

import argparse
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Mock Data Models (for standalone testing)
# ============================================================================

@dataclass
class Product:
    """Represents a product in the catalog."""
    id: str
    name: str
    description: str
    price: float
    currency: str = "USD"
    available_quantity: int = 100
    category: str = "general"
    image_url: Optional[str] = None


@dataclass
class LineItem:
    """Represents an item in a checkout session."""
    product_id: str
    name: str
    quantity: int
    unit_price: float
    total_price: float


@dataclass
class CheckoutSession:
    """Represents a checkout session."""
    id: str
    status: str  # "open", "pending_payment", "completed", "cancelled"
    line_items: list[LineItem] = field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    shipping: float = 0.0
    total: float = 0.0
    currency: str = "USD"
    shipping_address: Optional[dict] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Order:
    """Represents a completed order."""
    id: str
    checkout_id: str
    status: str  # "confirmed", "processing", "shipped", "delivered", "cancelled"
    line_items: list[LineItem] = field(default_factory=list)
    total: float = 0.0
    currency: str = "USD"
    shipping_address: Optional[dict] = None
    payment_method: str = "mock_payment"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tracking_number: Optional[str] = None


# ============================================================================
# Mock Data Store
# ============================================================================

class MockStore:
    """In-memory mock store for standalone testing."""

    def __init__(self):
        self.products: dict[str, Product] = {}
        self.checkout_sessions: dict[str, CheckoutSession] = {}
        self.orders: dict[str, Order] = {}
        self._initialize_sample_products()

    def _initialize_sample_products(self):
        """Initialize with sample flower shop products (matching REST sample)."""
        sample_products = [
            Product(
                id="prod_roses_red",
                name="Red Roses Bouquet",
                description="A beautiful bouquet of 12 fresh red roses",
                price=49.99,
                category="bouquets",
                available_quantity=50,
            ),
            Product(
                id="prod_tulips_mixed",
                name="Mixed Tulips",
                description="Colorful assortment of 15 spring tulips",
                price=34.99,
                category="bouquets",
                available_quantity=30,
            ),
            Product(
                id="prod_orchid_white",
                name="White Orchid Plant",
                description="Elegant white phalaenopsis orchid in ceramic pot",
                price=79.99,
                category="plants",
                available_quantity=15,
            ),
            Product(
                id="prod_sunflowers",
                name="Sunflower Arrangement",
                description="Bright sunflower arrangement with greenery",
                price=44.99,
                category="arrangements",
                available_quantity=25,
            ),
            Product(
                id="prod_lily_stargazer",
                name="Stargazer Lilies",
                description="Fragrant pink stargazer lily bouquet",
                price=54.99,
                category="bouquets",
                available_quantity=20,
            ),
        ]
        for product in sample_products:
            self.products[product.id] = product


# Global store instance (for standalone mode)
mock_store = MockStore()


# ============================================================================
# MCP Server Configuration
# ============================================================================

mcp = FastMCP(
    name="UCP Shopping Service",
    instructions="""
    This MCP server provides access to UCP (Universal Commerce Protocol) shopping
    capabilities. You can:

    1. Browse Products: Use list_products or get_product to explore the catalog
    2. Create Checkout: Use create_checkout to start a shopping session
    3. Add Items: Use add_to_checkout to add products to your cart
    4. Update Address: Use set_shipping_address to configure delivery
    5. Complete Purchase: Use complete_payment to finalize the order
    6. Track Orders: Use get_order to check order status

    Start by listing available products, then guide the user through checkout.
    """,
)


# ============================================================================
# Resources - Data Exposure (Read-only access to UCP data)
# ============================================================================

@mcp.resource("ucp://catalog/products")
def get_catalog() -> str:
    """
    Get the complete product catalog.

    Returns a JSON array of all available products with their details
    including name, description, price, and availability.
    """
    products = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "currency": p.currency,
            "available_quantity": p.available_quantity,
            "category": p.category,
        }
        for p in mock_store.products.values()
    ]
    return json.dumps(products, indent=2)


@mcp.resource("ucp://catalog/products/{product_id}")
def get_product_resource(product_id: str) -> str:
    """
    Get details for a specific product.

    Returns product information including name, description, price,
    and current availability.
    """
    product = mock_store.products.get(product_id)
    if not product:
        return json.dumps({"error": f"Product '{product_id}' not found"})

    return json.dumps({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "available_quantity": product.available_quantity,
        "category": product.category,
    }, indent=2)


@mcp.resource("ucp://checkout/{session_id}")
def get_checkout_resource(session_id: str) -> str:
    """
    Get the current state of a checkout session.

    Returns the complete checkout state including items, totals,
    and shipping information.
    """
    session = mock_store.checkout_sessions.get(session_id)
    if not session:
        return json.dumps({"error": f"Checkout session '{session_id}' not found"})

    return json.dumps({
        "id": session.id,
        "status": session.status,
        "line_items": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in session.line_items
        ],
        "subtotal": session.subtotal,
        "tax": session.tax,
        "shipping": session.shipping,
        "total": session.total,
        "currency": session.currency,
        "shipping_address": session.shipping_address,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }, indent=2)


@mcp.resource("ucp://orders/{order_id}")
def get_order_resource(order_id: str) -> str:
    """
    Get the status and details of an order.

    Returns complete order information including status,
    items, and tracking details if available.
    """
    order = mock_store.orders.get(order_id)
    if not order:
        return json.dumps({"error": f"Order '{order_id}' not found"})

    return json.dumps({
        "id": order.id,
        "checkout_id": order.checkout_id,
        "status": order.status,
        "line_items": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in order.line_items
        ],
        "total": order.total,
        "currency": order.currency,
        "shipping_address": order.shipping_address,
        "payment_method": order.payment_method,
        "created_at": order.created_at,
        "tracking_number": order.tracking_number,
    }, indent=2)


@mcp.resource("ucp://discovery/profile")
def get_discovery_profile() -> str:
    """
    Get the UCP discovery profile for this merchant.

    Returns the merchant's UCP capabilities, supported services,
    and available extensions following the UCP specification.
    """
    return json.dumps({
        "ucp": {
            "version": "2026-01-11",
            "services": {
                "dev.ucp.shopping": {
                    "version": "2026-01-11",
                    "spec": "https://ucp.dev/specs/shopping",
                    "mcp": {
                        "endpoint": "stdio://ucp-mcp-server",
                    },
                    "rest": None,
                    "a2a": None,
                }
            },
            "capabilities": [
                {
                    "name": "dev.ucp.shopping.checkout",
                    "version": "2026-01-11",
                    "spec": "https://ucp.dev/specs/shopping/checkout",
                },
                {
                    "name": "dev.ucp.shopping.fulfillment",
                    "version": "2026-01-11",
                    "spec": "https://ucp.dev/specs/shopping/fulfillment",
                },
            ]
        }
    }, indent=2)


# ============================================================================
# Tools - Actions (Operations with side effects)
# ============================================================================

@mcp.tool()
async def list_products(
    category: str | None = None,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    List available products from the catalog.

    Args:
        category: Optional filter by category (e.g., "bouquets", "plants", "arrangements")

    Returns:
        List of products with their details and availability.
    """
    if ctx:
        await ctx.info("Fetching product catalog...")

    products = list(mock_store.products.values())

    if category:
        products = [p for p in products if p.category.lower() == category.lower()]

    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "currency": p.currency,
                "available_quantity": p.available_quantity,
                "category": p.category,
            }
            for p in products
        ],
        "total_count": len(products),
    }


@mcp.tool()
async def get_product(
    product_id: str,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Get detailed information about a specific product.

    Args:
        product_id: The unique identifier of the product.

    Returns:
        Product details including availability and pricing.
    """
    product = mock_store.products.get(product_id)

    if not product:
        return {"error": f"Product '{product_id}' not found"}

    if ctx:
        await ctx.info(f"Found product: {product.name}")

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "available_quantity": product.available_quantity,
        "category": product.category,
        "in_stock": product.available_quantity > 0,
    }


@mcp.tool()
async def create_checkout(
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Create a new checkout session.

    Creates an empty checkout session that can be populated with items.
    Use add_to_checkout to add products to the session.

    Returns:
        The new checkout session with its unique ID.
    """
    session_id = f"checkout_{uuid.uuid4().hex[:12]}"
    session = CheckoutSession(id=session_id, status="open")
    mock_store.checkout_sessions[session_id] = session

    if ctx:
        await ctx.info(f"Created checkout session: {session_id}")

    return {
        "checkout_id": session.id,
        "status": session.status,
        "message": "Checkout session created. Use add_to_checkout to add items.",
    }


@mcp.tool()
async def add_to_checkout(
    checkout_id: str,
    product_id: str,
    quantity: int = 1,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Add a product to an existing checkout session.

    Args:
        checkout_id: The checkout session ID.
        product_id: The product to add.
        quantity: Number of items to add (default: 1).

    Returns:
        Updated checkout state with current totals.
    """
    session = mock_store.checkout_sessions.get(checkout_id)
    if not session:
        return {"error": f"Checkout session '{checkout_id}' not found"}

    if session.status != "open":
        return {"error": f"Checkout session is {session.status}, cannot modify"}

    product = mock_store.products.get(product_id)
    if not product:
        return {"error": f"Product '{product_id}' not found"}

    if quantity > product.available_quantity:
        return {
            "error": f"Insufficient stock. Available: {product.available_quantity}"
        }

    # Check if product already in cart, update quantity
    existing_item = next(
        (item for item in session.line_items if item.product_id == product_id),
        None
    )

    if existing_item:
        existing_item.quantity += quantity
        existing_item.total_price = existing_item.quantity * existing_item.unit_price
    else:
        line_item = LineItem(
            product_id=product.id,
            name=product.name,
            quantity=quantity,
            unit_price=product.price,
            total_price=product.price * quantity,
        )
        session.line_items.append(line_item)

    # Recalculate totals
    session.subtotal = sum(item.total_price for item in session.line_items)
    session.tax = round(session.subtotal * 0.08, 2)  # 8% tax
    session.total = round(session.subtotal + session.tax + session.shipping, 2)
    session.updated_at = datetime.utcnow().isoformat()

    if ctx:
        await ctx.info(f"Added {quantity}x {product.name} to checkout")

    return {
        "checkout_id": session.id,
        "status": session.status,
        "items_count": len(session.line_items),
        "subtotal": session.subtotal,
        "tax": session.tax,
        "shipping": session.shipping,
        "total": session.total,
        "currency": session.currency,
    }


@mcp.tool()
async def remove_from_checkout(
    checkout_id: str,
    product_id: str,
    quantity: int | None = None,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Remove a product from the checkout session.

    Args:
        checkout_id: The checkout session ID.
        product_id: The product to remove.
        quantity: Number of items to remove. If None, removes all.

    Returns:
        Updated checkout state with current totals.
    """
    session = mock_store.checkout_sessions.get(checkout_id)
    if not session:
        return {"error": f"Checkout session '{checkout_id}' not found"}

    if session.status != "open":
        return {"error": f"Checkout session is {session.status}, cannot modify"}

    item_index = next(
        (i for i, item in enumerate(session.line_items) if item.product_id == product_id),
        None
    )

    if item_index is None:
        return {"error": f"Product '{product_id}' not in checkout"}

    item = session.line_items[item_index]

    if quantity is None or quantity >= item.quantity:
        session.line_items.pop(item_index)
        removed_quantity = item.quantity
    else:
        item.quantity -= quantity
        item.total_price = item.quantity * item.unit_price
        removed_quantity = quantity

    # Recalculate totals
    session.subtotal = sum(i.total_price for i in session.line_items)
    session.tax = round(session.subtotal * 0.08, 2)
    session.total = round(session.subtotal + session.tax + session.shipping, 2)
    session.updated_at = datetime.utcnow().isoformat()

    if ctx:
        await ctx.info(f"Removed {removed_quantity}x {item.name} from checkout")

    return {
        "checkout_id": session.id,
        "status": session.status,
        "items_count": len(session.line_items),
        "subtotal": session.subtotal,
        "tax": session.tax,
        "shipping": session.shipping,
        "total": session.total,
        "currency": session.currency,
    }


@mcp.tool()
async def set_shipping_address(
    checkout_id: str,
    street: str,
    city: str,
    state: str,
    postal_code: str,
    country: str = "US",
    name: str | None = None,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Set the shipping address for a checkout session.

    Args:
        checkout_id: The checkout session ID.
        street: Street address.
        city: City name.
        state: State/Province code.
        postal_code: Postal/ZIP code.
        country: Country code (default: "US").
        name: Recipient name (optional).

    Returns:
        Updated checkout state with shipping calculated.
    """
    session = mock_store.checkout_sessions.get(checkout_id)
    if not session:
        return {"error": f"Checkout session '{checkout_id}' not found"}

    if session.status not in ("open", "pending_payment"):
        return {"error": f"Checkout session is {session.status}, cannot modify address"}

    session.shipping_address = {
        "name": name,
        "street": street,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
    }

    # Calculate shipping based on location (mock logic)
    if country != "US":
        session.shipping = 29.99
    elif state in ("AK", "HI"):
        session.shipping = 19.99
    else:
        session.shipping = 9.99

    session.total = round(session.subtotal + session.tax + session.shipping, 2)
    session.updated_at = datetime.utcnow().isoformat()

    if ctx:
        await ctx.info(f"Set shipping address to {city}, {state}")

    return {
        "checkout_id": session.id,
        "status": session.status,
        "shipping_address": session.shipping_address,
        "shipping_cost": session.shipping,
        "subtotal": session.subtotal,
        "tax": session.tax,
        "total": session.total,
        "currency": session.currency,
    }


@mcp.tool()
async def get_checkout(
    checkout_id: str,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Get the current state of a checkout session.

    Args:
        checkout_id: The checkout session ID.

    Returns:
        Complete checkout state including items, totals, and shipping info.
    """
    session = mock_store.checkout_sessions.get(checkout_id)
    if not session:
        return {"error": f"Checkout session '{checkout_id}' not found"}

    return {
        "checkout_id": session.id,
        "status": session.status,
        "line_items": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in session.line_items
        ],
        "subtotal": session.subtotal,
        "tax": session.tax,
        "shipping": session.shipping,
        "total": session.total,
        "currency": session.currency,
        "shipping_address": session.shipping_address,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@mcp.tool()
async def complete_payment(
    checkout_id: str,
    payment_method: str = "mock_credit_card",
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Complete payment and create an order.

    Args:
        checkout_id: The checkout session ID.
        payment_method: Payment method identifier (e.g., "mock_credit_card", "mock_paypal").

    Returns:
        Order confirmation with order ID and details.
    """
    session = mock_store.checkout_sessions.get(checkout_id)
    if not session:
        return {"error": f"Checkout session '{checkout_id}' not found"}

    if session.status == "completed":
        return {"error": "Checkout session already completed"}

    if not session.line_items:
        return {"error": "Cannot complete payment with empty cart"}

    if not session.shipping_address:
        return {"error": "Shipping address required before payment"}

    # Validate inventory
    for item in session.line_items:
        product = mock_store.products.get(item.product_id)
        if not product or product.available_quantity < item.quantity:
            return {"error": f"Insufficient stock for {item.name}"}

    if ctx:
        await ctx.report_progress(0.3, 1.0, "Processing payment...")

    # Simulate payment processing (in real implementation, call payment provider)
    await asyncio.sleep(0.5)  # Simulate processing time

    if ctx:
        await ctx.report_progress(0.6, 1.0, "Payment accepted, creating order...")

    # Create order
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    order = Order(
        id=order_id,
        checkout_id=checkout_id,
        status="confirmed",
        line_items=session.line_items.copy(),
        total=session.total,
        currency=session.currency,
        shipping_address=session.shipping_address,
        payment_method=payment_method,
        tracking_number=f"TRK{uuid.uuid4().hex[:10].upper()}",
    )
    mock_store.orders[order_id] = order

    # Update inventory
    for item in session.line_items:
        product = mock_store.products.get(item.product_id)
        if product:
            product.available_quantity -= item.quantity

    # Update checkout status
    session.status = "completed"
    session.updated_at = datetime.utcnow().isoformat()

    if ctx:
        await ctx.report_progress(1.0, 1.0, "Order created successfully!")
        await ctx.info(f"Order {order_id} created successfully")

    return {
        "order_id": order.id,
        "checkout_id": checkout_id,
        "status": order.status,
        "total": order.total,
        "currency": order.currency,
        "tracking_number": order.tracking_number,
        "shipping_address": order.shipping_address,
        "items_count": len(order.line_items),
        "message": "Order placed successfully! You will receive a confirmation email shortly.",
    }


@mcp.tool()
async def get_order(
    order_id: str,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Get the status and details of an order.

    Args:
        order_id: The order ID.

    Returns:
        Order details including status, items, and tracking info.
    """
    order = mock_store.orders.get(order_id)
    if not order:
        return {"error": f"Order '{order_id}' not found"}

    if ctx:
        await ctx.info(f"Retrieved order {order_id}: {order.status}")

    return {
        "order_id": order.id,
        "checkout_id": order.checkout_id,
        "status": order.status,
        "line_items": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in order.line_items
        ],
        "total": order.total,
        "currency": order.currency,
        "shipping_address": order.shipping_address,
        "payment_method": order.payment_method,
        "tracking_number": order.tracking_number,
        "created_at": order.created_at,
    }


@mcp.tool()
async def cancel_checkout(
    checkout_id: str,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Cancel an open checkout session.

    Args:
        checkout_id: The checkout session ID to cancel.

    Returns:
        Confirmation of cancellation.
    """
    session = mock_store.checkout_sessions.get(checkout_id)
    if not session:
        return {"error": f"Checkout session '{checkout_id}' not found"}

    if session.status == "completed":
        return {"error": "Cannot cancel a completed checkout"}

    if session.status == "cancelled":
        return {"error": "Checkout session already cancelled"}

    session.status = "cancelled"
    session.updated_at = datetime.utcnow().isoformat()

    if ctx:
        await ctx.info(f"Cancelled checkout session {checkout_id}")

    return {
        "checkout_id": session.id,
        "status": session.status,
        "message": "Checkout session cancelled successfully",
    }


# ============================================================================
# Prompts - Reusable conversation patterns
# ============================================================================

@mcp.prompt(title="Shopping Assistant Introduction")
def shopping_intro() -> str:
    """Generate an introduction for the shopping assistant."""
    return """You are a helpful shopping assistant for a flower shop.
You can help customers:
1. Browse our product catalog (use list_products)
2. Get details about specific products (use get_product)
3. Create a checkout session (use create_checkout)
4. Add items to their cart (use add_to_checkout)
5. Set shipping address (use set_shipping_address)
6. Complete their purchase (use complete_payment)
7. Track their orders (use get_order)

Start by asking what the customer is looking for today."""


@mcp.prompt(title="Order Confirmation")
def order_confirmation(order_id: str, total: str) -> str:
    """Generate an order confirmation message."""
    return f"""The customer's order has been placed successfully!

Order ID: {order_id}
Total: {total}

Please confirm the order details with the customer and let them know:
1. They will receive a confirmation email shortly
2. Their order will be processed within 1-2 business days
3. They can track their order using the order ID

Ask if there's anything else you can help them with."""


@mcp.prompt(title="Product Recommendation")
def recommend_products(occasion: str) -> str:
    """Generate product recommendations for an occasion."""
    return f"""The customer is looking for flowers for: {occasion}

Based on this occasion, use the list_products tool to find suitable options,
then recommend 2-3 products that would be perfect for this occasion.

Consider:
- Price range appropriate for the occasion
- Flower meanings and symbolism
- Seasonal availability

Provide personalized recommendations with reasons why each would be a good choice."""


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Entry point for the UCP MCP Server."""
    parser = argparse.ArgumentParser(
        description="UCP MCP Server - Model Context Protocol for Universal Commerce"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport mechanism (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP/SSE transport (default: 8000)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP/SSE transport (default: 0.0.0.0)",
    )

    args = parser.parse_args()

    logger.info(f"Starting UCP MCP Server with {args.transport} transport")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    elif args.transport == "sse":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
