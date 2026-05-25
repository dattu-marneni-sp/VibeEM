---
name: mcp-gateway-delivery
description: MCP Platform sub-topic — SailPoint MCP Gateway delivery (INIT-2704). Use for universal URL, OAuth/PKCE, AgentCore Gateway, tenant routing to sp-mcp-server, global URL rollout, DPDE epics, week-1 execution, and client migration off sp-token.
---

# MCP Gateway (platform sub-topic)

**Parent:** [MCP Platform](../SKILL.md) · **Initiative:** [INIT-2704](https://sailpoint.atlassian.net/browse/INIT-2704)

## Document map (read in order)

1. **Concept primer** — [`docs/mcp-platform/gateway/mcp-gateway.md`](../../../docs/mcp-platform/gateway/mcp-gateway.md)
2. **MVP spec (canonical scope)** — [`mcp-gateway-mvp-spec.md`](../../../docs/mcp-platform/gateway/mcp-gateway-mvp-spec.md)
3. **Execution plan** — [`mcp-gateway-execution-plan.md`](../../../docs/mcp-platform/gateway/mcp-gateway-execution-plan.md)
4. **Delivery kit (week-1, Jira, RACI)** — [`mcp-gateway-delivery-kit.md`](../../../docs/mcp-platform/gateway/mcp-gateway-delivery-kit.md)
5. **Rollout sync (May 2026)** — [`mcp-gateway-rollout-migration-sync.md`](../../../docs/mcp-platform/gateway/mcp-gateway-rollout-migration-sync.md)

## Critical constraints

- **Do not reimplement** access-request MCP tools — route to [sp-mcp-server](https://github.com/sailpoint-core/sp-mcp-server).
- **Starter gateway code:** [sailpoint-agentcore-pdp](https://github.com/sailpoint-core/sailpoint-agentcore-pdp).
- **Two tracks:** Global URL ([APIMGMT-1699](https://sailpoint.atlassian.net/browse/APIMGMT-1699)) vs AgentCore GW — see rollout sync doc.
- **Backend contract:** `/{version}/access-requests/mcp`; env vars `SP_MCP_GLOBAL_MCP_PUBLIC_URL`, `SP_MCP_GLOBAL_AUTHORIZATION_SERVER_ISSUER`.

## Jira quick index

- Kickoff: [DPDE-1767](https://sailpoint.atlassian.net/browse/DPDE-1767)
- FR1 URL: [DPDE-1768](https://sailpoint.atlassian.net/browse/DPDE-1768)
- Migration/compat: [DPDE-1773](https://sailpoint.atlassian.net/browse/DPDE-1773)
- Full index: MVP spec §4.1

## Scripts

- `scripts/create_mcp_gateway_jira_stories.py` — week-1 story creation

## Not in gateway MVP scope

- Full MCP Server registry (see platform `mcp-server-registry.md`)
- Platform-wide observability (see `mcp-observability.md`)
- IIQ MCP backends (future platform phase)
