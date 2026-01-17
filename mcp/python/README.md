<!--
   Copyright 2026 UCP Authors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
-->

# UCP MCP Sample (Python)

This is a reference implementation of a UCP Merchant Server using the
[Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It demonstrates
how to expose UCP shopping capabilities as MCP tools and resources, enabling
AI agents to perform commerce operations through a standardized protocol.

## Overview

The Model Context Protocol (MCP) is an open standard for connecting AI systems
with external data sources and tools. This sample shows how UCP's shopping
capabilities can be exposed via MCP, allowing LLMs and AI agents to:

- Browse product catalogs
- Manage checkout sessions
- Process payments
- Track orders

### Why MCP for UCP?

| Feature | REST API | MCP |
|---------|----------|-----|
| Integration | HTTP endpoints, OpenAPI | Standardized protocol |
| AI Compatibility | Requires custom tooling | Native LLM integration |
| Discovery | `/.well-known/ucp` | Built-in capability listing |
| Interactivity | Request/Response | Bidirectional, streaming |
| Context | Stateless | Session-aware |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Agent / LLM                          │
│                    (Claude, GPT, Gemini, etc.)                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MCP Protocol
                              │ (stdio / HTTP / SSE)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      UCP MCP Server                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │     Tools       │  │   Resources     │  │    Prompts      │ │
│  │ ─────────────── │  │ ─────────────── │  │ ─────────────── │ │
│  │ • list_products │  │ • catalog       │  │ • shopping_intro│ │
│  │ • get_product   │  │ • checkout/{id} │  │ • order_confirm │ │
│  │ • create_checkout│ │ • orders/{id}   │  │ • recommend     │ │
│  │ • add_to_checkout│ │ • discovery     │  │                 │ │
│  │ • set_shipping  │  │                 │  │                 │ │
│  │ • complete_pay  │  │                 │  │                 │ │
│  │ • get_order     │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Mock Data Store / Real UCP Server             │
│                   (Products, Checkout, Orders)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager

## Quick Start

### 1. Install Dependencies

```bash
cd mcp/python
uv sync
```

### 2. Run the MCP Server

**Using stdio transport (for LLM integration):**

```bash
uv run ucp-mcp-server
```

**Using HTTP transport (for web clients):**

```bash
uv run ucp-mcp-server --transport http --port 8000
```

The server will start and expose UCP capabilities via the MCP protocol.

### 3. Run the Example Client

In a separate terminal, run the demo client that performs a complete shopping
flow:

```bash
uv run ucp-mcp-client
```

This demonstrates:
1. Connecting to the MCP server
2. Listing available products
3. Creating a checkout session
4. Adding items to cart
5. Setting shipping address
6. Completing payment
7. Retrieving order confirmation

## Project Structure

```
mcp/python/
├── pyproject.toml       # Project configuration and dependencies
├── README.md            # This documentation
├── ucp_mcp_server.py    # MCP server implementation
└── ucp_mcp_client.py    # Example client demonstrating usage
```

## Server Components

### Tools (Actions with Side Effects)

Tools are functions that can modify state, similar to POST/PUT/DELETE endpoints:

| Tool | Description |
|------|-------------|
| `list_products` | List available products, optionally filtered by category |
| `get_product` | Get detailed information about a specific product |
| `create_checkout` | Create a new checkout session |
| `add_to_checkout` | Add a product to an existing checkout |
| `remove_from_checkout` | Remove a product from checkout |
| `set_shipping_address` | Set the delivery address |
| `get_checkout` | Get current checkout state |
| `complete_payment` | Process payment and create order |
| `get_order` | Retrieve order details and status |
| `cancel_checkout` | Cancel an open checkout session |

### Resources (Read-Only Data)

Resources provide read-only access to data, similar to GET endpoints:

| Resource URI | Description |
|--------------|-------------|
| `ucp://catalog/products` | Complete product catalog |
| `ucp://catalog/products/{id}` | Specific product details |
| `ucp://checkout/{session_id}` | Checkout session state |
| `ucp://orders/{order_id}` | Order details and tracking |
| `ucp://discovery/profile` | UCP discovery profile |

### Prompts (Conversation Templates)

Prompts provide reusable conversation patterns for AI agents:

| Prompt | Description |
|--------|-------------|
| `shopping_intro` | Introduction for shopping assistant |
| `order_confirmation` | Order confirmation message template |
| `recommend_products` | Product recommendations for occasions |

## Integration with Claude Desktop

To use this MCP server with Claude Desktop, add the following to your
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ucp-shopping": {
      "command": "uv",
      "args": ["run", "ucp-mcp-server"],
      "cwd": "/path/to/samples/mcp/python"
    }
  }
}
```

After restarting Claude Desktop, you can ask Claude to help you shop:

> "I'm looking for flowers for Mother's Day. Can you help me find something nice?"

Claude will use the MCP tools to browse products and guide you through checkout.

## Integration with Other LLM Clients

### Using HTTP Transport

Start the server with HTTP transport:

```bash
uv run ucp-mcp-server --transport http --port 8000
```

Then connect your client to `http://localhost:8000/mcp`.

