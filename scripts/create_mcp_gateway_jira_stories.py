#!/usr/bin/env python3
"""Create MCP Gateway Gate 1 Jira stories under DPDE epics (INIT-2704).

Requires: JIRA_API_TOKEN env var, SailPoint Jira access.
Usage: python3 scripts/create_mcp_gateway_jira_stories.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

JIRA_BASE = "https://sailpoint.atlassian.net"
JIRA_USER = "dattu.marneni@sailpoint.com"
PROJECT = "DPDE"
COMPONENT_ID = "38674"  # DP-SAF
LABELS = ["INIT-2704", "mcp-gateway"]
DOC_LINK = "docs/mcp-gateway-delivery-kit.md §4"


def adf_description(body: str) -> dict:
    paragraphs = []
    for line in body.strip().split("\n"):
        paragraphs.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": line}],
            }
        )
    return {"type": "doc", "version": 1, "content": paragraphs}


def create_story(
    epic_key: str,
    summary: str,
    description: str,
    dry_run: bool,
) -> str | None:
    token = os.environ.get("JIRA_API_TOKEN")
    if not token and not dry_run:
        print("ERROR: Set JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    payload = {
        "fields": {
            "project": {"key": PROJECT},
            "parent": {"key": epic_key},
            "issuetype": {"name": "Story"},
            "summary": summary,
            "description": adf_description(description),
            "labels": LABELS,
            "components": [{"id": COMPONENT_ID}],
        }
    }

    if dry_run:
        print(f"DRY-RUN {epic_key} | {summary}")
        return None

    req = urllib.request.Request(
        f"{JIRA_BASE}/rest/api/3/issue",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    import base64

    creds = base64.b64encode(f"{JIRA_USER}:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {creds}")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            key = data["key"]
            print(f"Created {key} | {epic_key} | {summary}")
            return key
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"FAILED {epic_key} | {summary}\n  {e.code} {err[:800]}", file=sys.stderr)
        return None


# Week 1 stories (delivery kit §4.1)
WEEK1: list[tuple[str, str, str]] = [
    (
        "DPDE-1767",
        "[Gate1-W1] Schedule week-1 decision workshop and pre-read",
        "Acceptance criteria:\n"
        "- All required attendees accepted (delivery kit §2.2)\n"
        "- Pre-read links sent 24h before\n"
        f"Source: {DOC_LINK}.1 DPDE-1767-1",
    ),
    (
        "DPDE-1767",
        "[Gate1-W1] Publish two-gate funding narrative for leadership",
        "Acceptance criteria:\n"
        "- §1 two-gate model linked from INIT-2704 or Confluence\n"
        f"Source: {DOC_LINK}.1 DPDE-1767-2",
    ),
    (
        "DPDE-1767",
        "[Gate1-W1] Stand up weekly demo cadence (Fri 30m)",
        "Acceptance criteria:\n"
        "- Recurring invite; template: demo + risks + decisions\n"
        f"Source: {DOC_LINK}.1 DPDE-1767-3",
    ),
    (
        "DPDE-1767",
        "[Gate1-W1] Create decision log page and RACI",
        "Acceptance criteria:\n"
        "- D1–D12 table live; owners assigned (§5–6)\n"
        f"Source: {DOC_LINK}.1 DPDE-1767-4",
    ),
    (
        "DPDE-1781",
        "[Gate1-W1] Deploy AgentCore gateway from sailpoint-agentcore-pdp in dev",
        "Acceptance criteria:\n"
        "- Gateway URL documented; IaC in repo\n"
        f"Source: {DOC_LINK}.1 DPDE-1781-1 | Spike §3.1",
    ),
    (
        "DPDE-1781",
        "[Gate1-W1] Register one MCP target → tenant access-requests/mcp",
        "Acceptance criteria:\n"
        "- tools/list succeeds with user bearer token\n"
        f"Source: {DOC_LINK}.1 DPDE-1781-2",
    ),
    (
        "DPDE-1781",
        "[Gate1-W1] Spike interceptor pass-through + request logging",
        "Acceptance criteria:\n"
        "- CloudWatch shows MCP method + request_id\n"
        f"Source: {DOC_LINK}.1 DPDE-1781-3",
    ),
    (
        "DPDE-1781",
        "[Gate1-W1] Document edge architecture decision (AgentCore vs sp-gateway)",
        "Acceptance criteria:\n"
        "- Lori + EM sign-off in decision log (EDGE row)\n"
        f"Source: {DOC_LINK}.1 DPDE-1781-4",
    ),
    (
        "DPDE-1781",
        "[Gate1-W1] Week-1 exit: tools/list via gateway in dev",
        "Acceptance criteria:\n"
        "- Demo recording attached to epic\n"
        f"Source: {DOC_LINK}.1 DPDE-1781-5",
    ),
    (
        "DPDE-1769",
        "[Gate1-W1] Obtain dev OAuth static client + scopes",
        "Acceptance criteria:\n"
        "- client_id, redirect URIs, scopes documented (Rahul)\n"
        f"Source: {DOC_LINK}.1 DPDE-1769-1",
    ),
    (
        "DPDE-1769",
        "[Gate1-W1] Spike customJWTAuthorizer with SailPoint JWKS",
        "Acceptance criteria:\n"
        "- Valid JWT → 200; invalid → 401\n"
        f"Source: {DOC_LINK}.1 DPDE-1769-2 | Spike §3.2",
    ),
    (
        "DPDE-1769",
        "[Gate1-W1] Document JWT claims for tenant routing (D3, D11)",
        "Acceptance criteria:\n"
        "- Claim matrix reviewed by Rahul + Masala\n"
        f"Source: {DOC_LINK}.1 DPDE-1769-3",
    ),
    (
        "DPDE-1769",
        "[Gate1-W1] OAuth spike go/no-go memo (D9)",
        "Acceptance criteria:\n"
        "- Green / yellow (Cognito) / red with escalation path\n"
        f"Source: {DOC_LINK}.1 DPDE-1769-4",
    ),
    (
        "DPDE-1768",
        "[Gate1-W1] Confirm dev hostname with SRE/APIMGMT (mcp-dev.*)",
        "Acceptance criteria:\n"
        "- DNS/TLS path documented or ticket linked\n"
        f"Source: {DOC_LINK}.1 DPDE-1768-1",
    ),
    (
        "DPDE-1768",
        "[Gate1-W1] Draft Cursor mcp.json for gateway URL (stub)",
        "Acceptance criteria:\n"
        "- Checked into repo; works when gateway live\n"
        f"Source: {DOC_LINK}.1 DPDE-1768-2",
    ),
    (
        "DPDE-1776",
        "[Gate1-W1] Choose mapping store and schema (DynamoDB vs RDS)",
        "Acceptance criteria:\n"
        "- ADR: client_id, tenant_id, revoked_at\n"
        f"Source: {DOC_LINK}.1 DPDE-1776-1",
    ),
    (
        "DPDE-1776",
        "[Gate1-W1] Define admin CRUD API contract for CLI",
        "Acceptance criteria:\n"
        "- OpenAPI or markdown; no UI required for Gate 1\n"
        f"Source: {DOC_LINK}.1 DPDE-1776-2",
    ),
]

# Weeks 2–4 (delivery kit §4.2) — one story per epic per week
WEEKS_2_4: list[tuple[str, str, str, str]] = [
    ("DPDE-1771", "W2", "Mapping store v1 + route to tenant target"),
    ("DPDE-1771", "W3", "Second tenant; routing cache"),
    ("DPDE-1771", "W4", "Fuzz tests; zero cross-tenant"),
    ("DPDE-1770", "W2", "tools/call E2E one tool"),
    ("DPDE-1770", "W3", "All four tools via gateway"),
    ("DPDE-1770", "W4", "Error paths on tool failure"),
    ("DPDE-1772", "W2", "PKCE E2E Cursor"),
    ("DPDE-1772", "W3", "Expired token 401 envelope"),
    ("DPDE-1772", "W4", "Revoked client 403"),
    ("DPDE-1778", "W2", "/health + error envelope v1"),
    ("DPDE-1778", "W3", "Contract tests all 4xx/5xx"),
    ("DPDE-1778", "W4", "request_id in logs"),
    ("DPDE-1779", "W2", "Structured CW logs, no bearer in logs"),
    ("DPDE-1779", "W3", "PII redaction checklist"),
    ("DPDE-1779", "W4", "Log retention policy"),
    ("DPDE-1773", "W2", "FR6 harness tenant-direct"),
    ("DPDE-1773", "W3", "FR6 via gateway"),
    ("DPDE-1773", "W4", "CI gate on PR"),
    ("DPDE-1775", "W2", "Admin CLI create/revoke client"),
    ("DPDE-1775", "W3", "Bind client_id→tenant_id"),
    ("DPDE-1775", "W4", "Documented admin flow"),
    ("DPDE-1782", "W2", "Quickstart draft"),
    ("DPDE-1782", "W3", "Timed dev test (NFR-011)"),
    ("DPDE-1782", "W4", "Demo video ≤3 min"),
    ("DPDE-1780", "W2", "k6 smoke 50 concurrent"),
    ("DPDE-1780", "W3", "Security review scheduled"),
    ("DPDE-1780", "W4", "Gate-1 success checklist complete (§10)"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--week1-only", action="store_true")
    args = parser.parse_args()

    created: list[str] = []
    failed = 0

    for epic, summary, desc in WEEK1:
        key = create_story(epic, summary, desc, args.dry_run)
        if key:
            created.append(key)
        elif not args.dry_run:
            failed += 1

    if not args.week1_only:
        for epic, week, ac in WEEKS_2_4:
            summary = f"[Gate1-{week}] {ac[:70]}"
            desc = (
                f"Acceptance criteria:\n- {ac}\n"
                f"Epic: {epic}\n"
                f"Source: {DOC_LINK}.2"
            )
            key = create_story(epic, summary, desc, args.dry_run)
            if key:
                created.append(key)
            elif not args.dry_run:
                failed += 1

    print(f"\nDone. Created: {len(created)}, Failed: {failed}")
    if created:
        print("Keys:", ", ".join(created))


if __name__ == "__main__":
    main()
