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

# UCP Node.js Server Reference Implementation

This directory contains a reference implementation of a Universal Commerce
Protocol (UCP) server built with Node.js, Hono and Zod. It demonstrates how to
implement the UCP specifications for shopping, checkout, and order management.

## Prerequisites

- Node.js 20, 22, or 24
- npm (Node Package Manager)

## Setup

1.  **Clone this repo**

    ```shell
    git clone https://github.com/Universal-Commerce-Protocol/samples.git
    cd samples/rest/nodejs
    ```

2.  **Install Dependencies**

    Run the following command in this directory to install the required Node.js
    packages:

    ```bash
    npm install
    ```

3.  **Database Setup**

    The server uses SQLite for persistence. Ensure the `databases` directory
    exists. The server will automatically initialize the database files
    (`products.db` and `transactions.db`) and tables on the first run.

    If the `databases` directory does not exist, create it:

    ```bash
    mkdir -p databases
    ```

    **Note:** For the server to function fully (e.g., to create a checkout), you
    may need to populate `products.db` with sample product data, as the server
    expects products to exist for validation.

## Running the Server

To start the server in development mode (with hot reloading):

```bash
npm run dev
```

To build and start the server for production:

```bash
npm run build
npm start
```

The server will start on port **3000** by default. You can access the discovery
endpoint at:

```
http://localhost:3000/.well-known/ucp
```

## Request Signatures (RFC 9421)

The server verifies UCP request signatures as defined in the specification's
[`signatures.md`](https://github.com/Universal-Commerce-Protocol/ucp/blob/main/docs/specification/signatures.md):
[RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) HTTP Message Signatures
with an [RFC 9530](https://www.rfc-editor.org/rfc/rfc9530.html) `Content-Digest`
over the raw body. The signer's public key is discovered from the profile URL in
the `UCP-Agent` header (its `keys[]`). `ES256` (fixed-width raw `r||s`, not
ASN.1/DER) is the baseline; `Ed25519` is also supported. The behaviour mirrors
the Python reference server (`rest/python/server`).

Behaviour is controlled by two environment variables:

| Variable                      | Default | Effect                                                                                                                                                                                                             |
| ----------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `REQUIRE_SIGNATURES`          | `false` | Reject requests whose signature is missing or invalid. When `false`, a present signature is still verified and the result logged, but unsigned or invalid requests are allowed — so existing clients keep working. |
| `ALLOW_INSECURE_PROFILE_URLS` | `false` | Permit `http` and loopback/private profile URLs when resolving keys. For localhost demos and CI only; it disables SSRF protections and must never be enabled in production.                                        |

When verification fails under enforcement, the server returns the spec's error
code: `401 signature_missing` / `signature_invalid` / `key_not_found`,
`400 digest_mismatch` / `algorithm_unsupported` / `invalid_profile_url`,
`424 profile_unreachable`, or `422 profile_malformed`.

To reject anything unsigned, start the server with enforcement on:

```bash
REQUIRE_SIGNATURES=true npm run dev
```

Each verified request logs
`RFC 9421 signature verified (keyid=..., profile=...)`. The discovery profile
at `/.well-known/ucp` stays unverified: it is the public document a platform
must read before it can sign anything.

## Running Conformance Tests

To verify that this server implementation complies with the UCP specifications,
use the official UCP Conformance Test Suite.

1.  **Get the Conformance Tests**

    Clone the conformance repository:

    ```bash
    git clone https://github.com/Universal-Commerce-Protocol/conformance.git
    cd conformance
    ```

2.  **Run the Tests**

    Follow the instructions in the conformance repository to install its
    dependencies. Then, run the tests against this local server implementation.

    Assuming the conformance suite uses a configuration file or environment
    variables to target the server, ensure it is pointing to:

    ```
    http://localhost:3000
    ```

## Project Structure

- `src/api`: Contains the implementation of UCP services (Discovery, Checkout,
  Order).
- `src/data`: Database access layer (SQLite).
- `src/models`: TypeScript types and Zod schemas (some generated from specs).
- `src/utils`: Helper utilities for validation and logging.
- `databases`: Directory where SQLite database files are stored.