### Using SSE Transport

For Server-Sent Events (legacy compatibility):

```bash
uv run ucp-mcp-server --transport sse --port 8000
```

## Example Interaction

Here's an example of how an AI agent might use the MCP tools:

```
User: I'd like to order some flowers for a birthday

Agent: I'd be happy to help you find flowers for a birthday! Let me show you
       what we have available.

       [Calls list_products()]

       We have these beautiful options:
       1. Red Roses Bouquet - $49.99
       2. Mixed Tulips - $34.99
       3. Sunflower Arrangement - $44.99
       4. Stargazer Lilies - $54.99

       Which would you like to add to your cart?

User: Let's go with the stargazer lilies

Agent: Great choice! Stargazer lilies have a beautiful fragrance.

       [Calls create_checkout()]
       [Calls add_to_checkout(product_id="prod_lily_stargazer", quantity=1)]

       I've added 1 Stargazer Lilies to your cart.

       Current total: $54.99 + $4.40 tax = $59.39

       Would you like to add anything else, or shall we proceed to checkout?

User: That's all. Ship it to 456 Oak Ave, Seattle WA 98101

Agent: [Calls set_shipping_address(...)]

       Your shipping address is set. Here's your order summary:

       Items: 1x Stargazer Lilies - $54.99
       Tax: $4.40
       Shipping: $9.99
       Total: $69.38

       Ready to complete your purchase?

User: Yes, please complete the order

Agent: [Calls complete_payment()]

       🎉 Order placed successfully!

       Order ID: order_a1b2c3d4e5f6
       Tracking: TRKABCDEF1234

       You'll receive a confirmation email shortly. The flowers will be
       delivered within 1-2 business days.
```

## Development

### Running Tests

```bash
uv run pytest
```

### Adding New Tools

To add a new tool, use the `@mcp.tool()` decorator:

```python
@mcp.tool()
async def my_new_tool(
    param1: str,
    param2: int = 10,
    ctx: Context[ServerSession, None] | None = None
) -> dict:
    """
    Description of what the tool does.

    Args:
        param1: Description of first parameter.
        param2: Description of optional parameter (default: 10).

    Returns:
        Dictionary with result data.
    """
    if ctx:
        await ctx.info("Performing operation...")

    # Implementation
    return {"result": "success"}
```

### Adding New Resources

To add a new resource, use the `@mcp.resource()` decorator:

```python
@mcp.resource("ucp://my-resource/{param}")
def my_resource(param: str) -> str:
    """
    Description of the resource.

    Returns JSON data for the specified parameter.
    """
    data = {"param": param, "info": "..."}
    return json.dumps(data, indent=2)
```

## Connecting to Real UCP Server

This sample includes a mock data store for standalone testing. To connect to
a real UCP REST server, you would modify the tool implementations to make HTTP
calls:

```python
import httpx

UCP_SERVER_URL = "http://localhost:8182"

@mcp.tool()
async def list_products(category: str | None = None) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{UCP_SERVER_URL}/products",
            params={"category": category} if category else None
        )
        return response.json()
```

## Related Resources

- [UCP Specification](https://github.com/Universal-Commerce-Protocol/ucp)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [REST Sample](../rest/python/server/README.md)
- [A2A Sample](../a2a/README.md)

## Disclaimer

This is an example implementation for demonstration purposes and is not
intended for production use without additional security, error handling,
and integration with real payment providers.
