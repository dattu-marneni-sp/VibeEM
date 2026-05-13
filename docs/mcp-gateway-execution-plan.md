# MCP Gateway — Execution Plan

This is an EM-level execution plan for delivering a SailPoint MCP gateway built on **AWS Bedrock AgentCore Gateway** as the managed service foundation, satisfying the FRs and NFRs in:

- `[MCP Q1-2 PRD] SailPoint MCP Server Single URL and OAuth Support`
- `[MCP PRD] Tenant-Agnostic MCP Server Endpoint & OAuth Integration`

For background concepts, see `docs/mcp-gateway.md`.

This plan is intentionally a working draft — Jira epics are **not** created yet. The intent is to align with leadership and the PMs (Ye Zhu, Rahul Mishra) before locking scope.

## TL;DR For Leadership

- **What we're building.** A single, tenant-agnostic MCP endpoint for SailPoint, fronted by AWS Bedrock AgentCore Gateway, that routes authenticated MCP traffic to the correct tenant's ISC backend and provides centralized auth, tool discovery, telemetry, and policy.
- **Why now.** Per-tenant URLs block AWS Marketplace listing, "one-click install" in Cursor / Claude / VS Code, and competitive parity with Saviynt and Wiz, who already shipped marketplace MCP listings in mid-2025. Two PRDs already exist and the team is ready to start.
- **Approach.** Buy the gateway plane (AgentCore Gateway, AgentCore Identity), build the SailPoint-specific glue (tenant routing, client mapping, admin UI integration, telemetry pipeline). Avoid building a JSON-RPC / SSE proxy from scratch.
- **Headcount ask.** Recommended team: 1 EM, 1 tech lead, 3–4 backend engineers (1 with AWS depth, 1 with identity/OAuth depth), 1 SRE/DevOps, 0.5 SDET, with shared support from existing OAuth (Rahul Mishra), UI (Ben Coble), and Docs teams.
- **Timeline shape.** Phase 0 design + reconciliation (3 weeks) → Phase 1 PoC (6 weeks) → Phase 2 MVP (8–10 weeks) → Phase 3 closed beta (4 weeks) → Phase 4 GA (4 weeks). Total \~6 months from kickoff to GA for the P0 scope; Phase II features (DCR, dev portal, tool namespacing) follow after GA.
- **Risks to flag now.** Two PRDs disagree on URL and OAuth model; AgentCore is AWS-coupled (data residency, FedRAMP); bedrock-agentcore-control APIs are new and still evolving.

## Key Caveat: The Two PRDs Disagree

Before we write a line of code, the team needs PM alignment on three points where the PRDs conflict:

| Topic | PRD 1 (`fIBAFAE`) | PRD 2 (`NIDUAgE`) | What we need to decide |
| --- | --- | --- | --- |
| Public URL | `https://mcp.sailpoint.com/` | `https://mcp.identitynow.com/` | One canonical hostname (and FedRAMP / UAE1 variants). |
| Tenant resolution | `client_id → tenant_id` static mapping table | Email-based discovery via `login.sailpoint.com/oauth/authorize` | Static map for MVP, email discovery for GA, or both? |
| OAuth model | Authorization Code, static client registration | OAuth 2.1 + PKCE + Dynamic Client Registration (RFC 7591) | Pick the v1 protocol; defer DCR to Phase II if needed. |
| Backward compatibility | Existing tenant URLs continue indefinitely | Deprecate when traffic < 5 tenants | Set a deprecation policy now. |
| Audit / telemetry sink | Snowflake | Snowflake + alerts on anomalies | Confirm pipeline owner. |

**Recommended call:** EM (Dattu) + PMs (Ye, Rahul) + OAuth lead (Rahul Mishra) + UI lead (Ben Coble) + Masala EM (Dave Owens) before Phase 0 sign-off.

## How AgentCore Gateway Maps To The FRs / NFRs

This is the build-vs-buy table, which directly informs the workstream breakdown.

