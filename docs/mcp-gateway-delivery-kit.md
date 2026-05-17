# MCP Gateway — Delivery Kit

**Initiative:** [INIT-2704](https://sailpoint.atlassian.net/browse/INIT-2704) · **Component:** DP-SAF · **Project:** DPDE  
**Owner:** Dattu Marneni (EM)  
**Related:** [`mcp-gateway-execution-plan.md`](mcp-gateway-execution-plan.md) · [`mcp-gateway-mvp-spec.md`](mcp-gateway-mvp-spec.md) · [`mcp-gateway.md`](mcp-gateway.md)

This kit supports **week-1 execution**, **Jira story breakdown**, spikes, stakeholder alignment, risks, competitive context, cost modeling, **skills ramp** (repo-based learning), **success checklist**, and the **two funding gates** (pilot → GA).

---

## 1. Two funding gates — pilot → GA

Leadership should fund **two explicit gates**, not one ambiguous “12-week program.” Weeks 1–4 are **Gate 1**; weeks 5–12 are **Gate 2** contingent on a successful Gate 1 demo.

```
                    GATE 1 (approve now)              GATE 2 (approve at week-4 demo)
                    ───────────────────              ─────────────────────────────
Team                2–3 eng + 0.5 EM + Cursor       5–6 eng + EM (+ partners)
Duration            4 weeks                         8 weeks (weeks 5–12)
Spend (order of)    ~3–4 person-months              ~16–17 person-months
Delivers            Internal-pilot MVP              Closed beta + GA
Exit artifact       Demo + decision log + spikes    ORR + 5–10 tenants + launch

Week:  1    2    3    4  |  5    6    7    8  |  9   10  | 11   12
       └──── Gate 1 ────┘  └── Gate 2a ──────┘  └β─┘  └─GA─┘
                            P0 hardening          beta   launch
```

### Gate 1 — Internal pilot (weeks 1–4)

| Item | Detail |
| --- | --- |
| **Ask** | Approve **Option D** staffing; calendar-bound partner time (OAuth, Masala, SRE). |
| **Success** | Cursor E2E: universal URL + `client_id` → `tools/list` + one `tools/call` on **2 tenants**; FR6 smoke green; decision log D1–D12 signed; OAuth spike **go/no-go** documented. |
| **Not promised** | GA, ISC Admin UI, Snowflake CDC, marketplace live, 1M req/month proof, FedRAMP. |
| **Week-4 meeting** | **Go/no-go for Gate 2** — leadership + PM + EM; show demo recording + honest gap list. |

### Gate 2 — Complete solution (weeks 5–12)

| Item | Detail |
| --- | --- |
| **Ask** | Approve **Option B** (5–6 engineers + EM) only if Gate 1 exit met. |
| **Success** | [`mcp-gateway-mvp-spec.md` §14](mcp-gateway-mvp-spec.md#14-mvp-exit-criteria-closed-beta-ready); ORR week 8; beta week 10; GA week 12. |
| **Pre-approved descopes** (if behind) | FR7 → CLI-only; FR9 Snowflake → week 10+; docs → Cursor + Claude Desktop only. |
| **Budget signal** | ~5.5 FTE × 2 months core team + partner calendars already booked in week 5. |

### Gate 2 approval criteria (week 4 checklist)

- [ ] Live demo: PKCE in Cursor, not Postman-only.
- [ ] `test_mcp_tools.py` passes against **gateway** base URL (not only tenant-direct).
- [ ] Cross-tenant fuzz: **0** wrong-tenant `tools/call` in automated suite.
- [ ] D1–D7 **Required** decisions recorded (Confluence or this repo).
- [ ] OAuth path: SailPoint JWT validated by AgentCore **or** documented Cognito bridge with date.
- [ ] **Edge owner** decided: AgentCore (DPDE) vs sp-gateway (APIMGMT) vs hybrid — one paragraph signed by Lori + EM.
- [ ] Rahul Mishra confirms week-5–8 OAuth capacity for static clients + PKCE.

---

## 2. Week-1 execution

### 2.1 Calendar (days 1–5)

| Day | EM / all | Eng 1 (platform) | Eng 2 (identity) | Eng 3 (quality) |
| --- | --- | --- | --- | --- |
| **Mon** | Kickoff 60m; send pre-read | Clone `sailpoint-agentcore-pdp`; sandbox AWS | Read OAuth / JWKS docs; list blockers | Run `sp-mcp-server` + `test_mcp_tools.py` tenant-direct |
| **Tue** | **Decision workshop** (2h) — §2.2 | AgentCore gateway + 1 MCP target (tutorial 05) | OAuth authorizer spike (`customJWTAuthorizer`) | MCP Inspector on [public tenant URL](https://developer.sailpoint.com/docs/extensibility/mcp-getting-started/) |
| **Wed** | Stakeholder 30m: Kartik; 30m: Antoine/Dave | Wire target → dev tenant `/access-requests/mcp` | PKCE redirect URI policy with Rahul | Baseline harness: direct vs gateway stub |
| **Thu** | Stakeholder 30m: Lori (edge owner) | Interceptor stub (tutorial 09) — pass-through OK | JWT claims doc: `tenant_id`, `client_id`, `sub` | Admin CLI/API **contract** draft (no UI) |
| **Fri** | **Week-1 demo** 30m; decision log published | `tools/list` via gateway (hardcoded upstream OK) | Authorizer go/no-go memo | Publish spike results in kit §3 |

### 2.2 Decision workshop (Tuesday, 2 hours)

**Pre-read (send 24h before):** [`mcp-gateway-mvp-spec.md` §4](mcp-gateway-mvp-spec.md#4-prd-reconciliation--decisions-required) · [PRD 1](https://sailpoint.atlassian.net/wiki/spaces/~7120200fd8a6740fdb4ca9bd0f88f478f134a5/pages/4634738812/MCP+Q1-2+PRD+SailPoint+MCP+Server+Single+URL+and+Oauth+Support) · [PRD 2](https://sailpoint.atlassian.net/wiki/spaces/~7120200fd8a6740fdb4ca9bd0f88f478f134a5/pages/4342448180/MCP+PRD+Tenant-Agnostic+MCP+Server+Endpoint+Oauth+Integration) · §1 two funding gates (this doc).

**Required attendees**

| Name | Role | Must decide |
| --- | --- | --- |
| Ye Zhu | PM ([PRD 1](https://sailpoint.atlassian.net/wiki/x/fIBAFAE)) | D1 hostname, D4 scope, Gate 1/2 narrative |
| Rahul Mishra | PM / OAuth ([PRD 2](https://sailpoint.atlassian.net/wiki/x/NIDUAgE)) | D2, D3, D9; week 5–8 OAuth capacity |
| Dave Owens | Masala EM | D6 backend, D11/D12, global env vars owner |
| Ben Coble | UI | D7: Admin UI in Gate 2 vs CLI in Gate 1 |
| Lori Van Gulick | APIMGMT / global URL | **Edge owner:** AgentCore vs sp-gateway |
| Kartik Khamborkar | API Mgmt / AgentCore PoC | Interceptor ownership; APIMGMT-1863 link |
| Security delegate | AppSec | Threat-model week-2 slot; routing invariant S1 |
| SRE delegate | Ops | DNS/TLS path; ORR owner for Gate 2 |
| Dattu Marneni | EM | Facilitator; records decisions |

**Optional:** Evan Anandappa (INIT-2090), Antoine Troadec (`sp-mcp-server`), David Peterson (SAASSRE-6461).

**Agenda**

| Time | Topic | Output |
| --- | --- | --- |
| 0:00–0:10 | Goal: Gate 1 in 4 weeks; Gate 2 at week 12 **if** demo passes | Alignment on two gates |
| 0:10–0:35 | Walk D1–D7: URL, OAuth, tenant map, scope, AgentCore, backends, admin | **Decision or owner+date** per row |
| 0:35–0:50 | D8–D12: telemetry, Cognito, target model, auth layers, Marketplace | Same |
| 0:50–1:05 | **Edge architecture:** INIT-2704 vs APIMGMT-1699 vs Marketplace hostname | One owner + diagram on whiteboard |
| 1:05–1:20 | Partner SLAs: OAuth, UI, SRE, Masala — dates on calendar | Shared Slack/Jira links |
| 1:20–1:50 | Gate 2 pre-approval: headcount, descopes, week-4 go/no-go criteria | §1 checklist agreed |
| 1:50–2:00 | Actions: who publishes decision log by EOD Wed | Named owners |

### 2.3 Week-1 exit criteria (Friday)

- [ ] Decision log updated (§2.4 template) with D1–D12 status.
- [ ] `tools/list` through AgentCore gateway in **dev** (hardcoded tenant upstream acceptable).
- [ ] OAuth spike result: **green** / **yellow (Cognito)** / **red (escalate)**.
- [ ] `test_mcp_tools.py` green on **tenant-direct** dev URL.
- [ ] Jira: week-1 stories in §4 moved to Done or blocked with owner.
- [ ] Gate 2 **not** assumed approved — only pre-conditions agreed.

### 2.4 Decision log template (Confluence or repo)

```markdown
| ID | Decision | Chosen option | Approver | Date | Notes |
|----|----------|---------------|----------|------|-------|
| D1 | Public hostname | mcp.sailpoint.com | Ye | YYYY-MM-DD | |
| D2 | OAuth model | Auth Code + PKCE + static | Rahul | | |
| … | | | | | |
| EDGE | System of record for MCP edge | AgentCore / sp-gateway / hybrid | Lori + EM | | |
```

---

## 3. Technical spike briefs

### 3.1 Spike A — Platform (Eng 1) — AgentCore + `sp-mcp-server` target

**Duration:** 3 days (Wed–Fri week 1)  
**Epic:** [DPDE-1781](https://sailpoint.atlassian.net/browse/DPDE-1781), [DPDE-1770](https://sailpoint.atlassian.net/browse/DPDE-1770)

**Hypothesis:** AgentCore Gateway can register `sp-mcp-server` as an MCP target and return the same four public tools as tenant-direct.

**Steps**

1. Fork/branch [sailpoint-agentcore-pdp](https://github.com/sailpoint-core/sailpoint-agentcore-pdp); deploy gateway in sandbox account.
2. Add MCP target per [AWS tutorial 05](https://github.com/awslabs/agentcore-samples/tree/main/01-tutorials/02-AgentCore-gateway/05-mcp-server-as-a-target): upstream = `https://{tenant}.api.cloud.sailpoint.com/v2025/access-requests/mcp` (or Masala-provided dev host).
3. Call `tools/list` with **user bearer** (from Antoine/Masala) through gateway endpoint.
4. Optional day 3: interceptor pass-through ([tutorial 09](https://github.com/awslabs/agentcore-samples/tree/main/01-tutorials/02-AgentCore-gateway/09-fgac-interceptor)); log `client_id` claim only.

**Success**

- `tools/list` returns `list-requestable`, `create-access-request`, `view-access-requests`, `cancel-access-request`.
- Latency noted (p50/p95); cold start observed.
- **D10:** recommend one-target-per-tenant vs routing Lambda.

**Fail / pivot**

- Target limits / auth mismatch → document; schedule Masala + AWS SA 30m.
- Do **not** reimplement tools in gateway.

---

### 3.2 Spike B — Identity (Eng 2) — OAuth + AgentCore authorizer

**Duration:** 3 days (Wed–Fri week 1)  
**Epic:** [DPDE-1769](https://sailpoint.atlassian.net/browse/DPDE-1769)

**Hypothesis:** SailPoint OAuth JWT is accepted by AgentCore `customJWTAuthorizer` without Cognito.

**Steps**

1. Obtain dev static OAuth client from Rahul (redirect URIs for Cursor / `mcp-remote`).
2. Complete one PKCE flow; capture access token; decode claims (`iss`, `aud`, `sub`, custom claims).
3. Configure authorizer discovery URL + JWKS; call gateway with Bearer token.
4. Verify **same user token** forwarded to `sp-mcp-server` (IdentityID present — Masala confirms).

**Success**

- 401 without token; 200 with valid token on `tools/list`.
- Memo: claim → `tenant_id` mapping approach (D3, D11).
- **D9:** direct OAuth **go**.

**Fail / pivot**

- JWKS / issuer incompatible → **D9: Cognito bridge** with estimated +1–2 weeks; escalate to leadership same day.

---

### 3.3 Spike C — Quality (Eng 3) — Golden path harness

**Duration:** week 1 ongoing  
**Epic:** [DPDE-1773](https://sailpoint.atlassian.net/browse/DPDE-1773), [DPDE-1782](https://sailpoint.atlassian.net/browse/DPDE-1782)

**Steps**

1. Run [MCP Inspector](https://developer.sailpoint.com/docs/extensibility/mcp-getting-started/) against public tenant URL (PAT).
2. Run `sp-mcp-server` `test_mcp_tools.py` with dev user token — **direct** baseline.
3. Add `GATEWAY_BASE_URL` env; same tests against gateway when Spike A ready.
4. Draft dual-path quickstart outline: PAT/tenant-direct (debug) vs OAuth/gateway (product).

**Success**

- Baseline JSON saved for tool names + schema smoke.
- CI-ready script stub (exit non-zero on regression).

---

## 4. Jira — story breakdown

**Conventions:** Project **DPDE**, labels `INIT-2704`, `mcp-gateway`, component **DP-SAF**. Stories use **parent epic** (hierarchy). 

**Bulk create (week 1 + weeks 2–4):**

```bash
export JIRA_API_TOKEN='…'   # Atlassian API token
python3 scripts/create_mcp_gateway_jira_stories.py --dry-run   # preview
python3 scripts/create_mcp_gateway_jira_stories.py           # create 44 stories
python3 scripts/create_mcp_gateway_jira_stories.py --week1-only  # 17 stories only
```

After creation, assign Eng 1/2/3 and set sprint targets in Jira.

### 4.0 Stories created in Jira (2026-05-17)

**44 stories** created under INIT-2704 epics (`DPDE-1835` … `DPDE-1878`), labels `INIT-2704`, `mcp-gateway`, component **DP-SAF**.

| Range / epic | Keys | Count |
| --- | --- | --- |
| [DPDE-1767](https://sailpoint.atlassian.net/browse/DPDE-1767) kickoff | DPDE-1835 – DPDE-1838 | 4 |
| [DPDE-1781](https://sailpoint.atlassian.net/browse/DPDE-1781) foundation | DPDE-1839 – DPDE-1843 | 5 |
| [DPDE-1769](https://sailpoint.atlassian.net/browse/DPDE-1769) OAuth | DPDE-1844 – DPDE-1847 | 4 |
| [DPDE-1768](https://sailpoint.atlassian.net/browse/DPDE-1768) URL | DPDE-1848 – DPDE-1849 | 2 |
| [DPDE-1776](https://sailpoint.atlassian.net/browse/DPDE-1776) mapping | DPDE-1850 – DPDE-1851 | 2 |
| Weeks 2–4 (remaining epics) | DPDE-1852 – DPDE-1878 | 27 |

Board filter: `project = DPDE AND labels = mcp-gateway ORDER BY created ASC`

### 4.1 Gate 1 — Week 1 stories (reference — created in Jira)

#### Epic [DPDE-1767](https://sailpoint.atlassian.net/browse/DPDE-1767) — Program kickoff

| Story | Summary | Acceptance criteria |
| --- | --- | --- |
| DPDE-1767-1 | Schedule week-1 decision workshop and pre-read | All required attendees accepted; pre-read links sent 24h before |
| DPDE-1767-2 | Publish two-gate funding narrative for leadership | §1 of this doc (or Confluence) linked from INIT-2704 |
| DPDE-1767-3 | Stand up weekly demo cadence (Fri 30m) | Recurring invite; template: demo + risks + decisions |
| DPDE-1767-4 | Create decision log page and RACI (§5–6) | D1–D12 table live; owners assigned |

#### Epic [DPDE-1781](https://sailpoint.atlassian.net/browse/DPDE-1781) — Foundation / PoC

| Story | Summary | Acceptance criteria |
| --- | --- | --- |
| DPDE-1781-1 | Deploy AgentCore gateway from sailpoint-agentcore-pdp in dev | Gateway URL documented; IaC in repo |
| DPDE-1781-2 | Register one MCP target → tenant access-requests/mcp | `tools/list` succeeds with user bearer |
| DPDE-1781-3 | Spike interceptor pass-through + request logging | CloudWatch shows MCP method + request_id |
| DPDE-1781-4 | Document edge architecture decision (AgentCore vs sp-gateway) | Lori + EM sign-off in decision log |
| DPDE-1781-5 | Week-1 exit: tools/list via gateway in dev | Demo recording attached to epic |

#### Epic [DPDE-1769](https://sailpoint.atlassian.net/browse/DPDE-1769) — OAuth / JWT

| Story | Summary | Acceptance criteria |
| --- | --- | --- |
| DPDE-1769-1 | Obtain dev OAuth static client + scopes from platform team | client_id, redirect URIs, scopes documented |
| DPDE-1769-2 | Spike customJWTAuthorizer with SailPoint JWKS | Valid JWT → 200; invalid → 401 |
| DPDE-1769-3 | Document JWT claims for tenant routing (D3, D11) | Claim matrix reviewed by Rahul + Masala |
| DPDE-1769-4 | OAuth spike go/no-go memo (D9) | Green/yellow/red with escalation path |

#### Epic [DPDE-1768](https://sailpoint.atlassian.net/browse/DPDE-1768) — Universal URL (week 1 slice)

| Story | Summary | Acceptance criteria |
| --- | --- | --- |
| DPDE-1768-1 | Confirm dev hostname with SRE/APIMGMT (mcp-dev.*) | DNS/TLS path documented or ticket linked |
| DPDE-1768-2 | Draft Cursor `mcp.json` for gateway URL (stub) | Checked into repo; works when gateway live |

#### Epic [DPDE-1776](https://sailpoint.atlassian.net/browse/DPDE-1776) — Mapping store (week 1 design only)

| Story | Summary | Acceptance criteria |
| --- | --- | --- |
| DPDE-1776-1 | Choose mapping store (DynamoDB vs RDS) and schema | ADR: partition key, client_id, tenant_id, revoked_at |
| DPDE-1776-2 | Define admin CRUD API contract for Eng 3 CLI | OpenAPI or markdown; no UI required Gate 1 |

---

### 4.2 Gate 1 — Weeks 2–4 (summary stories per epic)

| Epic | W2 | W3 | W4 |
| --- | --- | --- | --- |
| [DPDE-1771](https://sailpoint.atlassian.net/browse/DPDE-1771) | Mapping store v1 + route to tenant target | Second tenant; routing cache | Fuzz tests; zero cross-tenant |
| [DPDE-1770](https://sailpoint.atlassian.net/browse/DPDE-1770) | tools/call E2E one tool | All four tools via gateway | Error paths on tool failure |
| [DPDE-1772](https://sailpoint.atlassian.net/browse/DPDE-1772) | PKCE E2E Cursor | Expired token 401 envelope | Revoked client 403 |
| [DPDE-1778](https://sailpoint.atlassian.net/browse/DPDE-1778) | /health + error envelope v1 | Contract tests all 4xx/5xx | request_id in logs |
| [DPDE-1779](https://sailpoint.atlassian.net/browse/DPDE-1779) | Structured CW logs, no bearer | PII redaction checklist | Log retention policy |
| [DPDE-1773](https://sailpoint.atlassian.net/browse/DPDE-1773) | FR6 harness tenant-direct | FR6 via gateway | CI gate on PR |
| [DPDE-1775](https://sailpoint.atlassian.net/browse/DPDE-1775) | Admin CLI create/revoke client | Bind client_id→tenant_id | Documented admin flow |
| [DPDE-1782](https://sailpoint.atlassian.net/browse/DPDE-1782) | Quickstart draft | Timed dev test (NFR-011) | Demo video ≤3 min |
| [DPDE-1780](https://sailpoint.atlassian.net/browse/DPDE-1780) | k6 smoke 50 concurrent | Security review scheduled | Gate-1 checklist §1 |

---

### 4.3 Gate 2 — Weeks 5–12 (epic-level story themes)

Use for sprint planning after week-4 approval.

| Epic | Gate 2 story themes (4–6 each) |
| --- | --- |
| DPDE-1771 / 1776 | Target automation; cache TTL; routing deny integration tests |
| DPDE-1769 / 1772 | Production OAuth clients; VS Code path; scope enforcement |
| DPDE-1775 | ISC Admin UI **or** harden CLI; audit log integration |
| DPDE-1774 / 1777 / 1779 | Snowflake CDC; Grafana dashboards; alarms → PagerDuty |
| DPDE-1780 | Load test 100 concurrent; 24h soak; ORR with SRE |
| DPDE-1782 | developer.sailpoint.com publish; beta + GA comms |
| DPDE-1773 | Migration guide; traffic comparison dashboards |

---

## 5. Stakeholder map (RACI)

**R** = Responsible · **A** = Accountable · **C** = Consulted · **I** = Informed

| Area | R | A | C | I |
| --- | --- | --- | --- | --- |
| **Program / gates** | EM (Dattu) | INIT-2704 sponsor | Ye, Rahul | Leadership |
| **PRD / product scope** | Ye + Rahul | PM director | EM, Dave | Eng |
| **AgentCore gateway IaC** | Eng 1 | Tech lead / EM | Kartik, AWS SA | SRE |
| **OAuth / JWT / PKCE** | Eng 2 | Rahul Mishra | INIT-2090, Security | Eng 1 |
| **sp-mcp-server backend** | Masala (Antoine) | Dave Owens | Eng 1, Eng 2 | EM |
| **Global URL / DNS / TLS** | Lori / SRE (APIMGMT, SAASSRE) | Lori | Eng 1, David Peterson | EM |
| **sp-gateway vs AgentCore edge** | Lori + Kartik | Lori + EM | Dave, Rahul | Leadership |
| **Mapping store + routing** | Eng 1 | Tech lead | Security, Masala | Rahul |
| **Admin client registration** | Eng 3 CLI; Ben UI (Gate 2) | Ben / EM | Rahul | Security |
| **Telemetry / Snowflake** | Eng 1 / DP | DP lead | Security, SRE | PM |
| **FR6 backward compat** | Eng 3 | EM | Masala | PM |
| **Security / threat model** | Security | CISO delegate | Eng 1, Eng 2 | All |
| **SRE / ORR / on-call** | SRE | SRE manager | Eng 1, EM | Leadership |
| **Docs / DevRel** | Eng 3 / DevRel | PM | Masala | Customers (beta) |
| **Marketplace (post–Gate 1)** | Dave Owens | PM | AWS partnership | EM |
| **Public developer docs** | DevRel | PM | Masala | EM |

### Integration meetings (book week 1)

| Meeting | Attendees | Duration | Outcome |
| --- | --- | --- | --- |
| PRD reconciliation | §2.2 | 2h | Decision log |
| Kartik — AgentCore + interceptor | EM, Eng 1, Kartik | 30m | Extend PoC; link APIMGMT-1863 |
| Antoine/Dave — sp-mcp-server | EM, Eng 1–3, Masala | 30m | Dev URL, token, global issuer env |
| Lori — edge owner | EM, Eng 1, Lori | 30m | AgentCore vs sp-gateway |
| Rahul — OAuth SLA | EM, Eng 2, Rahul | 30m | JWKS, clients, week 5–8 capacity |
| Security — threat model | EM, Eng 1, Security | 2h (week 2) | STRIDE sign-off scheduled |

---

## 6. Risk register

| ID | Risk | L | I | Owner | Mitigation | Due |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | PRD D1–D7 not decided week 1 | M | H | EM | Decision workshop §2.2; escalate >5 days | W1 Fri |
| R2 | OAuth JWT incompatible with AgentCore (D9) | M | H | Eng 2 / Rahul | Spike B; Cognito bridge plan | W1 Fri |
| R3 | INIT-2090 / ISCINTAKE-248 blocks static client + PKCE | M | H | Rahul | Week-1 capacity commit; scope DCR to Phase II | W1 |
| R4 | Edge split: DPDE AgentCore vs APIMGMT sp-gateway | H | H | EM / Lori | EDGE decision in workshop | W1 Wed |
| R5 | Masala bandwidth — global URL / claims | M | H | Dave Owens | ISCANT-12559; named engineer | W1 |
| R6 | Cross-tenant routing bug | L | C | Eng 1 / Security | Invariant S1; fuzz week 3–4; review before Gate 2 | W4 |
| R7 | AgentCore latency eats NFR budget | M | M | Eng 1 | Week 1 latency note; provisioned concurrency in Gate 2 | W2 |
| R8 | Ben UI not available — FR7 slips | H | M | Ben / EM | CLI Gate 1; UI Gate 2 only | W1 |
| R9 | 12-week GA over-promised | M | H | EM | Two gates; week-4 honest checklist | W4 |
| R10 | Public docs (PAT/tenant) vs gateway (OAuth) confusion | M | M | DevRel / EM | Dual-path quickstart Spike C | W4 |
| R11 | AWS lock-in / FedRAMP | M | H | EM | Abstract edge; FedRAMP Phase II | Gate 2 plan |
| R12 | AgentCore API churn | M | M | Eng 1 | Pin SDK; thin adapter layer | W2 |
| R13 | Snowflake CDC delays Gate 2 | M | L | DP | Defer to week 9–10; CW for beta | W6 |
| R14 | Gate 2 funding not approved after good demo | L | H | EM | Pre-agree criteria §1; leadership in W4 demo | W4 |

**L** = Likelihood · **I** = Impact · **C** = Critical

---

## 7. Competitive one-pager

### Why this matters

Enterprises adopting MCP clients (Cursor, Claude, Copilot) expect **one URL + OAuth**, not per-tenant hostname assembly. Marketplace listings reinforce that pattern.

### Competitor snapshot (2025–2026)

| Vendor | MCP entry pattern | Auth | Notes |
| --- | --- | --- | --- |
| **Saviynt** | Marketplace listing; hosted MCP endpoint (`*.saviyntcloud.com`) | OAuth via product | Listed mid-2025; identity governance angle |
| **Wiz** | AWS Marketplace; per-customer AgentCore deployment | Cloud/IAM + product | Security graph / cloud context |
| **GitHub** | `api.githubcopilot.com` remote MCP | GitHub OAuth | Developer-native; single URL |
| **Atlassian** | Remote MCP (Rovo) | Atlassian OAuth | Jira/Confluence tools |
| **Linear** | `mcp.linear.app` | Linear OAuth | Narrow tool surface, polished DX |
| **SailPoint (today)** | Per-tenant `https://[tenant].api.identitynow.com/.../mcp` | API token (public docs) | Strong tools; weak install UX |

### SailPoint positioning (Gate 1 → Gate 2)

| Message | Proof |
| --- | --- |
| **Governed identity MCP** — access requests, not generic chat | Four production tools + `sp-mcp-server` |
| **Enterprise gateway** — audit, routing, policy chokepoint | INIT-2704 + AgentCore interceptors |
| **One URL for ISC** | `mcp.sailpoint.com` + PKCE (Gate 2 GA) |
| **Additive** — tenant URLs keep working | FR6 harness |

### Gaps vs competitors (honest)

- No marketplace live at Gate 1 — Saviynt/Wiz ahead on **distribution**, not necessarily tool depth.
- Public docs still tenant+PAT — fix at GA (developer.sailpoint.com).
- FedRAMP / gov cloud — Phase II.

---

## 8. Cost model skeleton

**Purpose:** Order-of-magnitude for leadership and NFR-014/015 reframing. **Replace assumptions** after week-1 AgentCore metering sample.

### 8.1 Assumptions (editable)

| Parameter | Low | Medium | High |
| --- | --- | --- | --- |
| Monthly MCP requests | 100k | 500k | 1M |
| `tools/list` vs `tools/call` mix | 70% / 30% | 60% / 40% | 50% / 50% |
| AgentCore cache hit rate on list | 80% | 85% | 90% |
| Avg request size | Small JSON | Small JSON | + larger call payloads |
| Regions | 1 | 1 | 2 |
| Environments | dev+stage+prod | same | same |

### 8.2 Cost components

| Component | Pricing approach | Low (100k req) | Med (500k) | High (1M) |
| --- | --- | --- | --- | --- |
| **AgentCore Gateway** | Per-request + control plane (confirm AWS list price; use $X/1M req placeholder) | $TBD | $TBD | $TBD |
| **Lambda (interceptor)** | Invocations × duration (128–512MB, &lt;100ms) | $TBD | $TBD | $TBD |
| **CloudWatch Logs** | Ingest + storage (1–2 KB/req, 30d retention) | $TBD | $TBD | $TBD |
| **DynamoDB (mapping)** | On-demand RCU/WCU; low volume admin | &lt;$50 | &lt;$50 | &lt;$100 |
| **Route 53 + ACM** | Hosted zone + cert | ~$1–5 | ~$5 | ~$10 |
| **Data transfer** | Egress to tenant MCP backends | $TBD | $TBD | $TBD |
| **Snowflake ingest** (Gate 2) | Storage + pipes | defer | $TBD | $TBD |
| **Total infra / month** | Sum | **$TBD** | **$TBD** | **$TBD** |

**Placeholder formula (fill when AWS quotes known):**

```
monthly_cost ≈ (requests × (1 - list_cache_hit) × agentcore_per_req)
             + (requests × lambda_per_invocation)
             + (requests × log_kb × cw_ingest_per_gb)
             + mapping_store_fixed
```

### 8.3 Engineering cost (two gates)

| Gate | Duration | FTE | Person-months (approx) |
| --- | --- | --- | --- |
| Gate 1 | 4 weeks | 2.5 eng + 0.5 EM | ~3–4 |
| Gate 2 | 8 weeks | 5.5 eng + EM | ~16–17 |
| **Total program** | 12 weeks | — | **~20–21** |

Partner effort (OAuth, UI, SRE, Security) not included — calendar risk, not dollar risk in DPDE headcount.

### 8.4 Actions to firm TBD cells

1. Eng 1: run 10k synthetic `tools/list` in sandbox; export AgentCore + CW bill line items.
2. FinOps / AWS SA: validate AgentCore Gateway meter in commercial region.
3. PM: reframe NFR-015 (“&lt;$100/month”) against **Medium** column — likely unrealistic at 1M req with full logging.

---

## 9. Skills ramp — learn from the repos (not from scratch)

Gate 1 assumes **extend existing code**, not greenfield MCP. Building skills from the repos below **before** week-1 spikes turns discovery into validation. Full workstream skills map: [`mcp-gateway-execution-plan.md` § Workstream → Skills Map](mcp-gateway-execution-plan.md#workstream--skills-map).

### 9.1 Why start now

| Repo | Teaches | Gateway owns |
| --- | --- | --- |
| [`sp-mcp-server`](https://github.com/sailpoint-core/sp-mcp-server) | Streamable HTTP MCP, access-request tools, OAuth metadata, user bearer + `IdentityID` | **Routing to** this backend only |
| [`sailpoint-agentcore-pdp`](https://github.com/sailpoint-core/sailpoint-agentcore-pdp) | AgentCore Gateway IaC, interceptor hooks, audit logging | **Front door** — fork/extend |
| [AgentCore tutorials 05 + 09](https://github.com/awslabs/agentcore-samples/tree/main/01-tutorials/02-AgentCore-gateway) | MCP-as-target, FGAC interceptor | Week-1 spikes (§3) |

**Schedule risk if skipped:** Engineers learn MCP + AWS during week 1 instead of proving spikes — decision workshop and Friday demo slip.

### 9.2 Depth by role (Gate 1)

| Role | Primary repos / refs | Gate 1 bar (can demo or review PR) | Hours (part-time) |
| --- | --- | --- | --- |
| **Eng 1 — Platform** | `sailpoint-agentcore-pdp`, tutorial **05**, optional **09** | Deploy gateway; register MCP target; `tools/list` via gateway; explain interceptor extension point | **12–16** |
| **Eng 2 — Identity** | `sp-mcp-server` (`oauth.go`, handlers), SailPoint OAuth docs, Cursor/`mcp-remote` PKCE | JWT claims documented; authorizer go/no-go; same user token works direct + via gateway | **12–16** |
| **Eng 3 — Quality** | `test_mcp_tools.py`, [MCP Getting Started](https://developer.sailpoint.com/docs/extensibility/mcp-getting-started/) | Tenant-direct baseline green; harness ready for gateway URL; dual-path quickstart outline | **8–12** |
| **EM** | Both repos at architecture level, §1 two gates, [backend contract](mcp-gateway-execution-plan.md#backend-contract--sp-mcp-server) | Explain gateway → `sp-mcp-server` in 5 min; block “reimplement tools in gateway” | **4–6** |

### 9.3 One-week learning path (before / during week 1)

| When | All roles | Eng 1 | Eng 2 | Eng 3 |
| --- | --- | --- | --- | --- |
| **Day 1–2** | Read [backend contract](mcp-gateway-execution-plan.md#backend-contract--sp-mcp-server); skim [mcp-gateway.md § Related Repositories](mcp-gateway.md#related-repositories) | Clone `sailpoint-agentcore-pdp` | Read `sp-mcp-server` README + OAuth paths | Run `make run` + `test_mcp_tools.py` tenant-direct |
| **Day 3–4** | Attend decision workshop (§2.2) | Sandbox deploy + tutorial **05** target | PKCE once; decode JWT; Spike B (§3.2) | MCP Inspector on tenant URL; Spike C (§3.3) |
| **Day 5** | Friday demo (§2.3) | `tools/list` via gateway (hardcoded upstream OK) | Authorizer go/no-go memo | Publish baseline test results |

Align spikes with [§3 Technical spike briefs](#3-technical-spike-briefs).

### 9.4 Gate 2 skills (weeks 5–12) — defer until Gate 2 approved

| Area | Resources | When |
| --- | --- | --- |
| ISC Admin UI (FR7) | Ben Coble’s stack + admin API contract from week 1 | Gate 2 track “Experience” |
| Snowflake CDC (FR9) | Data Platform patterns | Week 6+ or defer |
| k6 / load (NFR-004–005) | k6 or Locust + AgentCore quotas | Week 7–8 |
| SRE ORR | Runbook templates, on-call with SRE | Week 8 |
| Marketplace / two-layer auth | [Dave Owens Confluence](https://sailpoint.atlassian.net/wiki/spaces/~978782161/pages/4347527504/AWS+Agent+Core+Gateway+Integration) | Post-GA / Phase II |

### 9.5 Do not study yet (common traps)

| Trap | Why it hurts |
| --- | --- |
| Reimplementing `list-requestable` / other tools in the gateway | Adds **4–8+ weeks**; Masala owns tools in `sp-mcp-server` |
| Deep `workflow` / `transform` MCP paths | Out of MVP scope |
| Custom JSON-RPC / SSE proxy | AgentCore already provides protocol plane |
| Marketplace ResolveCustomer + nested service tokens | Gate 2+; not Cursor pilot |
| FedRAMP / multi-region AgentCore | Phase II until region availability confirmed |

### 9.6 Skills exit check (week 4, optional Gate 1 criterion)

- [ ] Eng 1: whiteboard **AgentCore → mapping → tenant `sp-mcp-server` URL** without notes.
- [ ] Eng 2: explain **which JWT claims** drive `tenant_id` and what happens when token expires.
- [ ] Eng 3: run harness **tenant-direct vs gateway** in &lt;5 minutes.
- [ ] EM: articulate **EDGE** decision (AgentCore vs `sp-gateway`) and why tools stay in Masala repo.

### 9.7 If edge owner chooses sp-gateway (APIMGMT) instead of AgentCore

Shift Eng 1 ramp toward [Global OAuth and MCP URLs](https://sailpoint.atlassian.net/wiki/spaces/ISC/pages/4146135316/Global+OAuth+and+MCP+URLs+for+AI+client+integration) + Lori’s `sp-gateway` work ([APIMGMT-1699](https://sailpoint.atlassian.net/browse/APIMGMT-1699)). **Still** learn `sp-mcp-server` wire contract — backend unchanged. Interceptor/routing concepts from `sailpoint-agentcore-pdp` remain useful even if Terraform target differs.

---

## 10. Success checklist — what “done” looks like

Use this as the EM scorecard. Documentation alone does not equal success — **decisions, people, and proof** do.

### 10.1 Week-1 must-haves (Gate 1 starts here)

| # | Item | Owner | Done when |
| --- | --- | --- | --- |
| W1-1 | **Decision workshop** (§2.2) — D1–D12 + **EDGE** | EM | Decision log updated ≤24h after workshop |
| W1-2 | **OAuth spike go/no-go** (§3.2) | Eng 2 / Rahul | Green, yellow+Cognito date, or escalated red |
| W1-3 | **Eng 1 / 2 / 3 named** (not TBD) | EM | On execution plan + Jira assignees |
| W1-4 | **Partner meetings booked** — Rahul, Lori, Antoine/Dave, Security | EM | Calendar invites accepted |
| W1-5 | **`tools/list` via gateway** in dev | Eng 1 | Friday demo (hardcoded tenant OK) |
| W1-6 | **`test_mcp_tools.py` baseline** tenant-direct | Eng 3 | Green on Masala dev URL |
| W1-7 | **Jira week-1 stories** created under epics | EM | See §4.1; script: `scripts/create_mcp_gateway_jira_stories.py` |

### 10.2 Gate 1 exit (week 4) — internal pilot

| # | Criterion | Evidence |
| --- | --- | --- |
| G1-1 | Cursor E2E: universal URL + `client_id` → `tools/list` + one `tools/call` | Demo recording |
| G1-2 | **2 tenants** routed correctly | Live demo or test log |
| G1-3 | **Zero cross-tenant** in fuzz suite | CI / test output |
| G1-4 | FR6 smoke: tenant-direct URLs unchanged | `test_mcp_tools.py` both modes |
| G1-5 | OAuth path documented (D9) | Memo in decision log |
| G1-6 | EDGE owner documented | Decision log row |
| G1-7 | Honest **not in scope** list for leadership | Slide: no GA, no marketplace, no full UI |
| G1-8 | Skills exit (optional) | §9.6 checkboxes |

**Do not request Gate 2 funding** if G1-3, G1-4, or W1-2 (OAuth) are red.

### 10.3 Gate 2 exit (week 12) — complete solution

| # | Criterion | Evidence |
| --- | --- | --- |
| G2-1 | [`mcp-gateway-mvp-spec.md` §14](mcp-gateway-mvp-spec.md#14-mvp-exit-criteria-closed-beta-ready) signed off | PM + Security + SRE |
| G2-2 | ORR complete (week 8) | SRE ticket / sign-off |
| G2-3 | Closed beta: **5–10 tenants**, 7+ days active | Usage metrics |
| G2-4 | Go/no-go week 10 passed | Meeting notes |
| G2-5 | GA on canonical URL; developer quickstart live | Link + blog |
| G2-6 | Marketplace **submitted** (if in scope) | AWS ticket (review may extend past week 12) |

### 10.4 Organizational success factors

| Factor | Action |
| --- | --- |
| **One edge owner** | AgentCore (DPDE) vs `sp-gateway` (Lori) — single paragraph, week 1 |
| **Masala partnership** | Dave/Antoine own `sp-mcp-server`; gateway only routes |
| **Scope discipline** | No tool reimplementation; no marketplace in Gate 1 |
| **Friday demos** | Every week, even thin |
| **Escalate at 5 days** | PRD or OAuth blocked (risks R1, R3) |
| **Two-gate narrative** | Never imply “GA in 4 weeks” |

### 10.5 EM weekly rhythm

1. Update **decision log** after any workshop or PM change.  
2. Send **one slide**: green / yellow / red on OAuth, edge, Masala, UI.  
3. Review Jira: every story **assigned** or **blocked** with named blocker.  
4. Prep **Gate 2 ask** only in week 4 with §1 checklist + demo.

### 10.6 Top five gaps to close first

1. EDGE owner undecided  
2. Engineer names TBD  
3. OAuth not proven on AgentCore  
4. Kartik HLD not walked (30m)  
5. Jira stories not on the board → run §4 / creation script

---

## Document history

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 0.1 | 2026-05-17 | Dattu Marneni | Initial delivery kit |
| 0.2 | 2026-05-17 | Dattu Marneni | §9 Skills ramp (repo-based learning paths) |
| 0.3 | 2026-05-17 | Dattu Marneni | §10 Success checklist; §4 Jira script reference |
| 0.4 | 2026-05-17 | Dattu Marneni | §4.0 Jira stories DPDE-1835–1878 created |
