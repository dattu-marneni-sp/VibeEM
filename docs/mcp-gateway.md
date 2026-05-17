# MCP Gateway

This document is a working primer on what an MCP (Model Context Protocol) gateway is, why an organization would build one, and the specific shape it is taking at SailPoint.

It exists to give context to anyone joining the discussion without needing to read all of the underlying PRDs and HLDs first.

**MVP scope and acceptance criteria:** see [`mcp-gateway-mvp-spec.md`](mcp-gateway-mvp-spec.md).

## What An MCP Gateway Is

An MCP gateway is a server that sits in front of one or more MCP servers and acts as a single, governed entry point between AI clients (Cursor, Claude, ChatGPT, custom agents) and the actual tools or services those clients want to use.

It is the API gateway pattern, applied to the MCP protocol.

## What It Typically Does

- **Single endpoint.** One URL like `https://mcp.company.com` that clients point at, instead of dozens of per-team or per-tenant MCP server URLs.
- **Authentication and authorization.** Validates OAuth tokens, JWTs, or API keys and enforces who can call which tool. Usually integrates with an enterprise IdP.
- **Routing.** Forwards each MCP request (`tools/list`, `tools/call`, `resources/read`, etc.) to the correct downstream MCP server based on tool namespace, tenant claim in the token, or environment.
- **Tool aggregation and namespacing.** Merges tool catalogs from many backend MCP servers into one `tools/list` response, usually prefixed (for example `sailpoint.access_requests.list`, `github.repos.search`).
- **Policy and guardrails.** Rate limiting per user, tenant, or tool. PII or secret redaction. Tool-level allowlists and denylists. Human-in-the-loop approval for sensitive tools.
- **Observability.** Structured logs of every tool call: who, what tool, what arguments, latency, status. Audit trail for compliance. Metrics and dashboards.
- **Transport handling.** Speaks Streamable HTTP or SSE on the client side and can fan out to backends that use stdio, HTTP, or SSE. Handles session management, reconnects, and resumability.

## Why Companies Build One

Without a gateway:

- Every team stands up its own MCP server with its own auth.
- Users have to configure many URLs in Cursor or Claude.
- Security has no single chokepoint to audit, throttle, or block.
- Multi-tenant SaaS leaks tenant URLs to clients.

With a gateway:

- One URL, one OAuth flow, one place to enforce policy and capture audit logs.
- Backend MCP servers stay simple; the gateway owns the cross-cutting concerns.

## JWT-Based Tenant Routing

A specific pattern that shows up in the SailPoint design: the gateway figures out which backend to forward a request to by reading claims out of the caller's JWT bearer token, instead of relying on the URL or a separate header.

How it works:

1. Client calls a single universal endpoint, for example `POST https://mcp.sailpoint.com/` with `Authorization: Bearer <jwt>`.
2. Gateway validates the JWT (signature, expiry, issuer).
3. Gateway extracts a tenant identifier from the token claims (`tenant_id`, `org`, `pod`, `client_id`, `identity_id`).
4. Gateway looks up that tenant in a routing table and constructs the tenant-specific backend URL, for example `https://{tenant}.api.identitynow.com/mcp`.
5. Gateway proxies the original MCP request body and headers to that backend, then returns the response unchanged.

Why this pattern is used:

- **One URL for every tenant.** Clients do not need to know `acme.api.identitynow.com` vs `globex.api.identitynow.com`; they all point at `mcp.sailpoint.com`.
- **Identity is already in the token.** OAuth/JWT carries who the user is, which org or tenant they belong to, and which OAuth client is calling, so no extra tenant parameter, header, or path segment is needed.
- **Strong isolation.** A user can only ever reach the tenant their token was issued for; the gateway cannot be tricked into cross-tenant routing by a path or query string.
- **Lets the backend stay tenant-specific.** Existing per-tenant MCP backends keep working unchanged; the gateway is just a thin router in front of them.

Contrast with alternatives:

- **Path-based routing** (`https://mcp.sailpoint.com/acme/...`): works but exposes tenant in the URL and requires the client to know it.
- **Subdomain routing** (`https://acme.mcp.sailpoint.com`): the current SailPoint model; defeats the single-universal-URL goal.
- **Header-based routing** (`X-Tenant: acme`): easy to spoof unless verified against the token anyway, so JWT-based is the cleaner source of truth.

## MCP Gateway Is Not An API Gateway