| Requirement | AgentCore Gives Us | We Have To Build / Configure |
| --- | --- | --- |
| FR1 — single endpoint URL | Gateway endpoint (`*.bedrock-agentcore.<region>.amazonaws.com`) | Custom domain (`mcp.sailpoint.com`) via Route 53 + ACM, CloudFront if needed. |
| FR2 — OAuth/JWT auth | `customJWTAuthorizer` with discovery URL + allowed clients | Wire SailPoint OAuth as the IdP (or Cognito as a bridge). |
| FR3 — `tools/list` / `tools/call` | Native MCP protocol; cache-first `ListTools`; live `tools/call` | Per-tenant target registration; tool namespacing strategy. |
| FR4 — tenant routing | Targets per backend; gateway routes by tool name | Mapping `client_id` (or email-derived `tenant_id`) → target ARN; routing Lambda interceptor if claim-based routing is needed. |
| FR5 — token expiration handling | Standard 401 from authorizer | Custom error response shape (`{error, message, request_id}`). |
| FR6 — backward compatibility | N/A — purely additive | Keep existing tenant-specific URLs unchanged. |
| FR7 — admin portal for client registration | N/A | UI changes in ISC Admin Portal (collab with Ben Coble's team). |
| FR8 — `client_id → tenant_id` mapping | N/A | Backing store (DynamoDB or RDS), CRUD APIs, auth on those APIs. |
| FR9 — Snowflake mapping query | N/A | CDC pipeline from mapping store to Snowflake. |
| FR10 — usage dashboards | CloudWatch metrics, gateway logs | Grafana / Snowflake dashboards, alarm definitions. |
| FR11 — structured error responses | Default error envelope | Custom error transformer (Lambda) for 4xx/5xx normalization. |
| FR12 — structured request logs | CloudWatch Logs JSON | Log shipping to OpenSearch + Snowflake; PII redaction. |
| NFR-001..003 — latency p50 / p95 / p99 | AgentCore latency baseline | Performance test suite; tune Lambda/cache; warm pools. |
| NFR-004..006 — scale | Managed scaling | Load tests at 100 concurrent / 1M req/month / 1k clients. |
| NFR-007..008 — uptime, error rate | AWS SLA | Multi-AZ; canary alarms; runbook. |
| NFR-009..010 — TLS, JWT validation | Native | Configure TLS policy, allowed clients, token verification. |
| NFR-011..013 — usability | N/A | Setup docs, error messages with hints, time-to-config tests. |
| NFR-014..015 — cost | AWS billing | Cost tagging, monthly cost reports, budget alerts. |
| Security NFRs (PRD 2) — zero cross-tenant leakage | Per-target credential isolation | Conformance tests, fuzz testing, security review. |

The honest read: AgentCore covers the heavy lifting on the gateway plane (protocol, auth scaffolding, scale, observability primitives). The SailPoint-specific work concentrates on **identity integration, client/tenant mapping, admin UX, telemetry pipeline, and FedRAMP / UAE1 strategy**.

## Phased Execution Plan

### Phase 0 — Reconciliation & Design (3 weeks)

**Goal:** Lock product scope, pick the canonical URL, choose the OAuth model, sign off on the architecture.

- Reconcile PRDs with Ye, Rahul, Dave Owens, Ben Coble.
- Architecture review: AgentCore Gateway + SailPoint OAuth + tenant routing model.
- Decision: AgentCore-managed JWT vs. custom Lambda authorizer.
- Define interface between gateway and ISC tenant backends (request/response contract, headers, identity propagation).
- Spike: AgentCore Gateway in a sandbox AWS account with a stub MCP server and a Cognito JWT (1 engineer, 3 days).
- Cost model: estimate AgentCore + Lambda + storage at expected load (NFR-014/15).
- Output: signed HLD, exit criteria for Phase 1.

### Phase 1 — Foundation / PoC (6 weeks)

**Goal:** End-to-end path working for one demo tenant, in a non-production AWS account.

- AWS account, IAM roles, VPC/networking baseline.
- AgentCore Gateway provisioned via IaC (CDK or Terraform).
- Custom domain `mcp.sailpoint.com` (or `mcp.identitynow.com` once decided) wired via Route 53 + ACM.
- SailPoint OAuth integrated as `customJWTAuthorizer` (or via Cognito federation if a bridge is required).
- One AgentCore Gateway target pointing at one ISC tenant MCP backend.
- `tools/list` and `tools/call` working end-to-end from Cursor and Claude Desktop using the universal URL.
- CloudWatch logs flowing; minimal dashboard.
- Output: working demo + design validation report; updated cost estimate against actuals.

### Phase 2 — MVP (8–10 weeks)

**Goal:** All P0 FRs and NFRs satisfied; ready for closed beta.

Workstreams in parallel:

- **WS-A Routing & Targets.** `client_id → tenant_id` mapping store, target registration automation, multi-tenant routing, hot-path caching of mappings.
- **WS-B Auth.** Final OAuth model implemented end-to-end (PKCE, scopes, revocation, expired-token UX).
- **WS-C Admin Portal.** With Ben Coble's UI team — MCP client registration page, scope assignment, client lifecycle (FR7).
- **WS-D Telemetry.** Snowflake pipeline for client metadata (FR9) and usage logs (FR10/12), Grafana dashboards, alarm definitions.
- **WS-E Error & Health.** Standardized error envelope (FR11), `/health` endpoint, structured logs with no PII (FR12).
- **WS-F Backward Compatibility.** Test harness validating tenant-specific URLs continue to work (FR6).
- **WS-G Performance.** Load tests for NFR-001..006; tune Lambda concurrency, cache TTLs.
- **WS-H Documentation.** Cursor / Claude Desktop / Claude Code / VS Code setup guides; troubleshooting; migration guide.

Exit criteria: P0 acceptance criteria met for every FR/NFR; SLO dashboards green; runbook drafted.

### Phase 3 — Closed Beta (4 weeks)

**Goal:** Real customers (or internal SailPoint AI use cases) on the gateway with limited blast radius.

- Pilot with 5–10 tenants (mix of internal + external if PMs agree).
- Operational readiness review (ORR) with SRE.
- Daily error / latency review; weekly customer feedback sync.
- Fix top 5 friction points before GA.
- Confirm Snowflake telemetry and dashboards meet FR9/10/12.

### Phase 4 — GA (4 weeks)

**Goal:** Public availability on `mcp.sailpoint.com` (or chosen URL), AWS Marketplace listing if scope.

- Documentation finalized; community / DevRel announcement.
- AWS Marketplace listing (if PRD 2 scope is in).
- 24×7 on-call coverage handed to SRE.
- Launch metrics tracked: adoption (≥10 customers in 90 days per PRD 2), latency, error rate, cost.

### Phase II (Post-GA)

Per PRD 1 explicit deferrals — separate planning when the time comes:

- Dynamic Client Registration (RFC 7591).
- Developer self-service portal.
- Tool namespacing / discovery UI.
- Per-tenant rate limiting.
- FedRAMP / UAE1 region rollouts (may move earlier depending on customer asks).

## Workstream → Skills Map

| Workstream | Primary skills | Secondary skills |
| --- | --- | --- |
| WS-A Routing & Targets | AWS (Lambda, DynamoDB, IaC), Python or Go, MCP/JSON-RPC understanding | Performance engineering |
| WS-B Auth | OAuth 2.0 / 2.1, PKCE, JWT, IdP integration (Cognito, Okta-style) | Security review experience |
| WS-C Admin Portal | React / TypeScript (matches existing ISC UI stack), API integration | UX collaboration with Ben Coble's team |
| WS-D Telemetry | Snowflake, OpenSearch, Grafana, data engineering | Observability tooling, dashboarding |
| WS-E Error & Health | API design, structured logging | Compliance / PII awareness |
| WS-F Backward Compat | Test engineering, contract testing | Existing ISC API knowledge |
| WS-G Performance | k6 / Locust, AWS Lambda tuning, profiling | Capacity planning |
| WS-H Documentation | Tech writing, DevRel | Cursor / Claude / VS Code MCP client experience |
| Cross-cutting | AWS IaC (Terraform / CDK), CI/CD, threat modeling, cost engineering | Incident response, on-call |

## Team Shape — Three Staffing Options

These are starting points to pitch to leadership. All assume some shared support from OAuth, UI, and Docs teams.

### Option A — Lean (4 engineers + EM)

- 1 EM
- 1 staff/tech lead (AWS + identity)
- 2 backend engineers (one MCP/Lambda, one telemetry/Snowflake)
- 0.5 SDET, 0.25 SRE (shared)

Risk: slower to GA (\~7–8 months), one person deep on each axis is a single point of failure, hard to parallelize WS-A through WS-D.

### Option B — Recommended (6 engineers + EM)

- 1 EM
- 1 staff/tech lead
- 1 senior backend (routing, AgentCore, Lambda)
- 1 senior identity engineer (OAuth, JWT, PKCE)
- 1 backend engineer (telemetry, Snowflake)
- 1 frontend engineer (or a borrowed slot from Ben's UI team)
- 0.5 SDET, 0.5 SRE

Hits the \~6 month GA target, leaves capacity for Phase II planning in parallel.

### Option C — Aggressive (8 engineers + EM)

Adds a dedicated SRE, full-time SDET, and a second backend on routing/perf. Use only if leadership wants to pull GA in by 4–6 weeks or do FedRAMP in parallel.

## Timeline Snapshot

```
Week:        0    3    6    9    12   15   18   21   24
Phase:       |P0--|P1-------|P2--------------|P3---|P4---|
Outputs:     HLD  PoC       MVP              Beta  GA
                            (P0 FR/NFRs)     (5-10 (10+
                                              tenants) customers)
```

## Risks

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| PRDs not reconciled in time | Medium | High | Phase 0 as a hard gate; weekly PM sync. |
| AgentCore API changes (still GA-fresh) | Medium | Medium | Pin SDK versions; abstract behind internal interface. |
| AWS lock-in / FedRAMP gap | Medium | High | Keep gateway plane swappable; don't hardcode AgentCore semantics into business code. |
| Latency NFR-001 (p95 < 300ms overhead) hard to hit cold | Medium | Medium | Provisioned Lambda concurrency, mapping cache, regional warm pools. |
| Cross-tenant leakage in routing logic | Low | Critical | Threat model in Phase 0; routing tests + fuzzers in Phase 2; independent security review before Beta. |
| OAuth team bandwidth (Rahul) | Medium | High | Lock dependency dates in Phase 0; escalate via leadership if slipping. |
| Cost (NFR-015 < $100/month) likely unrealistic at real load | High | Low | Reframe NFR-015 with PM during Phase 0; set realistic budget. |

## Dependencies

- **OAuth / Platform team (Rahul Mishra).** Token issuance, JWKS endpoint, login-to-tenant mapping (PRD 2).
- **ISC Admin UI team (Ben Coble).** MCP client registration page, scope picker.
- **ISC API Gateway / Tenant team.** Accept gateway-injected identity headers; ensure tenant MCP backends are stable.
- **Data Platform / Snowflake team.** Sink for client mappings (FR9) and request logs (FR12).
- **Security.** Threat model sign-off, JWT validation review, cross-tenant test plan.
- **DevRel / Docs.** Setup guides for Cursor / Claude / VS Code, marketplace listing copy.

## Leadership Pitch — Recommended Structure

If you only have 1 page or 5 slides for an LT review, this ordering tends to work:

1. **The problem in one sentence.** "Per-tenant MCP URLs block AWS Marketplace, one-click installs, and competitive parity — Saviynt and Wiz already shipped."
2. **What we'll build.** One slide diagram: client → `mcp.sailpoint.com` → AgentCore Gateway → tenant ISC backends.
3. **Buy vs. build.** AgentCore Gateway gives us 70% of the MCP plane (protocol, auth scaffolding, scale, telemetry primitives). We focus the team on SailPoint-specific glue, not on writing a JSON-RPC proxy.
4. **Phased plan.** The 5-phase chart above. Highlight that Phase 0 closes open product decisions.
5. **Headcount and timeline ask.** Option B by default; show A and C as flex.
6. **Top 3 risks.** AWS lock-in / FedRAMP, PRD reconciliation, cross-tenant security.
7. **Decision asked of leadership.** (a) approve Option B staffing, (b) approve AgentCore as managed-service foundation, (c) sponsor the PM reconciliation meeting in week 1.

## What I'd Want To Validate Before Locking This Plan

- AgentCore Gateway pricing at expected SailPoint load (need to model 1M+ requests/month with tools/list cache hits).
- Whether SailPoint's existing OAuth server can be configured directly as `customJWTAuthorizer`, or whether Cognito is needed as a bridge.
- FedRAMP and UAE1 region availability of AgentCore.
- Whether the Masala (MCP) team is being absorbed, partnered with, or kept separate.

## Pre-Epic Outline (For When We're Ready)

When you're ready to create Jira epics, the natural cut points are the workstreams above. Suggested epic structure (intentionally not creating these yet):

- **EPIC: MCP Gateway Foundation (Phase 0–1).** HLD, AWS account setup, AgentCore baseline, custom domain, PoC demo.
- **EPIC: Tenant Routing & Backend Targets (WS-A).** Mapping store, target registration, routing logic.
- **EPIC: OAuth & Identity Integration (WS-B).** SailPoint OAuth as JWT authorizer, PKCE, scope handling.
- **EPIC: ISC Admin Portal — MCP Client Registration (WS-C).** UI work with Ben Coble's team.
- **EPIC: Telemetry & Snowflake Integration (WS-D).** Mapping CDC, request logs, dashboards, alarms.
- **EPIC: Error Handling & Health (WS-E).** Error envelope, `/health`, log redaction.
- **EPIC: Backward Compatibility & Migration (WS-F).** Tests, migration guide.
- **EPIC: Performance, Security, Load Testing (WS-G).** NFR validation.
- **EPIC: Documentation & GA Launch (WS-H + Phase 4).** Setup guides, marketplace listing, GA cutover.

Each epic is sized roughly 4–8 stories; ticket-level breakdown is best done after Phase 0 sign-off so we don't create tickets that get rewritten.

## References

- `[MCP Q1-2 PRD] SailPoint MCP Server Single URL and OAuth Support` — Confluence tiny link `fIBAFAE`
- `[MCP PRD] Tenant-Agnostic MCP Server Endpoint & OAuth Integration` — Confluence tiny link `NIDUAgE`
- `docs/mcp-gateway.md` — concept primer
- [AWS — Bedrock AgentCore Gateway](https://aws.amazon.com/bedrock/agentcore/)
- [AWS — Transform your MCP architecture: Unite MCP servers through AgentCore Gateway](https://aws.amazon.com/blogs/machine-learning/transform-your-mcp-architecture-unite-mcp-servers-through-agentcore-gateway/)
