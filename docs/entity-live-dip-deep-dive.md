# entity-live-dip Deep Analysis

This single-page analysis summarizes `sailpoint/entity-live-dip` using tab-style sections. GitHub Markdown does not support native tabs, so the sections below use anchor links plus expandable panels to behave like readable tabs.

Companion visual canvas: `canvases/entity-live-dip-deep-dive.canvas.tsx`

## Tabs

[Overview](#tab-overview) |
[Generated Entity Trace](#tab-generated-entity-trace) |
[Schema Converter](#tab-schema-converter) |
[Custom And Stateful Tables](#tab-custom-and-stateful-tables) |
[Runtime Operations](#tab-runtime-operations) |
[Quality And Metrics](#tab-quality-and-metrics) |
[CI And Deploy](#tab-ci-and-deploy) |
[Review Checklist](#tab-review-checklist)

---

<details open>
<summary id="tab-overview"><strong>Tab: Overview</strong></summary>

## Overview

`entity-live-dip` is a schema-driven platform for building low-latency Snowflake live tables from compacted Kafka entity topics.

The core path is:

```text
JSON schema
  -> generated dbt source/model
  -> Airflow/Flink streaming pipeline
  -> Snowflake history/live/view tables
  -> Soda, metrics, reconciler, migration, and CI controls
```

The key mental model: the JSON schema is the primary contract. Generated dbt, Airflow templates, checkpoint config, and Soda checks are derived or validated around that contract.

Each normal live-table entity has these major outputs:

| Output | Purpose |
| --- | --- |
| `<table_name>_history` | Raw Snowpipe Streaming history table. |
| `<table_name>_live` | Current-state table after merge/upsert behavior. |
| `<table_name>` | Query-facing view combining live state and unmerged history. |

Primary repo areas:

| Area | Path | Responsibility |
| --- | --- | --- |
| Schema converter | `transformers/streaming/schema_converter` | Generates dbt source YAML, dbt model SQL, Airflow pipeline YAML, checkpoint entries, and Soda checks. |
| Streaming dbt | `transformers/streaming/dbt` | dbt-Flink models and macros that move Kafka data into Snowflake. |
| Airflow DAGs | `pipelines/dags/entity_live_dip` | Dynamic YAML templates for generated live tables, migrations, metrics, quality checks, reconciler, and stateful changelog tables. |
| Fire runtime | `transformers/fire` | Python jobs for Reconciler, Soda execution, Flink health, Kafka replay, and support jobs. |
| CI/CD | `.github/workflows`, `.pre-commit-config.yaml`, `cicd` | Autogen validation, local hooks, Jenkins build/deploy, bulk deploy helpers, and Atlan publishing. |

</details>

---

<details open>
<summary id="tab-generated-entity-trace"><strong>Tab: Generated Entity Trace</strong></summary>

## Generated Entity Trace: `machine_account_v1`

`machine_account_v1` is a useful reference because it follows the normal schema-to-live-table path.

| Layer | File | What It Proves |
| --- | --- | --- |
| Schema | `transformers/streaming/schema_converter/schemas/machine_account_v1.json` | Declares required fields, UUID/date-time formats, object fields, and `additionalProperties: false`. |
| Kafka source | `transformers/streaming/dbt/models/entity_live_tables/machine_account_v1/source.yml` | Reads topic pattern `^machine_account_v1(_backfill)?$`; includes Kafka key, headers, timestamp, partition, offset, and topic metadata. |
| dbt model | `transformers/streaming/dbt/models/entity_live_tables/machine_account_v1/machine_account_v1.sql` | Adds standard platform columns, `KAFKA_KEY` primary key, `TENANT_ID` partitioning, and casts `attributes` to `VARIANT`. |
| Airflow/Flink job | `pipelines/dags/entity_live_dip/entity_live_dags/machine_account_template.yml` | Creates `sf_live_machine_account_v1_<env>`, depends on migrations, and wires checkpoint, Flink, Kafka, and Snowflake arguments. |
| Checkpoint config | `pipelines/dags/entity_live_dip/entity_live_dags/configs/**` | Adds `machine_account_v1_checkpoint_version` per environment and `dag_label`; some environments show `v1`, while prod/staging entries show `v2`. |
| Soda checks | `transformers/fire/src/soda_quality_checks/auto_generated_checks/machine_account_v1.yml` | Checks required fields, platform headers, deprecated iris format, uniqueness, booleans, timestamps, and ID validity. |

Important observations:

- The generated dbt model extracts `POD`, `ORG`, `TENANT_ID`, and `EVENT_ID` from Kafka headers.
- `KAFKA_METADATA` preserves Kafka timestamp, partition, offset, and topic.
- `KAFKA_KEY` is the dbt model primary key.
- Object fields such as `attributes` become semi-structured Snowflake data through a `VARIANT` alias.
- The generated pipeline binds checkpoint version into both Flink checkpoint config and Kafka `GROUP_ID`.

Review implication: a schema change is incomplete unless the generated source YAML, model SQL, pipeline YAML, checkpoint config, Soda YAML, and Soda manifest are all aligned.

</details>

---

<details open>
<summary id="tab-schema-converter"><strong>Tab: Schema Converter</strong></summary>

## Schema Converter

Main workflow entry point: `transformers/streaming/schema_converter/Makefile`

`make autogen_all` runs deterministic generation and validation:

1. `autogen_sources`
2. `autogen_models`
3. `autogen_pipelines`
4. `autogen_checkpoints`
5. `validate_soda_checks`

`make autogen_soda_checks` is separate because it can call AWS Bedrock. CI validates Soda freshness, but does not generate new checks.

| Component | Path | Important Behavior |
| --- | --- | --- |
| CLI entrypoint | `transformers/streaming/schema_converter/src/main.py` | Dispatches `generate`, `validate`, `update`, and `compare` subcommands. |
| `SourceYMLGenerator` | `transformers/streaming/schema_converter/src/generators/source_yml.py` | Adds standard Kafka metadata fields, `sp-json` parser config, earliest-offset startup, Confluent SASL settings, and topic pattern. |
| `DBTModelGenerator` | `transformers/streaming/schema_converter/src/generators/dbt_model.py` | Builds Snowflake connector config, checkpoint env vars, `KAFKA_KEY` primary key, `TENANT_ID` partitioning, tags, header extraction, and `VARIANT`/`ARRAY` casts. |
| `PipelineGenerator` | `transformers/streaming/schema_converter/src/generators/pipeline.py` | Writes `streaming_v1` YAML with Airflow metadata, migration dependency, global placeholders, job args, `GROUP_ID`, and checkpoint version binding. |
| `CheckpointUpdater` | `transformers/streaming/schema_converter/src/util/checkpoint.py` | Walks environment config YAML files and appends `<schema>_checkpoint_version: v1` for each non-blacklisted schema and `dag_label` entry. |
| `SodaChecksGenerator` | `transformers/streaming/schema_converter/src/generators/soda_checks.py` | Generates Soda check YAML through Bedrock-backed logic and updates the auto-generated checks manifest. |
| `SodaChecksValidator` | `transformers/streaming/schema_converter/src/validators/soda_checks.py` | CI-safe validator that checks every eligible schema has a check file and that `_manifest.json` hashes match current schema content. |
| `SchemaComparator` | `transformers/streaming/schema_converter/src/util/schema_diff.py` | Supports local versus remote JSON schema comparison before assuming producer contract drift. |

Key gotcha: the `BLACKLIST` in the schema converter `Makefile` is a major behavior switch. It controls which schemas skip generator paths. Editing it can move ownership between generated artifacts and hand-maintained artifacts.

</details>

---

<details open>
<summary id="tab-custom-and-stateful-tables"><strong>Tab: Custom And Stateful Tables</strong></summary>

## Custom And Stateful Tables

Not every entity follows the simple generated `machine_account_v1` pattern. Some schemas are blacklisted or have custom/stateful behavior.

### Blacklisted And Custom Entities

Blacklist source of truth:

- `transformers/streaming/schema_converter/Makefile`

Examples listed in the blacklist include:

- `identity_role_assignment_account_target.json`
- `identity_role_detection_account_target.json`
- `access_profile_v1.json`
- `dimension_v1.json`
- `role_v1.json`
- `identity_v1.json`
- `cis_identity.json`
- `entitlement_additional_owner_aggregate_v1.json`

Examples of custom or non-simple dbt live-table models:

| Example | Path | Why It Matters |
| --- | --- | --- |
| Identity role assignment account target | `transformers/streaming/dbt/models/entity_live_tables/identity_role_assignment_account_target/identity_role_assignment_account_target.sql` | Representative blacklisted/custom entity path. |
| Identity exceptional entitlement | `transformers/streaming/dbt/models/entity_live_tables/identity_exceptional_entitlement/identity_exceptional_entitlement.sql` | Shows more specialized entitlement-related logic. |
| Identity entitlement assignment v1 | `transformers/streaming/dbt/models/entity_live_tables/identity_entitlement_assignment_v1/identity_entitlement_assignment_v1.sql` | Useful when reviewing changelog or assignment-oriented behavior. |

Review implication: when a schema is blacklisted, do not expect `autogen_all` to repair every artifact. Reviewers should identify whether the source of truth is schema-driven generation or hand-maintained SQL/YAML.

### Stateful Changelog Tables

Stateful changelog tables are used when Kafka records contain collections and the platform needs row-level add/update/remove deltas instead of full record replacement.

Relevant paths:

| Path | Purpose |
| --- | --- |
| `pipelines/dags/entity_live_dip/stateful_changelog_tables` | Airflow templates and configs for stateful changelog pipelines. |
| `transformers/streaming/dbt/macros/create_udfs.sql` | Registers changelog UDFs such as `map_diff_changelog` and `array_diff_changelog`. |
| `transformers/streaming/dbt/models/entity_live_tables/**` | dbt models that call changelog UDFs for collection diff behavior. |

Common stateful template examples:

- `pipelines/dags/entity_live_dip/stateful_changelog_tables/identity_role_assignment_account_target_template.yml`
- `pipelines/dags/entity_live_dip/stateful_changelog_tables/role_dimension_template.yml`
- `pipelines/dags/entity_live_dip/stateful_changelog_tables/cis_identity_access_profile_assignment_template.yml`

Review implication: stateful changelog changes should be reviewed for collection grain, operation semantics, UDF behavior, checkpoint impact, and downstream merge behavior.

</details>

---

<details open>
<summary id="tab-runtime-operations"><strong>Tab: Runtime Operations</strong></summary>

## Runtime Operations

Runtime behavior is spread across generated Airflow templates, dynamic YAML processing, the Fire image, Snowflake migrations, and Reconciler jobs.

| Surface | Path | What To Inspect |
| --- | --- | --- |
| Dynamic DAG expansion | `pipelines/dags/entity_live_dip/entity_live_dip_handler.py` | Delegates template expansion to `saas_airflow_utils` through `process_template_config`. |
| Generated live-table DAGs | `pipelines/dags/entity_live_dip/entity_live_dags/*_template.yml` | Streaming DAG metadata, migration dependency, Flink job config, checkpoint version, and Snowflake args. |
| Migrations | `pipelines/dags/entity_live_dip/entity_live_dags/migrations` | Procedures run first, active versioned migrations run once, archived migrations are already applied. |
| Reconciler DAG | `pipelines/dags/entity_live_dip/entity_live_dags/reconciler_template.yml` | Hourly replay flow: migrations, procedure creation, replay ID generation, then Fire pod execution. |
| Fire job runner | `transformers/fire/src/job_runner.py` | Python Fire CLI exposing reconciler, Kafka replay, entity ID dump, Flink health, and Soda checks. |

### Reconciler Flow

The Reconciler is the correction path when live table records need replay or repair.

Key files:

| File | Role |
| --- | --- |
| `pipelines/dags/entity_live_dip/entity_live_dags/reconciler_template.yml` | Airflow orchestration for replay. |
| `pipelines/dags/entity_live_dip/entity_live_dags/reconciler/generation/procedures` | Snowflake stored procedures used by replay generation. |
| `pipelines/dags/entity_live_dip/entity_live_dags/reconciler/generation/scripts` | SQL scripts that create replay requests. |
| `transformers/fire/src/jobs/base_event_reconciler.py` | Reads `EVENT_DATA.REPLAY_REQUEST`, groups by topic, processes work in parallel, and batch-updates replay status. |
| `transformers/fire/src/jobs/event_reconciler_api.py` | Sends replay requests to IDN service APIs and expects HTTP 202. |
| `transformers/fire/src/jobs/event_reconciler_kafka.py` | Kafka replay variant. |

Important operational detail: `BaseEventReconciler` serializes Snowflake status updates with a global lock to reduce table lock contention. Failed batch status updates are skipped and retried later rather than falling back to individual updates.

### Migration Flow

Migration docs live at `pipelines/dags/entity_live_dip/entity_live_dags/migrations/README.md`.

Migration rules:

- Repeatable scripts live under `procedures/`.
- New versioned scripts go under `active/`.
- Applied scripts are moved to `archived/`.
- Versioned files use Flyway-style names such as `V10.0.108__add_columns_to_discovered_application.sql`.
- Most live-table pipelines depend on `sf_live_event_data_migrations_<env>`.

Review implication: migration changes can block live-table jobs if they fail. Version collisions across PRs are a real risk.

</details>

---

<details open>
<summary id="tab-quality-and-metrics"><strong>Tab: Quality And Metrics</strong></summary>

## Quality And Metrics

The repo uses two quality paths:

1. Auto-generated Soda checks tied to schemas.
2. Team or domain-specific Soda DAGs and checks.

### Soda Quality Checks

| Path | Purpose |
| --- | --- |
| `transformers/fire/src/soda_quality_checks/auto_generated_checks` | Bedrock-generated checks tied to JSON schemas. |
| `transformers/fire/src/soda_quality_checks/_manifest.json` | Schema hash manifest used by `validate_soda_checks`. |
| `transformers/fire/src/jobs/run_soda_checks.py` | Fire job that runs Soda checks against Snowflake. |
| `pipelines/dags/entity_live_dip/quality_checks` | Per-team nightly quality check DAG templates. |
| `pipelines/dags/entity_live_dip/edm_quality_checks` | EDM-specific comparison and schema drift checks. |

Team quality DAGs commonly use `template: soda_quality_checks` and point to team directories such as:

- `/app/soda_quality_checks/arcadia`
- `/app/soda_quality_checks/fastdata`
- `/app/soda_quality_checks/lanai`
- `/app/soda_quality_checks/rap`
- `/app/soda_quality_checks/rcp`

Review implication: schema-generated checks catch generic contract issues, but team checks catch business-specific correctness. A PR can pass autogen validation and still need targeted Soda coverage.

### Metrics And Flink Health

Key metrics path:

| File | Role |
| --- | --- |
| `pipelines/dags/entity_live_dip/entity_live_dags/metrics_generation_template.yml` | Airflow metrics DAG. |
| `transformers/fire/src/jobs/flink_job_health.py` | Queries Flink job health and writes metric rows. |
| `metrics/flink_health_metrics.yml` | Metric definitions for Flink health. |
| `metrics/reconciler_metrics.yml` | Metric definitions for Reconciler behavior. |
| `transformers/streaming/dbt/models/metrics/event_relay` | dbt-side event relay metrics chain. |

Metrics generation flow:

```text
create_procedures
  -> generate_sf_metrics
  -> list_active_flink_jobs
  -> generate_flink_job_metrics
```

Important detail: `list_active_flink_jobs` discovers active jobs by grepping `job_name:` from DAG YAML. Renaming or malformed job YAML can affect both orchestration and metrics visibility.

</details>

---

<details open>
<summary id="tab-ci-and-deploy"><strong>Tab: CI And Deploy</strong></summary>

## CI And Deploy

The repo has strong controls around generated-file drift.

| Control | Path | What It Enforces |
| --- | --- | --- |
| Pre-commit | `.pre-commit-config.yaml` | Runs `make -C transformers/streaming/schema_converter autogen_all` on every commit. |
| GitHub Actions | `.github/workflows/validate-autogen.yml` | Installs Python 3.12 dependencies and runs `make autogen_all` for schema, generated dbt, DAG, Soda, converter, and Makefile changes. |
| Dirty tree gate | `.github/workflows/validate-autogen.yml` | Fails if `git status --porcelain` is non-empty after generation. |
| Soda freshness | `transformers/streaming/schema_converter/src/validators/soda_checks.py` | Fails if a schema has no check file or `_manifest.json` hash is stale. |
| Jenkins deploy | `cicd/Jenkinsfile` | Builds streaming and Fire transformers, deploys workflows, creates a deploy ticket, and publishes the Atlan data product. |
| Bulk DAG trigger docs | `cicd/bulk_deploy/trigger_dags.md` | Documents operational DAG triggering patterns. |

Jenkins deploy stages:

1. Checkout `main`.
2. Build transformers through `atlasDataBuildTransformers`.
3. Deploy workflows through `atlasDataDeployWorkflow`.
4. Cleanup release artifacts.
5. Create a deployment ticket.
6. Publish the data product to Atlan.

Important deploy detail: workflow deploy passes `streaming_tag`, `fire_tag`, and `version`. That matters because live-table DAGs run streaming jobs, while metrics, Soda, and Reconciler jobs use the Fire image.

Branch and ownership controls:

- `.github/CODEOWNERS` routes changes to multiple SailPoint teams.
- `.github/SETUP_BRANCH_PROTECTION.md` documents branch protection setup.

</details>

---

<details open>
<summary id="tab-review-checklist"><strong>Tab: Review Checklist</strong></summary>

## Review Checklist

Use this checklist when reviewing `entity-live-dip` changes.

### Schema And Contract

- Does the JSON schema match the producer payload?
- Are required fields, nullability, UUID formats, date-time formats, object fields, and array fields accurate?
- Is `additionalProperties` intentional?
- Is this schema generated, custom, or blacklisted?

### Generated Artifacts

- Did the PR include schema, `source.yml`, model SQL, pipeline YAML, checkpoint config, Soda YAML, and manifest changes together?
- Was `make autogen_all` run cleanly?
- If a schema changed, was `make autogen_soda_checks` run and committed?
- Are generated files being hand-edited without a blacklist reason?

### dbt And Table Semantics

- Is `KAFKA_KEY` the correct live-table primary key?
- Are `POD`, `ORG`, `TENANT_ID`, and `EVENT_ID` extracted and checked?
- Are object and array fields intentionally mapped to Snowflake `VARIANT` or `ARRAY`?
- Is the table pass-through, live, history-only, or stateful changelog?
- If stateful changelog, are collection grain and operation semantics clear?

### Runtime And Operations

- Does the PR require checkpoint version changes?
- Does it require a migration?
- Does it require replay, backfill, or Reconciler coordination?
- Are Flink `GROUP_ID`, checkpoint name, checkpoint version, and Snowflake sink behavior aligned?
- Could the change affect metrics discovery through `job_name:` parsing?

### Data Quality

- Do Soda checks cover completeness, uniqueness, validity, freshness, and known producer format issues?
- Are failed-row samples useful enough for incident triage?
- Are team/domain Soda checks needed in addition to auto-generated checks?
- Are missing Kafka headers detectable?

### Deploy Risk

- Could migrations collide with another PR's Flyway version?
- Does the change need cross-team code owner review?
- Does it affect both streaming and Fire runtime images?
- Is the operational rollback or replay plan clear?

## Recommended Next Analysis Steps

1. Compare one fully generated entity with one blacklisted/custom entity.
2. Trace a stale-data incident through Airflow, Flink, Kafka offsets, Snowflake live/history tables, Soda samples, metrics, and Reconciler replay.
3. Walk a real schema change PR and verify every generated artifact.
4. Inspect `dynamic_yaml_v1` templates for metrics, Reconciler, quality checks, and stateful changelog tables.
5. Build a separate runbook for checkpoint bumps and backfills.

</details>
