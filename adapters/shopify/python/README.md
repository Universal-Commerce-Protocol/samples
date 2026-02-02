# UCP Shopify Adapter (Mock) + MCP Bridge

This sample provides:

1. **UCP-like REST adapter (mock)** that exposes a minimal shopping API compatible with UCP-style flows:
   - Discovery profile: `GET /.well-known/ucp`
   - Catalog: `GET /products`, `GET /products/{id}`
   - Checkout: `POST /checkout-sessions`, `GET /checkout-sessions/{id}`, `PUT /checkout-sessions/{id}`, `POST /checkout-sessions/{id}/complete`
   - Orders: `GET /orders/{id}`
   - Testing: `POST /testing/simulate-shipping/{id}` *(requires `Simulation-Secret`)*

2. **MCP server (bridge)** that exposes the adapter endpoints as MCP tools for agent clients (e.g. Claude Desktop).
   See [`mcp/README.md`](./mcp/README.md).

> This is a **mock** "Shopify adapter": it does **not** call Shopify yet.  
> It uses an in-memory catalog and in-memory checkout/order storage so the full flow can be tested without tokens or a Shopify account.

---

## Layout

```
samples/adapters/shopify/python/
├── README.md
├── pyproject.toml
├── app/
│   ├── main.py
│   ├── config.py
│   ├── shopify_client.py
│   ├── ucp_mappers.py
│   ├── storage.py
│   ├── models.py
│   └── routes/
│       ├── discovery.py
│       ├── catalog.py
│       ├── checkout.py
│       ├── orders.py
│       └── testing.py
└── mcp/
    ├── README.md
    ├── pyproject.toml
    └── ucp_mcp_server.py
```

---

## Prerequisites

- Python 3.10+
- macOS/Linux shell (examples use `uuidgen`)

---

## Install & Run (REST Adapter)

From repo root:

```bash
cd samples/adapters/shopify/python
python -m venv .venv
source .venv/bin/activate
pip install -e .
ucp-shopify-adapter
```

Adapter runs at:
- http://127.0.0.1:8183

---

## Quick Checks

### Discovery profile

```bash
curl -s http://127.0.0.1:8183/.well-known/ucp | python -m json.tool
```

### List products

```bash
curl -s http://127.0.0.1:8183/products | python -m json.tool
```

### Get product

```bash
curl -s http://127.0.0.1:8183/products/bouquet_roses | python -m json.tool
```

---

## End-to-End REST Flow

### 1) Create a checkout

```bash
REQ_ID=$(uuidgen)
IDEMP=$(uuidgen)

curl -s -X POST http://127.0.0.1:8183/checkout-sessions \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $REQ_ID" \
  -H "idempotency-key: $IDEMP" \
  -d '{
    "buyer": {"full_name":"John Doe","email":"john.doe@example.com"},
    "currency":"USD",
    "line_items":[{"product_id":"bouquet_roses","quantity":1}],
    "discount_codes":["10OFF"]
  }' | tee /tmp/checkout_create.json | python -m json.tool
```

Extract the IDs:

```bash
CHECKOUT_ID=$(python -c 'import json;print(json.load(open("/tmp/checkout_create.json"))["id"])')
LINE_ITEM_ID=$(python -c 'import json;d=json.load(open("/tmp/checkout_create.json"));print(d["line_items"][0]["id"])')
echo "CHECKOUT_ID=$CHECKOUT_ID"
echo "LINE_ITEM_ID=$LINE_ITEM_ID"
```

---

### 2) Set shipping destination + choose shipping option

This sample exposes 2 options once a destination is set:
- `std-ship` (free)
- `exp-ship-intl` (+2500 cents)

Create update payload:

```bash
cat > /tmp/checkout_update.json <<JSON
{
  "id": "$CHECKOUT_ID",
  "fulfillment": {
    "methods": [
      {
        "type": "shipping",
        "line_item_ids": ["$LINE_ITEM_ID"],
        "destinations": [
          {
            "id": "dest_1",
            "street_address": "10 Downing St",
            "address_locality": "London",
            "address_region": "London",
            "address_country": "GB",
            "postal_code": "SW1A 2AA",
            "full_name": "John Doe",
            "phone_number": "+447000000000"
          }
        ],
        "selected_destination_id": "dest_1",
        "groups": [
          { "selected_option_id": "std-ship" }
        ]
      }
    ]
  }
}
JSON
```

