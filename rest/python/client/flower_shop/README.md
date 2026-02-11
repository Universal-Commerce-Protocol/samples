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

<!-- disableFinding(LINK_RELATIVE_G3DOC) -->

# Simple Happy Path Client Script for UCP SDK.

## Scope

This script demonstrates a complete "happy path" user journey: 0. **Discovery**:
Querying the merchant to see what they support. 1. **Create Checkout**: Creating
a new checkout session (cart). 2. **Add Items**: Adding items to the checkout
session. 3. **Fulfillment**: Triggering fulfillment option generation, selecting
a destination, and choosing a shipping option. 4. **Complete**: Completing the
checkout by processing a payment.

## Prerequisites

1.  **Install Dependencies**: `bash uv sync`

2.  **Start the Merchant Server**: You need a running UCP Merchant Server to
    execute this client against. Follow the instructions in the
    [Server README](../../server/README.md) to start the server on port 8182.

        _Quick start (from `../../server/`):_ `bash uv run server.py

    --products_db_path=/tmp/ucp_test/products.db
    --transactions_db_path=/tmp/ucp_test/transactions.db --port=8182`

## Running the Client

Once the server is running, you can execute the client script:

```bash
uv run simple_happy_path_client.py --server_url=http://localhost:8182
```

### Options

- `--server_url`: The base URL of the UCP Merchant Server (default:
  `http://localhost:8182`).
- `--export_requests_to`: Path to a markdown file where the request/response
  dialog will be logged.

  ```bash
  uv run simple_happy_path_client.py --export_requests_to=interaction_log.md
  ```

## Automated Demo (extract_json_dialog.sh)

For a fully automated demonstration that sets up the database, starts the
server, runs the client, and generates a transaction log, use the included shell
script:

```bash
./extract_json_dialog.sh
```

This will output the interaction log to `/tmp/ucp_test/happy_path_dialog.md`.
