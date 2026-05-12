# MCP Gateway

This document is a working primer on what an MCP (Model Context Protocol) gateway is, why an organization would build one, and the specific shape it is taking at SailPoint.

It exists to give context to anyone joining the discussion without needing to read all of the underlying PRDs and HLDs first.

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

## Examples In The Wild

- **AWS AgentCore Gateway** — AWS's managed MCP gateway and control plane.
- **TrueFoundry, agentgateway, MCP-Cloud, IBM** — vendor offerings.
- **Atlassian Remote MCP, GitHub Copilot MCP, Linear MCP** — single-URL SaaS gateways in front of per-tenant backends.
- **SailPoint `mcp.sailpoint.com`** — in-progress design fronting per-tenant ISC MCP servers.

## SailPoint Context

There are two existing internal documents that describe the early thinking, both of which are expected to be superseded by what is being asked of the team now:

- `[MCP Q1-2 PRD] SailPoint MCP Server Single URL and OAuth Support` — proposes a thin routing gateway at `https://mcp.sailpoint.com/` that validates OAuth or JWT and forwards MCP requests like `tools/list` and `tools/call` to the correct tenant-specific backend. Existing tenant-specific MCP URLs continue to work; the gateway is additive.
- `[HLD] SailPoint MCP Server` — earlier design for `sp-mcp-server`, an internal microservice that acts as an API gateway for MCP calls into SailPoint systems. Implements the MCP spec (`tools/call`, `tools/list`, `resources/list`, etc.) and delegates execution to other internal services such as RATS and `sp-workflow-*`.

The current state of the approved MCP server list points to a tenant-specific endpoint (for example `https://adi-01.api.cloud.sailpoint.com/v2025/access-requests/mcp`) rather than a universal gateway URL. The universal gateway is still draft or design-stage, and the new ask is to build something that supersedes both of the above.

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

### External

- [Model Context Protocol specification](https://modelcontextprotocol.io)
- [Anthropic — Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol)
- [AWS — Bedrock AgentCore Gateway](https://aws.amazon.com/bedrock/agentcore/)
- [Atlassian Remote MCP Server announcement](https://www.atlassian.com/blog/announcements/remote-mcp-server)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [AWS Labs MCP Servers](https://github.com/awslabs/mcp)
