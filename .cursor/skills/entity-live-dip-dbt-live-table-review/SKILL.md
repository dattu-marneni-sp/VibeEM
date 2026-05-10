---
name: entity-live-dip-dbt-live-table-review
description: Entity-live-dip — reviews dbt live table changes in SailPoint entity-live-dip for generated-file safety, blacklist/stateful changelog customs, Snowflake connector config (including SCD sink strategy), Kafka source consistency, standard platform columns, primary key/grain, type mapping, delete handling, tags, lag views and changelog UDFs, checkpoint/parallelism alignment, team-owned Soda, and validation. Use when reviewing generated or custom dbt models under entity_live_tables.
---

# dbt Live Table Review

Use this workflow when reviewing dbt live table changes in `sailpoint/entity-live-dip`, especially models under `transformers/streaming/dbt/models/entity_live_tables`.

## Review Principle

For generated dbt live tables, review the schema-to-output contract, not just the SQL file. If a generated model is wrong, prefer fixing the JSON schema or schema converter and rerunning generation.

## Checklist

### 1. Generated File Safety

- Confirm whether the model is generated or custom.
- If generated, do not hand-edit it unless the schema is intentionally blacklisted in `transformers/streaming/schema_converter/Makefile`.
- Prefer fixing the JSON schema or generator, then rerun `make autogen_all`.

### 2. dbt Config

Verify expected model config:

- `materialized = 'table'`
- `connector_properties.connector = 'snowflake'`
- `connector_properties.table` matches the schema/table name
- Optional: `connector_properties` may include `'sink-strategy': 'SNOWFLAKE_STREAM_SCD_STRATEGY'` for SCD sinks—then review SCD semantics and team Soda checks, not only live columns.
- `checkpointing_enabled = true`
- `checkpoint_version = env_var("CHECKPOINT_VERSION")`
- `checkpoint_name` usually defaults to `<table_name>_live`; **custom/blacklisted models** may use `env_var("CHECKPOINT_NAME", ...)`—must match Airflow `checkpoint_name`.
- `primary_key` is usually `'KAFKA_KEY'`; **changelog / blacklisted** models may use `'PK'` or another enforced grain—validate uniqueness and Flink upsert behavior.
- `partition_by = 'TENANT_ID'`
- `tags` include `ENTITY_LIVE` and the table-specific tag; changelog tables may use tags like `CHANGELOG` instead—confirm observability and DAG conventions.

### 3. Source Consistency

Compare the model with its source YAML:

- The model uses `{{ source('<table>', '<table>_source') }}`.
- The source topic pattern matches the Kafka topic: `^<table>(_backfill)?$`.
- The source includes `kafka_key`, `headers`, `hard_deleted`, and Kafka metadata fields.
- The source uses key config: `key.format: raw`, `key.fields: kafka_key`, `value.fields-include: EXCEPT_KEY`.

### 4. Required Platform Columns

Confirm the model emits these standard columns:

- `POD`
- `ORG`
- `TENANT_ID`
- `EVENT_ID`
- `KAFKA_METADATA`
- `KAFKA_KEY`
- `HARD_DELETED`

`HARD_DELETED` should default safely:

```sql
COALESCE(hard_deleted, false) AS HARD_DELETED
```

### 5. Grain And Primary Key

- Confirm `KAFKA_KEY` is the correct live-table primary key.
- Confirm `PK` from the payload exists when expected.
- For entity records, verify the schema's logical grain matches the Kafka key.
- Watch for models where multiple records could share the same `KAFKA_KEY`, `PK`, or entity ID unexpectedly.

### 6. Type Mapping

Check complex fields carefully:

- JSON objects should become Snowflake `VARIANT`.
- JSON arrays should become Snowflake `ARRAY`.
- Reserved words like `date`, `value`, `partition`, and `offset` should be backticked.
- CamelCase payload fields should become uppercase snake-case aliases.

Expected patterns:

```sql
assignmentContext AS `ASSIGNMENT_CONTEXT::VARIANT`
assignedDimensions AS `ASSIGNED_DIMENSIONS::ARRAY`
`date` AS `DATE`
`value` AS `VALUE`
```

### 7. Header And Metadata Semantics

- `TENANT_ID`, `ORG`, `POD`, and `EVENT_ID` come from Kafka headers, not payload.
- `KAFKA_METADATA` should include event timestamp, partition, offset, and topic.
- If a downstream process relies on event ordering or replay diagnostics, do not drop metadata.

### 8. Delete Handling

