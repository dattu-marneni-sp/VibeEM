// @ts-nocheck
import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Code,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

const entityTraceRows = [
  [
    "Schema",
    "transformers/streaming/schema_converter/schemas/machine_account_v1.json",
    "Declares required fields, uuid/date-time formats, object fields, and additionalProperties false.",
  ],
  [
    "Kafka source",
    "transformers/streaming/dbt/models/entity_live_tables/machine_account_v1/source.yml",
    "Reads topic pattern ^machine_account_v1(_backfill)?$, includes Kafka key, headers, timestamp, partition, offset, and topic metadata.",
  ],
  [
    "dbt model",
    "transformers/streaming/dbt/models/entity_live_tables/machine_account_v1/machine_account_v1.sql",
    "Adds standard headers, Kafka metadata, KAFKA_KEY primary key, TENANT_ID partitioning, and casts attributes to VARIANT.",
  ],
  [
    "Airflow/Flink job",
    "pipelines/dags/entity_live_dip/entity_live_dags/machine_account_template.yml",
    "Creates sf_live_machine_account_v1_<env>, depends on migrations, sets checkpoint name and Flink/Snowflake arguments.",
  ],
  [
    "Checkpoint config",
    "pipelines/dags/entity_live_dip/entity_live_dags/configs/**",
    "Adds machine_account_v1_checkpoint_version per dag_label; prod and staging currently show v2, some fed configs show v1.",
  ],
  [
    "Soda checks",
    "transformers/fire/src/soda_quality_checks/auto_generated_checks/machine_account_v1.yml",
    "Checks required fields, platform headers, deprecated iris format, uniqueness, booleans, timestamps, and id validity.",
  ],
];

const generatorRows = [
  [
    "SourceYMLGenerator",
    "generators/source_yml.py",
    "Adds standard Kafka metadata fields, sp-json parser config, earliest-offset startup, Confluent SASL settings, and topic-pattern.",
  ],
  [
    "DBTModelGenerator",
    "generators/dbt_model.py",
    "Builds Snowflake connector config, checkpoint env vars, KAFKA_KEY primary key, TENANT_ID partitioning, tags, header extraction, and VARIANT/ARRAY casts.",
  ],
  [
    "PipelineGenerator",
    "generators/pipeline.py",
    "Writes streaming_v1 YAML with Airflow metadata, migration dependency, global environment placeholders, job args, GROUP_ID, and checkpoint version binding.",
  ],
  [
    "CheckpointUpdater",
    "util/checkpoint.py",
    "Walks config YAML files and appends <schema>_checkpoint_version: v1 for each non-blacklisted schema and dag_label entry.",
  ],
  [
    "SodaChecksValidator",
    "validators/soda_checks.py",
    "CI-only validator that checks every eligible schema has a check file and that manifest hashes match current schema content.",
  ],
  [
    "SchemaComparator",
    "util/schema_diff.py",
    "Compare path exists for local versus remote JSON schema review; useful before assuming producer contract changes.",
  ],
];

const operationalRows = [
  [
    "Dynamic DAG expansion",
    "pipelines/dags/entity_live_dip/entity_live_dip_handler.py",
    "Delegates template expansion to saas_airflow_utils process_template_config over /opt/airflow/dags/entity_live_dip.",
  ],
  [
    "Migrations",
    "entity_live_dags/migrations/README.md",
    "Procedures run first, active versioned migrations run once, and most live pipelines depend on sf_live_event_data_migrations_<env>.",
  ],
  [
    "Metrics",
    "entity_live_dags/metrics_generation_template.yml",
    "Runs every 30 minutes, discovers job_name values from YAML, then calls run_flink_job_health in the Fire image.",
  ],
  [
    "Reconciler",
    "entity_live_dags/reconciler_template.yml",
    "Runs hourly, generates replay ids in Snowflake, then calls run_event_reconciler_api from the Fire image.",
  ],
  [
    "Fire job runner",
    "transformers/fire/src/job_runner.py",
    "Python Fire CLI exposes reconciler, Kafka replay, entity id dump, Flink health, and Soda check jobs.",
  ],
  [
    "Deploy",
    "cicd/Jenkinsfile",
    "Builds streaming and fire transformers, deploys workflows with streaming_tag/fire_tag/version, creates deploy ticket, publishes Atlan product.",
  ],
];

