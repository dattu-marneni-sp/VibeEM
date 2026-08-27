# Data Platform COGS — 1-Pager Summary

**Follow-up:** SAF fast-lane readout action item (Gaurav)  
**Parent initiative:** [INIT-2955 — 2026-2027 Cost Savings Initiative](https://sailpoint.atlassian.net/browse/INIT-2955)  
**Jira filter:** [COGS epics under INIT-2955](https://sailpoint.atlassian.net/issues?jql=parent%3DINIT-2955%20and%20project%20in%20%28%22DP%20-%20Data%20Engineering%22%2C%20%22Data%20Platform%20Intake%22%29%20ORDER%20BY%20rank)  
**Program context:** Q3 target **$1M** run-rate savings · FY27 target **~$9M** · Savings validated via 7-day before/after average × remaining FY days

---

## Where work is tracked

| Source | Link | What it holds |
| --- | --- | --- |
| **INIT-2955 epics** | [Jira filter](https://sailpoint.atlassian.net/issues?jql=parent%3DINIT-2955%20and%20project%20in%20%28%22DP%20-%20Data%20Engineering%22%2C%20%22Data%20Platform%20Intake%22%29%20ORDER%20BY%20rank) | Implementation epics + intake tickets |
| **Snowflake program** | [DPDE-1947](https://sailpoint.atlassian.net/browse/DPDE-1947) · [INIT-1581](https://sailpoint.atlassian.net/browse/INIT-1581) | Query/warehouse cost & perf stories |
| **Snowflake playbook** | [Confluence — Snowflake Cost Optimization](https://sailpoint.atlassian.net/wiki/spaces/data/pages/5249630233/Snowflake+Cost+Optimization) | Patterns, diagnostics, team guidance |
| **FinOps tracker** | [Cost Savings Initiatives 2026.xlsx](https://sailpoint-my.sharepoint.com/:x:/r/personal/robert_wellman_sailpoint_com/Documents/Projects/Budget/FinOps/Cost%20Savings%20Initiatives%202026.xlsx) | Monthly $ estimates (FinOps validates) |
| **Slack** | [#proj-cogs-optimization](https://grid-sailpoint.enterprise.slack.com/archives/C0982LGTQ6Q) | Program coordination |

---

## Intake status

| Ticket | Team | Owner | Status | Q3 note |
| --- | --- | --- | --- | --- |
| [DPDE-4064](https://sailpoint.atlassian.net/browse/DPDE-4064) | Data Engineering | Dattu | In Progress | Master intake — ME-central stop, SF tuning, live-table right-size, Airflow/DAG opt, Flink opt |
| [DPINTAKE-120](https://sailpoint.atlassian.net/browse/DPINTAKE-120) | Data Presentation | Jon | **Closed** | **No dedicated Q3 capacity** — organic hardening only |

---

## Implementation line items & Q3 milestones

| Epic | Summary | Owner | Est. impact | Status | **Q3 target (by Sep 30)** |
| --- | --- | --- | --- | --- | --- |
| [DPDE-777](https://sailpoint.atlassian.net/browse/DPDE-777) | Upgrade all DAGs to **Airflow 3** | Rusty | Ops / infra efficiency | **Done** | ✅ Complete |
| [DPDE-4745](https://sailpoint.atlassian.net/browse/DPDE-4745) | Stop Snowflake warehouses in **me-central-1** | Dattu | Quick win | In Progress | **Aug 2026** — warehouses stopped; FinOps sign-off |
| [DPDE-4033](https://sailpoint.atlassian.net/browse/DPDE-4033) | Deprecate **ENTITY_DATA / ENTITY_LIVE** → EVENT_DATA | Prashant | **~$30K+/mo** | In Progress | **Sep 2026** — Phase 1: zero-consumer tables removed; migration plan locked |
| [DPDE-1947](https://sailpoint.atlassian.net/browse/DPDE-1947) | Snowflake **query & warehouse** cost/perf program | Siva | TBD (top-K fixes) | In Progress | **Sep 2026** — Phases 1–2 (diagnostics + quick-win controls) |
| [DPDE-4746](https://sailpoint.atlassian.net/browse/DPDE-4746) | **Right-size** Snowflake warehouses for live tables | Dattu | TBD | Backlog | **Sep 2026** — analysis + first production right-size (stretch; needs Aug kickoff) |
| [DPDE-4730](https://sailpoint.atlassian.net/browse/DPDE-4730) | Flink **RocksDB → ForStDB** (POC → rollout) | Geremiah | AWS/Flink infra | Backlog | **Sep 2026** — POC on entitlement-composite; full migration → **Q4** |
| [SAASPSCOPE-10563](https://sailpoint.atlassian.net/browse/SAASPSCOPE-10563) | **Logging costs reduction** 2026 | Caitlin Green | Observability / ingest | In Progress | **Sep 2026** — top noisy services identified; 1 pilot reduction shipped (coordinate with DE-owned pipelines) |

_Note: [SAASPSCOPE-10563](https://sailpoint.atlassian.net/browse/SAASPSCOPE-10563) is under INIT-2955 but lives in **SAASPSCOPE**, not the [DPDE/DPINTAKE filter](https://sailpoint.atlassian.net/issues?jql=parent%3DINIT-2955%20and%20project%20in%20%28%22DP%20-%20Data%20Engineering%22%2C%20%22Data%20Platform%20Intake%22%29)._

---

## Additional COGS levers (ideation — not yet epics)

Confirm with **Dattu** and **Jon** for gaps vs. the Jira filter and FinOps tracker.

| Lever | Signal / dashboard | Suggested Q3 milestone | Owner |
| --- | --- | --- | --- |
| **S3 Tables / Iceberg storage** | [Grafana — S3 table buckets](https://sailpoint.grafana.net/d/s3-tables-iceberg/s3-table-buckets-iceberg?from=now-30d&to=now) | Baseline top buckets + 1 optimization by Sep | TBD |
| **Confluent / flatter topics** | [Finout — Confluent cost](https://app.finout.io/app/dashboards/e52bb168-411f-424e-b339-67b058773595?accountId=1f3d980d-0bda-45df-9a68-275fbb57e220) | Topic inventory + 1 region/topic pilot | TBD |

---

## Q3 scorecard (maximize milestones hit)

| Confidence | Items |
| --- | --- |
| **Hit / done** | DPDE-777 (Airflow 3) |
| **High** | DPDE-4745 (me-central-1), DPDE-1947 Phases 1–2 |
| **Medium–high** | DPDE-4033 Phase 1 (ENTITY_DATA/LIVE) |
| **Medium (POC only)** | DPDE-4730 ForStDB POC |
| **Medium** | SAASPSCOPE-10563 logging reduction (cross-team; Caitlin Green) |
| **Stretch** | DPDE-4746 live-table right-size |
| **Out of Q3** | DPINTAKE-120 (Presentation); DPDE-4730 full fleet rollout |

**Largest $ lever in filter:** DPDE-4033 (~$30K+/mo Snowflake duplicate ingest/path).

---

## Exec summary (one slide)

Data Platform COGS work rolls up to **INIT-2955** with **seven tracked epics** (six DPDE + [SAASPSCOPE-10563](https://sailpoint.atlassian.net/browse/SAASPSCOPE-10563) logging reduction): Airflow 3 is **done**; **me-central-1 warehouse stop** and **Snowflake quick-win programs (DPDE-1947)** are highest-confidence Q3 completes; **ENTITY_DATA/LIVE deprecation** is the biggest dollar lever; **Flink ForStDB** targets a Q3 POC with Q4 rollout; **logging cost reduction** is in progress under Caitlin Green. **Data Presentation has no dedicated Q3 COGS capacity** (DPINTAKE-120 closed). Additional candidates—**S3 Tables/Iceberg**, **Confluent topic flattening**—need epic/tracker rows and owner confirmation with Dattu and Jon.

---

## Open actions

- [ ] Dattu / Jon: confirm additional items not in [Jira filter](https://sailpoint.atlassian.net/issues?jql=parent%3DINIT-2955%20and%20project%20in%20%28%22DP%20-%20Data%20Engineering%22%2C%20%22Data%20Platform%20Intake%22%29)
- [ ] Populate FinOps tracker column F (monthly $) for DPDE-4745, DPDE-4746, ideation levers
- [ ] Pull DPDE-4746 forward to Aug if Q3 right-size milestone is committed
- [ ] Align DE pipeline owners with [SAASPSCOPE-10563](https://sailpoint.atlassian.net/browse/SAASPSCOPE-10563) (Caitlin Green) on Q3 logging pilot scope
- [ ] Create epics for S3 Tables, Confluent if leadership prioritizes for Q3
