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

This directory contains sample implementations and client scripts for the
Universal Commerce Protocol (UCP).

## Sample Implementations

### Python

A reference implementation of a UCP Merchant Server using Python and FastAPI.

*   **Server**: [Documentation](rest/python/server/README.md)

    *   Located in `rest/python/server/`.
    *   Demonstrates capability discovery, checkout session management, payment
        processing, and order lifecycle.
    *   Includes simulation endpoints for testing.

*   **Client**:
    [Happy Path Script](rest/python/client/flower_shop/simple_happy_path_client.py)

    *   Located in `rest/python/client/`.
    *   A script demonstrating a full "happy path" user journey (discovery ->
        checkout -> payment).

### Node.js

A reference implementation of a UCP Merchant Server using Node.js, Hono, and
Zod.

*   **Server**: [Documentation](rest/nodejs/README.md)
    *   Located in `rest/nodejs/`.
    *   Demonstrates implementation of UCP specifications for shopping,
        checkout, and order management using a Node.js stack.

### A2A (Agent-to-Agent)

An AI-powered retail agent implementing UCP via the A2A protocol.

*   **Cymbal Retail Agent**: [Documentation](a2a/README.md)
    *   Located in `a2a/business_agent/`.
    *   Demonstrates A2A protocol integration with UCP Extension.
    *   Includes AI-powered shopping assistant with Google ADK and Gemini.
    *   React-based chat client for user interaction.

## Getting Started

Please refer to the specific README files linked above for detailed instructions
on how to set up, run, and test each sample.