const ciRows = [
  [
    "Pre-commit",
    ".pre-commit-config.yaml",
    "Runs make -C transformers/streaming/schema_converter autogen_all on every commit.",
  ],
  [
    "GitHub Actions",
    ".github/workflows/validate-autogen.yml",
    "On schema, generated dbt, DAG, Soda, converter, or Makefile changes, installs Python 3.12 deps and runs make autogen_all.",
  ],
  [
    "Dirty tree gate",
    "validate-autogen workflow",
    "Fails if git status --porcelain is non-empty after generation, then prints remediation commands.",
  ],
  [
    "Soda freshness",
    "validators/soda_checks.py",
    "Fails when a schema has no check file or when the _manifest.json hash no longer matches.",
  ],
];

const riskRows = [
  [
    "BLACKLIST controls generation",
    "Several schemas are skipped by default. A schema can exist without full generated outputs if it is blacklisted.",
    "Always inspect WHITELIST/BLACKLIST before reviewing missing dbt, pipeline, checkpoint, or Soda changes.",
  ],
  [
    "Soda generation is not deterministic CI work",
    "make autogen_all validates Soda but does not call Bedrock to generate checks.",
    "After schema edits, run make autogen_soda_checks locally and commit generated YAML plus manifest changes.",
  ],
  [
    "Generated files are not source of truth",
    "Generated SQL/YAML headers explicitly warn against manual edits unless the schema is blacklisted.",
    "Prefer schema or generator fixes. Treat direct generated-file edits as exceptional.",
  ],
  [
    "Checkpoint version changes alter stream state",
    "Changing checkpoint version changes GROUP_ID and checkpoint path semantics.",
    "Require an operational reason, rollout plan, and awareness of backfill/replay behavior.",
  ],
  [
    "Migration version collisions",
    "Flyway-style V10.0.N files can collide across PRs.",
    "Check active migrations and recent PRs before merging.",
  ],
  [
    "Parser tolerates bad input",
    "source.yml sets sp-json.fail-on-missing-field false and ignore-parse-errors true.",
    "Use Soda and failed-row samples to catch producer drift that streaming may not hard-fail.",
  ],
];

const reviewRows = [
  ["Contract", "Does the JSON schema match the producer payload, required fields, nullability, uuid/date-time formats, object and array intent?"],
  ["Generated artifacts", "Are schema, source.yml, model SQL, pipeline YAML, checkpoints, Soda YAML, and manifest updated together?"],
  ["Grain", "Is KAFKA_KEY the correct live-table primary key, and are duplicate checks aligned with consumer expectations?"],
  ["Headers", "Are POD, ORG, TENANT_ID, and EVENT_ID present and checked? Missing headers often explain downstream gaps."],
  ["Types", "Are object and array fields intentionally VARIANT or ARRAY in Snowflake, not accidentally stringified?"],
  ["Operations", "Does the PR require checkpoint bumps, migrations, replay, backfill, or coordinated deploy timing?"],
  ["Quality", "Do Soda checks cover completeness, uniqueness, validity, freshness, and known producer format issues?"],
];

