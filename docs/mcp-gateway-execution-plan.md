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

**Goal:** All P0 FRs and NFRs satisfied for a single primary region; ready for closed beta.

The MVP runs as 8 parallel workstreams. Each is sized for one engineer (or pair) over the phase, with explicit week-by-week sequencing inside the phase.

#### Sequencing Inside Phase 2

```
Week:                1   2   3   4   5   6   7   8   9   10
WS-A Routing         |design|--build---|integrate|test|
WS-B Auth            |design|--build---|integrate|test|
WS-C Admin Portal              |design|------build------|test|
WS-D Telemetry           |spike|--build---|wire----|verify|
WS-E Error & Health  |design|build|----------------verify|
WS-F Backward Compat                       |build harness|run|
WS-G Performance                                |baseline|tune|sign off|
WS-H Documentation                       |draft|review|polish|
Cross-cutting        |IaC, CI/CD, threat model, weekly demos
```

Weeks 1–2 are design / spikes that unblock the longest paths (WS-A and WS-B). WS-C starts in week 3 once the auth contract with WS-B is locked. WS-G runs against the latest build from week 7.

#### WS-A — Routing & Targets (FR3, FR4, FR8)

- **Goal.** Resolve every authenticated request to the correct tenant ISC backend, with sub-10ms routing overhead and zero cross-tenant leakage.
- **Deliverables.**
  - `client_id → tenant_id` mapping store (DynamoDB or RDS — decision in Phase 0).
  - Mapping CRUD API behind admin auth, used by WS-C.
  - AgentCore Gateway target provisioning automation (one target per tenant, or one target per backend with claim-based routing — pick one).
  - Routing Lambda interceptor (if AgentCore's native routing is insufficient) that reads `tenant_id` claim and selects the target.
  - Hot-path in-memory cache (TTL ≤ 60s) with cache-miss path to mapping store.
  - Routing decision logs (correlated with WS-D).
- **Acceptance.**
  - p50 routing overhead < 10ms; p95 < 50ms (contributes to NFR-001..003).
  - 100% of requests hit a tenant target derived only from token claims (no path/header inputs).
  - Negative tests: tampered tokens, missing claims, revoked clients all return correct 4xx.
- **Decisions to lock.** Mapping store choice; one-target-per-tenant vs one-target-with-routing-Lambda; cache invalidation strategy when an admin rotates a mapping.
- **Dependencies.** WS-B (token claim shape); WS-C (admin write path); ISC tenant team (backend URL contract).
- **Risks.** AgentCore target limits per gateway (verify in Phase 1 spike); cold-start on routing Lambda eating latency budget.

#### WS-B — Auth & Identity (FR2, FR5, NFR-009, NFR-010)

- **Goal.** SailPoint OAuth integrated as the gateway's authorizer; JWTs validated on every request; clear UX on token expiry.
- **Deliverables.**
  - Decision and implementation of `customJWTAuthorizer` config — direct against SailPoint OAuth or via Cognito as a bridge.
  - JWKS caching strategy (refresh interval, fallback on validation endpoint outage per PRD 2 NFR3).
  - Scope handling (e.g. `sp:mcp:all`, `mcp:read`, `mcp:submit_access_request`).
  - Token-expired error response (`401` with `{error: "token_expired", message, hint}` and `request_id`).
  - PKCE flow validated against Cursor / Claude Desktop / Claude Code via `mcp-remote`.
  - VS Code header-token path validated (PRD 1 §6.1).
- **Acceptance.**
  - 100% of requests pass through JWT validation (NFR-010).
  - 0 unauthenticated requests reach a backend in security tests.
  - Round-trip from "user opens client" to "tools/list returns" under 10s in fresh browser (contributes to NFR-011).
- **Decisions to lock.** Cognito bridge yes/no; scope taxonomy with Rahul Mishra; refresh-token lifetime; redirect URI policy for static clients.
- **Dependencies.** Rahul Mishra (OAuth platform team) — issuer URL, JWKS endpoint, scope registration.
- **Risks.** SailPoint OAuth not yet exposing a discovery URL compatible with `customJWTAuthorizer`; PKCE quirks across MCP clients.

#### WS-C — ISC Admin Portal: MCP Client Registration (FR7)

- **Goal.** Admins can create, label, view, and revoke MCP clients in the existing ISC Admin Portal.
- **Deliverables.**
  - "MCP Clients" section in the ISC Admin UI (with Ben Coble's team).
  - Create flow: name, description, grant type (`Authorization code`), scopes, redirect URIs.
  - Display generated `client_id`, link to consent screen URL.
  - List / search / filter / revoke flows.
  - Audit log entries on every admin action.
  - API contract with WS-A's mapping store.
- **Acceptance.**
  - End-to-end: admin creates a client, developer pastes the `client_id` into Cursor, tools/list works.
  - All actions audited; revoke is effective within 60s (cache TTL).
- **Decisions to lock.** Whether tenant_id binding is set at client creation (PRD 1 model) or derived from the admin's own session (cleaner). Whether to expose this in the Customer-facing portal or only the SailPoint internal admin portal in MVP.
- **Dependencies.** Ben Coble's UI team (component library, design review); ISC platform team (admin auth, audit log infra).
- **Risks.** UI bandwidth; design review cycle; deciding scope of "labeling" (FR7 mentions it but acceptance criteria are thin).

#### WS-D — Telemetry, Logging & Snowflake (FR9, FR10, FR12)

- **Goal.** Every request and every admin action is observable in dashboards and queryable in Snowflake within minutes.
- **Deliverables.**
  - Structured JSON logs from gateway: `request_id`, `client_id`, `tenant_id`, `method`, `status_code`, `latency_ms`, `timestamp`, `error_type`, `error_message`.
  - PII / token redaction in log pipeline (no bearer tokens, no PII fields, NFR-008 + PRD 2 NFR1).
  - CloudWatch → OpenSearch shipping for ops queries.
  - CDC pipeline from mapping store to Snowflake (FR9).
  - Request log shipping to Snowflake (FR12).
  - Grafana dashboards: request rate, p50/p95/p99 latency, error rate, requests per tenant, top MCP methods, auth failures (PRD 1 §6.3 mock).
  - CloudWatch alarms: error rate > 1% (5 min), p95 latency > 500ms (5 min), 5xx spike, auth failure spike.
- **Acceptance.**
  - Dashboards filterable by 1h / 6h / 24h / 7d.
  - Alarms paged within 5 minutes of threshold breach.
  - Snowflake queries return mapping + usage data within 15 minutes of the event.
  - PII / token redaction passes a security review checklist.
- **Decisions to lock.** Log retention durations; alert routing (PagerDuty / Slack / email); whether to use Grafana, Datadog, or both.
- **Dependencies.** Data Platform / Snowflake team; Security for redaction sign-off.
- **Risks.** Log volume / cost (1M req/month with verbose logs is non-trivial); CDC lag; PII leaks slipping through.

#### WS-E — Error Handling & Health (FR11)

- **Goal.** Every failure path returns a consistent envelope; clients can programmatically handle every status code we promise.
- **Deliverables.**
  - `GET /health` returns `{status, version, timestamp}` with HTTP 200.
  - Error envelope `{error, message, request_id}` for all 4xx / 5xx.
  - Status code coverage per PRD 1 FR11: 400 malformed, 401 auth failure, 403 unregistered/revoked, 502 backend bad, 503 service unavailable.
  - Error message audit: every response includes a next-step hint (NFR-013).
  - Stack traces only in 5xx logs, never in client responses.
- **Acceptance.**
  - Contract test asserts envelope shape on every status code.
  - 100% of error responses include a `request_id` traceable in WS-D logs.
- **Decisions to lock.** Whether to expose `request_id` in headers, body, or both; localization (likely deferred).
- **Dependencies.** WS-D for `request_id` propagation.
- **Risks.** Inconsistency between AgentCore default errors and our envelope (may need a Lambda response transformer).

#### WS-F — Backward Compatibility (FR6)

- **Goal.** Existing tenant-specific MCP URLs continue to work, untouched, throughout MVP and beyond.
- **Deliverables.**
  - Test harness against existing tenant-specific endpoints in dev/staging before and after gateway deploy.
  - Compatibility test suite covering `tools/list`, `tools/call`, error envelopes, response timing.
  - Migration guide (paired with WS-H) showing the path from tenant URL to gateway URL.
  - Per-tenant traffic graphs (gateway vs direct) shipped to WS-D.
- **Acceptance.**
  - Zero regressions on tenant-direct URLs.
  - Test suite runs on every CI build of the gateway.
- **Decisions to lock.** Sunset criteria for tenant-direct URLs (PRD 2 says "<5 tenants of traffic"); communication policy if/when sunset begins.
- **Dependencies.** ISC tenant team; access to representative dev tenants.
- **Risks.** Subtle drift in response headers/timing between gateway and direct paths.

#### WS-G — Performance, Scale, Reliability (NFR-001..008)

- **Goal.** Prove the gateway hits the NFRs at and beyond the target load.
- **Deliverables.**
  - Load test harness (k6 or Locust) parameterized by concurrency and request mix.
  - Baseline runs at 10, 50, 100 concurrent (NFR-004).
  - Sustained 1M-request burndown over 24h to validate NFR-005.
  - Profiling / tuning of routing Lambda (cold start, memory, concurrency reservations).
  - Cache effectiveness report (hit rate ≥ 95% on mapping cache).
  - Multi-AZ failover test (NFR-007).
  - Runbook for top 10 incident scenarios.
- **Acceptance.**
  - Latency: p50 < 10ms, p95 < 300ms, p99 < 500ms overhead (NFR-001..003).
  - Error rate < 0.1% (NFR-008).
  - Sign-off from SRE on operational readiness.
- **Decisions to lock.** Where load tests run (separate AWS account?); SLO budgets; on-call rotation policy.
- **Dependencies.** SRE for ORR; AgentCore service quotas confirmed with AWS.
- **Risks.** AgentCore latency floor may already eat much of the 300ms budget; need an early reading.

#### WS-H — Documentation, Setup & Migration Guides (NFR-011, NFR-012, FR1)

- **Goal.** A new developer can go from "I have a SailPoint account" to "tools/list works in my MCP client" in under 10 minutes (NFR-011).
- **Deliverables.**
  - Setup guides for Cursor, Claude Desktop, Claude Code, VS Code (+ Continue.dev, Windsurf as best-effort).
  - CLI token helper documentation (`@sailpoint/mcp-auth login` from PRD 1 §5.7).
  - Troubleshooting guide for the top 10 expected error codes.
  - Migration guide from tenant URL to gateway URL.
  - Demo video (≤ 3 minutes) for internal enablement.
  - Timed user test with 3+ developers (NFR-011 acceptance).
- **Acceptance.**
  - 3 developers configure a client end-to-end in < 10 minutes without help.
  - Docs reviewed by DevRel and pass a copy editorial pass.
- **Decisions to lock.** Where docs live (developer.sailpoint.com vs Confluence); ownership of ongoing updates.
- **Dependencies.** WS-A through WS-G producing stable behavior to document; DevRel calendar.
- **Risks.** Docs always slip last; assign a named owner with capacity reserved.

#### Cross-Cutting Throughout Phase 2

- **IaC.** Terraform or CDK from day one; no console-only changes.
- **CI/CD.** Per-environment pipelines (dev → stage → preprod). Block merges on contract + perf smoke tests.
- **Threat modeling.** STRIDE pass on routing logic and admin APIs in week 2; security sign-off before WS-A merges to main.
- **Weekly demos.** Friday demo to PMs (Ye, Rahul) and Ben's UI lead. Trim scope explicitly each week, don't let it accrete.
- **Cost tracking.** Cost-per-1k-requests reported weekly to validate NFR-014/15 reframing.

#### Phase 2 Exit Criteria

- All P0 acceptance criteria for FR1–FR12 met (FR7 admin portal at "internal-admin only" minimum; full external-admin flow may slip to Phase 3 if needed).
- All P0 NFRs met or have a documented exception with PM agreement.
- ORR passed with SRE.
- Runbook published; on-call rotation defined.
- At least one internal team using the gateway on a non-production tenant for ≥ 1 week without a P1 incident.

### Phase 3 — Closed Beta (4 weeks)

**Goal:** Real customers (or internal SailPoint AI use cases) on the gateway with limited blast radius. Prove operational readiness with real traffic.

#### Pilot Tenant Selection

- Aim for 5–10 tenants spanning at least three personas: an internal SailPoint dev team, an existing MCP preview customer, and a marketplace-target enterprise customer.
- Selection criteria: low political risk, technically engaged contact, willingness to give weekly feedback, traffic volume that exercises (but doesn't saturate) NFR-004/005.
- Each pilot signs a 30-day commitment with a clear exit path.

#### Operational Readiness Review (ORR) Checklist

- Runbook reviewed with on-call.
- Alarm thresholds tuned with real baseline data from Phase 2.
- Rollback plan documented (DNS swap back to direct tenant URLs).
- Tabletop exercise: simulate a backend outage, an OAuth IdP outage, and a cross-tenant leak alert.
- Security: independent security review of WS-A and WS-B sign-off.
- Privacy: log redaction validated by an external reviewer.
- Capacity: AWS service quotas raised for projected beta load.

#### Beta Cadence

- **Daily:** error / latency review by tech lead and SRE.
- **Weekly:** customer feedback sync; triage top friction list; ship fixes mid-week.
- **End of week 2:** go/no-go checkpoint to continue toward GA.

#### Beta Success Criteria (Required For GA)

- ≥ 5 tenants actively using the gateway for 7+ consecutive days.
- 0 P1 incidents related to cross-tenant leakage, auth bypass, or data integrity.
- All P0 NFRs met against real traffic for 14 consecutive days.
- ≥ 80% of pilot customers say "I would recommend this" in feedback survey.
- Top 5 customer-reported issues fixed and verified.

### Phase 4 — General Availability (4 weeks)

**Goal:** Public availability on the chosen URL with full launch communications and (if in scope) AWS Marketplace listing.

#### Launch Checklist

- DNS cutover plan rehearsed; rollback plan documented.
- 24×7 on-call rotation handed to SRE; pager hygiene reviewed.
- Status page entry created (status.sailpoint.com or equivalent).
- Customer-facing release notes published.
- Internal enablement: support, sales engineering, and customer success briefed and have demo access.

#### AWS Marketplace Listing (If In Scope)

- Listing copy written and legal-reviewed (PRD 2 §Documentation appendix has the form template).
- Single endpoint URL confirmed (`https://mcp.identitynow.com/` per PRD 2, or chosen alternative).
- OAuth scopes registered and documented.
- Submission timeline: AWS marketplace review historically 2–4 weeks; start in week 1 of Phase 4.

#### Communications Plan

- **Internal.** All-hands lightning talk; #engineering and #product Slack announcements; customer success enablement deck.
- **External.** Blog post on developer.sailpoint.com; LinkedIn post from product leadership; mention in next customer newsletter; community post in MCP / Cursor / Claude developer channels.
- **Sales / GTM.** Battlecard against Saviynt and Wiz marketplace listings; one-pager for AEs.

#### 30 / 60 / 90 Day Success Metrics

| Metric | 30 days | 60 days | 90 days |
| --- | --- | --- | --- |
| Customers using gateway | 5 | 15 | 25+ |
| Monthly request volume | 100k | 500k | 1M+ |
| Latency p95 overhead | < 300ms | < 250ms | < 200ms |
| Error rate | < 0.5% | < 0.2% | < 0.1% |
| Cost per 1k requests | Document | Trending down | Within budget |
| Marketplace listing live | In review | Live | Trending traffic |

### Phase II — Post-GA (Q3+ planning)

These items are **explicitly deferred** in PRD 1 and PRD 2; they get their own planning cycle once GA is stable. Listed in roughly the order I'd recommend tackling them.

#### II-1: Dynamic Client Registration (RFC 7591) — High Priority

- Lets MCP clients self-register without an admin step, satisfying PRD 2 OAuth 2.1 + DCR direction.
- Removes the biggest friction point in the developer onboarding flow.
- Effort: 1 senior identity engineer + 1 backend, 6–8 weeks.
- Pre-req: lock down rate limiting (II-4) so DCR doesn't open an abuse vector.

#### II-2: Developer Self-Service Portal — High Priority

- A `developer.sailpoint.com/mcp` portal where developers manage their own clients, see usage, rotate credentials, view docs.
- Replaces the admin-only registration from MVP for the customer-facing case.
- Effort: 1 frontend + 1 backend + design support, 8–10 weeks.

#### II-3: Tool Namespacing & Discovery UI — Medium Priority

- Prefix tools by domain (`access_requests.*`, `workflows.*`, `identity.*`) and expose discovery in the gateway response.
- Pairs naturally with AgentCore's semantic search tool.
- Effort: 1 backend, 4–6 weeks; coordinated with each tool-owning team.

#### II-4: Per-Tenant Rate Limiting — Medium Priority

- Required before opening DCR; protects backends from a single noisy tenant.
- Token-bucket on `tenant_id` claim; configurable per-tenant overrides.
- Effort: 1 backend, 3–4 weeks.

#### II-5: FedRAMP / UAE1 Region Rollout — High Priority If Customer-Driven

- Mirror MVP architecture into FedRAMP-eligible AWS region (`us-gov-east-1` or equivalent).
- Confirm AgentCore Gateway availability in FedRAMP regions before committing.
- Includes data-residency review and possibly a separate URL (`mcp-gov.identitynow.com`).
- Effort: 2 backend + SRE + compliance partner, 8–12 weeks.

#### II-6: Federation Across Gateways — Lower Priority

- AgentCore supports gateway-of-gateways. Useful if internal SailPoint AI use cases want their own MCP plane that nests under the customer-facing one.
- Defer until at least one concrete internal use case requires it.

#### II-7: Tool Catalog Consolidation Across SailPoint — Lower Priority

- Onboard non-ISC backends (NERM, AIS, SaaS Identity) as additional AgentCore targets.
- Each new backend type is its own mini-project; pace by customer demand.

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

## Leadership Pitch

This section is structured as a 7-slide deck you can lift directly. Each slide has speaker notes (what to actually say) and the data points behind the claims. Length is intentional — keep it short on the slide, long in the speaker notes.

### Slide 1 — Problem In One Sentence

**On the slide:**
> Today, every MCP integration with SailPoint requires a tenant-specific URL. That single fact blocks AWS Marketplace, blocks one-click install in Cursor / Claude / VS Code, and leaves us behind Saviynt and Wiz who already shipped MCP marketplace listings in mid-2025.

**Speaker notes.**
- Customers cannot copy-paste a single URL into Cursor or Claude Desktop the way they can for GitHub, Linear, or Atlassian's MCP servers.
- AWS Marketplace listings require one stable endpoint URL. We can't list today.
- Two competitors are already on AWS Marketplace with MCP offerings — Saviynt (`saviynt-ispm-mcp.saviyntcloud.com/sse`) and Wiz (per-customer container in AWS AgentCore). Both shipped in July 2025.
- This is documented in PRD 2, §"Competitive Benchmark".

**Anticipated questions.**
- *"How many customers are actually asking for this?"* PRD 2 cites 28% of Fortune 500 implementing MCP servers in 2025, up from 12% in 2024. MCP preview customers have requested this directly.
- *"Could we just keep the per-tenant URL?"* Yes for existing customers — backward compatibility is part of the plan. But for new customer acquisition through marketplaces and one-click installs, no.

### Slide 2 — What We'll Build

**On the slide:** one diagram.
```
   MCP Clients (Cursor, Claude, VS Code, Custom)
                       │
                       ▼
        ┌──────────────────────────────┐
        │  mcp.sailpoint.com           │
        │  (AWS Bedrock AgentCore      │
        │   Gateway, managed)          │
        │                              │
        │  - SailPoint OAuth (JWT)     │
        │  - Tenant routing            │
        │  - Tool discovery + cache    │
        │  - Telemetry → Snowflake     │
        └──────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   ISC Tenant A    ISC Tenant B    ISC Tenant C
   (existing)      (existing)      (existing)
```

**Speaker notes.**
- One URL for every customer. One OAuth flow. One audit trail.
- Existing tenant URLs continue to work unchanged — this is additive.
- The gateway plane (the box in the middle) is AWS-managed. We own everything that touches SailPoint identity, customer data, and admin UX.
- This is a deliberate choice not to rebuild a JSON-RPC proxy — see slide 3.

**Anticipated questions.**
- *"Why one URL and not subdomains per tenant?"* Subdomains require the client to know the tenant. The whole point of marketplace and one-click install is that they don't.
- *"What about FedRAMP customers?"* Out of MVP scope. Phase II includes a separate FedRAMP region rollout (`mcp-gov.identitynow.com`).

### Slide 3 — Buy vs. Build

**On the slide:** a 3-column table.

| Concern | AgentCore Gives Us | We Build |
| --- | --- | --- |
| MCP protocol (`tools/list`, `tools/call`, sessions, SSE) | ✓ Native | – |
| OAuth / JWT validation | ✓ `customJWTAuthorizer` | Wire SailPoint OAuth |
| Tool discovery + semantic search | ✓ Native | Tool catalog metadata |
| Multi-target routing | ✓ Targets model | Tenant→target mapping |
| Scale, multi-AZ, managed ops | ✓ Native | SLOs, runbooks |
| Tenant routing logic, admin UX, telemetry to Snowflake, FedRAMP | – | All of it |

**Speaker notes.**
- AgentCore Gateway is purpose-built for MCP. It handles JSON-RPC, SSE streams, session state, multi-target fan-out, and tool catalog caching out of the box.
- An API gateway (Apigee, Kong, etc.) would not — there's an industry-recognized gap (cite Christian Posta's Oct 2025 New Stack article *"MCP vs. API Gateways: They're Not Interchangeable"*).
- The alternative is to either (a) retrofit an API gateway with custom JS/Lua plugins, which becomes brittle as the MCP spec evolves, or (b) build our own from scratch on top of `agentgateway` (Rust, CNCF), which is feasible but adds 3–6 months.
- Buying the gateway plane lets the team focus on SailPoint-specific glue — identity, tenant isolation, admin UX, telemetry — which is where the real value lives.

**Anticipated questions.**
- *"Aren't we locking into AWS?"* Yes, deliberately. Mitigation: keep the routing/auth/admin code free of AgentCore-specific business logic so we could re-front in 6 months if needed.
- *"What if AWS changes the API?"* AgentCore Gateway hit GA in 2025. We'll pin SDK versions and isolate the AgentCore surface behind an internal interface.
- *"Could we use Cognito or API Gateway alone?"* Cognito is auth only; API Gateway is HTTP only. Neither speaks MCP. We'd be writing the MCP protocol layer ourselves.

### Slide 4 — Phased Plan

**On the slide:**
```
Week:    0    3    6    9    12   15   18   21   24
Phase:   |P0--|P1-------|P2--------------|P3---|P4---|
Outputs: HLD  PoC       MVP              Beta  GA
              demo      P0 FR/NFRs       5-10  10+
                        all met          tenants customers
```

**Speaker notes.**
- **Phase 0 (3 wks).** Not implementation — it's a hard gate to reconcile two PRDs that disagree on URL, OAuth model, and scope. Without this, we'll rewrite work.
- **Phase 1 (6 wks).** PoC with one tenant, end to end. Validates AgentCore against our actual constraints.
- **Phase 2 (8–10 wks).** MVP: 8 parallel workstreams covering all P0 FRs and NFRs. This is where the bulk of the team's time goes.
- **Phase 3 (4 wks).** Closed beta with 5–10 tenants. Hard go/no-go at week 2.
- **Phase 4 (4 wks).** GA + AWS Marketplace listing. 30/60/90 day metrics tracked from day 1.
- **Phase II (post-GA).** DCR, dev portal, namespacing, FedRAMP, federation. Each gets its own planning.

**Anticipated questions.**
- *"Can we skip Phase 0 and start building?"* No. The two PRDs disagree on what URL to ship. Building before that decision is locked is throwaway work.
- *"Can we compress to 4 months?"* Yes with Option C staffing or by descoping the admin portal (FR7) to a CLI tool in MVP. Either is worth discussing.
- *"What slips first if we're behind?"* WS-C (admin portal) → CLI fallback. WS-G (perf tuning) → ship at higher latency, fix in patch. WS-H (docs) → cover only Cursor + Claude Desktop in launch.

### Slide 5 — Headcount And Timeline Ask

**On the slide:**

| Option | Team | GA target | Risk profile |
| --- | --- | --- | --- |
| A — Lean | 4 eng + EM | 7–8 months | Single points of failure |
| **B — Recommended** | **6 eng + EM** | **\~6 months** | **Balanced** |
| C — Aggressive | 8 eng + EM | 4–5 months or parallel FedRAMP | High change cost if scope shifts |

Recommend Option B. Composition: 1 EM, 1 staff/tech lead, 1 senior backend (routing/AgentCore), 1 senior identity engineer (OAuth), 1 backend (telemetry/Snowflake), 1 frontend (or borrowed from UI team), 0.5 SDET, 0.5 SRE. Plus shared support from OAuth (Rahul Mishra), UI (Ben Coble), Docs.

**Speaker notes.**
- Option B is the lowest-regret choice: it hits the natural 6-month GA window and leaves capacity for Phase II planning to start in parallel from month 4.
- Option A is achievable but every engineer is a single point of failure on a workstream. Vacation, illness, or attrition stops a workstream.
- Option C only makes sense if leadership wants to commit to FedRAMP in parallel or beat a competitive deadline by a quarter.

**Anticipated questions.**
- *"Can we build it with the existing Masala (MCP) team?"* Possibly with reshaping, but the Masala team is currently focused on the existing tenant-specific MCP server. Either we expand them, or stand up a new team with a clean charter.
- *"What's the cost of Option B?"* Roughly 6.5 FTE engineering for 6 months ≈ 39 person-months, plus AWS infra. Infra at expected MVP load is single-digit thousands per month; we'll firm this up in Phase 0.
- *"What happens if we say no?"* We stay on per-tenant URLs, lose the marketplace channel, lose competitive parity with Saviynt and Wiz. Phase 0 design work could happen with no incremental headcount.

### Slide 6 — Top Risks

**On the slide:** the top 3 only.

| Risk | Mitigation |
| --- | --- |
| AWS lock-in / FedRAMP gap | Abstract AgentCore behind an internal interface; confirm FedRAMP region availability in Phase 0; keep FedRAMP rollout as a Phase II workstream. |
| PRDs not reconciled in time | Phase 0 as a hard gate; weekly PM sync; escalate decisions to leadership if blocked > 5 business days. |
| Cross-tenant security leak | Threat model in Phase 0; routing fuzzers and contract tests in WS-A; independent security review before Beta; redaction validated by external reviewer. |

**Speaker notes.**
- Honesty about AWS lock-in earns credibility. We're choosing managed for speed and we accept the tradeoff with explicit mitigations.
- The PRD reconciliation risk is the most likely to slip the timeline; ask leadership to sponsor that meeting in week 1.
- Cross-tenant security is the only "career-ending if it goes wrong" risk on the list — call it out by name even though likelihood is low.

**Other risks (in the doc, not on the slide).** AgentCore API churn, latency p95 budget, OAuth team bandwidth, cost NFR-015 unrealistic at real load.

**Anticipated questions.**
- *"What's our exit strategy if AgentCore regresses or AWS changes terms?"* Re-front on agentgateway (CNCF, Rust). The SailPoint-specific code (routing, mapping, admin UX, telemetry) is the same; only the gateway plane changes. Estimated 3–4 months to re-host.
- *"Have we threat-modeled this yet?"* No, that's Phase 0 work. We won't merge any routing code until we have a STRIDE pass with security sign-off.

### Slide 7 — The Three Decisions We're Asking For

**On the slide:**

1. **Approve Option B staffing** for the MCP gateway team starting at the next planning cycle.
2. **Approve AWS Bedrock AgentCore Gateway** as the managed-service foundation, with the explicit understanding that we accept AWS coupling in exchange for time-to-market.
3. **Sponsor the PRD reconciliation meeting** in week 1 — Ye Zhu (PM, PRD 1), Rahul Mishra (PM, PRD 2 / OAuth lead), Dave Owens (Masala EM), Ben Coble (UI), and engineering leadership.

**Speaker notes.**
- The first two are standing decisions; the third is a one-meeting ask but it unlocks everything downstream.
- If leadership defers (1) or (2) we can still start Phase 0 design with current capacity, but we lose the timeline.
- Confirm in the room who will own each decision and by when.

**Anticipated questions.**
- *"Can you give me an answer in two weeks instead of today?"* Yes. The cost of two weeks is two weeks of GA — not material at this stage.
- *"Who's the single owner if we say yes today?"* Dattu (EM) until a tech lead is hired/named, then jointly. PM ownership stays with Ye + Rahul jointly until reconciliation; one PM after.

### Optional Backup Slides

Keep these in the appendix and pull them out only if asked:

- **B1.** AgentCore Gateway architecture in detail (targets, identity, semantic search, sync model). Lift from `docs/mcp-gateway.md` §"Reference Architecture".
- **B2.** Full FR/NFR-to-AgentCore mapping table. Lift from this doc §"How AgentCore Gateway Maps To The FRs / NFRs".
- **B3.** Detailed Phase 2 workstream plan. Lift from this doc §"Phase 2 — MVP".
- **B4.** Competitive benchmark — Saviynt, Wiz, GitHub MCP, Atlassian Remote MCP, Linear MCP. Lift from PRD 2 §"Competitive Benchmark" and `docs/mcp-gateway.md` §"Examples In The Wild".
- **B5.** Cost model placeholder — fill in after Phase 0.

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
