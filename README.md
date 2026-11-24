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

# Universal Commerce Protocol (UCP) Samples

Full-stack sample applications for building and testing integrations with the
[Universal Commerce Protocol (UCP)](https://ucp.dev) against ratified
specification releases.

## Repository Scope

UCP separates lightweight specification validation from full-stack integration
samples across two repositories:

| Implementation                     | Location                                                                                                                                                                         | Role                                                                                                                                                                                                                                               | Specification Cadence                                                                                                                                   |
| :--------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Reference Implementation**       | `reference/` in [Universal-Commerce-Protocol/ucp](https://github.com/Universal-Commerce-Protocol/ucp) ([ucp#1090](https://github.com/Universal-Commerce-Protocol/ucp/pull/1090)) | Minimal, in-memory walkthrough for learning core protocol mechanics (discovery, capability negotiation, closed-world extension composition, and REST and MCP parity) and validating specification pull requests in CI.                             | Continuous, same-commit with the draft specification.                                                                                                   |
| **Sample Store & Sample Platform** | `store/` and platform tooling in `Universal-Commerce-Protocol/samples`                                                                                                           | Full-stack integration targets with decoupled domain services, local persistence, a thin UCP protocol adapter layer, interactive storefront UI, OAuth 2.0 identity linking, 3DS2 escalation, fulfillment, order webhooks, and conformance backing. | Pinned to ratified specification releases via spec-aligned release channels ([ucp#909](https://github.com/Universal-Commerce-Protocol/ucp/issues/909)). |

Start with the in-tree Reference Implementation in
[Universal-Commerce-Protocol/ucp](https://github.com/Universal-Commerce-Protocol/ucp)
to read a small, self-contained protocol walkthrough or validate draft schema
changes. Use this repository to test against realistic merchant and platform
workloads or examine how to layer UCP adapters onto an existing commerce domain
without coupling business logic to wire schemas.

## Current Samples

### Python Flower Shop (Transitional)

> [!IMPORTANT]
> **Status: Transitional (`rest/python/`)**
>
> The Python Flower Shop sample (`rest/python/`, targeting the 2026-04-08
> specification) is transitional and retained temporarily only because
> [Universal-Commerce-Protocol/conformance](https://github.com/Universal-Commerce-Protocol/conformance)
> CI executes against `rest/python/server/`. Once the full-stack Sample Store
> lands at `store/` and the conformance suite migrates to it, `rest/python/`
> will be retired. Please hold off on adding new capabilities or features to
> `rest/python/` in the meantime.

Sample UCP merchant server and happy-path client built with Python, FastAPI, and
SQLite:

- **Merchant Server** ([Documentation](rest/python/server/README.md)): Located
  in `rest/python/server/`. Covers capability discovery, cart and checkout
  sessions, payment handlers, request and webhook signing, and order simulation
  endpoints.
- **Happy Path Client**
  ([Documentation](rest/python/client/flower_shop/README.md),
  [Script](rest/python/client/flower_shop/simple_happy_path_client.py)): Located
  in `rest/python/client/flower_shop/`. Runs an end-to-end discovery, checkout,
  fulfillment selection, and payment completion flow against the local server.

## Contributing

Going forward, this repository accepts contributions scoped to the **Sample
Store** (`store/`) and **Sample Platform** maintained on specification-aligned
release channels
([ucp#909](https://github.com/Universal-Commerce-Protocol/ucp/issues/909)),
rather than standalone unowned sample implementations. Changes to `rest/python/`
are limited to maintenance needed to keep existing
[conformance](https://github.com/Universal-Commerce-Protocol/conformance) CI
passing until `store/` replaces it. For minimal protocol examples or changes
coupled to draft specification pull requests, contribute to the Reference
Implementation in
[Universal-Commerce-Protocol/ucp](https://github.com/Universal-Commerce-Protocol/ucp).