export default function EntityLiveDipDeepDive() {
  return (
    <Stack gap={22}>
      <Stack gap={8}>
        <H1>entity-live-dip Deep Analysis</H1>
        <Text tone="secondary">
          Implementation-level map for reviewing and operating SailPoint's schema-driven Kafka to Flink to Snowflake live table platform.
        </Text>
        <Row gap={8} wrap>
          <Pill active tone="info">schema contract</Pill>
          <Pill>generated dbt</Pill>
          <Pill>dynamic Airflow</Pill>
          <Pill>Flink checkpoints</Pill>
          <Pill>Soda quality</Pill>
          <Pill>Fire runtime</Pill>
        </Row>
      </Stack>

      <Grid columns={5} gap={12}>
        <Stat value="6" label="artifacts per generated entity" />
        <Stat value="5" label="autogen_all stages" tone="info" />
        <Stat value="2" label="transformer images: streaming + fire" />
        <Stat value="30m" label="metrics DAG cadence" />
        <Stat value="1h" label="reconciler DAG cadence" tone="warning" />
      </Grid>

      <Callout tone="info" title="Mental model">
        Review this repo as a contract and operations system. JSON schema is the source contract; generated dbt and Airflow move data; Soda, metrics, reconciler, migrations, and CI keep the platform trustworthy.
      </Callout>

      <H2>Worked Entity Trace: machine_account_v1</H2>
      <Table
        headers={["Layer", "File", "What it proves"]}
        rows={entityTraceRows}
        striped
      />

      <Grid columns="1fr 1fr" gap={16}>
        <Card>
          <CardHeader trailing={<Pill size="sm" tone="info">generated</Pill>}>dbt Model Behavior</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Model config uses <Code>materialized = 'table'</Code>, Snowflake connector, checkpoint env vars, <Code>KAFKA_KEY</Code> as primary key, and <Code>TENANT_ID</Code> partitioning.</Text>
              <Text tone="secondary" size="small">For machine_account_v1, <Code>attributes</Code> becomes <Code>ATTRIBUTES::VARIANT</Code>, which confirms object fields are preserved as semi-structured data.</Text>
            </Stack>
          </CardBody>
        </Card>

        <Card>
          <CardHeader trailing={<Pill size="sm" tone="warning">operational</Pill>}>Pipeline Behavior</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>The generated DAG depends on <Code>sf_live_event_data_migrations_{"{{ dag_label }}"}</Code> before starting the streaming job.</Text>
              <Text tone="secondary" size="small">Checkpoint version flows into both <Code>checkpoint_version</Code> and Kafka <Code>GROUP_ID</Code>, so version bumps are runtime events, not just config edits.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Generator Internals</H2>
      <Table
        headers={["Component", "Path", "Important behavior"]}
        rows={generatorRows}
        striped
      />

      <H2>CI And Deployment Controls</H2>
      <Grid columns="1fr 1fr" gap={16}>
        <Table
          headers={["Control", "Path", "What it enforces"]}
          rows={ciRows}
          rowTone={[undefined, undefined, "danger", "warning"]}
        />
        <Card>
          <CardHeader>Deploy Path</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text><Code>cicd/Jenkinsfile</Code> builds transformers, deploys workflows, creates a deployment ticket, and publishes the data product to Atlan.</Text>
              <Text tone="secondary" size="small">Deploy passes <Code>streaming_tag</Code>, <Code>fire_tag</Code>, and <Code>version</Code>. That matters because runtime DAGs call both the streaming and Fire images.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Runtime And Operations</H2>
      <Table
        headers={["Surface", "Path", "What to inspect during incidents"]}
        rows={operationalRows}
        striped
      />

      <Grid columns="1fr 1fr" gap={16}>
        <Card>
          <CardHeader trailing={<Pill size="sm" tone="info">Fire CLI</Pill>}>Reconciler Flow</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text><Code>BaseEventReconciler</Code> reads pending rows from <Code>EVENT_DATA.REPLAY_REQUEST</Code>, groups work by topic, processes topics in parallel, and batch-updates replay status.</Text>
              <Text tone="secondary" size="small">The API reconciler sends replay requests to service endpoints and expects HTTP 202. Failures are recorded as replay exceptions for retry/inspection.</Text>
            </Stack>
          </CardBody>
        </Card>

        <Card>
          <CardHeader trailing={<Pill size="sm" tone="warning">on-call</Pill>}>Metrics Flow</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>The metrics DAG scrapes active <Code>job_name</Code> values from DAG YAML, then calls <Code>run_flink_job_health</Code> with the Flink job manager URL.</Text>
              <Text tone="secondary" size="small">This means renamed or malformed job YAML can affect metrics visibility as well as runtime orchestration.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Risks And Gotchas</H2>
      <Table
        headers={["Risk", "Why it matters", "Review move"]}
        rows={riskRows}
        rowTone={["warning", "warning", "warning", "danger", "warning", "warning"]}
      />

      <Divider />

      <Grid columns="1fr 1fr" gap={16}>
        <Stack gap={10}>
          <H2>PR Review Questions</H2>
          <Table
            headers={["Area", "Question"]}
            rows={reviewRows}
            striped
          />
        </Stack>

        <Stack gap={12}>
          <H2>Best Next Analysis Steps</H2>
          <Card>
            <CardHeader>Learning path</CardHeader>
            <CardBody>
              <Stack gap={8}>
                <H3>1. Compare generated and blacklisted entities</H3>
                <Text size="small">This reveals where the platform is fully automated versus hand-maintained.</Text>
                <H3>2. Trace one incident path</H3>
                <Text size="small">Start with stale data, then inspect Airflow, Flink, Kafka offsets, Snowflake live/history, Soda samples, metrics, and reconciler replay.</Text>
                <H3>3. Walk a schema change PR</H3>
                <Text size="small">Check schema intent, generated artifacts, migration needs, checkpoint impact, and Soda freshness.</Text>
                <H3>4. Inspect dynamic_yaml_v1 templates</H3>
                <Text size="small">Non-generated templates such as metrics, reconciler, quality checks, and stateful changelog tables show platform extension patterns.</Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      </Grid>
    </Stack>
  );
}
