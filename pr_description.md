# feat: Python Self-Healing Supply Chain Demo (Interactive + Gemini 3)

## 📝 Summary
This PR adds a comprehensive Python sample demonstrating an **Autonomous Supply Chain Agent** capable of "Self-Healing" when a primary supplier fails. It leverages the **Google Agent Development Kit (ADK)** and the latest **Gemini 3 Flash** model to orchestrate a recovery workflow using **UCP** (Commerce) and **AP2** (Governance) protocols.

## ✨ Key Features
*   **Interactive Simulation**: Includes a CLI-based `InventoryManager` where users simulate sales. The Autonomous Restock triggers automatically when inventory drops below a critical threshold.
*   **Dynamic Discovery (UCP)**: The agent dynamically resolves backup suppliers via `/.well-known/ucp` instead of hardcoded endpoints, demonstrating true network autonomy.
*   **Negotiation Capability (UCP)**: Handles multi-step checkout flows, including providing Shipping Address and Discount Codes (`PARTNER_20`) to finalize Tax and Totals.
*   **Governance & Trust (AP2)**:
    *   Implements **Detached JWS** signatures for verifiable user intent.
    *   Enforces a **Variance-Based Spending Policy** (15% threshold).
    *   **Human-in-the-Loop**: High-variance transactions pause for manual admin sign-off.
*   **Modern Stack**: Built with `google-genai` (Gemini 3 Flash Preview) and standard `pydantic` models for UCP/AP2 schemas.

## 🏗️ Architecture
*   **`buyer_agent.py`**: The ADK Agent utilizing a "Brain + Tools" pattern.
*   **`supplier_server.py`**: A lightweight Mock UCP Server (FastAPI) that handles Discovery, Checkout Negotiation, and Mandate Verification.
*   **`mock_db.py`**: Simulates a Product Catalog and Corporate Spending Policy.

## 🧪 How to Test
1.  **Start the Supplier Server**:
    ```bash
    python supplier_server.py
    ```
2.  **Run the Buyer Agent**:
    ```bash
    python buyer_agent.py
    ```
3.  **Interactive Loop**:
    *   Enter sales (e.g., `90` units) to drop inventory below 20.
    *   Observe the Agent detect the Primary Supplier failure (503).
    *   Watch the Agent discover the Backup Supplier and request approval for the price variance.
    *   Approve the purchase to see the Inventory restock.

## ✅ Checklist
- [x] Code adheres to UCP & AP2 Architectural Best Practices.
- [x] Includes detailed `README.md` with production architecture diagrams.
- [x] Secrets managed via `.env.local` (excluded from git).
- [x] Dependencies listed in `requirements.txt`.
