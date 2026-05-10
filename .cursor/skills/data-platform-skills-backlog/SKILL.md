---
name: data-platform-skills-backlog
description: Maintains the prioritized backlog of Cursor skills to build for Data Platform work. Use when planning, sequencing, or creating data platform skills for entity-live-dip, dbt live tables, pipeline incidents, schema converters, or data quality reviews.
disable-model-invocation: true
---

# Data Platform Skills Backlog

## Priority Order

Build these Cursor skills in this order:

1. `entity-live-table-onboarding`
2. `dbt-live-table-review`
3. `pipeline-incident-triage`
4. `schema-converter-debugging`
5. `data-quality-review`

## Skill Summaries

### entity-live-table-onboarding

Guides adding a new live table in `entity-live-dip`, including schema creation, generated dbt models, Airflow DAG templates, checkpoint config, Soda checks, and CI validation.

### dbt-live-table-review

Reviews generated or custom dbt live table models for correctness, grain, primary keys, Snowflake types, streaming behavior, and downstream impact.

### pipeline-incident-triage

Guides debugging failed, delayed, or inconsistent data pipelines using Airflow logs, Flink job state, Kafka topics, Snowflake tables, metrics, and recent schema or deployment changes.

### schema-converter-debugging

Helps diagnose schema-driven generation failures in `transformers/streaming/schema_converter`, including source YAML generation, dbt model generation, pipeline template generation, checkpoint updates, and Soda check validation.

### data-quality-review

Reviews data platform changes for schema drift, null handling, duplicate records, row count changes, freshness, referential integrity, data contracts, and missing tests.

## Build Guidance

When turning one backlog item into a real Cursor skill:

1. Create a dedicated skill directory under `.cursor/skills/<skill-name>/`.
2. Write a focused `SKILL.md` with specific trigger terms in the description.
3. Keep the main skill concise and move detailed examples into adjacent reference files when needed.
4. Prefer repo-specific workflow steps over generic data engineering advice.
5. Test the skill against a real task before expanding it.
