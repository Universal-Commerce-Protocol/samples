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

# UCP Merchant Server (Java/Spring Boot)

This directory contains a reference implementation of a Universal Commerce
Protocol (UCP) server built with Java 25 and Spring Boot 3.5.9. It demonstrates
how to implement the UCP specifications for checkout sessions, including modular
support for fulfillment, discounts, and order extensions.

## Project Structure

*   `src/main/java/com/dev/ucp/actions`: Contains the business logic for
    checkout operations (Create, Update, Complete, etc.).
*   `src/main/java/com/dev/ucp/entities`: JPA entities with nested repository
    interfaces for persistence.
*   `src/main/java/com/dev/ucp/service`: REST controllers and exception
    handlers.
*   `src/main/resources/openapi.extensions.json`: Defines modular UCP schema
    extensions (e.g., fulfillment, discounts) used for model generation.
*   `generated/`: Source root for models and interfaces generated from OpenAPI
    specs.
*   `pom.xml`: Main Maven configuration.
*   `codegen.pom.xml`: Specialized Maven configuration for OpenAPI code
    generation.

## Prerequisites

*   Java 25 JDK
*   Apache Maven 3.9+
*   (Optional) Official `ucp` repository for
    [model generation](#generating-models).

## Setup

```shell
# Clone the samples repository if you haven't already
git clone https://github.com/Universal-Commerce-Protocol/samples.git
cd samples/rest/java-spring

# Build the project (pre-generated models are included in the repository)
mvn clean install
```

## Run the Server

Start the server on port 8182. Using the `conformance` profile enables
simulation endpoints required for testing.

```bash
# Start the server in the background, redirecting output to server.log
mvn spring-boot:run -Dspring-boot.run.arguments=--server.port=8182 -Pconformance > server.log 2>&1 &
SERVER_PID=$!
```

Note: You can monitor the logs with `tail -f server.log`.

## Discovery & Health Check

To verify the operational status and discover the capabilities of your local
server, you can query the UCP discovery endpoint. This serves as a primary
validation that the service is correctly configured and accessible.

```bash
curl -s http://localhost:8182/.well-known/ucp
```

### Example Discovery Response:

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
                    "endpoint": "http://localhost:8182/ucp"
                }
            }
        },
        "capabilities": [
            {
                "name": "dev.ucp.shopping.checkout",
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping/checkout",
                "schema": "https://ucp.dev/schemas/shopping/checkout.json"
            },
            {
                "name": "dev.ucp.shopping.discount",
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping/discount",
                "schema": "https://ucp.dev/schemas/shopping/discount.json",
                "extends": "dev.ucp.shopping.checkout"
            },
            {
                "name": "dev.ucp.shopping.fulfillment",
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping/fulfillment",
                "schema": "https://ucp.dev/schemas/shopping/fulfillment.json",
                "extends": "dev.ucp.shopping.checkout"
            },
            {
                "name": "dev.ucp.shopping.order",
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping/order",
                "schema": "https://ucp.dev/schemas/shopping/order.json"
            }
        ]
    },
    "payment": {
        "handlers": [
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
    }
}
```

## Running Conformance Tests

To verify that this server implementation complies with the UCP specifications,
please use the official
[UCP Conformance Test Suite](https://github.com/Universal-Commerce-Protocol/conformance).
Refer to its documentation for prerequisites, installation, and detailed
execution instructions.

Assuming the conformance suite is configured to target port **8182**, you can
run the fulfillment tests with a command similar to:

```bash
.venv/bin/python3 fulfillment_test.py \
   --server_url=http://localhost:8182 \
   --simulation_secret=super-secret-sim-key \
   --conformance_input=test_data/flower_shop/conformance_input.json
```

## Testing Endpoints

The server exposes additional endpoints for simulation and testing purposes.
These are only available when the server is started with the `conformance`
profile.

**Note:** If you are relying on hot-swapping, ensure that you also include the
`-Pconformance` flag during your build or compilation steps to keep these
test-only classes active.

*   `POST /testing/simulate-shipping/{id}`: Triggers a simulated "order shipped"
    event for the specified order ID. This updates the order status and sends a
    webhook notification. This endpoint requires the `Simulation-Secret` header.

## Database & Test Data

The server uses an in-memory H2 database for the demo. The schema and initial
flower shop data are automatically loaded on startup.

If you wish to add custom products, discounts, or inventory for testing, you can
modify `src/main/resources/data.sql`

## Generating Models

This project uses OpenAPI Generator to maintain strict adherence to the UCP
schemas. Pre-generated models are provided in the `generated/` directory.

### Workspace Structure

The generation process assumes that the main `ucp` repository (containing the
official specifications) is checked out in a directory sibling to the `samples`
repository:

```text
/work/
  ├── ucp/          <-- Official specifications
  └── samples/      <-- This repository
```

### Regeneration Steps

If the specifications change, you can regenerate the models:

1.  **Run the preparation and generation script**:

    ```bash
    ./generate_ucp_models.sh [optional_path_to_ucp_root]
    ```

    By default, it looks for UCP at `../../../ucp`.

This script copies the official specs to `target/spec`, applies necessary
compatibility transformations, and runs the code generator.

The generated code will be placed in the `generated/` directory and is
automatically included in the main build's classpath.

## Terminate the server

Terminate the server process when finished:

```bash
kill -9 $(lsof -t -i :8182)
```

## Developer Guide: Core Framework Components

The following files provide essential infrastructure for UCP compliance and are designed to be reused or extended as the protocol evolves:

*   **`CheckoutSessionsApiController.java`**: The primary REST entry point for the UCP Shopping API. It handles protocol-level concerns like `UCP-Agent` header validation before delegating business logic to specialized action classes.
*   **`DiscoveryController.java`**: Implements the mandatory UCP discovery endpoint (`.well-known/ucp`), advertising the server's supported protocol versions, services, and capabilities to the platform.
*   **`ExtensionsHelper.java` & `src/main/resources/openapi.extensions.json`**: These work in tandem to manage UCP extension fields. `openapi.extensions.json` defines the schema extensions for model generation, while `ExtensionsHelper.java` provides typed access to these fields. This infrastructure only requires updates when a new extension module is added to or removed from the protocol.
*   **`JacksonConfig.java`**: Handles the specialized JSON processing required by the UCP specification, including `JsonNullable` support and custom polymorphic deserialization for union types like `PaymentCredential` and `FulfillmentDestination`.
*   **`UCPExceptionControllerAdvice.java`**: Ensures that all service-layer exceptions are automatically transformed into structured, UCP-compliant error responses with appropriate protocol-standard error codes.
*   **`PlatformProfileResolver.java`**: Orchestrates the discovery and resolution of platform UCP profiles, enabling the server to dynamically determine capability endpoints and webhook configurations.