A common early instinct is to reuse an existing API gateway (Apigee, Kong, Envoy, etc.) for MCP traffic. This works for the easy parts and breaks down quickly on the hard parts. The core reason is that **APIs are stateless and MCP is stateful**.

### Why The Two Are Different

- **APIs** route on the HTTP layer: method, path, headers, query parameters. Each request is independent. The body is mostly opaque to the gateway.
- **MCP** routes on the body: every meaningful detail (`method`, tool name, arguments) lives inside a JSON-RPC payload. Sessions are tracked via `Mcp-Session-Id`. A single client `POST /mcp` can produce multiple streamed SSE events back, and servers can initiate messages back to clients (notifications, elicitations, sampling).

In short: an API gateway sees `POST /mcp` and a JSON blob. An MCP gateway has to understand the protocol inside the blob, keep session state, and broker bidirectional streams.

### Spectrum Of MCP Gateway Capabilities

There is a useful ladder of capability — most teams start at the bottom and find they need to climb:

1. **Simple passthrough proxy.** Treats MCP as opaque HTTP. Gives you TLS, JWT validation on the `Authorization` header, basic rate limiting, and request/response logs. Can't inspect tool calls, can't apply policy mid-stream, loses session context across SSE events.
2. **Partial protocol understanding.** Custom scripts (JS, Lua) parse JSON-RPC and apply tool-level policy ("marketing users can't call `database_query`"). Quickly becomes brittle: every new tool means new gateway policy, performance overhead from scripting, limited streaming support.
3. **MCP brokering.** Gateway is an active participant in the MCP conversation: protocol version shielding (client speaks v1 while server speaks v2), tool filtering on `tools/list`, response sanitization based on user clearance, context injection (user/tenant), error normalization. Requires native JSON-RPC understanding and session-aware policy.
4. **MCP multiplexing (virtual MCP server).** One logical endpoint that aggregates many backend MCP servers. Needs session fan-out on `tools/list`, name-based routing on `tools/call`, response merging across SSE streams from multiple backends, cross-backend session and error coordination. This is where traditional API gateways hit a wall.

### Implications For The SailPoint Design

