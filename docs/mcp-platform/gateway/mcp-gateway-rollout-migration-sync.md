# INIT-2704 — MCP rollout & migration sync (May 2026)

**MCP Platform:** [`../README.md`](../README.md) · sub-topic: **MCP Gateway**

**Status:** Active  
**Last updated:** 2026-05-25  
**Owner:** Dattu Marneni (EM)  
**Initiative:** [INIT-2704](https://sailpoint.atlassian.net/browse/INIT-2704)  
**Epic:** [DPDE-1767](https://sailpoint.atlassian.net/browse/DPDE-1767) — Understanding and kickoff  

**Related documents:** [MCP Platform hub](../README.md) · [`mcp-gateway.md`](mcp-gateway.md) · [`mcp-gateway-execution-plan.md`](mcp-gateway-execution-plan.md) · [`mcp-gateway-mvp-spec.md`](mcp-gateway-mvp-spec.md) · [`mcp-gateway-delivery-kit.md`](mcp-gateway-delivery-kit.md)

**Confluence (published):** [INIT-2704 — MCP rollout and migration sync (May 2026)](https://sailpoint.atlassian.net/wiki/spaces/data/pages/5135074261/INIT-2704+MCP+rollout+and+migration+sync+May+2026)

---

## Context

Slack sync ([May 22–25 thread](https://sailpoint.slack.com/archives/C09R91SCJ9L/p1779485709467059)): **Jinder Aujla** raised how the **MCP Gateway build** will affect rollout when **access-request OAuth metadata** changes and **registered MCP clients** may need to migrate if auth moves off **sp-token**.

| When | Who | Message |
| --- | --- | --- |
| May 22 | Jinder Aujla | Global URL testing is very close; asked how AgentCore MCP GW rollout affects access-request metadata and registered clients (sp-token → new auth server). |
| May 23 | Ye Zhu | Clarified: future AgentCore GW dependency vs impact on current single-URL launch? |
| May 25 | Jinder | **Future:** registered clients will need to switch after MCP GW rollout. **Near term:** OK for now. |
| May 25 | Ye Zhu | Acknowledged — will factor into planning. |

---

## Two tracks (keep sequenced)

| Track | What | Owner | Status |
| --- | --- | --- | --- |
| **A — Global URL** | `mcp.api.cloud.sailpoint.com`, RFC 9728 OAuth metadata, sp-gateway routing | Lori / API Mgmt ([APIMGMT-1699](https://sailpoint.atlassian.net/browse/APIMGMT-1699)) | **In testing** — very close; minor issues |
| **B — AgentCore MCP Gateway** | Universal URL, OAuth/PKCE, tenant routing → [sp-mcp-server](https://github.com/sailpoint-core/sp-mcp-server) | Data Engineering ([DPDE-1767](https://sailpoint.atlassian.net/browse/DPDE-1767)) | **Gate 1 MVP** — 4-week internal pilot |

**Key point:** Track A does **not** block today. Track B introduces **client migration** when auth/metadata model changes.

---

## Implications for INIT-2704

1. **Do not reimplement** access-request tools — gateway routes to `sp-mcp-server` (`/access-requests/mcp`).
2. **OAuth metadata contract** — gateway and backend must agree on **host** and **issuer**:
   - `SP_MCP_GLOBAL_MCP_PUBLIC_URL`
   - `SP_MCP_GLOBAL_AUTHORIZATION_SERVER_ISSUER`
3. **Backward compatibility (FR6)** — tenant-direct URLs stay valid; document what changes for **registered clients** when GW ships ([DPDE-1773](https://sailpoint.atlassian.net/browse/DPDE-1773)).
4. **Rollout sequencing** — global URL launch → AgentCore GW → **client re-registration window** (coordinate with Ye, Lori, Jinder).

---

## Actions

| # | Action | Owner | Jira / artifact |
| --- | --- | --- | --- |
| 1 | Client migration + backward-compat plan | DE + Masala | [DPDE-1773](https://sailpoint.atlassian.net/browse/DPDE-1773) |
| 2 | Align OAuth issuer/host with backend env vars | DE + access-request | DPDE-1769 / FR2 |
| 3 | Publish rollout sequencing with PM | Dattu + Ye + Lori/Jinder | [DPDE-1767](https://sailpoint.atlassian.net/browse/DPDE-1767), this doc |
| 4 | Week-1 decisions: URL model, PKCE redirect, Kartik/APIMGMT boundary | EM | DPDE-1835–1838 |

---

## Gate 1 exit criteria (unchanged)

- Fork [sailpoint-agentcore-pdp](https://github.com/sailpoint-core/sailpoint-agentcore-pdp); MCP target → tenant `/access-requests/mcp`.
- Cursor E2E: OAuth → `tools/list` → `tools/call`.
- **Written migration note** for sp-token / registered clients (add to Gate 1 demo).

---

## Suggested Slack reply (DE)

> Thanks Jinder — helpful heads-up. For the global URL work we're aligned there's no immediate conflict. For INIT-2704 (AgentCore MCP Gateway), we'll treat **client migration** and **OAuth/metadata alignment** with access-request as explicit deliverables — including what changes for registered clients when we move off sp-token. Captured in [Confluence](https://sailpoint.atlassian.net/wiki/spaces/data/pages/5135074261/INIT-2704+MCP+rollout+and+migration+sync+May+2026) and [DPDE-1767](https://sailpoint.atlassian.net/browse/DPDE-1767). Happy to sync with Ye and Lori on rollout sequencing.

---

## Changelog

| Date | Change |
| --- | --- |
| 2026-05-25 | Initial sync from Slack thread; Jira comment on DPDE-1767; Confluence page published |
