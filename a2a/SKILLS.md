---
name: cymbal-retail-agent
description: AI-powered shopping agent built with Google ADK, demonstrating UCP commerce integration via A2A protocol. Use this context when working on the Cymbal Retail Agent codebase.
triggers:
  - working on a2a sample
  - modifying agent tools
  - updating checkout flow
  - adding UCP capabilities
  - debugging A2A communication
globs:
  - "a2a/**/*"
  - "business_agent/**/*"
  - "chat-client/**/*"
---

# Cymbal Retail Agent - AI Assistant Context

> **Purpose**: This file provides context for AI coding assistants (Claude Code, Gemini CLI, Cursor, Codex, etc.) to understand and extend the Cymbal Retail Agent codebase.

AI-powered shopping agent built with Google ADK, demonstrating UCP commerce integration via A2A protocol.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Agent Framework | [Google ADK](https://google.github.io/adk-docs/) (Agent Development Kit) |
| LLM | Gemini 3.0 Flash |
| Commerce Protocol | [UCP](https://ucp.dev/) (Universal Commerce Protocol) |
| Agent Protocol | [A2A](https://a2a-protocol.org/) (Agent-to-Agent) JSON-RPC 2.0 |
| Backend | Python 3.13, Uvicorn, Starlette, Pydantic |
| Frontend | React 19, TypeScript, Vite, Tailwind |

## Directory Structure

```
a2a/
├── business_agent/src/business_agent/
│   ├── agent.py              # ADK agent with 8 shopping tools
│   ├── agent_executor.py     # A2A ↔ ADK bridge
│   ├── store.py              # Mock retail store (replace for production)
│   ├── main.py               # Uvicorn server entry point
│   ├── ucp_profile_resolver.py # UCP capability negotiation
│   ├── payment_processor.py  # Mock payment processing
│   ├── constants.py          # State keys and extension URLs
│   ├── helpers/type_generator.py # Dynamic Pydantic checkout types
│   ├── a2a_extensions/       # A2A extension implementations
│   └── data/                 # JSON configs and product images
├── chat-client/
│   ├── App.tsx               # React main component, A2A messaging
│   ├── components/           # ProductCard, Checkout, PaymentMethodSelector
│   ├── types.ts              # TypeScript interfaces
│   └── profile/agent_profile.json # Client UCP capabilities
├── docs/                     # Detailed documentation (see below)
├── DEVELOPER_GUIDE.md        # Developer overview and reading roadmap
├── README.md                 # Quick start and demo
└── SKILLS.md                 # This file (AI assistant context)
```

## Core Concepts

| Term | Definition |
|------|------------|
| **A2A** | Agent-to-Agent Protocol - How agents discover and communicate |
| **UCP** | Universal Commerce Protocol - Standard commerce data types |
| **ADK** | Agent Development Kit - Google's framework for building agents |
| **Tool** | Python function the LLM can invoke (has `ToolContext` parameter) |
| **Capability** | Feature set the agent supports (e.g., `dev.ucp.shopping.checkout`) |

## State Keys (constants.py)

```python
# Session state keys - naming conventions:
# - user:     User-scoped data (persists across turns)
# - __xxx__   System/internal data (managed by framework)
# - temp:     Temporary data (cleared after use)

ADK_USER_CHECKOUT_ID = "user:checkout_id"           # Current checkout session ID
ADK_PAYMENT_STATE = "__payment_data__"               # PaymentInstrument from client
ADK_UCP_METADATA_STATE = "__ucp_metadata__"          # Negotiated UCP capabilities
ADK_EXTENSIONS_STATE_KEY = "__session_extensions__"  # Active A2A extensions
ADK_LATEST_TOOL_RESULT = "temp:LATEST_TOOL_RESULT"   # Last tool result for output

# Response data keys (used in tool returns)
UCP_CHECKOUT_KEY = "a2a.ucp.checkout"                # Checkout data in response
UCP_PAYMENT_DATA_KEY = "a2a.ucp.checkout.payment_data"
UCP_RISK_SIGNALS_KEY = "a2a.ucp.checkout.risk_signals"

# Extension constants
A2A_UCP_EXTENSION_URL = "https://ucp.dev/specification/reference?v=2026-01-11"
UCP_AGENT_HEADER = "UCP-Agent"                       # HTTP header for client profile
```

## Agent Tools (agent.py)

| Tool | Purpose | Returns |
|------|---------|---------|
| `search_shopping_catalog(query)` | Search products by keyword | ProductResults |
| `add_to_checkout(product_id, quantity)` | Add item to checkout | Checkout |
| `remove_from_checkout(product_id)` | Remove item from checkout | Checkout |
| `update_checkout(product_id, quantity)` | Update item quantity | Checkout |
| `get_checkout()` | Get current checkout state | Checkout |
| `update_customer_details(email, address...)` | Set buyer and delivery info | Checkout |
| `start_payment()` | Validate checkout, set ready status | Checkout |
| `complete_checkout()` | Process payment, create order | Checkout + OrderConfirmation |

## Checkout State Machine

```
incomplete → ready_for_complete → completed
     ↑              ↑                 ↑
  add item    start_payment    complete_checkout
```

| State | Meaning | Transition |
|-------|---------|------------|
| `incomplete` | Missing buyer email or fulfillment address | Add required info |
| `ready_for_complete` | All info collected, awaiting payment | Call `complete_checkout()` |
| `completed` | Order created with OrderConfirmation | Terminal state |

## UCP Capabilities

```
dev.ucp.shopping.checkout      # Base checkout capability
dev.ucp.shopping.fulfillment   # Shipping (extends checkout)
dev.ucp.shopping.discount      # Promotional codes (extends checkout)
dev.ucp.shopping.buyer_consent # Consent management (extends checkout)
```

## Common Tasks

### Add a New Tool
```python
# In agent.py
def my_tool(tool_context: ToolContext, param: str) -> dict:
    """Tool docstring (visible to LLM for reasoning)."""
    # 1. Access state
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)
    metadata = tool_context.state.get(ADK_UCP_METADATA_STATE)

    # 2. Validate
    if not metadata:
        return {"message": "Missing UCP metadata", "status": "error"}

    # 3. Business logic
    result = store.some_method(...)

    # 4. Update state if needed
    tool_context.state[ADK_USER_CHECKOUT_ID] = result.id

    # 5. Return UCP-formatted response
    return {UCP_CHECKOUT_KEY: result.model_dump(mode="json")}

# Add to root_agent tools list
root_agent = Agent(..., tools=[..., my_tool])
```

### Add a Product
Edit `data/products.json`:
```json
{
  "productID": "NEW-001",
  "name": "New Product",
  "image": ["http://localhost:10999/images/new.jpg"],
  "brand": {"name": "Brand"},
  "offers": {"price": "9.99", "priceCurrency": "USD", "availability": "InStock"}
}
```

### Modify Checkout Flow
Key methods in `store.py`:
- `add_to_checkout()` - Creates checkout, adds items
- `_recalculate_checkout()` - Updates totals, tax, shipping
- `start_payment()` - Validates readiness, transitions state
- `place_order()` - Creates OrderConfirmation

## Key Files for Changes

| Change | File |
|--------|------|
| Add/modify tools | `agent.py` |
| Checkout logic | `store.py` |
| A2A/ADK bridging | `agent_executor.py` |
| UCP profiles | `data/ucp.json`, `chat-client/profile/agent_profile.json` |
| Products | `data/products.json` |
| Frontend components | `chat-client/components/` |
| Frontend types | `chat-client/types.ts` |

## Commands

```bash
# Start backend
cd a2a/business_agent && uv sync && uv run business_agent

# Start frontend
cd a2a/chat-client && npm install && npm run dev

# Verify endpoints
curl http://localhost:10999/.well-known/agent-card.json
curl http://localhost:10999/.well-known/ucp
```

## Response Format Pattern

```python
# For UCP data (checkout, products)
return {
    UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
    "status": "success",
}

# For errors
return {"message": "Error description", "status": "error"}
```

## Production Considerations

> **WARNING**: This sample is NOT production-ready. See `docs/08-production-notes.md`.

| Component | Current | Production |
|-----------|---------|------------|
| Session Storage | In-memory | Redis |
| Checkout Storage | Python dict | PostgreSQL |
| Authentication | None | JWT/API key |
| Secrets | Plaintext .env | Secret Manager |

## Documentation

| Guide | Topics |
|-------|--------|
| [Glossary](docs/00-glossary.md) | Key terms, acronyms, external resources |
| [Architecture](docs/01-architecture.md) | System components, data flow, mock store |
| [ADK Agent](docs/02-adk-agent.md) | Tools, callbacks, prompt engineering |
| [UCP Integration](docs/03-ucp-integration.md) | Capabilities, profiles, negotiation |
| [Commerce Flows](docs/04-commerce-flows.md) | Checkout lifecycle, payment flow |
| [Frontend](docs/05-frontend.md) | React components, A2A client |
| [Extending](docs/06-extending.md) | Add tools, products, capabilities |
| [Testing Guide](docs/07-testing-guide.md) | Testing, debugging, troubleshooting |
| [Production Notes](docs/08-production-notes.md) | Security gaps, deployment checklist |

## External Resources

| Resource | URL |
|----------|-----|
| **ADK Docs** | https://google.github.io/adk-docs/ |
| **A2A Protocol** | https://a2a-protocol.org/latest/ |
| **UCP Specification** | https://ucp.dev/specification/overview/ |
| **Gemini API** | https://ai.google.dev/gemini-api/docs |

## Dependencies

**Backend** (pyproject.toml):
- `google-adk[a2a]>=1.22.0`
- `ucp-sdk==0.1.0`
- `pydantic>=2.12.3`

**Frontend** (package.json):
- `react ^19.2.0`
- `vite ^6.2.0`