- Confirm `hard_deleted` exists in source YAML.
- Confirm the model exposes `HARD_DELETED`.
- Review whether downstream consumers expect soft delete behavior from the live table.

### 9. Tags And Special Rollouts

- Confirm table tags match naming conventions.
- Check for special tags such as rollout or migration markers.
- If adding a new special tag, update the generator intentionally instead of editing only one generated model.

### 10. Validation Before PR

Run from `transformers/streaming/schema_converter`:

```bash
make autogen_all
```

For changed schemas, also run:

```bash
make autogen_soda_checks
make autogen_all
```

Then confirm `git status` only shows intentional schema and generated changes.

### 11. Blacklisted / Custom Live Tables And Stateful Changelog (High Priority)

Some entities are listed in `BLACKLIST` in `transformers/streaming/schema_converter/Makefile` (comma-separated schema filenames). Generator output is intentionally skipped for those schemas; live pipelines are **team-maintained**. Treat reviews of these models as **custom contract reviews**, not “fix the JSON schema and regenerate.”

**Concrete reference:** `identity_role_assignment_account_target`

| Area | What to verify |
|------|----------------|
| **Blacklist** | Schema `identity_role_assignment_account_target.json` is on `BLACKLIST`; dbt/source/DAG/Soda are not expected to be produced by autogen for that name. |
| **DAG family** | Stateful changelog tables use templates under `pipelines/dags/entity_live_dip/stateful_changelog_tables/` (e.g. `identity_role_assignment_account_target_template.yml`), not only `entity_live_dip/entity_live_dags/`. Match `dag_id`, `job_name`, `checkpoint_name`, and env vars to the dbt model. |
| **Checkpoint version** | Per-environment values live under `pipelines/dags/entity_live_dip/stateful_changelog_tables/configs/**` as `<table>_checkpoint_version`. Align bumps with Flink consumer groups / recovery expectations. |
| **Parallelism** | Stateful templates may define `parallelism` and `<table>_parallelism_override` (see template task `spec`). Overrides affect throughput and ordering assumptions—review blast radius when they change. |
| **Lag / state model** | Changelog tables often use a **lag view** (materialized `view`) over the Kafka source, e.g. `transformers/streaming/dbt/models/entity_live_tables/identity_role_assignment_account_target/identity_role_assignment_account_target_lag.sql`, with window functions (`LAG`) to carry prior array/blob state for diffing. The main model should `ref()` the lag model, not the raw source. |
| **Changelog UDFs** | Per-event diffs use Flink SQL UDFs registered in dbt, e.g. `array_diff_changelog` and `map_diff_changelog` (see `transformers/streaming/dbt/macros/create_udfs.sql`). Review **key columns passed into the UDF** (e.g. which JSON paths define “same row”), **NULL/empty array sentinels**, and **LATERAL TABLE** grain—wrong keys duplicate or drop changelog rows. |
| **`SNOWFLAKE_STREAM_SCD_STRATEGY`** | When `connector_properties` sets `'sink-strategy': 'SNOWFLAKE_STREAM_SCD_STRATEGY'`, Snowflake maintains **SCD** semantics downstream of the streaming sink (history/current rows, validity intervals). Review how live-row deletes (`HARD_DELETED`), updates, and natural keys map to SCD `VALID_FROM` / `VALID_TO` / `IS_CURRENT` behavior expected by consumers—not only the live projection in dbt. |
| **Custom primary keys** | Blacklisted/changelog models may set `primary_key = 'PK'` (or another column) and custom `checkpoint_name` via `env_var` defaults instead of the generated `KAFKA_KEY` + `<table>_live` pattern. Confirm PK stability, uniqueness per tenant, and alignment with the changelog UDF output. |
| **Team-owned Soda** | Autogen checks under `transformers/fire/src/soda_quality_checks/auto_generated_checks/` may not cover SCD or cross-table logic. Look for RCP/team YAML under `transformers/fire/src/soda_quality_checks/rcp_team/` (e.g. `scd_checks_identity_role_assignment_account_target.yml`) and ensure the quality DAG lists them—`pipelines/dags/entity_live_dip/quality_checks/rcp_team_template.yml` references `checks_dir: .../rcp_team` and named check files. |

## Findings Format

When reviewing, lead with issues ordered by severity. Include:

- Correctness or data loss risks (including SCD and changelog UDF behavior when applicable)
- Schema/source/model mismatches
- Primary key or grain concerns
- Type mapping problems
- Missing validation or stale generated outputs (and missing team Soda when autogen does not apply)
