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

# UCP Merchant Server (Python/FastAPI)

This is a reference implementation of a UCP Merchant Server, designed to be
deployable both inside and outside of Google.

## Project Structure

- `server.py`: The entry point for the FastAPI application.
- `pyproject.toml`: Project configuration for external dependency management
  and packaging.

## Prerequisites

1.  Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2.  Install dependencies: `uv sync`

## Prepare the workspace

First, clone the Samples repository.

```shell
git clone https://github.com/Universal-Commerce-Protocol/samples.git
cd samples/rest/python/server
uv sync
```

### Developing with a local SDK checkout (Optional)

If you are actively developing the SDK and want to test local changes against the server, clone the SDK repository as a sibling and install it in editable mode:

```shell
# Clone SDK as sibling to samples
git clone https://github.com/Universal-Commerce-Protocol/python-sdk.git

# Install it in editable mode in the server's virtual environment
cd samples/rest/python/server
uv pip install -e ../../../../python-sdk
```

## Initialize the sample database

The test server is a store front for a flower shop; we have some test data to
exemplify ordering various items. The data is a simple SQLite database created
in a separate step to allow easy experimentation and inspection after each
request.

Run the following commands to create a local database populated with example
test data. This script maps raw product information into the UCP schema so the
sample server can respond to queries.

```shell
mkdir /tmp/ucp_test
uv run import_csv.py \
    --products_db_path=/tmp/ucp_test/products.db \
    --transactions_db_path=/tmp/ucp_test/transactions.db \
    --data_dir=../test_data/flower_shop
```

## Run the Server

Start the server on port 8182, pointing to your initialized data.

Start it in the background so we can use the terminal for other commands or
start the server and the client in separate terminals.

```shell
uv run server.py \
   --products_db_path=/tmp/ucp_test/products.db \
   --transactions_db_path=/tmp/ucp_test/transactions.db \
   --port=8182 &
SERVER_PID=$!
```

Note: Keep the server running for the duration of running the client and the
following experiments.

## Request Signatures (RFC 9421)

