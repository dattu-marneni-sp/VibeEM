# Entity Live DIP Deep Dive

This document summarizes the deeper analysis of `sailpoint/entity-live-dip` in a readable format. The companion visual canvas is stored at `canvases/entity-live-dip-deep-dive.canvas.tsx`.

## Mental Model

`entity-live-dip` is a schema-driven platform for building low-latency Snowflake live tables from compacted Kafka entity topics.

The core path is:

```text
JSON schema -> generated dbt source/model -> Airflow/Flink pipeline -> Snowflake history/live/view tables -> Soda/metrics/reconciler controls
```

The JSON schema is the primary contract. Most production-facing artifacts are generated or validated from that contract.

## Worked Entity Trace: `machine_account_v1`

The `machine_account_v1` table shows the typical generated path.

| Layer | File | What It Proves |
| --- | --- | --- |
| Schema | `transformers/streaming/schema_converter/schemas/machine_account_v1.json` | Declares required fields, UUID/date-time formats, object fields, and `additionalProperties: false`. |
| Kafka source | `transformers/streaming/dbt/models/entity_live_tables/machine_account_v1/source.yml` | Reads topic pattern `^machine_account_v1(_backfill)?$` and includes Kafka key, headers, timestamp, partition, offset, and topic metadata. |
| dbt model | `transformers/streaming/dbt/models/entity_live_tables/machine_account_v1/machine_account_v1.sql` | Adds platform columns, `KAFKA_KEY` primary key, `TENANT_ID` partitioning, and casts `attributes` to `VARIANT`. |
| Airflow/Flink job | `pipelines/dags/entity_live_dip/entity_live_dags/machine_account_template.yml` | Creates the streaming DAG, depends on migrations, and wires checkpoint and Flink/Snowflake arguments. |
| Checkpoint config | `pipelines/dags/entity_live_dip/entity_live_dags/configs/**` | Adds `machine_account_v1_checkpoint_version` per environment and `dag_label`. |
| Soda checks | `transformers/fire/src/soda_quality_checks/auto_generated_checks/machine_account_v1.yml` | Checks required fields, platform headers, deprecated iris format, uniqueness, booleans, timestamps, and ID validity. |

## Schema Converter Internals

`transformers/streaming/schema_converter/Makefile` is the main workflow entry point.

`make autogen_all` runs:

1. `autogen_sources`
2. `autogen_models`
3. `autogen_pipelines`
4. `autogen_checkpoints`
5. `validate_soda_checks`

Important generator files:

| Component | Path | Important Behavior |
| --- | --- | --- |
| `SourceYMLGenerator` | `transformers/streaming/schema_converter/src/generators/source_yml.py` | Adds standard Kafka metadata fields, `sp-json` parser config, earliest-offset startup, Confluent SASL settings, and topic pattern. |
| `DBTModelGenerator` | `transformers/streaming/schema_converter/src/generators/dbt_model.py` | Builds Snowflake connector config, checkpoint env vars, `KAFKA_KEY` primary key, `TENANT_ID` partitioning, tags, header extraction, and `VARIANT`/`ARRAY` casts. |
| `PipelineGenerator` | `transformers/streaming/schema_converter/src/generators/pipeline.py` | Writes `streaming_v1` YAML with Airflow metadata, migration dependency, environment placeholders, job args, `GROUP_ID`, and checkpoint version binding. |
| `CheckpointUpdater` | `transformers/streaming/schema_converter/src/util/checkpoint.py` | Walks config YAML files and appends `<schema>_checkpoint_version: v1` for each non-blacklisted schema and `dag_label` entry. |
| `SodaChecksValidator` | `transformers/streaming/schema_converter/src/validators/soda_checks.py` | CI-only validator that checks every eligible schema has a check file and that manifest hashes match current schema content. |

## CI And Deployment Controls

The repo has strong controls around generated-file drift.

