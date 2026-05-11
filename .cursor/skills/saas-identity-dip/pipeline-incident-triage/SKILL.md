---
name: pipeline-incident-triage
description: Saas-identity-dip — triage SailPoint saas-identity-dip / Identity Materializer streaming incidents using an evidence-first workflow across Airflow (`cbc_materializers_identity_*`), Flink jobs and SQL Gateway, Kafka source/intermediate/final topics (including `segmented_identity_all`, `segmented_identity`, `search_lite_identity_intermediate`, `search_lite_identity_v1`), checkpoint versions and `prefer_checkpoint`, `job_suffix` variants such as `group_22`, per-env parallelism and `enabled` flags, Grafana IDN DIP STREAMING signals, materializer output gaps, and dbt-Flink sink models. Use when investigating delayed, missing, duplicate, or wrong identity materialization in Kafka (not Snowflake live tables).
---

# Pipeline incident triage (saas-identity-dip)

Use this for `sailpoint-core/saas-identity-dip` incidents: Identity Materializer Flink jobs, Kafka topic throughput or contract issues, checkpoint/parallelism misconfiguration, UDF or deploy regressions, or downstream symptoms in **segmented identity** or **Search Lite** identity streams.

## Principle

Evidence first: classify the symptom and the layer (orchestration vs runtime vs contract vs deploy) before changing code or bumping checkpoints. See also `docs/saas-identity-dip-deep-dive.md` in this workspace for architecture context.

## How this differs from entity-live-dip

- **No schema_converter / `make autogen_all` / autogen CI gate** for the streaming Identity path. Models are hand-written under `transformers/streaming/dbt/models/entity_models/**`.
- **No in-repo Soda autogen, `_manifest.json` quality gate, or Reconciler replay** for the Kafka streaming path like entity-live-dip’s live-table stack.
- **Sinks are Kafka-to-Kafka**, not Snowflake `_live` / `_history` tables. Do not assume Snowflake live-table lag, SCD sinks, or Reconciler DAGs apply to these jobs unless you have explicitly traced a separate lakehouse path (`pipelines/dags/saas_identity_dip/lakehouse/**`).

## Evidence-first workflow

### 1. Classify symptom and scope

Capture: environment, region (`dag_label`), tenant/org if known, time window, and whether a **deploy, checkpoint bump, parallelism change, feature-flag change, or UDF jar** preceded the issue.

Map the symptom:

| Symptom | Likely first surfaces |
| --- | --- |
| No / stale events on product topics | Final sinks, upstream intermediates, job `enabled`, consumer lag, Flink backpressure |
| Duplicates or flapping keys | Dedup jobs, `ROW_NUMBER` partitions, checkpoint restore compatibility |
| Wrong segments or attributes | Join chain in dbt, UDF behavior (`create_udfs.sql`), LaunchDarkly flags |
| DAG failures only | Airflow task logs, template/config Jinja, Jenkins deploy ticket |
| One tenant class only | `group_22` job variants vs global jobs |

### 2. Recent changes

Scan git history and PRs for:

- `pipelines/dags/saas_identity_dip/identity/template.yml`
- `pipelines/dags/saas_identity_dip/identity/configs/**/*.yml`
- `transformers/streaming/dbt/models/entity_models/**` (sinks and staging `*_source*.sql`)
- `transformers/streaming/dbt/macros/create_udfs.sql`
- `transformers/flink_udf/**`
- `cicd/Jenkinsfile` / `cicd/PRB.Jenkinsfile`

### 3. Airflow

- **Template (source of job list):** `pipelines/dags/saas_identity_dip/identity/template.yml` — `type: streaming_v1`, `global.dip_name: saas-identity-dip`, `jobs:` entries with `job_name`, `checkpoint_name`, `checkpoint_version`, `prefer_checkpoint`, `parallelism`, `enabled`, optional `job_suffix: 'group_22'`.
- **DAG id pattern:** `cbc_materializers_identity_{{ dag_label }}` (e.g. `cbc_materializers_identity_prd-us-east-1`).
- **Per-env knobs:** `pipelines/dags/saas_identity_dip/identity/configs/{dev,internal,prod}/<region>.yml` — each job has `<snake_case_job>_checkpoint_version`, `_parallelism`, `_enabled`, and parallel `*_group_22_*` keys where the template defines a `group_22` job.
- **Handler:** `pipelines/dags/saas_identity_dip/saas_identity_dip_handler.py` delegates to `process_template_config` from `saas_airflow_utils` (template + config merge).

Checklist — **Airflow**

- [ ] Correct DAG for region; not paused; failed task and stack trace captured.
- [ ] For the affected `job_name`, config supplies matching `*_checkpoint_version`, `*_parallelism`, `*_enabled` (and `*_group_22_*` if the incident is MS / suffix-specific).
- [ ] Template Jinja still renders (bad substitution can break the whole job family).

### 4. Flink and Grafana

- **Config:** `sql_gateway_endpoint`, `flink_jobmanager_url` from the same per-region YAML as Airflow (e.g. `prd-use1-identitydip-sqlgateway...`, `http://...-rest...:8081`).
- **Job Manager / UI:** job state, restarts, checkpoint success/failure, checkpoint size, RocksDB pressure.
- **Grafana:** Confluence references **IDN DIP STREAMING** — filter by cluster (e.g. `stg-use1-identitydip` / prod equivalent), job name, operator; use for backpressure, latency, and failure correlation.

Checklist — **Flink**

- [ ] Job exists and is RUNNING; checkpoint bar moving; no continuous restart loop.
- [ ] Parallelism change aligns with config and does not violate state layout assumptions.
- [ ] SQL Gateway reachable from the cluster where Airflow runs jobs.

