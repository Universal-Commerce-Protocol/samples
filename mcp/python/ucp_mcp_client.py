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
UCP MCP Client - Example client demonstrating MCP interaction with UCP server.

This module demonstrates how to connect to the UCP MCP server and perform
shopping operations using the MCP protocol. It showcases a complete "happy path"
user journey:

1. Connect to the MCP server
2. List available products
3. Create a checkout session
4. Add items to checkout
5. Set shipping address
6. Complete payment
7. Retrieve order confirmation

Usage:
    # Connect to a running MCP server via stdio:
    uv run ucp-mcp-client

    # Connect via HTTP:
    uv run ucp-mcp-client --transport http --url http://localhost:8000/mcp
"""

import argparse
import asyncio
import json
import logging
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def print_separator(title: str):
    """Print a visual separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def display_tools(session: ClientSession):
    """Display available tools from the server."""
    await print_separator("Available Tools")

    tools = await session.list_tools()
    for tool in tools.tools:
        print(f"  📦 {tool.name}")
        if tool.description:
            # Show first line of description
            desc = tool.description.split('\n')[0].strip()
            print(f"     {desc}")


async def display_resources(session: ClientSession):
    """Display available resources from the server."""
    await print_separator("Available Resources")

    # List static resources
    resources = await session.list_resources()
    for resource in resources.resources:
        print(f"  📄 {resource.uri}")
        if resource.name:
            print(f"     Name: {resource.name}")

    # List resource templates
    templates = await session.list_resource_templates()
    for template in templates.resourceTemplates:
        print(f"  📋 {template.uriTemplate} (template)")
        if template.name:
            print(f"     Name: {template.name}")


async def display_prompts(session: ClientSession):
    """Display available prompts from the server."""
    await print_separator("Available Prompts")

    prompts = await session.list_prompts()
    for prompt in prompts.prompts:
        print(f"  💬 {prompt.name}")
        if prompt.description:
            print(f"     {prompt.description}")


async def call_tool(session: ClientSession, name: str, arguments: dict[str, Any]) -> dict:
    """Call a tool and return the result as a dictionary."""
    logger.info(f"Calling tool: {name} with args: {arguments}")

    result = await session.call_tool(name, arguments=arguments)

    # Extract text content from result
    if result.content and len(result.content) > 0:
        content = result.content[0]
        if isinstance(content, TextContent):
            try:
                return json.loads(content.text)
            except json.JSONDecodeError:
                return {"text": content.text}

    # Try structured content
    if result.structuredContent:
        return result.structuredContent

    return {"raw": str(result)}


async def read_resource(session: ClientSession, uri: str) -> str:
    """Read a resource and return its content."""
    from pydantic import AnyUrl

    logger.info(f"Reading resource: {uri}")

    result = await session.read_resource(AnyUrl(uri))
    if result.contents and len(result.contents) > 0:
        content = result.contents[0]
        if isinstance(content, TextContent):
            return content.text
    return str(result)


