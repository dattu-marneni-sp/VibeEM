# MCP Server Registry

**Parent:** [MCP Platform](README.md)  
**Initiative:** [INIT-2410 — MCP Platform](https://sailpoint.atlassian.net/browse/INIT-2410)  
**Status:** Planned — not in INIT-2704 gateway MVP scope

---

## Purpose

A **central registry** for MCP servers used at SailPoint: internal team servers, approved third-party servers, and customer-facing catalog entries. The registry is the governance layer that answers:

- Which MCP servers exist and who owns them?
- Which are approved for production / internal / experimental use?
- What tools does each server expose, and what policy applies?

Today, partial cataloging lives in Confluence ([Approved MCP Servers](https://sailpoint.atlassian.net/wiki/spaces/SDLC/pages/4951474326), [MCP Server Request Process](https://sailpoint.atlassian.net/wiki/spaces/SDLC/pages/4175036476)). The platform goal is to make that **machine-readable and gateway-integrated**.

---

## Planned capabilities

| Capability | Description |
| --- | --- |
| **Registration** | Teams register MCP server metadata (URL, owner, product, environment, tool namespace) |
| **Approval workflow** | Security / architecture review before production listing (align with [MCP Security Policies](https://sailpoint.atlassian.net/wiki/spaces/SEC/pages/4820926587/MCP+Agentic+Security+Policies)) |
| **Gateway integration** | Registered servers become routable targets on the MCP Gateway (tool namespacing, allowlists) |
| **Lifecycle** | Versioning, deprecation, ownership transfer |
| **Marketplace path** | Verified entries feed customer/marketplace listings ([AI-881](https://sailpoint.atlassian.net/browse/AI-881)) |

---

## Relationship to MCP Gateway

- **Gateway** = runtime entry point (auth, routing, policy enforcement).
- **Registry** = source of truth for *what* can be routed and *who* may call it.

INIT-2704 gateway MVP uses **static target registration** (AgentCore targets, admin CLI). INIT-2410 registry work should **replace or back** that with a durable catalog without duplicating gateway routing logic.

---

## Open questions

1. Registry as product UI vs API-only vs Confluence-backed MVP?
2. Single registry for ISC + IIQ + internal servers, or federated per product?
3. Overlap with existing SDLC MCP request process — migrate or integrate?

---

## References

- [MCP Platform hub](README.md)
- [MCP Gateway docs](gateway/mcp-gateway.md)
- [Draft MCP Platform Strategy](https://sailpoint.atlassian.net/wiki/spaces/~7120200fd8a6740fdb4ca9bd0f88f478f134a5/pages/4614226238/Draft+SailPoint+MCP+Platform+Strategy)
