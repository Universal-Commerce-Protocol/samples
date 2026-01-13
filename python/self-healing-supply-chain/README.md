# Self-Healing Supply Chain Demo (UCP & AP2)

This project demonstrates an **Autonomous Supply Chain Agent** capable of "Self-Healing" when a primary supplier fails. It leverages two key next-generation protocols:

*   **Google ADK (Agent Development Kit)**: For orchestrating the autonomous agent, managing state, and integrating with Gemini 3 Flash.
*   **UCP (Universal Commerce Protocol)**: For dynamic supplier discovery, checking inventory, and negotiating standardized checkout sessions.
*   **AP2 (Agent Payments Protocol)**: For secure, policy-driven transaction governance and "Agentic Payments".

## 🚀 Scenario

1.  **Start State**: The demo begins in an **Interactive Mode** with 100 units of inventory. You simulate sales manually.
2.  **Trigger**: When inventory drops below the critical threshold (20 units), the **Autonomous Agent** wakes up to restock.
3.  **Monitoring**: The Buyer Agent checks "Supplier A" for "Industrial Widget X". Supplier A is **Offline (503)**.
2.  **Discovery (UCP)**: The Agent queries its network and discovers "Supplier B" (running locally on port 8000).
3.  **Governance (AP2)**: The Agent compares the new price (£550) against the standard (£400).
    *   **Total Cost**: £55,000.
    *   **Variance**: +37.5%.
    *   **Policy Check**: The Corporate Spending Policy (`mock_db.py`) limits auto-approval to £1,000 or <15% variance.
    *   **Result**: The Agent pauses and requests **Human Sign-off** (Human-in-the-loop).
4.  **Execution**: Once approved, the Agent constructs a cryptographically signed **AP2 Payment Mandate**, enables the UCP Checkout, and finalizes the order.

## 🛠️ Setup & Installation

### Prerequisites
*   Python 3.12+
*   Google GenAI API Key

### 1. Environment Configuration
Create a `.env.local` file in the root directory:
```bash
GOOGLE_API_KEY=your_api_key_here
```

### 2. Install Dependencies
```bash
pip install fastapi uvicorn requests python-dotenv
# Note: google-adk, ucp-sdk, ap2-sdk are currently mocked or included in this demo structure.
```

## 🏃‍♂️ How to Run

You will need **two separate terminal windows**.

### Terminal 1: The Backup Supplier (Server)
Start the mock supplier server. This represents "Supplier B".
```bash
python supplier_server.py
```
*Output: `🏭 [SUPPLIER] Server Online at http://0.0.0.0:8000`*

### Terminal 2: The Buyer Agent (Client)
Run the agent.
```bash
python buyer_agent.py
```

*   **Interactive Loop**: The agent will display current inventory (100).
*   **Input**: Enter a number (e.g., `85`) to simulate sales.
*   **Auto-Restock**: Once inventory drops below 20, the Self-Healing Agent automatically runs.
*   **Approval**: When the policy check fails, press `Enter` to grant admin approval.

## 🧠 Agent Architecture (Google ADK)

The Buyer Agent is built using the **Google Agent Development Kit (ADK)**, utilizing a modular "Brain + Tools" pattern:

*   **Model**: Uses `gemini-2.0-flash` for high-speed reasoning and decision making.
*   **Tools**: Encapsulates specific capabilities as Python functions (`discover_backup_suppliers`, `execute_ucp_transaction`).
*   **Runner**: The ADK `Runner` handles the event loop, routing user inputs (sales data) or system triggers (low inventory) to the model, which then decides which Tool to call.
*   **State**: Uses `InMemorySessionService` to maintain context across the multi-step recovery flow.

## � Best Practices Alignment

This demo adheres to the official **Google Developers UCP & AP2 Architecture**:

1.  **Dynamic Discovery**: Endpoints are never hardcoded. The Agent resolves capabilities dynamically via `/.well-known/ucp`.
2.  **Service-Based Architecture**: Separation of concerns between UCP (Commerce) and AP2 (Trust).
3.  **Verifiable Intent**: Utilizes cryptographic **AP2 Mandates** (Detached JWS) to anchor every transaction to a signed user intent.
4.  **Standardized Schemas**: Uses official `ucp-sdk` Pydantic models generated from the canonical JSON Schemas.

## �🏭 Production Architecture

In a real-world enterprise environment, this architecture scales from local scripts to distributed cloud services.

```mermaid
graph TD
    subgraph Buyer_Enterprise ["Enterprise Environment (Buyer)"]
        Agent["Supply Chain Agent (Cloud Run)"]
        Orch["Orchestrator (Temporal)"]
        PolicyDB["Policy Engine (OPA)"]
        
        subgraph Human ["Human-in-the-Loop"]
            Approver(("Supply Chain Manager"))
            Dashboard["Operations Dashboard"]
        end
    end

    subgraph External ["External Ecosystem"]
        Registry["UCP Registry"]
        SupplierA["Supplier A (Primary - DOWN)"]
        SupplierB["Supplier B (Backup - FOUND)"]
    end

    Agent -->|1. Monitor| SupplierA
    Agent -->|2. Discover| Registry
    Registry -->|3. Resolve| SupplierB
    Agent -->|4. Negotiate| SupplierB
    
    Agent -->|5. Policy Check| PolicyDB
    PolicyDB -- Fail --> Orch
    Orch -->|6. Request Approval| Dashboard
    Approver -->|7. Approve| Dashboard
    Dashboard -->|8. Sign Mandate| Agent
    
    Agent -->|9. Execute Payment| SupplierB
```

### Key Differences in Production
1.  **Decentralized Discovery**: Instead of a hardcoded `mock_db.py`, the Agent queries a **UCP Registry** or DID Resolver to find verified suppliers dynamically.
2.  **Cryptographic Trust**: AP2 Mandates are signed with real enterprise Keys (KMS/Vault), providing non-repudiable proof of intent.
3.  **Governance Dashboard**: The `input()` prompt is replaced by a secure **Operations Dashboard** or Slack/Mobile push notification for one-click approval.