Send update:

```bash
REQ_ID=$(uuidgen)
IDEMP=$(uuidgen)

curl -s -X PUT http://127.0.0.1:8183/checkout-sessions/$CHECKOUT_ID \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $REQ_ID" \
  -H "idempotency-key: $IDEMP" \
  -d @/tmp/checkout_update.json | python -m json.tool
```

---

### 3) Complete checkout (mock payment)

This mock adapter accepts the token `success_token` as the "approved" payment credential.

```bash
REQ_ID=$(uuidgen)
IDEMP=$(uuidgen)

curl -s -X POST http://127.0.0.1:8183/checkout-sessions/$CHECKOUT_ID/complete \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $REQ_ID" \
  -H "idempotency-key: $IDEMP" \
  -d '{
    "payment_data": {
      "id": "pi_test_1",
      "handler_id": "mock_payment_handler",
      "type": "card",
      "brand": "VISA",
      "last_digits": "1111",
      "credential": { "type":"token", "token":"success_token" }
    },
    "risk_signals": {}
  }' | tee /tmp/checkout_complete.json | python -m json.tool
```

Extract order id:

```bash
ORDER_ID=$(python -c 'import json;d=json.load(open("/tmp/checkout_complete.json"));print(d["order"]["id"])')
echo "ORDER_ID=$ORDER_ID"
```

---

### 4) Get order

```bash
curl -s http://127.0.0.1:8183/orders/$ORDER_ID \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $(uuidgen)" \
| python -m json.tool
```

---

### 5) Simulate shipping event (testing endpoint)

Requires the header `Simulation-Secret` to match `SIMULATION_SECRET` (default `letmein`).

```bash
curl -s -X POST http://127.0.0.1:8183/testing/simulate-shipping/$ORDER_ID \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $(uuidgen)" \
  -H "Simulation-Secret: letmein" \
| python -m json.tool
```

Re-fetch the order to see the appended fulfillment event:

```bash
curl -s http://127.0.0.1:8183/orders/$ORDER_ID \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $(uuidgen)" \
| python -m json.tool
```

---

## Idempotency Behavior (Important)

The adapter enforces:
- If an `idempotency-key` is reused with the same payload, it returns the same response (safe retry).
- If the same `idempotency-key` is reused with a different payload, it returns:
  - `409` with code `IDEMPOTENCY_CONFLICT`

Example (conflict):

```bash
IDEMP="test-idem-key"
REQ_ID=$(uuidgen)

# quantity 1
curl -s -X POST http://127.0.0.1:8183/checkout-sessions \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $REQ_ID" \
  -H "idempotency-key: $IDEMP" \
  -d '{"currency":"USD","line_items":[{"product_id":"bouquet_roses","quantity":1}]}' | python -m json.tool

# quantity 2 with same key -> 409 conflict
REQ_ID=$(uuidgen)
curl -s -X POST http://127.0.0.1:8183/checkout-sessions \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=https://agent.example/profile" \
  -H "request-signature: test" \
  -H "request-id: $REQ_ID" \
  -H "idempotency-key: $IDEMP" \
  -d '{"currency":"USD","line_items":[{"product_id":"bouquet_roses","quantity":2}]}' | python -m json.tool
```

---

## Configuration

Environment variables (optional):
- `SERVER_BASE_URL` (default `http://localhost:8183`)
- `SIMULATION_SECRET` (default `letmein`)

Example:

```bash
export SIMULATION_SECRET="letmein"
export SERVER_BASE_URL="http://127.0.0.1:8183"
ucp-shopify-adapter
```

---

## MCP Bridge

To expose this adapter via MCP tools for Claude Desktop, see:
- [mcp/README.md](./mcp/README.md)

---

## Notes / Limitations

- Storage is in-memory. Restarting the server clears checkouts and orders.
- Payment is mocked. Only the token `success_token` is treated as "authorized."
- This is a "Shopify adapter" shape only. A real implementation would replace `MockShopifyClient` with Shopify Storefront API calls and map Shopify cart/checkout objects into these UCP-ish models.