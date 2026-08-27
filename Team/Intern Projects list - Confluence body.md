# Intern projects list — Data Engineering

*Use this file as the source to paste into Confluence, or drive a REST API update. Last aligned with repo `Intern Project list`.*

**Program:** 3-month internship program

**Related links**

* [Data Engineering Confluence space](https://sailpoint.atlassian.net/wiki/spaces/data/overview)
* [DPDE Jira board](https://sailpoint.atlassian.net/jira/software/c/projects/DPDE/boards/8265)
* [DPDE backlog](https://sailpoint.atlassian.net/jira/software/c/projects/DPDE/boards/8265/backlog)

---

## Observability & support engineering

Extend or harden local automation (e.g. weekly DE support summary scripts): richer summaries, links to Rootly and Slack runbooks, reliability metrics, or small Tech Ops doc improvements. Tie-ins: Rootly team, Slack alert channels, and Tech Ops references as documented for the DE team.

---

## Developer experience across many repos

With many `*-dip` and platform repos, interns often succeed on templates, scaffolding, READMEs, how to run locally, or a script to refresh the team’s GitHub repo inventory from org/team APIs so it stays accurate.

---

## Data quality / governance (bounded)

Governance stream work: document data contracts, add tests around known pipelines, or improve monitoring for a single service family—scoped with a staff sponsor.

---

## Streaming / Flink slice

A narrow Flink or connector task (one job, one topic family, metrics only) is typical intern scope, with an engineer owning architecture review.

---

## Orchestration & analytics engineering

Airflow- and dbt-related repos support classic intern projects: DAG cleanup, dbt test coverage, lineage documentation, or staging environment improvements—with clear acceptance criteria.

---

## Cross-team “glue”

Improve incident routing clarity (Rootly, Slack channels, on-call ergonomics) where scope is controllable and runbooks exist or are created alongside changes.

---

## Test coverage enhancement (bounded)

**Goal:** Improve reliability and maintainability by raising automated test coverage in critical or low-coverage areas—not chasing a vanity percentage across every repo.

**Learning:** Software quality assurance, testing strategy (unit vs integration), fixtures and mocking, CI signals, and maintainable test design.

**Scope guardrails:** Pick one or two services or one dbt project family from the DE-owned repo list; agree with a staff engineer on critical paths (e.g. ingestion edge cases, transforms, failure modes). Prefer fast unit tests and targeted integration tests over flaky end-to-end sprawl.

**Deliverables:** Baseline coverage or test inventory for chosen surfaces; new tests with clear names and ownership; short documentation on how to run tests locally and in CI; optional thresholds only where the team already uses that pattern.

---

## Legacy cleanup (repos, warehouse objects, DIPs, DAGs) — inventory-first, delete-last

**Goal:** Reduce confusion, cost, and incident surface from stale Git repos, warehouse tables/views, DIPs, or Airflow DAGs—without breaking production consumers.

**Learning:** Data lineage, ownership, change management, safe deprecation patterns, and proving “unused” with evidence (queries, logs, dependency graphs), not guesses.

**Scope guardrails:** Phase 1 is read-only: build a sunset candidate list using last-access or job-run metadata where available, upstream/downstream signals from dbt/Airflow/Flink documentation, and explicit owner sign-off. No drops or repo archival on production paths until a named engineer approves each item. Prefer one domain per intern cycle (e.g. one DIP family, one dbt project, or one Airflow deployment).

**Deliverables:** Spreadsheet or Confluence table of candidates with evidence columns; “safe to deprecate” vs “needs review” tiers; pull requests for documentation and non-breaking changes first (archive READMEs, DAG pause plus documentation, dbt model deprecation comments); optional automation sketch to refresh the inventory. Actual deletes or archivals only per team runbook and after approval.

**Risks to call out:** Downstream dashboards, reverse ETL, legal/retention constraints, and name reuse after drops. The intern project must not own silent production deletes.

---

## Sample charter — legacy cleanup (copy into Jira epic if useful)

| Field | Content |
| --- | --- |
| **Title** | Legacy data & pipeline cleanup — inventory, evidence, and safe deprecation (intern) |
| **Details** | Build an evidence-backed sunset catalog for a bounded DE domain (repos, warehouse objects, DIPs, and/or DAGs). Execute only approved, low-risk hygiene (documentation, tagging, pausing, recommendations)—not unilateral production deletes. Sponsor engineer required for technical review; involve TPM/product when ownership crosses teams. |
| **Objectives** | Learn dependency discovery; deliver a maintainable inventory with evidence and risk tiering; reduce ambiguity via controlled deprecation aligned to change practices; produce durable Confluence/Jira artifacts for handoff. |
| **In scope (summary)** | One agreed domain; read-only discovery; sunset candidate list with required columns; non-breaking changes first; short runbook for sign-off and status. |
| **Out of scope** | Bulk production drops without per-item approval; retention changes without governance/legal input; unrelated refactors; whole-org sweeps unless sponsor expands charter. |
| **Definition of done** | Signed charter with sponsor and metrics; inventory artifact with minimum agreed count and no orphan high-risk rows; at least one approved hygiene outcome per team policy; handoff session and written next-quarter backlog. |
| **Evaluation signals** | Quality of evidence; risk awareness; clarity for EM/TPM; execution discipline; useful depth without skipping sign-off. |

---

## Publishing this page yourself

1. Open [Intern Projects list — Data Engineering](https://sailpoint.atlassian.net/wiki/spaces/~712020a38ff96a4ed542b7aa579a70237b79ae/pages/4964483189/Intern+Projects+list+Data+Engineering) while logged into Atlassian.
2. Edit the page, paste sections from this file (Confluence editor accepts most Markdown when pasted), adjust headings, then **Publish**.

**Optional — Confluence REST API (advanced):** With an API token and your email, you can `GET /wiki/rest/api/content/4964483189?expand=body.storage,version`, merge new HTML or storage format, then `PUT` with `version.number` incremented. Prefer the UI unless you automate updates.