async def run_happy_path(session: ClientSession):
    """Run a complete shopping flow demonstrating UCP MCP capabilities."""

    await print_separator("🛒 UCP MCP Client - Happy Path Demo")
    print("This demo walks through a complete shopping experience using MCP.\n")

    # Step 1: Initialize connection
    print("✅ Connected to UCP MCP Server")
    await session.initialize()

    # Step 2: Display server capabilities
    await display_tools(session)
    await display_resources(session)
    await display_prompts(session)

    # Step 3: Browse products
    await print_separator("Step 1: Browse Products")
    products = await call_tool(session, "list_products", {})

    if "products" in products:
        print(f"Found {products['total_count']} products:\n")
        for p in products["products"]:
            print(f"  🌸 {p['name']}")
            print(f"     ID: {p['id']}")
            print(f"     Price: ${p['price']:.2f}")
            print(f"     In Stock: {p['available_quantity']}")
            print()

    # Step 4: Get details for a specific product
    await print_separator("Step 2: Get Product Details")
    product_id = "prod_roses_red"
    product = await call_tool(session, "get_product", {"product_id": product_id})

    if "error" not in product:
        print(f"Product Details for {product['name']}:")
        print(f"  Description: {product['description']}")
        print(f"  Price: ${product['price']:.2f} {product.get('currency', 'USD')}")
        print(f"  Available: {product['available_quantity']} units")
        print(f"  Category: {product['category']}")

    # Step 5: Create checkout session
    await print_separator("Step 3: Create Checkout Session")
    checkout = await call_tool(session, "create_checkout", {})

    if "error" not in checkout:
        checkout_id = checkout["checkout_id"]
        print(f"✅ Created checkout session: {checkout_id}")
        print(f"   Status: {checkout['status']}")

        # Step 6: Add items to cart
        await print_separator("Step 4: Add Items to Cart")

        # Add roses
        result = await call_tool(session, "add_to_checkout", {
            "checkout_id": checkout_id,
            "product_id": "prod_roses_red",
            "quantity": 2
        })
        print(f"Added 2x Red Roses Bouquet")
        print(f"  Subtotal: ${result.get('subtotal', 0):.2f}")

        # Add sunflowers
        result = await call_tool(session, "add_to_checkout", {
            "checkout_id": checkout_id,
            "product_id": "prod_sunflowers",
            "quantity": 1
        })
        print(f"Added 1x Sunflower Arrangement")
        print(f"  Subtotal: ${result.get('subtotal', 0):.2f}")
        print(f"  Tax: ${result.get('tax', 0):.2f}")
        print(f"  Total: ${result.get('total', 0):.2f}")

        # Step 7: Set shipping address
        await print_separator("Step 5: Set Shipping Address")
        result = await call_tool(session, "set_shipping_address", {
            "checkout_id": checkout_id,
            "name": "Jane Doe",
            "street": "123 Main Street",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94102",
            "country": "US"
        })
        print("✅ Shipping address set:")
        addr = result.get("shipping_address", {})
        print(f"   {addr.get('name')}")
        print(f"   {addr.get('street')}")
        print(f"   {addr.get('city')}, {addr.get('state')} {addr.get('postal_code')}")
        print(f"\n   Shipping Cost: ${result.get('shipping_cost', 0):.2f}")
        print(f"   Updated Total: ${result.get('total', 0):.2f}")

        # Step 8: Review checkout
        await print_separator("Step 6: Review Checkout")
        checkout_state = await call_tool(session, "get_checkout", {
            "checkout_id": checkout_id
        })

        print("Current Checkout State:")
        print(f"  Status: {checkout_state.get('status')}")
        print(f"\n  Items:")
        for item in checkout_state.get("line_items", []):
            print(f"    - {item['quantity']}x {item['name']}: ${item['total_price']:.2f}")
        print(f"\n  Subtotal: ${checkout_state.get('subtotal', 0):.2f}")
        print(f"  Tax: ${checkout_state.get('tax', 0):.2f}")
        print(f"  Shipping: ${checkout_state.get('shipping', 0):.2f}")
        print(f"  ──────────────")
        print(f"  TOTAL: ${checkout_state.get('total', 0):.2f} {checkout_state.get('currency', 'USD')}")

        # Step 9: Complete payment
        await print_separator("Step 7: Complete Payment")
        print("Processing payment...")

        order = await call_tool(session, "complete_payment", {
            "checkout_id": checkout_id,
            "payment_method": "mock_credit_card"
        })

        if "error" not in order:
            print("\n🎉 Order Placed Successfully!")
            print(f"   Order ID: {order['order_id']}")
            print(f"   Status: {order['status']}")
            print(f"   Total: ${order['total']:.2f}")
            print(f"   Tracking: {order['tracking_number']}")
            print(f"\n   {order['message']}")

            # Step 10: Retrieve order
            await print_separator("Step 8: Check Order Status")
            order_details = await call_tool(session, "get_order", {
                "order_id": order["order_id"]
            })

            print(f"Order {order_details['order_id']}:")
            print(f"  Status: {order_details['status']}")
            print(f"  Created: {order_details['created_at']}")
            print(f"  Payment: {order_details['payment_method']}")
            print(f"  Tracking: {order_details['tracking_number']}")
        else:
            print(f"❌ Payment failed: {order['error']}")
    else:
        print(f"❌ Failed to create checkout: {checkout['error']}")

    # Step 11: Read discovery profile resource
    await print_separator("Bonus: Read Discovery Profile")
    profile = await read_resource(session, "ucp://discovery/profile")
    print("UCP Discovery Profile:")
    print(json.dumps(json.loads(profile), indent=2))

    await print_separator("🎉 Demo Complete!")
    print("This demo showed the complete UCP shopping flow via MCP:")
    print("  1. Browsed product catalog")
    print("  2. Created checkout session")
    print("  3. Added items to cart")
    print("  4. Set shipping address")
    print("  5. Completed payment")
    print("  6. Retrieved order confirmation")
    print("\nThe same flow can be used by AI agents to enable")
    print("conversational commerce experiences!")


async def run_stdio_client():
    """Connect to the server using stdio transport."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "ucp-mcp-server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await run_happy_path(session)


async def run_http_client(url: str):
    """Connect to the server using HTTP transport."""
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await run_happy_path(session)


def main():
    """Entry point for the UCP MCP Client."""
    parser = argparse.ArgumentParser(
        description="UCP MCP Client - Demonstrate shopping via MCP"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mechanism (default: stdio)",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/mcp",
        help="Server URL for HTTP transport (default: http://localhost:8000/mcp)",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(run_stdio_client())
    else:
        asyncio.run(run_http_client(args.url))


if __name__ == "__main__":
    main()
