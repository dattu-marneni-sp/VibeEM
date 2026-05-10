---
name: entity-live-table-onboarding
description: Entity-live-dip — guides adding a new live table in SailPoint entity-live-dip from JSON schema through generated dbt models, Airflow/Flink DAG templates, checkpoint config, Soda checks, pre-commit, and CI validation. Use when onboarding a new entity-live-dip live table or explaining the schema-to-CI workflow.
---

# Entity Live Table Onboarding

Use this workflow for `sailpoint/entity-live-dip` when adding or changing a schema-backed live table.

## Overview

`entity-live-dip` is schema-driven. A JSON schema under `transformers/streaming/schema_converter/schemas` is the source of truth. The schema converter generates dbt source YAML, dbt model SQL, Airflow/Flink DAG templates, checkpoint config entries, and Soda data quality checks.

## Not Every Table Is “Schema → Autogen”

**Decision point (before assuming the standard workflow):** Open `transformers/streaming/schema_converter/Makefile` and inspect the `BLACKLIST` variable (comma-separated JSON filenames). If the entity’s schema file is listed there, the generator **intentionally skips** it. Onboarding is **manual** for that entity:

- Custom or hand-maintained dbt under `transformers/streaming/dbt/models/entity_live_tables/<entity>/` (possibly with a `*_lag.sql` view and changelog UDFs).
- Airflow/Flink templates under `pipelines/dags/entity_live_dip/stateful_changelog_tables/` (and configs under `stateful_changelog_tables/configs/**`), not only `entity_live_dags/`.
- Checkpoint keys and version entries in the matching config trees; parallelism overrides if the template supports them.
- Migrations under `pipelines/dags/entity_live_dip/entity_live_dags/migrations/**` when applicable.
- **Team-owned Soda** under `transformers/fire/src/soda_quality_checks/rcp_team/` and registration in quality DAG templates such as `pipelines/dags/entity_live_dip/quality_checks/rcp_team_template.yml`—do not expect `auto_generated_checks` alone to cover SCD or cross-table rules.

Example blacklist-driven entity: `identity_role_assignment_account_target.json` → custom model `transformers/streaming/dbt/models/entity_live_tables/identity_role_assignment_account_target/identity_role_assignment_account_target.sql` and template `pipelines/dags/entity_live_dip/stateful_changelog_tables/identity_role_assignment_account_target_template.yml`.

## Workflow

1. Add or update the schema:
   - Path: `transformers/streaming/schema_converter/schemas/<table_name>.json`
   - The filename becomes the table/entity name, such as `machine_account_v1`.
   - Do not use `_example.json` for deployable schemas.

2. Initialize the schema converter:

   ```bash
   cd transformers/streaming/schema_converter
   make init
   ```

   If dependency installation fails, check SailPoint JFrog/pip access first.

3. Generate Soda checks for new or changed schemas:

   ```bash
   make autogen_soda_checks
   ```

   This writes checks under `transformers/fire/src/soda_quality_checks/auto_generated_checks` and updates the Soda manifest. It may require AWS Bedrock access.

4. Generate and validate deterministic outputs:

   ```bash
   make autogen_all
   ```

   This runs source YAML generation, dbt model generation, pipeline template generation, checkpoint updates, and Soda check validation.

5. Return to repo root and inspect changes:

   ```bash
   cd ../../../
   git status
   git diff
   ```

6. Commit schema plus generated files together.

## Generated Outputs

For schema `my_entity_v1.json`, expect these outputs:

- `transformers/streaming/dbt/models/entity_live_tables/my_entity_v1/source.yml`
- `transformers/streaming/dbt/models/entity_live_tables/my_entity_v1/my_entity_v1.sql`
- `pipelines/dags/entity_live_dip/entity_live_dags/my_entity_template.yml`
- Checkpoint entries in `pipelines/dags/entity_live_dip/entity_live_dags/configs/**`
- Soda checks in `transformers/fire/src/soda_quality_checks/auto_generated_checks/my_entity_v1.yml`

## Review Checklist

Before opening a PR, verify:

- The schema field names, required fields, and types match the Kafka payload.
- Object and array fields are mapped intentionally to Snowflake `VARIANT` or `ARRAY`.
- The generated dbt model extracts `POD`, `ORG`, `TENANT_ID`, and `EVENT_ID` from headers.
- The generated dbt model uses the expected primary key, usually `KAFKA_KEY`.
- The DAG template has the expected `dag_id`, `job_name`, `checkpoint_name`, and checkpoint version variable.
- Checkpoint config entries were added for the target environments.
- Soda checks exist and are not stale for the schema.
- Generated files were not hand-edited unless the schema is intentionally blacklisted in the schema converter Makefile.

## CI Behavior

The PR workflow `.github/workflows/validate-autogen.yml` runs when schemas, generated dbt files, Airflow DAGs, Soda checks, schema converter code, the Makefile, or pre-commit config change.

CI performs this validation:

1. Install schema converter dependencies.
2. Run `make autogen_all`.
3. Fail if `git status --porcelain` shows generated file changes.

If CI fails with autogenerated files out of sync, run locally:

```bash
cd transformers/streaming/schema_converter
make autogen_soda_checks
make autogen_all
cd ../../../
git status
```

Then commit the regenerated files.

## Pre-commit

The repo pre-commit hook runs:

```bash
make -C transformers/streaming/schema_converter autogen_all
```

Install hooks with:

```bash
pip install pre-commit
pre-commit install
```

Bypassing hooks can leave generated files stale and block the PR in CI.
