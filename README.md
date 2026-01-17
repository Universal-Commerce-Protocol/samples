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

### Agentic Commerce (A2A)

Demonstrates how to build AI-powered shopping assistants using UCP as an
extension to the [A2A (Agent-to-Agent) protocol](https://google.github.io/A2A/).

*   **[Full A2A Sample](a2a/README.md)**: Overview of the agentic commerce
    architecture.
*   **Business Agent**: AI shopping assistant built with Python, Google ADK, and
    Gemini.
*   **Chat Client**: React-based UI that renders UCP data types for
    conversational commerce.

## Which Sample to Use?

This repository contains two different ways to implement UCP based on your
use-case:

| Use Case | Recommended Sample | Protocol |
| :--- | :--- | :--- |
| **Traditional E-commerce** | [REST Samples](rest/) | Standard RESTful HTTP |
| **AI / Conversational Commerce** | [A2A Samples](a2a/) | JSON-RPC over A2A |

*   Use the **REST Samples** if you are building a standard web store backend and
    want to follow the official UCP REST specification.
*   Use the **A2A Samples** if you are building an AI agent that needs to help
    users shop through natural language.

## Getting Started

Please refer to the specific README files linked above for detailed instructions
on how to set up, run, and test each sample.
