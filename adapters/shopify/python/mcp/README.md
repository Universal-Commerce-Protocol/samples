# MCP Server for UCP Shopify Adapter (Mock)

This MCP server exposes the mock Shopify adapter (`http://127.0.0.1:8183`) as **MCP tools** so agent clients (Claude Desktop, etc.) can perform an end-to-end shopping flow: browse → checkout → set shipping → complete → fetch order → simulate shipping.

This MCP server is a bridge: it calls the REST adapter under the hood.

---

## Prerequisites

1. The REST adapter must be running:

```bash
cd samples/adapters/shopify/python
source .venv/bin/activate
ucp-shopify-adapter
```

Default base URL: `http://127.0.0.1:8183`

---

## Install & Run (MCP Server)

From repo root:

```bash
cd samples/adapters/shopify/python/mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the MCP server:

```bash
ADAPTER_BASE_URL=http://127.0.0.1:8183 ucp-shopify-adapter-mcp
```

If `ADAPTER_BASE_URL` is not set, the MCP server should default to `http://127.0.0.1:8183` (keep it explicit for consistency in demos).

---

## Claude Desktop Configuration

Add an entry to Claude Desktop config (path varies by OS). On macOS the folder is commonly:

```
~/Library/Application Support/Claude/
```

In `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ucp-shopify-adapter": {
      "command": "bash",
      "args": ["-lc", "ADAPTER_BASE_URL=http://127.0.0.1:8183 ucp-shopify-adapter-mcp"],
      "cwd": "/Users/bilalahmad/ucp_lab/samples/adapters/shopify/python/mcp"
    }
  }
}
```

- `cwd` must be set to your local path of the mcp directory.
- The command uses `bash -lc` so env vars resolve reliably.

**Restart Claude Desktop after editing the config.**

---

## Available Tools (Expected)

The tool names below match the end-to-end test that succeeded in Claude Desktop:

**Product browsing**
- `discovery_profile`
- `list_products`
- `get_product`

**Checkout & purchase**
- `create_checkout`
- `set_shipping`
- `complete_checkout`

**Order management**
- `get_order`

**Testing**
- `simulate_shipping` (requires the correct simulation secret)

---

## Suggested Claude Test Prompt

Use something like this in Claude:

1. List products
2. Create a checkout with the cheapest item and discount `10OFF`
3. Set shipping to:
   - 10 Downing St, London, SW1A 2AA, GB
   - choose `std-ship`
4. Complete checkout with token `success_token`
5. Get order
6. Simulate shipping with `letmein`
7. Get order again and confirm `fulfillment.events` includes a shipped event

---

## Expected Behaviors / Guardrails

### Simulation secret

- Correct secret (default `letmein`) → success
- Wrong secret → 403 FORBIDDEN

### Idempotency

The REST adapter enforces idempotency:
- Same `idempotency-key` + same payload → same response
- Same `idempotency-key` + different payload → 409 IDEMPOTENCY_CONFLICT

The MCP tools should surface these failures transparently.

---

## Troubleshooting

### "Tools show up but calls fail"

- Confirm the adapter is reachable:

```bash
curl -s http://127.0.0.1:8183/.well-known/ucp | python -m json.tool
```

- Confirm `ADAPTER_BASE_URL` points to the running adapter.

### Port already in use

- Adapter uses 8183. Stop the process or change the port in the adapter and update `ADAPTER_BASE_URL`.

---

## Security Note

This sample includes a testing endpoint:
- `POST /testing/simulate-shipping/{id}`

It is protected by `Simulation-Secret` and is intended for local testing only.