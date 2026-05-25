---
name: mcp-platform
description: SailPoint MCP Platform (INIT-2410) — umbrella for MCP Server registry, observability, and MCP Gateway delivery (ISC, IIQ). Use when discussing MCP platform strategy, INIT-2410, registry, observability, or how gateway work fits the broader platform.
---

# MCP Platform

Use this skill for **strategic MCP Platform** context. For **tactical gateway delivery** (INIT-2704), also load the [gateway sub-skill](gateway/SKILL.md).

## Hub document

**Start here:** [`docs/mcp-platform/README.md`](../../../docs/mcp-platform/README.md)

## Platform pillars

| Pillar | Doc | Initiative |
| --- | --- | --- |
| **MCP Gateway** | [`docs/mcp-platform/gateway/`](../../../docs/mcp-platform/gateway/) | [INIT-2704](https://sailpoint.atlassian.net/browse/INIT-2704) — active delivery |
| **MCP Server registry** | [`docs/mcp-platform/mcp-server-registry.md`](../../../docs/mcp-platform/mcp-server-registry.md) | [INIT-2410](https://sailpoint.atlassian.net/browse/INIT-2410) — planned |
| **Observability** | [`docs/mcp-platform/mcp-observability.md`](../../../docs/mcp-platform/mcp-observability.md) | [INIT-2410](https://sailpoint.atlassian.net/browse/INIT-2410) — planned |
| **OAuth for MCP clients** | Gateway + INIT-2090 | [INIT-2090](https://sailpoint.atlassian.net/browse/INIT-2090) — dependency |

## Scope guardrails

- **INIT-2410** = umbrella (registry, observability, marketplace, multi-product gateway).
- **INIT-2704** = gateway sub-topic only — ISC MVP first; do not expand to full platform scope.
- **IIQ** MCP gateway routing is **future** platform work, not INIT-2704 Gate 1.

## Key people

- Ye Zhu — MCP Platform PM
- Maryam Agahi — INIT-2410 assignee
- Dattu Marneni — INIT-2704 / gateway EM delivery

## When to use which doc

| Question | Read |
| --- | --- |
| What is the overall platform vision? | Platform README + [Confluence strategy](https://sailpoint.atlassian.net/wiki/spaces/~7120200fd8a6740fdb4ca9bd0f88f478f134a5/pages/4614226238/Draft+SailPoint+MCP+Platform+Strategy) |
| Gateway MVP, Jira epics, week-1? | [gateway/SKILL.md](gateway/SKILL.md) |
| Server approval / catalog? | `mcp-server-registry.md` |
| Audit, metrics, FR12? | `mcp-observability.md` |
