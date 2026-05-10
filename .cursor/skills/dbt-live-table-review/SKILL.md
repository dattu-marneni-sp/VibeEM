---
name: dbt-live-table-review
description: Reviews dbt live table changes in SailPoint entity-live-dip for generated-file safety, Snowflake connector config, Kafka source consistency, standard platform columns, primary key/grain, type mapping, delete handling, tags, and validation. Use when reviewing generated or custom dbt models under entity_live_tables.
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
- `checkpointing_enabled = true`
- `checkpoint_version = env_var("CHECKPOINT_VERSION")`
- `checkpoint_name` defaults to `<table_name>_live`
- `primary_key = 'KAFKA_KEY'`
- `partition_by = 'TENANT_ID'`
- `tags` include `ENTITY_LIVE` and the table-specific tag

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

## Findings Format

When reviewing, lead with issues ordered by severity. Include:

- Correctness or data loss risks
- Schema/source/model mismatches
- Primary key or grain concerns
- Type mapping problems
- Missing validation or stale generated outputs