### 5. Kafka topics

**Example topic chain (segmented identity path):**

- `segmented_identity_all` — written by `SEGMENTED_IDENTITY_SINK.sql` (`transformers/streaming/dbt/models/entity_models/identity/segmented-identity/`).
- `segmented_identity` — written by `SEGMENTED_IDENTITY_DEDUP_SINK.sql` (`.../segmented-identity-dedup/`); product-facing stream after dedup.

**Search Lite path:**

- `search_lite_identity_intermediate` — `IDENTITY_LITE_SINK.sql` (`.../identity-lite/`).
- `search_lite_identity_v1` — `IDENTITY_LITE_FILTERED.sql` (`.../identity-lite-filtered/`).

**Upstream entity sources** (non-exhaustive; confirm in `sources.yml` per job): e.g. `account_v1`, `account_identity_v1`, `cis_identity_internal_v1`, `identity_v1`, `source_v1`, role/access objects as modeled.

Checklist — **Kafka**

- [ ] Lag and throughput on the **failing stage** topic (source vs intermediate vs final).
- [ ] Key format matches contract (e.g. `tenantId#identityId` where documented).
- [ ] Tombstones / `hard_delete` behavior if deletes are involved.

### 6. dbt model logic and tests

- **Project:** `transformers/streaming/dbt/dbt_project.yml` (`streaming` project; `on-run-start` runs `create_udfs()`).
- **Sinks:** each job folder under `transformers/streaming/dbt/models/entity_models/{common,identity}/<job>/` with `*_SINK.sql` defining `connector_properties.topic`.
- **Patterns:** keyed dedup via `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY procTime DESC NULLS LAST)`; `primary_key = 'pk'` for upsert-kafka; headers in `sources.yml` when used.

Checklist — **dbt model logic**

- [ ] Sink `topic` matches the symptom topic (`segmented_identity_all` → `segmented_identity` → consumers; `search_lite_identity_intermediate` → `search_lite_identity_v1`).
- [ ] Upstream `sources.yml` columns align with live schema (no autogen safety net).
- [ ] Run or review any project tests applicable to the touched models (streaming tests are not the same as entity-live Soda autogen).

### 7. Checkpoints and state

- **Airflow:** each job passes `checkpoint_version` / `prefer_checkpoint` into deployment from per-env YAML (see `template.yml` for `prefer_checkpoint: True` on many jobs).
- **dbt:** sinks set `checkpointing_enabled`, `checkpoint_version`, `checkpoint_name` (convention: `checkpoint_name` matches the dbt sink file name in lower snake style — see `transformers/streaming/README.md`).

Checklist — **Checkpoints**

- [ ] Logic or schema change is paired with a **bump** of the right `<job>_checkpoint_version` in **all** affected region files (partial bumps cause restore failures or split-brain behavior across regions).
- [ ] `group_22` variants bumped independently where they exist.
- [ ] If Flink fails restoring from savepoint, treat as checkpoint compatibility issue before rewriting business logic.

### 8. Data quality and tests

- There is **no** entity-live-style autogen Soda path for these streams. Quality may be operational dashboards, downstream service SLOs, or checks outside this repo — do not assume a Reconciler or Soda DAG will explain the gap.
- Still validate: sample keys on Kafka, consumer error logs (Search Lite / `sp_materializer`), and Flink watermarks / late data.

Checklist — **Data quality / tests**

- [ ] Consumer-side errors or deserialization failures.
- [ ] Feature flags (examples from ops docs): `SAAS_IDENTITY_DIP_MATERIALIZER_ENABLED`, `SAAS_IDENTITY_DIP_SKIP_CONTENT_DEDUP_ENABLED`, split sinks flags — confirm LaunchDarkly segment and env.

### 9. Deploy, rollback, CI

- **Jenkins:** `cicd/Jenkinsfile` — build transformers (`atlasDataBuildTransformers`), deploy workflow with `streaming_tag`, `lakehouse_tag`, `fire_tag`, `flink_udf_tag`, `udf_build` (S3 artifact path); deploy ticket project `SAASFD`; Slack `proj-eng-iai-cicd`.
- **PR builds:** `cicd/PRB.Jenkinsfile`.
- **Rollback:** prior `RELEASE_TAG` / artifact tags and Airflow config revert; coordinate **UDF jar** version with dbt models that call new functions (`create_udfs.sql` ↔ `transformers/flink_udf/build.gradle` / jar name `saas-idn-dip-udf.jar`).

Checklist — **Deploy / rollback**

- [ ] Correlate incident time with Jenkins build and deploy ticket.
- [ ] If UDFs changed: jar deployed and registered before or with model deploy.
- [ ] Rollback plan: previous checkpoint version + matching artifact tags (avoid mixing old jar with new SQL).

### 10. Escalation

- **Owners:** `CODEOWNERS` → `@sailpoint-core/fast-data`.
- Escalate with: DAG + region, Flink job name(s), topic names, sample keys, checkpoint id/version, last known good deploy tag, and Grafana snapshot window.

## Local reproduction pointers

From `transformers/streaming/README.md` in the saas-identity-dip repo:

1. JFrog / `dbt-flink-adapter` setup per README.
2. `make build-flink-udf` then copy `../flink_udf/build/libs/saas-idn-dip-udf.jar` to `./envs/flink/opt/`.
3. `make start-services` / `make restart-services` (local Flink + Kafka).
4. `make deploy-models MODEL_ARG=tags` to submit models via SQL Gateway.

Use this to reproduce sink SQL and UDF behavior against controlled Kafka input before proposing production checkpoint changes.
