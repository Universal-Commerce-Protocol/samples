# Goofre ACO - Agentic Commerce Orchestrator

**UCP Conformance:** v1.2 (baseline 2026-01-23)

## The problem

A merchant has GMC, GA4, GBP, a Magento catalog, and a POS. None talk to each
other. When a Gemini agent asks "is this available for pickup in Brooklyn?", the
answer requires synthesizing inventory, availability, and checkout eligibility in
real time. An Agentic Commerce Orchestrator (ACO) does that synthesis. This sample
shows the UCP shapes that flow through one.

## Contents

- schema-demo/ - UCPProduct, UCPCartEvent (RFC #355 identity), UCPOrderEvent (AP2), UCPInsight, B2B order
- mcp-integration/ - Drop-in config for Claude Desktop / Copilot (6 MCP tools)
- a2a-negotiation/ - B2C pickup intent + B2B procurement intent with MOQ/Net Terms

## Vendor namespace extensions

- com.goofre.agentic_trust_score - AI discoverability scoring (additive, ignorable)
- com.goofre.b2b_wholesale - MOQ, tiered pricing, Net Terms, KYB (additive, ignorable)

## Source

https://github.com/Goofre-Agentic-Commerce-Orchestrator/agentic_commerce_orchestrator_ACO