| Control | Path | What It Enforces |
| --- | --- | --- |
| Pre-commit | `.pre-commit-config.yaml` | Runs `make -C transformers/streaming/schema_converter autogen_all` on every commit. |
| GitHub Actions | `.github/workflows/validate-autogen.yml` | Installs Python 3.12 dependencies and runs `make autogen_all` for schema, generated dbt, DAG, Soda, converter, and Makefile changes. |
| Dirty tree gate | `.github/workflows/validate-autogen.yml` | Fails if `git status --porcelain` is non-empty after generation. |
| Soda freshness | `transformers/streaming/schema_converter/src/validators/soda_checks.py` | Fails if a schema has no check file or `_manifest.json` hash is stale. |
| Jenkins deploy | `cicd/Jenkinsfile` | Builds streaming and Fire transformers, deploys workflows with `streaming_tag`, `fire_tag`, and `version`, creates a deployment ticket, and publishes the Atlan data product. |

## Runtime And Operations

Operationally, this repo spans several surfaces:

| Surface | Path | What To Inspect |
| --- | --- | --- |
| Dynamic DAG expansion | `pipelines/dags/entity_live_dip/entity_live_dip_handler.py` | Delegates template expansion to `saas_airflow_utils` over `/opt/airflow/dags/entity_live_dip`. |
| Migrations | `pipelines/dags/entity_live_dip/entity_live_dags/migrations/README.md` | Procedures run first, active versioned migrations run once, and most live pipelines depend on `sf_live_event_data_migrations_<env>`. |
| Metrics | `pipelines/dags/entity_live_dip/entity_live_dags/metrics_generation_template.yml` | Runs every 30 minutes, discovers `job_name` values from YAML, and calls `run_flink_job_health`. |
| Reconciler | `pipelines/dags/entity_live_dip/entity_live_dags/reconciler_template.yml` | Runs hourly, generates replay IDs in Snowflake, and calls `run_event_reconciler_api`. |
| Fire runtime | `transformers/fire/src/job_runner.py` | Exposes reconciler, Kafka replay, entity ID dump, Flink health, and Soda check jobs through Python Fire. |

## Important Gotchas

- The schema converter `BLACKLIST` controls which schemas are generated. A schema can exist without a full generated dbt, pipeline, checkpoint, or Soda path.
- `make autogen_all` validates Soda checks but does not generate them. Schema edits may require `make autogen_soda_checks`, which can require AWS Bedrock access.
- Generated files should not be manually edited unless the schema is intentionally blacklisted and ownership is clear.
- Checkpoint version changes are runtime changes. They affect Flink state and Kafka `GROUP_ID` behavior, so they need an operational reason.
- Migrations use Flyway-style versions. Version collisions across PRs can block or confuse deploys.
- The Kafka source parser tolerates missing fields and parse errors, so Soda checks and failed-row samples are important for catching producer drift.

## PR Review Questions

Use these questions when reviewing `entity-live-dip` changes:

- Does the JSON schema match the producer payload, required fields, nullability, UUID/date-time formats, and object or array intent?
- Are schema, `source.yml`, model SQL, pipeline YAML, checkpoint config, Soda YAML, and manifest changes committed together?
- Is `KAFKA_KEY` the correct live-table primary key?
- Are `POD`, `ORG`, `TENANT_ID`, and `EVENT_ID` present and checked?
- Are object and array fields intentionally mapped to Snowflake `VARIANT` or `ARRAY`?
- Does the PR require checkpoint bumps, migrations, replay, backfill, or coordinated deploy timing?
- Do Soda checks cover completeness, uniqueness, validity, freshness, and known producer format issues?

## Recommended Next Deep Dives

1. Compare one generated entity with one blacklisted or custom entity.
2. Trace one stale-data incident from Airflow to Flink to Kafka to Snowflake to Soda to Reconciler.
3. Walk a schema change PR and check every generated artifact.
4. Inspect `dynamic_yaml_v1` templates such as metrics, reconciler, quality checks, and stateful changelog tables.
