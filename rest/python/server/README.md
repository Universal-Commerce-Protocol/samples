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

*   `server.py`: The entry point for the FastAPI application.
*   `pyproject.toml`: Project configuration for external dependency management
    and packaging.

## Prerequisites

1.  Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2.  Install dependencies: `uv sync`

## Prepare the workspace

First, clone the necessary repositories and set your environment variables. You
will need both the Samples repository (which contains the Python server) and the
SDK repository.

NOTE: Temporarily the Samples repository expects the SDK at a known relative
filesystem location, as such, the target paths in these example are significant.

```shell
mkdir sdk
git clone https://github.com/Universal-Commerce-Protocol/python-sdk.git sdk/python
pushd sdk/python
uv sync
popd
git clone https://github.com/Universal-Commerce-Protocol/samples.git
cd samples/rest/python/server
uv sync
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

## Running with Docker

For a quick start without installing Python or uv locally, you can use Docker:

```bash
cd ../../docker
docker-compose -f docker-compose.python.yml up
```

Or using the main compose file:

```bash
docker-compose up python-server
```

This will build and start the Python server in a Docker container, automatically
initializing the database with sample data. The server will be available at
`http://localhost:8182`.

For more details and options, see the [Docker documentation](../../docker/README.md).

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

*   `POST /testing/simulate-shipping/{id}`: Triggers a simulated "order shipped"
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
    "version": "2026-01-11",
    "services": {
      "dev.ucp.shopping": {
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/shopping",
        "rest": {
          "schema": "https://ucp.dev/services/shopping/openapi.json",
          "endpoint": "http://localhost:8182/"
        },
        "mcp": null,
        "a2a": null,
        "embedded": null
      }
    },
    "capabilities": [
      {
        "name": "dev.ucp.shopping.checkout",
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/shopping/checkout",
        "schema": "https://ucp.dev/schemas/shopping/checkout.json",
        "extends": null,
        "config": null
      },
      {
        "name": "dev.ucp.shopping.discount",
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/shopping/discount",
        "schema": "https://ucp.dev/schemas/shopping/discount.json",
        "extends": "dev.ucp.shopping.checkout",
        "config": null
      },
      {
        "name": "dev.ucp.shopping.fulfillment",
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/shopping/fulfillment",
        "schema": "https://ucp.dev/schemas/shopping/fulfillment.json",
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
        "version": "2026-01-11",
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
        "version": "2026-01-11",
        "spec": "https://example.com/spec",
        "config_schema": "https://example.com/schema",
        "instrument_schemas": [
          "https://ucp.dev/schemas/shopping/types/gpay_card_payment_instrument.json"
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
      {
        "id": "mock_payment_handler",
        "name": "dev.ucp.mock_payment",
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specs/mock",
        "config_schema": "https://ucp.dev/schemas/mock.json",
        "instrument_schemas": [
          "https://ucp.dev/schemas/shopping/types/card_payment_instrument.json"
        ],
        "config": {
          "supported_tokens": [
            "success_token",
            "fail_token"
          ]
        }
      }
    ]
  },
  "signing_keys": null
}
```

Full response
[example](https://github.com/Universal-Commerce-Protocol/samples/blob/main/rest/python/client/flower_shop/sample_output/happy_path_dialog.md#response).

## Capabilities & Extensions

*   Capabilities: Schema and Operations for commerce features identified via
    reverse-domain notation to prevent conflicts.

*   Extensions: Modular additions (e.g., discounts, fulfillment etc) that
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
  -H "UCP-Agent: profile="https://agent.example/profile"" \
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
        "version": "2026-01-11",
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
        "version": "2026-01-11",
        "spec": "https://example.com/spec",
        "config_schema": "https://example.com/schema",
        "instrument_schemas": [
          "https://ucp.dev/schemas/shopping/types/gpay_card_payment_instrument.json"
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
    "version": "2026-01-11",
    "capabilities": [
      {
        "name": "dev.ucp.shopping.checkout",
        "version": "2026-01-11",
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
  -H "UCP-Agent: profile="https://agent.example/profile"" \
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
    "version": "2026-01-11",
    "capabilities": [
      {
        "name": "dev.ucp.shopping.checkout",
        "version": "2026-01-11",
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
    "codes": [
      "10OFF"
    ],
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
