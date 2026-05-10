---
name: pipeline-incident-triage
description: Triage SailPoint entity-live-dip pipeline incidents using an evidence-first workflow across Airflow DAGs, Flink jobs, Kafka topics, Snowflake live/history tables, Soda checks, metrics, checkpoint config, and Reconciler replay. Use when investigating failed, delayed, missing, stale, or inconsistent live table data.
---

# Pipeline Incident Triage

Use this workflow for `sailpoint/entity-live-dip` incidents involving failed DAGs, missing records, stale live tables, failed quality checks, Flink job issues, Snowflake task failures, or replay/backfill questions.

## Principle

Do not jump to a fix. First identify the failed layer and collect evidence: Airflow orchestration, Flink streaming, Kafka input, Snowflake live/history state, Soda data quality, metrics, or Reconciler replay.

## Triage Flow

### 1. Define Scope And Impact

Capture:

- Environment, region, cluster, pod, org, and tenant if known.
- Affected table, topic, DAG, or Flink job.
- Symptom: missing data, stale data, duplicate data, failed DAG, failed Soda check, failed replay, or slow/timeout behavior.
- Start time and whether the issue followed a deploy, schema change, checkpoint bump, migration, or replay.

### 2. Check Recent Changes

Look for changes in:

- `transformers/streaming/schema_converter/schemas/**`
- `transformers/streaming/dbt/models/entity_live_tables/**`
- `pipelines/dags/entity_live_dip/entity_live_dags/**`
- `pipelines/dags/entity_live_dip/entity_live_dags/configs/**`
- `pipelines/dags/entity_live_dip/stateful_changelog_tables/**`
- `pipelines/dags/entity_live_dip/stateful_changelog_tables/configs/**`
- `transformers/fire/src/soda_quality_checks/**`
- `pipelines/dags/entity_live_dip/entity_live_dags/migrations/**`

If the issue followed a schema change, run or confirm:

```bash
cd transformers/streaming/schema_converter
make autogen_soda_checks
make autogen_all
```

### 3. Airflow Layer

Identify the DAG:

- Live table DAG: `sf_live_<table_name>_<dag_label>`
- Reconciler DAG: `sf_live_reconciler_<dag_label>`
- Metrics DAG: `sf_live_event_data_metrics_<dag_label>`

**Stateful changelog branch:** Tables driven from `pipelines/dags/entity_live_dip/stateful_changelog_tables/` use the same `sf_live_<table>_<dag_label>` naming but pull config from `stateful_changelog_tables/configs/**` (checkpoint version, parallelism overrides). If incident symptoms match changelog/SCD drift (duplicate PKs, wrong account targets, SCD vs live count mismatches), read that template YAML side-by-side with the dbt lag model and main model.

Check:

- Failed task name and full logs.
- Whether the DAG is paused.
- Whether upstream dependencies failed, especially migrations.
- Whether environment config has the expected checkpoint version **for this DAG family** (`entity_live_dags/configs` vs `stateful_changelog_tables/configs`).
- Whether `parallelism` or `<table>_parallelism_override` changed around the incident window (repartitioning can affect ordering assumptions before `LAG`/changelog UDFs).
- Whether the DAG was triggered in the expected cluster/region.

For bulk triggering or opening DAGs, use the repo's CLI docs in `cicd/bulk_deploy/trigger_dags.md`.

### 4. Flink Layer

Check whether the Flink job exists and is healthy.

The metrics DAG runs `run_flink_job_health`, which records `FLINK_JOB_DURATION_MS` rows into Snowflake `METRICS` with labels including:

- database
- schema
- job_name
- job_state
- jobmanager_url

Investigate:

- Job missing from Flink overview.
- Job state not running.
- Repeated restarts or unusually short duration.
- Job name mismatch between DAG template and active Flink jobs.
- Checkpoint or state restore errors after a checkpoint version change.

### 5. Kafka Source Layer

Compare the source YAML and expected topic:

- Source path: `transformers/streaming/dbt/models/entity_live_tables/<table>/source.yml`
- Topic pattern: `^<table>(_backfill)?$`
- Key config: `key.format: raw`, `key.fields: kafka_key`, `value.fields-include: EXCEPT_KEY`

Check:

- Topic exists and is receiving messages.
- Messages include the expected key.
- Headers include `pod`, `org`, `tenantId`, and `eventId`.
- Backfill topic naming matches the `_backfill` pattern if replaying.

### 6. Snowflake Layer

For a live table, inspect:

- `<table>_history`
- `<table>_live`
- `<table>` view
- `EVENT_DATA.REPLAY_REQUEST` for pending replay requests
- `METRICS` for generated live table, SCD, and Flink health metrics