The server verifies UCP request signatures as defined in the specification's
[`signatures.md`](https://github.com/Universal-Commerce-Protocol/ucp/blob/main/docs/specification/signatures.md):
[RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) HTTP Message Signatures
with an [RFC 9530](https://www.rfc-editor.org/rfc/rfc9530.html) `Content-Digest`
over the raw body. The signer's public key is discovered from the profile URL in
the `UCP-Agent` header (its `keys[]`). `ES256` (fixed-width raw `r||s`, not
ASN.1/DER) is the baseline; `Ed25519` is also supported.

Behaviour is controlled by two flags:

| Flag                            | Default | Effect                                                                                                                                                                                                             |
| ------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--require_signatures`          | `false` | Reject requests whose signature is missing or invalid. When `false`, a present signature is still verified and the result logged, but unsigned or invalid requests are allowed — so existing clients keep working. |
| `--allow_insecure_profile_urls` | `false` | Permit `http` and loopback/private profile URLs when resolving keys. For localhost demos and CI only; it disables SSRF protections and must never be enabled in production.                                        |

When verification fails under enforcement, the server returns the spec's error
code: `401 signature_missing` / `signature_invalid` / `key_not_found`,
`400 digest_mismatch` / `algorithm_unsupported` / `invalid_profile_url`,
`424 profile_unreachable`, or `422 profile_malformed`.

To see the full sign-then-verify loop locally, run the server with the demo
carve-out and let the client sign (it signs by default and publishes its key
from a local profile server):

```shell
uv run server.py \
   --products_db_path=/tmp/ucp_test/products.db \
   --transactions_db_path=/tmp/ucp_test/transactions.db \
   --port=8182 --allow_insecure_profile_urls &
```

Each verified request logs
`RFC 9421 signature verified (keyid=..., profile=...)`. Add `--require_signatures`
to reject anything unsigned.

## Webhook Signing & Delivery Retry

Outbound order-event webhooks are signed as the business, per the
specification's `order.md` (Webhook Signature Verification): every delivery
carries `UCP-Agent` (this server's profile URL), `Signature`,
`Signature-Input`, and a `Content-Digest` over the exact raw body bytes. The
signed components cover the full request-signing table (`@method`,
`@authority`, `@path`, `@query` when the platform URL has one,
`content-digest`, `content-type`, `idempotency-key`, `ucp-agent`) plus the
Standard Webhooks event headers (`webhook-id`, `webhook-timestamp`). The
matching public JWK is published in the served profile's `signing_keys[]`
(and mirrored into `ucp.keys[]`) so platforms can verify.

Failed deliveries — transport errors or a 5xx from the receiver — are retried
with exponential backoff, as `order.md` requires; a 4xx is treated as a
permanent rejection and is not retried. Retried attempts reuse the same
`Webhook-Id` and `Idempotency-Key`, so receivers can deduplicate.

| Flag                              | Default     | Effect                                                                                                                                                         |
| --------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--webhook_signing_key`           | (ephemeral) | Path to a PEM private key (EC P-256 or Ed25519) to sign webhooks with. When unset, an ephemeral demo key is generated at startup and published in the profile. |
| `--webhook_delivery_attempts`     | `3`         | Total delivery attempts per webhook (initial attempt plus retries).                                                                                            |
| `--webhook_retry_backoff_seconds` | `0.5`       | Delay before the first retry; doubles on each subsequent retry.                                                                                                |

## Run a Simple Client

Exercise a simple checkout path: Once the server is running, execute the simple
client that creates a checkout session, adds items to the card and completes the
order.

```shell
cd samples/rest/python/client/flower_shop/
uv sync
uv run simple_happy_path_client.py \
   --server_url=http://localhost:8182
```

## Testing Endpoints

The server exposes an additional endpoint for simulation and testing purposes:

- `POST /testing/simulate-shipping/{id}`: Triggers a simulated "order shipped"
  event for the specified order ID. This updates the order status and sends a
  webhook notification if configured. This endpoint requires the
  `Simulation-Secret` header to match the configured `--simulation_secret`.

## Discovery

Businesses publish their capabilities in a standard JSON manifest located at
/.well-known/ucp. This allows agents to dynamically discover features,
endpoints, and payment configurations without hard-coded integrations. Example
of Business Discovery Profile: This discovery profile declares a business'
shopping service endpoints and capabilities—including checkout, fulfillment, and
discount—and specifies a delegated payment handler for tokenizing card payment
instruments. Run the below command to retrieve the discovery profile for your
local business server.

`curl -X GET http://localhost:8182/.well-known/ucp | python3 -m json.tool`

Response:

```json
{
  "ucp": {
    "version": "2026-04-08",
    "services": {
      "dev.ucp.shopping": {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping",
        "rest": {
          "schema": "https://ucp.dev/2026-04-08/services/shopping/openapi.json",
          "endpoint": "http://localhost:8182/"
        },
        "mcp": null,
        "a2a": null,
        "embedded": null
      }
    },
    "capabilities": [
      {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping/checkout",
        "schema": "https://ucp.dev/2026-04-08/schemas/shopping/checkout.json",
        "extends": null,
        "config": null
      },
      {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping/discount",
        "schema": "https://ucp.dev/2026-04-08/schemas/shopping/discount.json",
        "extends": "dev.ucp.shopping.checkout",
        "config": null
      },
      {
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/shopping/fulfillment",
        "schema": "https://ucp.dev/2026-04-08/schemas/shopping/fulfillment.json",
        "extends": "dev.ucp.shopping.checkout",
        "config": null
      }
    ]
  },
  "payment": {
    "handlers": [
      {
        "id": "shop_pay",
        "name": "com.shopify.shop_pay",
        "version": "2026-04-08",
        "spec": "https://shopify.dev/ucp/handlers/shop_pay",
        "config_schema": "https://shopify.dev/ucp/handlers/shop_pay/config.json",
        "instrument_schemas": [
          "https://shopify.dev/ucp/handlers/shop_pay/instrument.json"
        ],
        "config": {
          "shop_id": "a1c4c1fc-6416-4103-afb3-65046e1c7787"
        }
      },
      {
        "id": "google_pay",
        "name": "google.pay",
        "version": "2026-04-08",
        "spec": "https://example.com/spec",
        "config_schema": "https://example.com/schema",
        "instrument_schemas": [
          "https://ucp.dev/2026-04-08/schemas/shopping/types/gpay_card_payment_instrument.json"
        ],
        "config": {
          "api_version": 2,
          "api_version_minor": 0,
          "merchant_info": {
            "merchant_name": "Flower Shop",
            "merchant_id": "TEST",
            "merchant_origin": "localhost"
          },
          "allowed_payment_methods": [
            {
              "type": "CARD",
              "parameters": {
                "allowedAuthMethods": ["PAN_ONLY", "CRYPTOGRAM_3DS"],
                "allowedCardNetworks": ["VISA", "MASTERCARD"]
              },
              "tokenization_specification": [
                {
                  "type": "PAYMENT_GATEWAY",
                  "parameters": [
                    {
                      "gateway": "example",
                      "gatewayMerchantId": "exampleGatewayMerchantId"
                    }
                  ]
                }
              ]
            }
          ]
        }
      },
      {
        "id": "mock_payment_handler",
        "name": "dev.ucp.mock_payment",
        "version": "2026-04-08",
        "spec": "https://ucp.dev/2026-04-08/specification/mock",
        "config_schema": "https://ucp.dev/2026-04-08/schemas/mock.json",
        "instrument_schemas": [
          "https://ucp.dev/2026-04-08/schemas/shopping/types/card_payment_instrument.json"
        ],
        "config": {
          "supported_tokens": ["success_token", "fail_token"]
        }
      }
    ]
  },
  "keys": null
}
```

Full response
[example](https://github.com/Universal-Commerce-Protocol/samples/blob/main/rest/python/client/flower_shop/sample_output/happy_path_dialog.md#response).

## Capabilities & Extensions

- Capabilities: Schema and Operations for commerce features identified via
  reverse-domain notation to prevent conflicts.

- Extensions: Modular additions (e.g., discounts, fulfillment etc) that
  augment the schema of the base functionality of a capability. These use JSON
  Schema’s allOf composition to modify capabilities predictably.

### Example of Checkout Capability

This schema defines the base properties required to initiate a checkout object,
such as line items, currency, and fulfillment address information. Platforms can
call operations like create, update and complete checkout with the defined
checkout object schema.

Run this command against the server to create a checkout session.

```shell
curl -X POST http://localhost:8182/checkout-sessions \
  -H 'UCP-Agent: profile="https://agent.example/profile"' \
  -H "request-signature: test" \
  -H "idempotency-key: a8ef6b00-b947-4eab-aa27-2e43bc93177b" \
  -H "request-id: 31530b95-2350-416f-a974-9429e0ff0663" \
  -d '{
  "line_items": [
    {
      "item": {
        "id": "bouquet_roses",
        "title": "Red Rose"
      },
      "quantity": 1
    }
  ],
  "buyer": {
    "full_name": "John Doe",
    "email": "john.doe@example.com"
  },
  "currency": "USD",
  "payment": {
    "instruments": [],
    "handlers": [
      {
        "id": "shop_pay",
        "name": "com.shopify.shop_pay",
        "version": "2026-04-08",
        "spec": "https://shopify.dev/ucp/handlers/shop_pay",
        "config_schema": "https://shopify.dev/ucp/handlers/shop_pay/config.json",
        "instrument_schemas": [
          "https://shopify.dev/ucp/handlers/shop_pay/instrument.json"
        ],
        "config": {
          "shop_id": "8f1947e7-0d98-4d5c-a65a-2b622ef07239"
        }
      },
      {
        "id": "google_pay",
        "name": "google.pay",
        "version": "2026-04-08",
        "spec": "https://example.com/spec",
        "config_schema": "https://example.com/schema",
        "instrument_schemas": [
          "https://ucp.dev/2026-04-08/schemas/shopping/types/gpay_card_payment_instrument.json"
        ],
        "config": {
          "api_version": 2,
          "api_version_minor": 0,
          "merchant_info": {
            "merchant_name": "Flower Shop",
            "merchant_id": "TEST",
            "merchant_origin": "localhost"
          },
          "allowed_payment_methods": [
            {
              "type": "CARD",
              "parameters": {
                "allowedAuthMethods": [
                  "PAN_ONLY",
                  "CRYPTOGRAM_3DS"
                ],
                "allowedCardNetworks": [
                  "VISA",
                  "MASTERCARD"
                ]
              },
              "tokenization_specification": [
                {
                  "type": "PAYMENT_GATEWAY",
                  "parameters": [
                    {
                      "gateway": "example",
                      "gatewayMerchantId": "exampleGatewayMerchantId"
                    }
                  ]
                }
              ]
            }
          ]
        }
      },
    ]
  }
}'
```

Full request
[example](https://github.com/Universal-Commerce-Protocol/samples/blob/main/rest/python/client/flower_shop/sample_output/happy_path_dialog.md#request-1).

### Response:

```json
{
  "ucp": {
    "version": "2026-04-08",
    "capabilities": [
      {
        "version": "2026-04-08",
        "spec": null,
        "schema": null,
        "extends": null,
        "config": null
      }
    ]
  },
  "id": "f49bc32e-068e-4b9a-bd17-a02757710f53",
  "line_items": [
    {
      "id": "e5df4cad-e229-4cbe-a29e-69e94f4ec12b",
      "item": {
        "id": "bouquet_roses",
        "title": "Bouquet of Red Roses",
        "price": 3500,
        "image_url": null
      },
      "quantity": 1,
      "totals": [
        {
          "type": "subtotal",
          "display_text": null,
          "amount": 3500
        },
        {
          "type": "total",
          "display_text": null,
          "amount": 3500
        }
      ],
      "parent_id": null
    }
  ],
  "buyer": {
    "first_name": null,
    "last_name": null,
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": null,
    "consent": null
  },
  "status": "ready_for_complete",
  "currency": "USD",
  "totals": [
    {
      "type": "subtotal",
      "display_text": null,
      "amount": 3500
    },
    {
      "type": "total",
      "display_text": null,
      "amount": 3500
    }
  ],
  "messages": null,
  "links": [],
  "expires_at": null,
  "continue_url": null,
  "payment": {
    "handlers": [],
    "selected_instrument_id": null,
    "instruments": []
  },
  "order_id": null,
  "order_permalink_url": null,
  "ap2": null,
  "discounts": {
    "codes": null,
    "applied": null
  },
  "fulfillment": null,
  "fulfillment_address": null,
  "fulfillment_options": null,
  "fulfillment_option_id": null,
  "platform": null
}
```

Full response
[example](https://github.com/Universal-Commerce-Protocol/samples/blob/main/rest/python/client/flower_shop/sample_output/happy_path_dialog.md#response-1).

### Example of Discount Extension

This schema extends the base checkout capability by adding a Discount object in
the update checkout request.

Run this command against the server to apply a discount code to your existing
checkout session.

```shell
# Replace with your existing Checkout ID CHECKOUT_ID="600b32d3-6f67-4444-ae77-4379277fd0c7"

curl -X PUT http://localhost:8182/checkout-sessions/$CHECKOUT_ID \
  -H 'UCP-Agent: profile="https://agent.example/profile"' \
  -H "request-signature: test" \
  -H "idempotency-key: 90ea35bd-636a-40ef-8f20-cd67c4c6f7e9" \
  -H "request-id: c6b6f52c-faa7-46c5-a4c5-7a6ed7cc5ad9" \
  -d '{
  "id": "600b32d3-6f67-4444-ae77-4379277fd0c7",
  "line_items": [
    {
      "id": "64df6244-9102-4a96-be07-0846140289d3",
      "item": {
        "id": "bouquet_roses",
        "title": "Red Rose"
      },
      "quantity": 1
    }
  ],
  "currency": "USD",
  "payment": {
    "instruments": [],
    "handlers": []
  },
  "discounts": {
    "codes": [
      "10OFF"
    ]
  }
}'
```

### Response:

```json
{
  "ucp": {
    "version": "2026-04-08",
    "capabilities": [
      {
        "version": "2026-04-08",
        "spec": null,
        "schema": null,
        "extends": null,
        "config": null
      }
    ]
  },
  "id": "f49bc32e-068e-4b9a-bd17-a02757710f53",
  "line_items": [
    {
      "id": "64df6244-9102-4a96-be07-0846140289d3",
      "item": {
        "id": "bouquet_roses",
        "title": "Bouquet of Red Roses",
        "price": 3500,
        "image_url": null
      },
      "quantity": 1,
      "totals": [
        {
          "type": "subtotal",
          "display_text": null,
          "amount": 3500
        },
        {
          "type": "total",
          "display_text": null,
          "amount": 3500
        }
      ],
      "parent_id": null
    }
  ],
  "buyer": {
    "first_name": null,
    "last_name": null,
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": null,
    "consent": null
  },
  "status": "ready_for_complete",
  "currency": "USD",
  "totals": [
    {
      "type": "subtotal",
      "display_text": null,
      "amount": 3500
    },
    {
      "type": "discount",
      "display_text": null,
      "amount": 350
    },
    {
      "type": "total",
      "display_text": null,
      "amount": 3150
    }
  ],
  "messages": null,
  "links": [],
  "expires_at": null,
  "continue_url": null,
  "payment": {
    "handlers": [],
    "selected_instrument_id": null,
    "instruments": []
  },
  "order_id": null,
  "order_permalink_url": null,
  "ap2": null,
  "discounts": {
    "codes": ["10OFF"],
    "applied": [
      {
        "code": "10OFF",
        "title": "10% Off",
        "amount": 350,
        "automatic": false,
        "method": null,
        "priority": null,
        "allocations": [
          {
            "path": "$.totals[?(@.type=='subtotal')]",
            "amount": 350
          }
        ]
      }
    ]
  },
  "fulfillment": null,
  "fulfillment_address": null,
  "fulfillment_options": null,
  "fulfillment_option_id": null,
  "platform": null
}
```

## Terminate the server

Terminate the server process when finished: `kill ${SERVER_PID}`
