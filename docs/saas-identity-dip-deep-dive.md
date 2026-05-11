# saas-identity-dip Deep Analysis

This single-page analysis summarizes `sailpoint-core/saas-identity-dip` using tab-style sections. GitHub Markdown does not support native tabs, so the sections below use anchor links plus expandable panels to behave like readable tabs.

Sources:

- GitHub repo: [`sailpoint-core/saas-identity-dip`](https://github.com/sailpoint-core/saas-identity-dip)
- Confluence: [Identity Materializer for Data Segmentation: Flows, Jobs, and Plans](https://sailpoint.atlassian.net/wiki/spaces/data/pages/4611342596/Identity+Materializer+for+Data+Segmentation+Flows+Jobs+and+Plans)

Local clone path used for evidence: `/Users/dattu.marneni/Workspace/saas-identity-dip`

## Tabs

[Overview](#tab-overview) |
[Identity Materializer Flow](#tab-identity-materializer-flow) |
[Repo Structure](#tab-repo-structure) |
[Core Runtime Architecture](#tab-core-runtime-architecture) |
[Key Workflows](#tab-key-workflows) |
[Operational Surfaces](#tab-operational-surfaces) |
[Risks And Review Checklist](#tab-risks-and-review-checklist) |
[Comparison To entity-live-dip](#tab-comparison-to-entity-live-dip) |
[Recommended Next Steps](#tab-recommended-next-steps) |
[Unknowns](#tab-unknowns)

---

<details open>
<summary id="tab-overview"><strong>Tab: Overview</strong></summary>

## Overview

`saas-identity-dip` is the streaming data pipeline that powers the Identity Materializer for ISC Data Segmentation. Per the [Confluence page](https://sailpoint.atlassian.net/wiki/spaces/data/pages/4611342596/Identity+Materializer+for+Data+Segmentation+Flows+Jobs+and+Plans), it consumes raw CIS / IAM entity events from Kafka, then "shapes, deduplicates, joins, and enriches" them into product-ready Kafka streams that Search, segmentation, display-name, and access-logic consumers depend on.

The two end-state product topics named on the Confluence page are:

| Output Topic | Description | Key | Consumer |
| --- | --- | --- | --- |
| `segmented_identity` | Identity-to-data-segment membership: identity id plus the list of segment ids it belongs to after segment rules are applied. | `tenantId#identityId` | `sp_materializer` service forwards full identity events to full search. |
| `search_lite_identity_v1` | Search-lite identity document: rich projection used by Search Lite (name, alias, state, attributes, manager ref, lifecycle/profile refs, processing state/details, segments, flags, etc.). | `tenantId#identityId` | Search Lite service. |

The repo's primary mental model is:

```text
Source Kafka entity topics
  -> hand-written dbt-Flink models (Kafka -> Kafka)
  -> intermediate dedup / join / aggregate Kafka topics
  -> final product Kafka topics (segmented_identity, search_lite_identity_v1)
```

There is no Snowflake live/history sink in the streaming path; everything is Kafka-to-Kafka via Flink jobs deployed by dbt-Flink models.

Key high-level facts grounded in the repo:

- DIP name: `saas-identity-dip` (declared in `pipelines/dags/saas_identity_dip/identity/template.yml` `global.dip_name`).
- Single Airflow template for the streaming Identity flow at `pipelines/dags/saas_identity_dip/identity/template.yml`.
- DAG id pattern: `cbc_materializers_identity_{{ dag_label }}` (per env).
- Code owners: `* @sailpoint-core/fast-data` (`CODEOWNERS`).

</details>

---

<details open>
<summary id="tab-identity-materializer-flow"><strong>Tab: Identity Materializer Flow</strong></summary>

## Identity Materializer Flow

Per the Confluence page section "IM Data Segment and Search lite", the Identity Materializer is implemented as 9 Flink jobs split into a Segmented Identity / Lite pipeline plus supporting jobs:

```text
### Segmented Identity & Lite Pipeline (4 jobs)
  - identity-lite
  - identity-lite-filtered
  - segmented-identity
  - segmented-identity-dedup

### Supporting Jobs (5 jobs)
  - cis_identity_internal_dedup
  - account_identity_joined
  - identity-name
  - account_dedup
  - account_identity_dedup
```

Each job corresponds to a hand-written dbt-Flink model directory under `transformers/streaming/dbt/models/entity_models/`:

| Job | dbt model directory | Sink file |
| --- | --- | --- |
| `identity-lite` | `transformers/streaming/dbt/models/entity_models/identity/identity-lite` | `IDENTITY_LITE_SINK.sql` |
| `identity-lite-filtered` | `transformers/streaming/dbt/models/entity_models/identity/identity-lite-filtered` | `IDENTITY_LITE_FILTERED.sql` (per directory contents) |
| `segmented-identity` | `transformers/streaming/dbt/models/entity_models/identity/segmented-identity` | `SEGMENTED_IDENTITY_SINK.sql` |
| `segmented-identity-dedup` | `transformers/streaming/dbt/models/entity_models/identity/segmented-identity-dedup` | `SEGMENTED_IDENTITY_DEDUP_SINK.sql` |
| `cis_identity_internal_dedup` | `transformers/streaming/dbt/models/entity_models/identity/cis_identity_internal_dedup` | `CIS_IDENTITY_INTERNAL_DEDUP_SINK.sql` |
| `account_identity_joined` | `transformers/streaming/dbt/models/entity_models/common/account-identity-joined` | `ACCOUNT_IDENTITY_JOINED_SINK.sql` |
| `identity-name` | `transformers/streaming/dbt/models/entity_models/identity/identity-name` | `IDENTITY_NAME_SINK.sql` |
| `account_dedup` | `transformers/streaming/dbt/models/entity_models/common/account_dedup` | `ACCOUNT_DEDUP_SINK.sql` |
| `account_identity_dedup` | `transformers/streaming/dbt/models/entity_models/common/account_identity_dedup` | `ACCOUNT_IDENTITY_DEDUP_SINK.sql` |

Source topics (per Confluence "Input source Topics"):

| Source topic | Description | Key |
| --- | --- | --- |
| `account_v1` | Account on a source: native id, attributes, source ref, lock/disable flags, etc. | `tenantId#accountId` |
| `account_identity_v1` | Account-identity correlation: which identity owns the account and whether correlation was manual. | `tenant_id#account_id` |
| `source_v1` | Source definition: name, connector, connection type, authoritative flag, features, owner, etc. | `tenant_id#source_id` |
| `cis_identity_internal_v1` | CIS internal identity snapshot: profile ref, manager, lifecycle state, processing state/details, last refresh. | `tenantId#identityId` |
| `identity_v1` | Identity (human-focused in schema rules): name/alias, state, flags, attributes map. | `tenantId#identityId` |
| `role_v1` | Role access object: id, name, owners, memberships, entitlements, etc. | `<tenant_id>##<role_id>` |
| `entitlement_v1` | Entitlement: privileged access object and metadata. | `<tenant_id>#<entitlement_id>` |
| `access_profile_v1` | Access profile: bundle of access. | `<tenant_id>##<access_profile_id>` |

Final product Kafka topics (verified in the dbt sinks):

- `segmented_identity` — `SEGMENTED_IDENTITY_DEDUP_SINK.sql` writes `connector_properties.topic = 'segmented_identity'`.
- `search_lite_identity_v1` — produced by the search-lite chain ending in `IDENTITY_LITE_SINK` / filtered variant. Confluence describes this as the Search-lite identity document.

Feature flags called out by Confluence as gates on the 9 Identity Materializer jobs (FD owns):

- `SAAS_IDENTITY_DIP_MATERIALIZER_ENABLED`
- `ACCOUNT_DEDUP_SINK_SPLIT`
- `ACCOUNT_IDENTITY_DEDUP_SINK_SPLIT`
- `ACCOUNT_IDENTITY_JOINED_SINK_SPLIT`
- `SAAS_IDENTITY_DIP_SKIP_CONTENT_DEDUP_ENABLED`
- `SAAS_IDENTITY_DIP_LOGGING_ENABLED`
- `SI_IDENTITY_SEGMENT_MATERIALIZATION`

Operational links from Confluence:

- DAG: [`cbc_materializers_identity_{env}`](https://github.com/sailpoint-core/saas-identity-dip/blob/main/pipelines/dags/saas_identity_dip/identity/template.yml)
- Flink jobs: [`transformers/streaming/dbt/models/entity_models`](https://github.com/sailpoint-core/saas-identity-dip/tree/main/transformers/streaming/dbt/models/entity_models) under `/common` and `/identity`
- Flink cluster: pipeline `identitydip` (Shared Flink Endpoints page).
- Grafana: IDN DIP STREAMING dashboard, filterable per Flink cluster (e.g., `stg-use1-identitydip`).

</details>

---

<details open>
<summary id="tab-repo-structure"><strong>Tab: Repo Structure</strong></summary>

## Repo Structure

Top-level layout under `/Users/dattu.marneni/Workspace/saas-identity-dip`:

```text
.
|- README.md
|- CODEOWNERS                # * @sailpoint-core/fast-data
|- _config.yml
|- copier.md / copier.mk     # copier-based scaffolding controls
|- docs/                     # currently only index.html (lineage graph entry)
|- cicd/                     # Jenkinsfile, PRB.Jenkinsfile, README.md
|- pipelines/                # Airflow DAGs and env config
|- transformers/             # streaming, lakehouse, fire, flink_udf
```

`pipelines/`:

| Path | Purpose |
| --- | --- |
| `pipelines/Makefile` | Local pipeline make targets. |
| `pipelines/dags/saas_identity_dip/saas_identity_dip_handler.py` | Airflow DAG entrypoint that delegates to `saas_airflow_utils`. |
| `pipelines/dags/saas_identity_dip/identity/template.yml` | Single `streaming_v1` template that wires every Identity Materializer Flink job. |
| `pipelines/dags/saas_identity_dip/identity/configs/{local,dev,internal,prod}/*.yml` | Per-env `dag_label` configs with checkpoint version, parallelism, and `enabled` flags per job. |
| `pipelines/dags/saas_identity_dip/lakehouse/identity_amm` | Separate sub-DAG path for AMM identity Snowflake-side flow. |
| `pipelines/dags/saas_identity_dip/lakehouse/identity_amm_aggregate` | Separate sub-DAG path for AMM aggregate flow. |
| `pipelines/envs/airflow/{Dockerfile,docker-compose.yml,airflow.cfg,requirements.txt}` | Local Airflow runner. |

`transformers/`:

| Path | Purpose |
| --- | --- |
| `transformers/streaming/README.md` | dbt-Flink usage guide (deploy models, sink config, headers, UDFs, local Kafka/Flink). |
| `transformers/streaming/dbt/dbt_project.yml` | dbt project named `streaming`; `on-run-start` registers UDFs via `create_udfs`. |
| `transformers/streaming/dbt/macros/create_udfs.sql` | Registers all Flink Java UDFs (60+ functions) used across the dbt models. |
| `transformers/streaming/dbt/models/entity_models/identity/**` | Hand-written identity dbt-Flink models including the 9 Identity Materializer jobs and other identity-aggregate jobs. |
| `transformers/streaming/dbt/models/entity_models/common/**` | Shared dedup/join models (`account_dedup`, `account_identity_dedup`, `account-identity-joined`, `account-source-schema-joined`, `source_schema_dedup`, `source-name`). |
| `transformers/streaming/metrics/resources/dynamic_tables.yaml` | Snowflake dynamic-table refresh metric definitions (Lakehouse-side). |
| `transformers/lakehouse/dbt/**` | Lakehouse dbt project (Snowflake side). Out of scope for the streaming Identity Materializer but lives in the same repo. |
| `transformers/flink_udf/build.gradle` | Gradle build for the Java UDF jar (`saas-idn-dip-udf.jar`). |
| `transformers/flink_udf/src/main/java/com/sailpoint/udf/**` | Identity-specific UDFs (e.g., `BuildHeaders`, `BuildAccountAttributes`, `DataSegmentMatcher`, `DataSegmentsToJson`, `BuildHydrateSegments`, `RoleAssignmentAggregation*`). |
| `transformers/flink_udf/src/main/java/com/sailpoint/data/segment/materializer/**` | Standalone `DataSegmentsByTenantMaterializerJob` Flink job that buffers `data_segment_v1` and emits `data_segments_by_tenant_v1` (per-tenant collapsed segments). |
| `transformers/fire/src/**` | Python "fire" runtime (Makefile, requirements, `main.py`). Used in the same repo, role in the streaming Identity flow not verified in detail. |

`cicd/`:

| Path | Purpose |
| --- | --- |
| `cicd/Jenkinsfile` | Main build/deploy pipeline. |
| `cicd/PRB.Jenkinsfile` | PR build pipeline. |
| `cicd/README.md` | Documents the copier `Jenkinsfile.jinja` template-extension model and overridable jinja blocks. |

</details>

---

<details open>
<summary id="tab-core-runtime-architecture"><strong>Tab: Core Runtime Architecture</strong></summary>

## Core Runtime Architecture

### Single Identity Airflow template

The Identity Materializer is wired by **one** `streaming_v1` Airflow template:

- File: `pipelines/dags/saas_identity_dip/identity/template.yml`
- DAG id: `cbc_materializers_identity_{{ dag_label }}`
- Owner: `Wasabi`, retries `5`, retry delay `300s`, schedule `null`, `catchup: False`.
- Tags: `streaming, entity-topics, real-time, data-engineering, identity`.

Globals in this template define the per-env wiring used by every job:

```yaml
global:
  aws_region: "{{ aws_region }}"
  dip_name: "saas-identity-dip"
  sql_gateway_endpoint: "{{ sql_gateway_endpoint }}"
  checkpoint_protocol: "{{ checkpoint_protocol }}"
  checkpoint_bucket: "{{ checkpoint_bucket }}"
  checkpoint_prefix: "{{ checkpoint_prefix }}"
  confluent_enabled: "{{ confluent_enabled }}"
  confluent_api_key_param: "{{ confluent_api_key_param }}"
  confluent_api_secret_param: "{{ confluent_api_secret_param }}"
  kafka_brokers: "{{ kafka_brokers }}"
  flink_jobmanager_url: "{{ flink_jobmanager_url }}"
  artifact_bucket: "{{ artifact_bucket }}"
  atlas_feature_flag_environment: "{{ atlas_feature_flag_environment }}"
```

Each Flink job is declared in the same template's `jobs:` list with a consistent shape:

```yaml
- job_name: SEGMENTED_IDENTITY_DEDUP_SINK
  release_mode: 'default'
  checkpoint_name: "segmented_identity_dedup_sink"
  checkpoint_version: {{ segmented_identity_dedup_sink_checkpoint_version }}
  prefer_checkpoint: True
  parallelism: {{ segmented_identity_dedup_sink_parallelism }}
  jar_upload_protocol: "{{ jar_upload_protocol }}"
  enabled: {{ segmented_identity_dedup_sink_enabled }}
```

Some jobs declare a `job_suffix`, most commonly `'group_22'`, which the file's inline comment marks as Morgan Stanley-specific:

> "this is group_22 is just for morgan stanley, this will continue to exist long term"

This is how the same logical job gets multiple deployed instances (e.g., `IDENTITY_ROLE_JOINED_SINK` group_22, `ACCOUNT_DEDUP_SINK` and a `group_22` variant, `IDENTITY_ACCOUNT_JOINED_MULTI_SINK` group_22, etc.).

### Airflow DAG handler

`pipelines/dags/saas_identity_dip/saas_identity_dip_handler.py` is a 3-line entrypoint:

```python
from saas_airflow_utils.platform_dip_factories.processors.template_config_processor import process_template_config

pipelines_dir = '/opt/airflow/dags/saas_identity_dip'

# TODO: Optional function or iterator for list of sub-dag breakdowns, ie per-tenant pipelines
process_template_config(pipelines_dir, globals())
```

Template expansion is delegated entirely to `saas_airflow_utils.process_template_config`, which discovers `template.yml` files under `pipelines_dir`, joins them with the per-env config YAMLs, and registers Airflow DAGs in `globals()`.

### Per-env configs drive all job knobs

For each env, files such as `pipelines/dags/saas_identity_dip/identity/configs/prod/prd-us-east-1.yml` provide:

- `dag_label`, `aws_region`, Confluent broker, SQL Gateway / Flink jobmanager URLs, S3 checkpoint bucket/prefix.
- Per-job triplets: `<job>_checkpoint_version`, `<job>_parallelism`, `<job>_enabled` (and the `_group_22_*` variants).

Concrete examples observed in `prd-us-east-1.yml`:

- `account_dedup_sink_checkpoint_version: v17`, `parallelism: 32`, `enabled: 'True'`.
- `identity_lite_sink_checkpoint_version: v11`, `parallelism: 64`, `enabled: 'True'`.
- `segmented_identity_sink_checkpoint_version: v10`, `parallelism: 64`, `enabled: 'True'`.
- `segmented_identity_dedup_sink_checkpoint_version: v10`, `parallelism: 16`, `enabled: 'True'`.
- `*_group_22_enabled: 'False'` for most group_22 variants in this region.

### dbt-Flink streaming project

`transformers/streaming/dbt/dbt_project.yml`:

- Project name `streaming`, profile `streaming`, on-run-start hook `{{ create_udfs() }}`.
- Vars sourced from env: `env`, `dip_name`, `udf_build`, `artifact_bucket`, `state_restore_path`, `parallelism`, `confluent_enabled`, `job_name`.
- All `entity_models/**` inherit `+default_connector_properties` for Confluent SASL_SSL Kafka and Snappy compression, plus `+metadata_columns: ["headers"]`.

Each job's behavior is encoded in a Kafka-sink dbt-Flink model. Example: `transformers/streaming/dbt/models/entity_models/identity/identity-lite/IDENTITY_LITE_SINK.sql`:

```sql
{{
    config(
        materialized = 'table',
        connector_properties = {
            'connector': 'upsert-kafka',
            'topic': 'search_lite_identity_intermediate',
            'value.fields-include': 'EXCEPT_KEY',
            ...
        },
        job_configuration = {
            'parallelism.default': var("parallelism"),
            'execution.checkpointing.interval': env_var('ENV', 'local') == 'local' and '10 s' or '60 s',
            'state.backend.rocksdb.predefined-options': 'FLASH_SSD_OPTIMIZED',
            'table.optimizer.multi-join.enabled': true,
        },
        primary_key = 'pk',
        is_enforced = False,
        tags = ["identity_lite", "identity"],
        checkpointing_enabled = true,
        checkpoint_version = env_var("CHECKPOINT_VERSION"),
        checkpoint_name = env_var("CHECKPOINT_NAME", "identity_lite_sink")
    )
}}

SELECT *
FROM {{ ref('il_identity_all_joined') }}
```

Repeating patterns visible across sinks:

- `connector: upsert-kafka` with explicit `topic`.
- `value.fields-include: EXCEPT_KEY` so the Kafka key is not duplicated in the value.
- `primary_key = 'pk'` with `is_enforced = False` — the `pk` column is the Kafka key.
- `checkpointing_enabled = true` plus `checkpoint_version`/`checkpoint_name` driven by env vars supplied by the Airflow template.
- Mini-batch and 2-phase aggregation tuning, RocksDB `FLASH_SSD_OPTIMIZED`.
- `tags = [...]` used for selective dbt deployment via `make deploy-models MODEL_ARG=tags`.

Within a job directory you typically see this hand-written staging chain (example `account_dedup`):

- `sources.yml`
- `ad_account_source.sql`
- `ad_account_source_keyed.sql`
- `ACCOUNT_DEDUP_SINK.sql` (the job)

For larger jobs (e.g., `identity-lite`, `segmented-identity`) the staging chain is much wider, with multiple `*_source.sql` and `*_source_keyed.sql` per upstream topic and explicit `*_joined.sql` / `*_dedup_*` intermediate models.

### Flink UDFs

- Macro: `transformers/streaming/dbt/macros/create_udfs.sql` — registers Java UDFs from the `saas-identity-dip-udf.jar` via `ADD JAR` (or local `file:///opt/flink/lib` for `env=local`). Examples observed: `array_size`, `build_reference`, `build_headers`, `build_account_attributes`, `hydrate_segment`, `data_segment_matcher`, `data_segments_to_json`, `is_materializer_enabled`, `role_assignment_agg_v4`, `role_assignment_end_date`, `identity_app_agg`, `account_agg`, `aggregate_amm`, `amm_search_transform`, etc.
- Java sources live in `transformers/flink_udf/src/main/java/com/sailpoint/udf/**`.
- Standalone Flink job: `transformers/flink_udf/src/main/java/com/sailpoint/data/segment/materializer/DataSegmentsByTenantMaterializerJob.java`. Per its `README.md`, it reads `data_segment_v1`, buffers per tenant for a short window, and emits collapsed records to `data_segments_by_tenant_v1` to reduce downstream work when "publish all" sends multiple segment events for the same tenant.

</details>

---

<details open>
<summary id="tab-key-workflows"><strong>Tab: Key Workflows</strong></summary>

## Key Workflows

### Local development (streaming)

From `transformers/streaming/README.md`:

1. `make dbt-init` — installs Python deps (requires JFrog access for `dbt-flink-adapter`).
2. `make build-flink-udf` — builds the Java UDF jar.
3. `cp ../flink_udf/build/libs/saas-idn-dip-udf.jar ./envs/flink/opt/` — places the jar where the local Flink container expects it.
4. `make start-services` / `make restart-services` — brings up Flink + Kafka in Docker.
5. `make deploy-models MODEL_ARG=tags` — deploys dbt-Flink models, submitting SQL via the Flink SQL Gateway.

Convention notes from the same README:

- `checkpoint_name` should be the dbt model file name in lowercase.
- Setting `hard_delete = true` causes the upsert-kafka sink to publish a `null` value (tombstone).
- Reading Kafka headers requires declaring `headers` as a metadata column (`MAP<STRING, BYTES>`) in `sources.yml`.
- Common dedupe pattern uses `ROW_NUMBER() OVER (PARTITION BY tenantId, id ORDER BY procTime DESC NULLS LAST)`, which also serves as keying for joins.

### Job rollout / version bump (per environment)

Operationally, changing a job's behavior follows this cycle:

1. Edit the dbt-Flink model under `transformers/streaming/dbt/models/entity_models/{common,identity}/<job>/`.
2. Bump `<job>_checkpoint_version` in every relevant per-env config under `pipelines/dags/saas_identity_dip/identity/configs/<env>/<region>.yml` (so Flink does not try to restore from an incompatible savepoint).
3. Adjust `<job>_parallelism` and `<job>_enabled` if needed.
4. Push to `main`, which triggers Jenkins (`cicd/Jenkinsfile`) to build transformers, deploy workflows with `streaming_tag`, `lakehouse_tag`, `fire_tag`, `flink_udf_tag`, and the UDF artifact location.
5. Confluence calls out separate "SavePoints / Checkpoint validation" and "Data checks" steps owned by the team; the in-repo evidence for these surfaces is limited (see Unknowns).

### Airflow DAG expansion

- `saas_identity_dip_handler.py` calls `process_template_config('/opt/airflow/dags/saas_identity_dip', globals())`.
- That helper from `saas_airflow_utils.platform_dip_factories.processors.template_config_processor` walks `pipelines_dir`, finds `template.yml` files, joins them with each entry in the matching `configs/<env>/<region>.yml`, and registers one Airflow DAG per `dag_label`.
- For Identity Materializer this yields one `cbc_materializers_identity_{dag_label}` DAG per region per env, each expanding the same `jobs:` list.

### Standalone Data Segments materializer (Java)

Per `transformers/flink_udf/src/main/java/com/sailpoint/data/segment/materializer/README.md`:

- Reads `data_segment_v1` and buffers per tenant.
- Emits one merged record per tenant on a time window to `data_segments_by_tenant_v1`.
- Local execution accepts CLI args like `--kafka-brokers`, `--input-topic-name`, `--consumer-group`, `--output-topic-name`.

This job collapses bursty "publish all" segment streams into a single per-tenant emission so the downstream identity-segment join only needs to react once per tenant per window.

</details>

---

<details open>
<summary id="tab-operational-surfaces"><strong>Tab: Operational Surfaces</strong></summary>

## Operational Surfaces

### Airflow

- DAG family: `cbc_materializers_identity_{env}` (e.g., `cbc_materializers_identity_prd-us-east-1`).
- Tags: `streaming, entity-topics, real-time, data-engineering, identity`.
- Schedule: `null` (event/manual orchestration; the actual streaming runs as Flink jobs, not as an Airflow schedule).
- Owner: `Wasabi`, retries `5`, retry delay `300s`.

### Flink

- Cluster: `identitydip` pipeline (per Confluence: Shared Flink Endpoints).
- Per-env Flink jobmanager and SQL Gateway URLs come from per-env config (e.g., `prd-us-east-1.yml`):
  - `sql_gateway_endpoint: prd-use1-identitydip-sqlgateway.flink.svc.cluster.local`
  - `flink_jobmanager_url: http://prd-use1-identitydip-rest.flink.svc.cluster.local:8081`
- State checkpoints land on S3 via `checkpoint_protocol: s3`, `checkpoint_bucket`, `checkpoint_prefix`.

### Kafka (Confluent Cloud)

- `confluent_enabled: true`, broker e.g. `pkc-do85r1.us-east-1.aws.confluent.cloud:9092`.
- API key/secret SSM parameter paths configured per env (e.g., `/confluent-kafka/cluster/kafka-broker-prd-us-east-1/...`).
- All entity-model dbt configs default to `SASL_SSL` + `PLAIN` with credentials read from `CONFLUENT_KEY` / `CONFLUENT_SECRET` env vars.

### Metrics & Dashboards

- Confluence references the Grafana dashboard "IDN DIP STREAMING" (e.g., `stg-use1-identitydip` cluster), filterable by region/Flink cluster, pods, job name, operator, metric (e.g., `mapStateRemoveLatency`).
- Repo-side metric definitions seen so far are Snowflake/Lakehouse-side: `transformers/streaming/metrics/resources/dynamic_tables.yaml` defines `dynamic_table_refresh_succeeded` / `dynamic_table_refresh_failed` gauges over `INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY`. These describe Lakehouse dynamic-table refresh state, not the streaming Flink jobs themselves.

### Feature flags

The Confluence page lists 7 flags FD owns that gate behavior across the 9 IM jobs (see Identity Materializer Flow tab). At least one (`SAAS_IDENTITY_DIP_SKIP_CONTENT_DEDUP_ENABLED`) is exposed via the Flink UDF `IsMaterializerEnabled` registered as both `is_materializer_enabled` and `skip_content_dedup_enabled` in `create_udfs.sql`.

### CI/CD (Jenkins)

`cicd/Jenkinsfile`:

- `JIRA_PROJECT = "SAASFD"`, `NOTIFICATION_CHANNEL = "proj-eng-iai-cicd"`, `DIP_NAME = 'saas-identity-dip'`, `ORG_NAME = 'sailpoint-core'`.
- Stages:
  1. Checkout `main`.
  2. `atlasDataBuildTransformers` — builds streaming, lakehouse, fire, flink_udf transformers.
  3. `atlasDataDeployWorkflow` — passes `lakehouse_tag`, `fire_tag`, `udf_build` (S3 path), `flink_udf_tag`, `streaming_tag` (all set to `RELEASE_TAG` = `BUILD_NUMBER`).
  4. `atlasDataCleanup`.
  5. `atlasDataCreateDeployTicket` — creates a deploy ticket against `JIRA_PROJECT` (`SAASFD`) using the `airflow2/release/latest/saas_identity_dip/` prefix.
- `post` actions send Slack success/failure messages to `proj-eng-iai-cicd`.

`cicd/PRB.Jenkinsfile` exists for PR builds (separate file; not deeply analyzed here).

`cicd/README.md` documents that `Jenkinsfile.jinja` and `PRB.Jenkinsfile.jinja` extend a copier template (`Jenkinsfile_template.j2`, `PRB.Jenkinsfile_template.j2`), with overridable jinja blocks: `header`, `agent`, `environment`, `additionalenv`, `checkoutscm`, `build_transformers`, `before_buildtransformers`, `after_buildtransformers`, `build_transformer_tests`, `before_deployairflow`, `deployairflow`, `after_deployairflow`, `cleanup`, `after_cleanup`, `pushtag`, `before_deployticket`, `deployticket`, `after_deployticket`, `post`.

</details>

---

<details open>
<summary id="tab-risks-and-review-checklist"><strong>Tab: Risks And Review Checklist</strong></summary>

## Risks And Review Checklist

### Risks

- **Hand-written dbt-Flink models** — There is no schema-driven generator. Drift between source-topic schemas and dbt `sources.yml` columns is a real risk; only PR review catches it.
- **Per-env configs are the source of truth for rollout** — Forgetting to bump a `<job>_checkpoint_version` after a logic change can let Flink restore from an incompatible savepoint, or vice versa. With 12+ region files per env (dev/internal/prod, plus stg/prd duals), partial bumps are easy to ship.
- **`group_22` Morgan Stanley variants** — Several jobs are duplicated with `job_suffix: 'group_22'`. Behavior for those tenants depends on independent `_group_22_*_enabled`/`_checkpoint_version`/`_parallelism` knobs. Edits intended to be global must touch both variants.
- **Single Identity template** — All Identity Materializer jobs share one Airflow template. Misformatted YAML or a bad jinja substitution can fail every job in the family at once.
- **Feature-flag gating across 9 jobs** — 7 flags interact with these jobs. Toggling them in production without a clear matrix is risky; some flags affect dedup behavior and segment materialization, which feeds the two product topics consumed by Search Lite and `sp_materializer`.
- **No in-repo Soda/Reconciler equivalent for the streaming path** — Quality and replay equivalents (analogous to `entity-live-dip`'s Soda + Reconciler) are not present in `saas-identity-dip`'s streaming path. Data-quality and replay validation likely lives elsewhere or is operational (see Unknowns).
- **Standalone Data Segments materializer (Java)** is deployed and tagged separately (`flink_udf_tag` plus the `udf_build` S3 path). Coordinating UDF jar changes with dbt model changes that depend on those UDFs requires explicit version coordination.

### Review checklist

For any PR touching the streaming Identity Materializer:

1. **Topic and key**
   - Does the sink config use the correct product topic (`segmented_identity`, `search_lite_identity_v1`, or the named intermediate topic)?
   - Is `primary_key` consistent with the Kafka key contract (`tenantId#identityId` or the documented variant)?
2. **Dedup / join correctness**
   - Are `*_source_keyed.sql` files using `ROW_NUMBER() OVER (PARTITION BY ...)` with the correct partition columns and `procTime DESC NULLS LAST`?
   - Are joins consuming keyed sources only, per the streaming README convention?
3. **Per-env config coverage**
   - Did the PR bump `<job>_checkpoint_version` in every region file under `pipelines/dags/saas_identity_dip/identity/configs/{dev,internal,prod}/<region>.yml` that serves the changed job?
   - Did it touch `_group_22_*` variants where applicable?
   - Are `_enabled` flags intentional (no accidental global enable/disable)?
4. **Headers and metadata**
   - Are `headers` (and `kafka_key`, `ts`, `procTime`) declared in `sources.yml` consistently with how the dbt model uses them?
   - For sinks that explicitly set headers (e.g., `SEGMENTED_IDENTITY_DEDUP_SINK` calls `build_headers('pod', pod, 'org', org, 'tenantId', tenantId, 'partitionKey', pk)`), does the change preserve those headers downstream?
5. **UDF coupling**
   - If new Flink UDFs are added in `transformers/flink_udf/src/main/java/com/sailpoint/udf/**`, is `transformers/streaming/dbt/macros/create_udfs.sql` updated and is `flink_udf_tag` / `udf_build` going to roll out together with the streaming change?
6. **Feature flags**
   - Which of the 7 Identity Materializer flags does the change interact with?
   - Are LaunchDarkly defaults / segment targeting aligned with the rollout plan?
7. **Operational visibility**
   - Are Grafana panels and the IDN DIP STREAMING dashboard sufficient to monitor the change (e.g., per-job parallelism changes, mini-batch settings)?
   - Will checkpoint state size or RocksDB pressure change meaningfully?
8. **Tenant-scope blast radius**
   - Does the change risk cross-tenant leakage in any join (Search Lite and segmentation are tenant-scoped by `tenantId#identityId`)?

</details>

---

<details open>
<summary id="tab-comparison-to-entity-live-dip"><strong>Tab: Comparison To entity-live-dip</strong></summary>

## Comparison To entity-live-dip

| Dimension | `saas-identity-dip` (streaming path) | `entity-live-dip` |
| --- | --- | --- |
| Source of truth | Hand-written dbt-Flink models per job in `transformers/streaming/dbt/models/entity_models/{common,identity}/<job>/`. | Per-entity JSON schema in `transformers/streaming/schema_converter/schemas/`, with generators producing `source.yml`, model SQL, pipeline YAML, checkpoint config, Soda checks. |
| Generation tool | None. No `schema_converter`. No `make autogen_all`. No autogen drift gate in CI. | `transformers/streaming/schema_converter` plus `make autogen_all`, blacklist-aware, with CI dirty-tree gate (`.github/workflows/validate-autogen.yml`). |
| Sinks | Kafka-to-Kafka via `connector: upsert-kafka` (intermediate Kafka topics + two final product topics: `segmented_identity`, `search_lite_identity_v1`). | Snowflake live tables via Snowpipe Streaming: `<table_name>_history`, `<table_name>_live`, `<table_name>` view. |
| Airflow templates | One central `streaming_v1` template at `pipelines/dags/saas_identity_dip/identity/template.yml` listing every Identity Materializer Flink job. | Many per-entity `streaming_v1` templates under `pipelines/dags/entity_live_dip/entity_live_dags/*_template.yml`, plus dedicated stateful changelog templates. |
| Per-env config shape | Per-region YAML per env with `<job>_checkpoint_version`, `<job>_parallelism`, `<job>_enabled` (and `_group_22_*` variants). | Per-env config YAMLs with `<schema>_checkpoint_version` and `dag_label` entries. |
| Quality framework | No in-repo Soda / `_manifest.json` equivalent for the streaming path. | Soda autogen (`transformers/fire/src/soda_quality_checks/auto_generated_checks/**`), `_manifest.json` hashing, validator in CI, plus team Soda DAGs (e.g., `arcadia`, `fastdata`, `lanai`, `rap`, `rcp`). |
| Replay/repair | No Reconciler equivalent observed in repo. Replay would have to come from upstream producers or operational tooling outside this repo (see Unknowns). | Reconciler DAG, Snowflake stored procedures, Fire job runner (`base_event_reconciler.py`) reading `EVENT_DATA.REPLAY_REQUEST` and calling IDN APIs. |
| Migrations | Not part of this repo's streaming path. | Snowflake migrations under `pipelines/dags/entity_live_dip/entity_live_dags/migrations/{procedures,active,archived}` with a Flyway-style versioning convention. |
| Stateful changelog tables | Not applicable (no Snowflake live-table sinks). Per-tenant collapsing is implemented via the Java `DataSegmentsByTenantMaterializerJob`. | Dedicated stateful changelog templates and UDFs (`map_diff_changelog`, `array_diff_changelog`) for collection-grain delta semantics. |
| CI controls | Jenkins build/deploy via `cicd/Jenkinsfile` with `streaming_tag`, `lakehouse_tag`, `fire_tag`, `flink_udf_tag`. PRB pipeline via `cicd/PRB.Jenkinsfile`. No GitHub Actions autogen gate observed in repo. | Pre-commit + GitHub Actions autogen gate plus Jenkins deploy that publishes the Atlan data product. |
| Code owners | `* @sailpoint-core/fast-data` (single team). | Multiple SailPoint teams via `.github/CODEOWNERS`. |
| Mental model | Stream-first, tenant-scoped enrichment publishing two product Kafka topics consumed by Search Lite and `sp_materializer`. | Schema-first, contract-driven materialization into Snowflake live tables for analytical query and reconciliation. |

Headline distinctions to keep in mind during review:

- **Hand-written models, not generated.** Reviewers cannot rely on autogen + manifest hashes to catch contract drift.
- **Kafka-to-Kafka product topics.** The streaming Identity Materializer terminates in Kafka, not Snowflake; downstream consumers (`sp_materializer`, Search Lite) treat those topics as the contract.
- **No Soda / Reconciler equivalent in the streaming path.** Quality and replay are not in-repo.
- **One central Airflow template** for all Identity Materializer Flink jobs versus a template-per-entity model in `entity-live-dip`.

</details>

---

<details open>
<summary id="tab-recommended-next-steps"><strong>Tab: Recommended Next Steps</strong></summary>

## Recommended Next Steps

1. **Trace one full PR** that bumps a single job's behavior (e.g., `IDENTITY_LITE_SINK`) end-to-end across `template.yml`, all per-env configs, and the dbt model staging chain. Use it as a canonical example for code review training.
2. **Build a job ↔ topic ↔ env-config matrix** from `template.yml` plus the `connector_properties.topic` of each sink and the per-env `_checkpoint_version` / `_enabled` keys. This shrinks the chance of partial rollouts.
3. **Document the `group_22` Morgan Stanley split** — owners, what guarantees it gives, whether it can ever be retired, and the explicit test plan when global jobs change.
4. **Catalog the Flink UDFs** (`transformers/flink_udf/src/main/java/com/sailpoint/udf/**` plus `create_udfs.sql`) and map each to the dbt models that call it. UDF jar version drift versus dbt model expectations is currently silent.
5. **Decide on a quality story for the streaming path.** Either onboard Soda-style checks (with a manifest gate similar to `entity-live-dip`) or document the current quality posture (where it lives, who owns it, what SLO it meets).
6. **Decide on a replay/repair story.** If `entity-live-dip`'s Reconciler model is the desired posture, design an equivalent for the Kafka-to-Kafka path; if not, document the operational replay path (re-emit from upstream, savepoint replay, etc.).
7. **Investigate the Lakehouse-side `transformers/lakehouse/dbt/**` and `transformers/streaming/metrics/resources/dynamic_tables.yaml`** to confirm the Snowflake side of Identity (e.g., `identity_amm`, `identity_amm_aggregate` lakehouse sub-DAGs) and how they relate to the streaming product topics.
8. **Stand up the local dev loop** end-to-end (Docker Flink + Kafka, `make deploy-models MODEL_ARG=tags`) and validate one job (e.g., `account_dedup`) against synthetic Kafka input to give reviewers a reproducible smoke test.
9. **Companion canvas** — once the above is solid, build a visual canvas (`canvases/saas-identity-dip-deep-dive.canvas.tsx`) to show the 9-job graph, source/intermediate/product topics, and per-env knobs.

</details>

---

<details open>
<summary id="tab-unknowns"><strong>Tab: Unknowns</strong></summary>

## Unknowns

The following items were not verified in this pass and should be confirmed before treating them as fact:

- **Exact role of `transformers/fire`** in the streaming Identity Materializer flow. The directory exists with `Makefile`, `requirements.txt`, `src/main.py`, `src/functions/`, but its specific responsibilities for this DIP were not inspected. `fire_tag` is passed to `atlasDataDeployWorkflow` in `cicd/Jenkinsfile`, so it deploys, but its runtime usage in the Identity Materializer was not confirmed.
- **Exact role of `transformers/lakehouse`** relative to the streaming Identity Materializer. It is a separate dbt project (Snowflake side) and likely supports the `identity_amm` / `identity_amm_aggregate` lakehouse sub-DAGs under `pipelines/dags/saas_identity_dip/lakehouse/`, but the dependency from streaming product topics to Lakehouse models was not traced.
- **Quality framework for the streaming path.** No in-repo Soda checks, manifest, or autogen validators were observed for the streaming dbt-Flink models. The Confluence page hints at "SavePoints / Checkpoint validation" and "Data checks" but the section is short and the tooling location was not identified.
- **Replay/Reconciler equivalent.** No equivalent of `entity-live-dip`'s Reconciler was found in this repo. Whether replay is handled by upstream producers, savepoint replay, or out-of-band tools was not confirmed.
- **Final `search_lite_identity_v1` writer.** `IDENTITY_LITE_SINK.sql` writes to `search_lite_identity_intermediate`, and there is an `identity-lite-filtered` directory whose sink behavior (whether it produces `search_lite_identity_v1` directly) was not opened in this pass.
- **`.github` CI controls.** The repo does not contain a `.github/` directory in the local clone, so there is no GitHub Actions / branch-protection / CODEOWNERS configuration beyond the top-level `CODEOWNERS` file. Whether branch protection is enforced elsewhere (organization-level rules, Bitbucket-style settings, etc.) was not verified.
- **Confluence-only assertions** that were not cross-checked in code: the precise list of feature flags (taken verbatim from Confluence), the exact statement that the `sp_materializer` service consumes `segmented_identity` and forwards to full search, and the LaunchDarkly environment names. These should be re-verified before being used as authoritative inputs to a runbook.

</details>