Look for:

- Rows present in history but missing from live.
- Null or malformed `TENANT_ID`, `ORG`, `POD`, `EVENT_ID`, `KAFKA_KEY`, or `PK`.
- Duplicate keys.
- Stale `modified`, `created`, or sync timestamps.
- Snowflake task failures, stale streams, or task timeouts.

If a stream is stale or task timeout occurred, inspect migrations under `pipelines/dags/entity_live_dip/entity_live_dags/migrations`.

### 7. Soda Data Quality Layer

Review the relevant Soda check file under:

`transformers/fire/src/soda_quality_checks`

Include **`rcp_team/`** (and paths referenced by `quality_checks/rcp_team_template.yml`) for SCD and cross-table checks—not only `auto_generated_checks/`.

Common incident signals:

- Missing required fields.
- Duplicate `PK`, `ID`, or `(ID, TENANT_ID)`.
- Invalid `PK` format or delimiter.
- Missing headers.
- Stale sync or modified dates.
- Wrong Snowflake column types.
- Referential integrity failures.
- **SCD:** failures on `VALID_FROM`/`VALID_TO`/`IS_CURRENT` schema or type checks; failed rows comparing **source live counts vs SCD non-deleted / current** counts (indicates changelog or assignment grain mismatch).

Use failed row samples to identify affected tenants, pods, orgs, keys, and source records.

### 7b. Stateful Changelog / UDF Layer (When Applicable)

For blacklist/stateful models (e.g. `identity_role_assignment_account_target`):

- **Lag view:** `*_lag.sql` builds prior state with window functions; if Kafka ordering or `procTime` semantics break, diffs explode or go silent.
- **Changelog UDFs:** `array_diff_changelog` / `map_diff_changelog` emit one row per detected change—misconfigured key paths or sentinel arrays cause missing or duplicate logical assignments.
- **SCD sink:** Downstream `*_SCD` tables may look wrong while `*_live` still looks plausible—compare team Soda failed-row queries and Snowflake SCD columns.

Correlate with Flink logs for the job name from the stateful template and with checkpoint restore errors after a **checkpoint version** bump.

### 8. Reconciler And Replay

Use Reconciler when records are missing or corrupt and replay is the right recovery path.

Relevant DAG:

`sf_live_reconciler_<dag_label>`

The Reconciler flow:

1. Runs Snowflake pre-migrations.
2. Creates procedures.
3. Generates replay IDs.
4. Runs `run_event_reconciler_api` to request replays.
5. Reads pending requests from `EVENT_DATA.REPLAY_REQUEST` where `REPLAY_DATE IS NULL`.

Check:

- Pending rows in `EVENT_DATA.REPLAY_REQUEST`.
- `TOPIC_NAME`, `KAFKA_KEYS`, `TENANT_ID`, `POD`, `ORG`, and `REPLAY_EXCEPTIONS`.
- Whether replay requests are grouped by topic and batch size.
- Whether API responses are `202`; non-202 responses are failures.
- Whether requests remain unreplayed because `REPLAY_DATE` is still null.

### 9. Checkpoint Bumps

A checkpoint version bump resets Kafka consumers and starts Flink from a clean state. Use it carefully.

Repo docs: `cicd/bulk_deploy/bump_checkpoint.md`

Before recommending a bump, confirm:

- The job cannot recover from current checkpoint state.
- Replaying from earliest offset is acceptable for the table.
- The affected table's checkpoint version exists in env config (**correct tree**: `pipelines/dags/entity_live_dip/stateful_changelog_tables/configs/**` vs `entity_live_dags/configs/**`).
- Parallelism overrides did not change consumer group behavior unexpectedly alongside the bump.
- The expected blast radius is understood.

### 10. Report Findings

Structure the incident summary as:

```markdown
## Scope
Affected env/region/table/DAG/job and user impact.

## Evidence
Airflow, Flink, Kafka, Snowflake, Soda, metrics, and recent-change findings.

## Hypotheses
One falsifiable hypothesis at a time, with supporting and contradicting evidence.

## Root Cause
Confirmed cause, not just symptom.

## Recovery
Immediate action: rerun DAG, replay, fix config, migration, checkpoint bump, or code/schema fix.

## Prevention
Monitoring, checks, validation, docs, or automation improvements.
```

## Red Flags

Stop and gather more evidence if:

- The proposed fix is a checkpoint bump without proof the checkpoint is the problem.
- Data is missing from live but history has not been checked.
- A Soda failure is treated as the root cause instead of a symptom.
- A replay is requested without identifying affected keys and tenants.
- Multiple layers changed recently and no timeline has been established.
