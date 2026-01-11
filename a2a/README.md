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

# Example Business Agent

This is an example Business A2A Agent that implements UCP Extension.
The extension allows the business agent to respond to the client applications
with UCP defined data types.

A simple chat client is also provided to interact with the business agent that
consumes the A2A interface exposed by the business agent.

The example uses a mock inmemory RetailStore to simulate a business store.

### Pre-requisites:

1. Python 3.13
2. UV
3. Gemini API Key (The agent uses Gemini model to generate responses)

### Agent Quick Start

1. `cd a2a/business_agent`
2. Run `uv sync`
3. Update the env.example file with your Gemini API key and rename it to .env
4. Run `uv run business_agent`
5. This starts the business agent on port 10999. You can verify by accessing
the agent card at http://localhost:10999/.well-known/agent-card.json
6. The business agent's UCP Profile can be found at
http://localhost:10999/.well-known/ucp

### Chat Client

**Prerequisites:**  Node.js

1. cd chat-client
2. Install dependencies:
   `npm install`
3. Run the app:
   `npm run dev`
4. The Chat Client UCP Profile can be found at
http://localhost:3000/profile/agent-profile.json

## Example interaction:

[ucp_a2a.webm](https://github.com/user-attachments/assets/8d3d17f5-dbcc-4cc8-91b9-2b7d48b3f2df)


1. Launch the browser and navigate to http://localhost:3000/
2. In the Chat interface, type "show me cookies available in stock" and press
enter.
3. The agent will return products available in stock.
4. Click 'Add to Checkout' for any product.
5. The agent will ask for required information such as email address, shipping
address etc.
6. Once the required information is provided, click 'Complete Payment'.
7. The UI shows available mock payment options.
8. Select a payment method and click 'Confirm Purchase'.
9. The agent will create an order and return the order response.

### Disclaimer

This is an example implementation for demonstration purposes and is not
intended for production use.
