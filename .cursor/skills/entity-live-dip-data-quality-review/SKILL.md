---
name: entity-live-dip-data-quality-review
description: Entity-live-dip — reviews SailPoint data platform changes for data quality risks in entity-live-dip and similar pipelines, including schema drift, null handling, uniqueness, key format, missing headers, freshness, referential integrity, type validation, Soda checks, failed-row samples, and downstream contract impact.
---

# Data Quality Review

Use this workflow when reviewing data platform changes, especially `sailpoint/entity-live-dip` schemas, dbt live table models, Soda checks, Snowflake live/history tables, and pipeline changes that affect data correctness.

## Principle

Review data quality as a contract: producers send records, streaming jobs preserve keys and headers, Snowflake exposes stable live/history tables, and checks catch drift before consumers are affected.

## Review Checklist

### 1. Schema Contract

Check the JSON schema and generated outputs together:

- Required fields match actual producer guarantees.
- Optional fields are not incorrectly marked required.
- Field names and casing match Kafka payloads.
- Object fields are intentionally stored as `VARIANT`.
- Array fields are intentionally stored as `ARRAY`.
- Date/time fields have clear format expectations.
- Enum-like strings have documented accepted values.

### 2. Required Platform Fields

For live tables, verify these fields are present and checked:

- `TENANT_ID`
- `ORG`
- `POD`
- `EVENT_ID`
- `KAFKA_KEY`
- `PK`
- `HARD_DELETED`
- `KAFKA_METADATA`

Missing `TENANT_ID`, `ORG`, or `POD` usually points to producer/header issues rather than only table logic.

### 3. Completeness Checks

Soda checks should include `missing_count = 0` for:

- Every field in the schema `required` list.
- Platform fields that should always exist in live tables.

Review whether nullable business fields are intentionally nullable. Do not add not-null checks just because a field is important if the producer can legitimately omit it.

**Auto-generated vs team-owned:** Most schema-backed tables ship checks from `make autogen_soda_checks` into `transformers/fire/src/soda_quality_checks/auto_generated_checks/`. **Blacklist/stateful/SCD-heavy tables** often add or rely on YAML under `transformers/fire/src/soda_quality_checks/rcp_team/` (and similar team dirs). When reviewing a PR, confirm those files are wired into the quality DAG (e.g. `pipelines/dags/entity_live_dip/quality_checks/rcp_team_template.yml` lists `check_files` under `checks_dir: .../rcp_team`). Missing wiring means checks never run in CI/schedules even if YAML exists.

### 4. Uniqueness And Grain

Confirm the intended grain:

- `PK` should usually be unique.
- `KAFKA_KEY` should match live-table upsert behavior.
- `(ID, TENANT_ID)` should be unique only when the schema has an `id` field and the entity grain supports it.
- Aggregate, flattened, dedup, and SCD-style tables may need different uniqueness rules.

Flag any change that can duplicate rows, collapse distinct records, or change live table grain.

### 5. Key Format And Tenant Consistency

Check:

- `PK` delimiter and format.
- Tenant portion of `PK` matches `TENANT_ID` when applicable.
- `KAFKA_KEY`, `PK`, and entity identifiers use the same expected business key.
- Empty, null, or malformed keys are rejected or surfaced by checks.

### 6. Validity Checks

Use Soda built-ins where possible:

- `invalid_count(<boolean>) = 0` with valid values `[true, false]`.
- `invalid_count(<date>) = 0` with `valid format: date iso 8601`.
- `invalid_count(<id>) = 0` with expected min/max length when IDs have fixed length.
- Accepted values for enum-like fields.
- `schema` checks for required columns and expected Snowflake types.

### 7. Referential Integrity

Add or review checks like:

```yaml
- values in (SOURCE_ID) must exist in SOURCE_V1_LIVE (ID)
```

Use referential checks when an ID field is expected to point to another live table. Avoid checks that create noisy failures for eventually consistent or intentionally partial references unless the lag is understood.

### 8. Freshness And Temporal Consistency

Check for:

- Stale `SYNC_DATE`, `MODIFIED`, or producer timestamps.
- `modified_before_created`.
- `created_in_future` or `modified_in_future`.
- End dates before start dates.
- Live rows lagging history rows.

Freshness failures should include affected tenants and keys so the incident path is clear.

### 9. Header And Producer Format Checks

For entity-live-dip, check for:

- Missing `ORG`, `POD`, or `TENANT_ID` headers grouped by tenant.
- Deprecated producer formats such as `iris.format = 1` when the table expects the newer format.
- Payload fields that moved between raw record content and `contentJson`.

### 10. Failed Row Samples

Every custom metric should have a paired `failed rows` query.

Failed row samples should include useful investigation columns:

- `PK`
- `TENANT_ID`
- relevant entity IDs
- timestamp fields
- offending value

Set `samples limit: 5` on built-in checks.

### 11. Row Count And Empty Table Checks

Use row count checks carefully:

- New tables may be empty before rollout.
- Production live tables usually should not unexpectedly drop to zero.
- Row count drops should be compared to deployment, replay, checkpoint, and producer timelines.

### 11b. SCD And Source-vs-SCD Consistency

When the streaming sink uses `SNOWFLAKE_STREAM_SCD_STRATEGY` (see dbt `connector_properties`), Snowflake exposes SCD tables/views with validity columns. Team checks often assert:

- **Schema:** presence and types of `VALID_FROM`, `VALID_TO`, and often `IS_CURRENT` (example pattern in `transformers/fire/src/soda_quality_checks/rcp_team/scd_checks_identity_role_assignment_account_target.yml`).
- **Temporal consistency:** no overlapping open intervals for the same business key unless the model explicitly allows it; `VALID_FROM`/`VALID_TO` ordering sanity.
- **Source live vs SCD non-deleted counts:** failed-row queries that compare a **source or live assignment grain** (e.g. counts from `IDENTITY_ROLE_ASSIGNMENT_V1_LIVE` in a time window) to **SCD rows** filtered with `IS_CURRENT = TRUE` (and optional validity overlap with the window). Mismatches flag changelog drift, missed deletes, or PK grain differences—triage with Flink changelog UDF output and Reconciler, not only Soda.

### 12. Downstream Impact

Before approving, identify consumers:

- Dashboards or metrics.
- Reconciler.
- APIs or hydration jobs.
- Other dbt models or Snowflake views.
- Soda checks and alerts.

Flag changes that rename columns, change types, alter grain, or remove fields without a migration plan.

## Review Output

Lead with findings ordered by severity:

- Data loss or incorrect live-table state.
- Broken schema contract or producer mismatch.
- Missing tests/checks for high-risk fields.
- Noisy or brittle checks likely to page unnecessarily.
- Downstream compatibility risks.

For each finding, include:

- What can go wrong.
- Which table/schema/check is affected.
- How to fix or validate it.

## Validation Commands

For schema-backed changes:

```bash
cd transformers/streaming/schema_converter
make autogen_soda_checks
make autogen_all
```

For local Soda check work, follow `transformers/fire/src/soda_quality_checks/README.md` and test with a supported Python version for Soda Core.
