# MCP Observability

**Parent:** [MCP Platform](README.md)  
**Initiative:** [INIT-2410 — MCP Platform](https://sailpoint.atlassian.net/browse/INIT-2410)  
**Status:** Planned — thin observability in INIT-2704 gateway MVP ([DPDE-1779](https://sailpoint.atlassian.net/browse/DPDE-1779) FR12)

---

## Purpose

**Platform-wide observability** for MCP traffic: who called which tool, latency, errors, tenant isolation, and compliance audit. Gateway MVP delivers **edge logging**; the platform delivers **unified dashboards, SLOs, and cross-server analytics**.

---

## Layers

| Layer | Owner (planned) | What to capture |
| --- | --- | --- |
| **Gateway edge** | INIT-2704 / DPDE | Request ID, client_id, tenant_id, tool name, status, latency ([FR12](gateway/mcp-gateway-mvp-spec.md)) |
| **Downstream MCP servers** | Product teams (e.g. sp-mcp-server) | Tool-specific business context, ISC API correlation |
| **Platform aggregation** | INIT-2410 | Cross-tenant/product metrics, anomaly detection, audit export |
| **Agent / SAF** | SAF initiative | Agent identity linkage where MCP calls map to governed agents |

---

## Gateway MVP (INIT-2704) — in scope now

From [`mcp-gateway-mvp-spec.md`](gateway/mcp-gateway-mvp-spec.md):

- Structured request logging at gateway
- Correlation IDs for support/debug
- Minimal metrics for pilot (not full Snowflake CDC / enterprise SIEM in Gate 1)

See [DPDE-1779](https://sailpoint.atlassian.net/browse/DPDE-1779) and [DPDE-1780](https://sailpoint.atlassian.net/browse/DPDE-1780) (NFR validation).

---

## Platform vision (INIT-2410) — later

- Central MCP audit trail (compliance, SOC2-style evidence)
- Dashboards: tool popularity, error rates, p95 latency by tenant/product
- Alerting on cross-tenant routing anomalies, auth failures, rate-limit breaches
- Integration with existing SailPoint telemetry (Datadog, Snowflake, etc.) — TBD

**De-risk reference:** [sailpoint-agentcore-pdp](https://github.com/sailpoint-core/sailpoint-agentcore-pdp) PDP audit interceptor patterns.

---

## Open questions

1. Single observability pipeline for ISC gateway + IIQ + internal MCPs?
2. PII/redaction policy at gateway vs downstream?
3. Customer-visible MCP audit vs internal-only?

---

## References

- [MCP Platform hub](README.md)
- [MCP Gateway execution plan — observability sections](gateway/mcp-gateway-execution-plan.md)
- [MCP / Agentic Security Policies](https://sailpoint.atlassian.net/wiki/spaces/SEC/pages/4820926587/MCP+Agentic+Security+Policies)