- The currently documented `mcp.sailpoint.com` PRD is mostly **level 1 + a bit of level 2**: validate JWT, route by `tenant_id` claim, forward to a tenant-specific backend. That works for a single-server, single-tenant routing problem.
- The version Gaurav is asking for almost certainly needs **level 3 and level 4**: brokering (policy, redaction, audit injection, version shielding) and multiplexing across multiple SailPoint MCP backends (ISC tools, workflows, AIS, NERM, possibly third-party MCPs governed under SailPoint identity).
- Choosing the foundation matters. Building level 3/4 on top of a generic API gateway means continuously fighting the architecture. Purpose-built MCP gateways (e.g. CNCF [agentgateway](https://agentgateway.dev/), AWS Bedrock AgentCore Gateway) start from session-aware, JSON-RPC-native, SSE-aware foundations.

### Decision Hooks To Bring To The Call

- What's the target capability level for v1: passthrough, brokering, or full multiplexing?
- Build on top of an existing API gateway, adopt a purpose-built MCP gateway (agentgateway, AgentCore), or build new in-house?
- Where does session state live, and how is it scaled across instances (sticky routing vs. shared store like Redis)?
- How is tool-level authorization expressed and enforced — at the gateway, at a separate PDP, or inside each backend?
- What is the contract for backends: do they all speak the same MCP version, or does the gateway broker versions?

## Reference Architecture: AWS Bedrock AgentCore Gateway

AWS's AgentCore Gateway is a useful concrete example of a managed MCP gateway because it explicitly implements the brokering and multiplexing patterns described above. The November 2025 update added "MCP server" as a first-class target type, alongside Lambda, OpenAPI, and Smithy targets.

### Core Concepts

- **Gateway.** A single MCP-protocol endpoint that agents connect to.
- **Targets.** What the gateway exposes as tools. A target can be a Lambda function, an OpenAPI spec, a Smithy model, an MCP server, an AgentCore Runtime instance, or even another AgentCore Gateway (federation).
- **Inbound auth.** JWT (e.g. Cognito) validated on every client request, decoupled from how the gateway talks to backends.
- **Outbound auth.** Per-target OAuth credentials managed by AgentCore Identity, fetched fresh at invocation time.
- **Semantic search.** Embeddings are generated over tool name, description, and parameter descriptions, exposed via a special `x_amz_bedrock_agentcore_search` tool so agents can discover relevant tools across all targets without exact-name matching.

### Tool Schema Synchronization

A nice solution to the "where do tool definitions live" problem:

- **Implicit sync** on `CreateGatewayTarget` / `UpdateGatewayTarget`: gateway calls the backend's `tools/list` and stores normalized definitions before the target is marked `READY`.
- **Explicit sync** via `SynchronizeGatewayTargets` API for on-demand refresh after backend tool changes.
- **Cache-first `ListTools`** at request time — no real-time fan-out to backends, so listing is fast and reliable.
- **Real-time `tools/call`** — actual invocation goes through to the backend with fresh OAuth credentials.
- **Tool name prefixing** during normalization to prevent collisions across targets.

This is a cleaner pattern than naive multiplexing because it separates the slow path (sync tool catalogs) from the hot path (list/call), and gives operators an explicit moment to validate new schemas.

### Patterns Worth Borrowing Or Contrasting For SailPoint

- **Treat backends as "targets" with a typed contract.** Don't hard-code routing to "tenant X's ISC MCP server" — make backend type a first-class concept (`isc-tenant`, `workflow`, `ais`, `third-party`) so the gateway can grow without protocol rewrites.
- **Decouple inbound and outbound auth.** Inbound: SailPoint IdP / OAuth. Outbound: per-backend credentials (could be tenant-scoped service tokens, on-behalf-of tokens, or PATs). Match AgentCore's "credential provider" abstraction.
- **Cache tool definitions; refresh on demand.** Avoid fanning out `tools/list` to every backend on every client connect — it will not scale to dozens of tenants times dozens of tools.
- **Add a semantic search tool.** Agents lose accuracy as the tool count grows; SailPoint's identity-governance vocabulary is a good fit for embedding-based discovery.
- **Allow gateway-of-gateways (federation).** Lets internal SailPoint AI use cases and external customer-facing MCP traffic share a control plane without merging into one giant tool list.
- **Watch the statefulness trap.** AgentCore's sample MCP server uses `stateless_http=True`. SailPoint will need to decide whether tenant backends are stateless (easy to scale, lose MCP session features) or stateful (richer protocol, requires sticky routing or shared session store).

### Caveats

- AgentCore Gateway is AWS-managed and Bedrock-coupled. Adopting it means accepting AWS as the control plane for SailPoint's agentic surface, which has data-residency, FedRAMP, and pricing implications.
- The cache-first `ListTools` model trades freshness for performance — fine for tools that change rarely, but the team should pick an explicit sync cadence.
- Federation across gateways simplifies organization but adds a hop of latency and another auth boundary.

## Examples In The Wild

- **AWS Bedrock AgentCore Gateway** — managed MCP gateway and control plane; supports MCP servers, Lambda, OpenAPI, Smithy, and federation as target types.
- **agentgateway** — CNCF / Linux Foundation, Rust, purpose-built for MCP and A2A; pairs with kgateway for Kubernetes-native control plane.
- **TrueFoundry, MCP-Cloud, IBM** — other vendor offerings.
- **Atlassian Remote MCP, GitHub Copilot MCP, Linear MCP** — single-URL SaaS gateways in front of per-tenant backends.
- **SailPoint `mcp.sailpoint.com`** — in-progress design fronting per-tenant ISC MCP servers.

## SailPoint Context

There are two existing internal documents that describe the early thinking, both of which are expected to be superseded by what is being asked of the team now:

- `[MCP Q1-2 PRD] SailPoint MCP Server Single URL and OAuth Support` — proposes a thin routing gateway at `https://mcp.sailpoint.com/` that validates OAuth or JWT and forwards MCP requests like `tools/list` and `tools/call` to the correct tenant-specific backend. Existing tenant-specific MCP URLs continue to work; the gateway is additive.
- `[HLD] SailPoint MCP Server` — earlier design for `sp-mcp-server`, an internal microservice that acts as an API gateway for MCP calls into SailPoint systems. Implements the MCP spec (`tools/call`, `tools/list`, `resources/list`, etc.) and delegates execution to other internal services such as RATS and `sp-workflow-*`.

The current state of the approved MCP server list points to a tenant-specific endpoint (for example `https://adi-01.api.cloud.sailpoint.com/v2025/access-requests/mcp`) rather than a universal gateway URL. The universal gateway is still draft or design-stage, and the new ask is to build something that supersedes both of the above.

**Related research (Dave Owens):** [AWS Agent Core Gateway Integration](https://sailpoint.atlassian.net/wiki/spaces/~978782161/pages/4347527504/AWS+Agent+Core+Gateway+Integration) documents how **AgentCore Gateway interceptors** can route Marketplace or agent traffic to existing **tenant-specific MCP URLs** on EKS (API-based SaaS listing, no container repackaging). It also defines **two authentication layers** — service/tenant identity at the gateway and **ISC user identity** at `sp-mcp-server` — which the 4-week INIT-2704 plan collapses into a single Cursor PKCE user token for the internal pilot. Full analysis: [`mcp-gateway-execution-plan.md` § Dave Owens — Marketplace & AgentCore](mcp-gateway-execution-plan.md#dave-owens--marketplace--agentcore-integration-confluence).

## Related Repositories

Internal codebases and Global Initiatives that overlap with the MCP gateway ([INIT-2704](https://sailpoint.atlassian.net/browse/INIT-2704)). Full MVP scope, initiative analysis, and Jira mapping: [`mcp-gateway-mvp-spec.md`](mcp-gateway-mvp-spec.md) · [`mcp-gateway-execution-plan.md`](mcp-gateway-execution-plan.md) (§ Initiative landscape, § Quick takeaway).

### [sailpoint-agentcore-pdp](https://github.com/sailpoint-core/sailpoint-agentcore-pdp) (`sailpoint-core`)

**What it is.** A reference deployment of **AWS Bedrock AgentCore Gateway** plus a **Policy Decision Point (PDP)** — a Python Lambda **interceptor** on the REQUEST and RESPONSE path. Today it **audit-logs** full MCP payloads to CloudWatch (sensitive headers redacted) and **passes traffic through unchanged**. Extension hooks in `interceptor/hooks.py` are stubs for future **allow/deny, redaction, and enrichment**.

**What it is not.** The customer-facing SailPoint universal gateway (`mcp.sailpoint.com`): no SailPoint OAuth productization, no `client_id → tenant_id` routing, no ISC tenant MCP backends, no ISC Admin client registration.

**Layout.**

| Path | Role |
| --- | --- |
| `terraform/` | Gateway, PDP Lambda, IAM, CloudWatch log groups, optional MCP targets |
| `interceptor/lambda_handler.py` | REQUEST vs RESPONSE dispatch, audit JSON, hook calls |
| `interceptor/hooks.py` | `process_request` / `process_response` (default: identity) |

**Default demo targets** (optional Terraform vars): GitHub Copilot MCP, Atlassian Remote MCP — useful to prove **multiplexing** and Cursor wiring, not SailPoint tenants.

**How it maps to DPDE epics**

| Epic | Relationship |
| --- | --- |
| [DPDE-1781](https://sailpoint.atlassian.net/browse/DPDE-1781) Foundation / PoC | **Largely de-risked** — AgentCore Gateway + Terraform + interceptor pattern exist; extend for SailPoint envs and targets |
| [DPDE-1770](https://sailpoint.atlassian.net/browse/DPDE-1770) FR3 `tools/list` & `tools/call` | **Partially de-risked** — MCP protocol path works with external MCP targets; **net-new** for ISC tenant backends |
| [DPDE-1779](https://sailpoint.atlassian.net/browse/DPDE-1779) FR12 Request logging | **Partially de-risked** — structured request/response audit to CloudWatch; **net-new** for Snowflake pipeline, SailPoint field schema, PII sign-off |
| [DPDE-1778](https://sailpoint.atlassian.net/browse/DPDE-1778) FR11 Errors & health | **Net-new** — PDP does not implement `{error, message, request_id}` envelope or `/health` |
| [DPDE-1769](https://sailpoint.atlassian.net/browse/DPDE-1769) FR2 OAuth / JWT | **Pattern only** — repo supports `CUSTOM_JWT` or `AWS_IAM`; **net-new** to wire SailPoint OAuth, PKCE, scopes |
| [DPDE-1771](https://sailpoint.atlassian.net/browse/DPDE-1771) FR4 Routing | **Net-new** — no tenant routing; demo routes to GitHub/Atlassian URLs |
| [DPDE-1776](https://sailpoint.atlassian.net/browse/DPDE-1776) FR8 Mapping store | **Net-new** |
| [DPDE-1775](https://sailpoint.atlassian.net/browse/DPDE-1775) FR7 Admin / CLI | **Net-new** |
| [DPDE-1768](https://sailpoint.atlassian.net/browse/DPDE-1768) FR1 Universal URL | **Net-new** for `mcp.sailpoint.com` DNS/TLS and SailPoint client docs; reuse only the generic “point Cursor at `gateway_url`” flow |
| [DPDE-1773](https://sailpoint.atlassian.net/browse/DPDE-1773) FR6 Backward compat | **Net-new** |
| [DPDE-1774](https://sailpoint.atlassian.net/browse/DPDE-1774) FR9 Snowflake | **Net-new** |
| [DPDE-1777](https://sailpoint.atlassian.net/browse/DPDE-1777) FR10 Dashboards | **Net-new** (beyond basic CloudWatch logs) |
| [DPDE-1780](https://sailpoint.atlassian.net/browse/DPDE-1780) NFR validation | **Net-new** at SailPoint scale |
| [DPDE-1782](https://sailpoint.atlassian.net/browse/DPDE-1782) Docs / GA | **Net-new** for SailPoint quickstarts |

**Recommended use for the 4-week accelerated plan.** Fork or extend this repo for **Eng 1 (Platform)** instead of greenfield AgentCore Terraform. Add SailPoint targets, `CUSTOM_JWT`, custom domain (coordinate [APIMGMT-1990](https://sailpoint.atlassian.net/browse/APIMGMT-1990), [SAASSRE-6461](https://sailpoint.atlassian.net/browse/SAASSRE-6461)), and implement policy in `hooks.py` when security is ready.

**AWS docs.** [Gateway interceptors](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-interceptors.html) · [Interceptor payload types](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-interceptors-types.html) · [MCP server targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-MCPservers.html)

### [sp-mcp-server](https://github.com/sailpoint-core/sp-mcp-server) (`sailpoint-core`)

**What it is.** The **downstream MCP backend** for ISC access requests (and additional paths for workflow/transform). Go service on Atlas: Streamable HTTP MCP, real `tools/list` and `tools/call`, integration with Request Center and related ISC APIs. Owned by Masala / ADI (Harbor Pilot).

**What it is not.** The universal MCP gateway — no `client_id → tenant_id` multiplexing at scale, no AgentCore front door, no external Cursor OAuth productization (those are INIT-2704 / DPDE).

**MVP path.** `https://{tenant}.api.cloud.sailpoint.com/{version}/access-requests/mcp` today; global host `mcp.api.cloud.sailpoint.com` in flight with RFC 9728 metadata env vars (`SP_MCP_GLOBAL_MCP_PUBLIC_URL`, `SP_MCP_GLOBAL_AUTHORIZATION_SERVER_ISSUER`).

**4-week implication.** Gateway team **routes** to this service; **does not reimplement** tools. Golden test: repo `test_mcp_tools.py`. Full wire contract: [`mcp-gateway-execution-plan.md` § Backend contract — sp-mcp-server](mcp-gateway-execution-plan.md#backend-contract--sp-mcp-server).

| Epic | Relationship |
| --- | --- |
| [DPDE-1770](https://sailpoint.atlassian.net/browse/DPDE-1770) FR3 | **Largely de-risked** — MCP protocol + access-request tools exist |
| [DPDE-1771](https://sailpoint.atlassian.net/browse/DPDE-1771) FR4 | Gateway picks correct upstream URL per mapping |
| [DPDE-1773](https://sailpoint.atlassian.net/browse/DPDE-1773) FR6 | Tenant-direct URLs remain valid; use for compat harness |

### Other in-flight work (coordinate, not duplicate)

| Item | Role |
| --- | --- |
| [APIMGMT-1990](https://sailpoint.atlassian.net/browse/APIMGMT-1990) | AgentCore MCP Gateway setup (us-east-1) |
| [SAASSIGMA-6213](https://sailpoint.atlassian.net/browse/SAASSIGMA-6213) | Lambda interceptor testing |
| [SAASSRE-6461](https://sailpoint.atlassian.net/browse/SAASSRE-6461) | Global OAuth/MCP URLs — DNS, CloudFront, sp-gateway |
| [APIMGMT-1699](https://sailpoint.atlassian.net/browse/APIMGMT-1699) | sp-gateway MCP and global URL support |
| [AI-881](https://sailpoint.atlassian.net/browse/AI-881) | External (customer-facing) MCP Gateway (on hold) |

## One-Line Definition

An MCP gateway is the enterprise control plane for AI tool use — a reverse proxy for MCP that adds identity, routing, policy, and observability so that "let an agent use our tools" becomes a governed product instead of a free-for-all.

## Open Questions

- What does "supersede" mean concretely: a new design, or a re-platforming of the gateway itself?
- Which backends are in scope at launch (ISC tools only, or also workflows, AIS, NERM, etc.)?
- Is multi-region and FedRAMP in scope for v1, or deferred?
- Where does authorization live: at the gateway, at a separate PDP, or inside each backend MCP server?
- What is the relationship to AWS AgentCore Gateway and other vendor options?
- How does this interact with the SAF initiative's view of agent identities?

## References

### SailPoint Internal

- [\[MCP Q1-2 PRD\] SailPoint MCP Server Single URL and OAuth Support](https://sailpoint.atlassian.net/wiki/spaces/~7120200fd8a6740fdb4ca9bd0f88f478f134a5/pages/4634738812/MCP+Q1-2+PRD+SailPoint+MCP+Server+Single+URL+and+Oauth+Support)
- [\[HLD\] SailPoint MCP Server](https://sailpoint.atlassian.net/wiki/spaces/~557058a92a897c42824a4792963165ed4eea38/pages/3670769784/HLD+SailPoint+MCP+Server)
- [\[Draft\] SailPoint MCP Platform Strategy](https://sailpoint.atlassian.net/wiki/spaces/~7120200fd8a6740fdb4ca9bd0f88f478f134a5/pages/4614226238/Draft+SailPoint+MCP+Platform+Strategy)
- [Enterprise MCP Server Infrastructure Research](https://sailpoint.atlassian.net/wiki/spaces/~7120200fd8a6740fdb4ca9bd0f88f478f134a5/pages/4631528649/Enterprise+MCP+Server+Infrastructure+Research)
- [AWS Agent Core Gateway Integration](https://sailpoint.atlassian.net/wiki/spaces/~978782161/pages/4347527504/AWS+Agent+Core+Gateway+Integration)
- [Approved MCP Servers](https://sailpoint.atlassian.net/wiki/spaces/SDLC/pages/4951474326)
- [MCP Server Request Process](https://sailpoint.atlassian.net/wiki/spaces/SDLC/pages/4175036476)
- [AI Assistants + MCP servers: Onboarding guide](https://sailpoint.atlassian.net/wiki/spaces/SDLC/pages/4914413686/AI+Assistants+MCP+servers+Onboarding+guide)
- [MCP / Agentic Security Policies](https://sailpoint.atlassian.net/wiki/spaces/SEC/pages/4820926587/MCP+Agentic+Security+Policies)
- [SailPoint MCP Server Announcement](https://sailpoint.atlassian.net/wiki/spaces/PMO/pages/4244439556/SailPoint+MCP+Server+Announcement)
- Jira epic: [External (Customer-facing) MCP Gateway — AI-881](https://sailpoint.atlassian.net/browse/AI-881)
- GitHub: [sailpoint-agentcore-pdp](https://github.com/sailpoint-core/sailpoint-agentcore-pdp) — AgentCore Gateway + PDP audit interceptor (see [Related Repositories](#related-repositories))
- GitHub: [sp-mcp-server](https://github.com/sailpoint-core/sp-mcp-server) — ISC MCP backend (access requests); gateway routes here (see [Related Repositories](#related-repositories))

### External

- [Model Context Protocol specification](https://modelcontextprotocol.io)
- [Anthropic — Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol)
- [Christian Posta — MCP vs. API Gateways: They're Not Interchangeable (The New Stack)](https://thenewstack.io/mcp-vs-api-gateways-theyre-not-interchangeable/)
- [agentgateway (CNCF / Linux Foundation, Rust)](https://agentgateway.dev/)
- [AWS — Bedrock AgentCore Gateway](https://aws.amazon.com/bedrock/agentcore/)
- [AWS — Transform your MCP architecture: Unite MCP servers through AgentCore Gateway](https://aws.amazon.com/blogs/machine-learning/transform-your-mcp-architecture-unite-mcp-servers-through-agentcore-gateway/)
- Video: [Amazon Bedrock AgentCore — Gateway (AWS, 4:29)](https://www.youtube.com/watch?v=B8FCjR8uIBI) — short demo and code walkthrough (create gateway, add Lambda target, MCP `tools/list` / `tools/call`, semantic tool search).
- [Atlassian Remote MCP Server announcement](https://www.atlassian.com/blog/announcements/remote-mcp-server)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [AWS Labs MCP Servers](https://github.com/awslabs/mcp)
