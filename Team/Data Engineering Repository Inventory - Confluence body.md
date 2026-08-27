# Data Engineering Repository Inventory (GitHub-Verified) — Aug 2026

*Source: [Confluence](https://sailpoint.atlassian.net/wiki/spaces/data/pages/5502534242/Data+Engineering+Repository+Inventory+GitHub-Verified+Aug+2026) · [tiny link](https://sailpoint.atlassian.net/wiki/x/YgL6RwE) · Last synced from Confluence 2026-08-27.*

**What this page is.** A GitHub-API-verified inventory of every repository owned by, or granted to, the Data Engineering / Data Platform team, generated 8/27/2026.

It is a **companion** to [Data Engineering Components & Services](https://sailpoint.atlassian.net/wiki/spaces/data/pages/4654104666), not a replacement. That page is broader (Jira boards, rosters, self-service maturity, service ownership) and carries a notice that its content is ROVO/Cursor-generated and unreviewed. This page covers only the repo-inventory question, and every row was checked against the GitHub API. **The other page was not modified.**

## Headline numbers

| Bucket | Count | What it means |
| --- | --- | --- |
| **Data Engineering estate** | **58** | DE is the primary or co-primary code owner, or holds the only team grant |
| — DE sole primary owner | 32 | Root `*` rule in CODEOWNERS names only DE teams |
| — DE co-primary owner | 12 | Root `*` rule names DE _and_ a product team |
| — No CODEOWNERS root rule | 14 | DE team grant only; ownership not declared in-repo |
| **Platform access only** | **26** | A DE team has repo access, but another team owns the code |
| **Total with a DE signal** | **84** | Union of DE team grants and DE mentions in CODEOWNERS |

**Team grant ≠ ownership.** This is the single most important correction. The `dipo` team is the DIP _platform_ team, so it holds access to many repos owned by consumer product teams (`scrum-sage`, `scrum-salt`, `scrum-wasabi`, devops/SRE, and others). Counting team grants alone overstates the DE estate by 26 repos. Read the CODEOWNERS column, not the grant column, to answer "who owns this?"

## Where ownership actually lives

There is no single GitHub team to read this off. `sailpoint/data-platform` is a **people-only team** — 25 members, **0 repos**. Repo ownership is spread across four teams, each existing in more than one org:

| Team | Orgs | Repos granted | Role |
| --- | --- | --- | --- |
| `dipo` | sailpoint (40), sailpoint-core (17) | 54 | DIP platform umbrella — broadest grant, includes consumer DIPs |
| `scrum-data-platform` | sailpoint (10), sailpoint-core (16) | 26 | Streaming / DIP core; most current work |
| `fast-data` | sailpoint (15), sailpoint-core (5) | 20 | Flink DataStream, IDA/IAI pipelines, materializers |
| `scrum-data-governance` | sailpoint (9) | 9 | EDM, ACL, lakehouse, data catalog |

## 1. DE sole primary owner (32)

| Repo | Org | CODEOWNERS root rule | Team grants | Last push |
| --- | --- | --- | --- | --- |
| `aperture-core` | sc | dipo | dipo | 2026-03-20 |
| `aperture-graph` | sc | dipo | dipo | 2026-04-15 |
| `aperture-search` | sc | dipo | dipo | 2025-12-17 |
| `connectivityinsights-ingress-dip` | sc | dipo | dipo | 2026-08-24 |
| `data-platform-almighty-agents` | sc | scrum-data-platform | scrum-data-platform | 2026-08-26 |
| `data-platform-cli` | sc | scrum-data-platform | scrum-data-platform | 2026-07-01 |
| `data-platform-tasks` | sc | dipo | dipo | 2026-03-06 |
| `data-platform-tasks-dip` | sc | scrum-data-platform | scrum-data-platform | 2026-08-25 |
| `dependency-inference-graph` | sc | scrum-data-platform | scrum-data-platform | 2026-06-30 |
| `dp-activity-data-dip` | sc | scrum-data-platform | scrum-data-platform | 2026-08-19 |
| `dp-entity-live-icehouse-dip` | sc | scrum-data-platform | scrum-data-platform | 2026-08-26 |
| `dp-iceberg-poc` | sc | dipo | dipo | 2026-02-26 |
| `dp-managed-services-dip` | sp | scrum-data-platform | dipo, scrum-data-platform | 2026-08-25 |
| `dp-pulp-services-dip` | sc | dipo | dipo | 2026-08-18 |
| `entity-mach5-dip` | sc | dipo | dipo | 2026-04-21 |
| `flink-connector-snowflake` | sp | dipo | dipo, fast-data, scrum-data-platform | 2026-08-07 |
| `flink-entity-topics-dip` | sc | dipo | dipo | 2026-07-09 |
| `mcp-curator` | sc | dipo | dipo | 2026-08-05 |
| `pointed-lookups-dip` | sc | dipo | dipo | 2026-04-21 |
| `saas_lakehouse_acl` | sp | scrum-data-governance | scrum-data-governance | 2026-08-26 |
| `saas_lakehouse_edm` | sp | scrum-data-governance | scrum-data-governance | 2026-08-26 |
| `saas-airflow-utils` | sp | dipo | dipo, scrum-data-platform | 2026-08-26 |
| `saas-data-platform-base-images` | sp | scrum-data-governance, scrum-data-platform | dipo, fast-data, scrum-data-governance, scrum-data-platform | 2026-08-26 |
| `saas-dip-template` | sp | dipo | dipo | 2026-08-20 |
| `saas-entitlement-materializer-dip` | sc | scrum-data-platform | scrum-data-platform | 2026-08-26 |
| `saas-flink-datastream-dip` | sc | scrum-data-platform | fast-data, scrum-data-platform | 2026-08-26 |
| `saas-identity-dip` | sc | scrum-data-platform | fast-data, scrum-data-platform | 2026-08-25 |
| `saas-idn-backfill` | sc | scrum-data-platform | scrum-data-platform | 2026-08-26 |
| `saas-idn-dip` | sp | scrum-data-platform (both orgs) | dipo, fast-data, scrum-data-platform | 2026-08-26 |
| `saas-role-lite-dip` | sc | scrum-data-platform | fast-data, scrum-data-platform | 2026-08-24 |
| `saas-role-lite-materializer-dip` | sc | scrum-data-platform | scrum-data-platform | 2026-06-04 |
| `simple-expectations` | sc | dipo | dipo | 2026-04-20 |

## 2. DE co-primary owner (12)

The root `*` rule names a DE team alongside a product team. Changes here need review from both.

| Repo | Org | CODEOWNERS root rule | Team grants | Last push |
| --- | --- | --- | --- | --- |
| `data-platform-admin-dip` | sp | saas-ips-fr8, scrum-data-platform, scrum-platform-data-presentation | dipo, scrum-data-governance, scrum-data-platform | 2026-08-26 |
| `entity-live-dip` | sp | dipo, scrum-data-governance, scrum-data-platform, scrum-wasabi | dipo, scrum-data-governance, scrum-data-platform | 2026-08-26 |
| `harbor-pilot-telemetry-dip` | sc | moonshot, scrum-data-platform | scrum-data-platform | 2026-08-17 |
| `ida-airflow` | sp | scrum-data-governance, scrum-sage, scrum-salt, scrum-tarragon | dipo, scrum-data-governance, scrum-data-platform | 2026-08-26 |
| `ida-harvesters` | sp | scrum-data-governance, scrum-wasabi | scrum-data-governance | 2026-08-24 |
| `platform-core-dip` | sp | DIPO, notifications-and-approvals-services | dipo, scrum-data-platform | 2026-08-21 |
| `saas-data-platform-utils` | sp | platform-devex, saas-ips-fr8, scrum-data-governance, scrum-data-platform | scrum-data-governance, scrum-data-platform | 2026-08-26 |
| `saas-dbt-core` | sp | dipo, scrum-data-governance, scrum-wasabi | dipo, scrum-data-governance, scrum-data-platform | 2026-08-24 |
| `saas-entity-topic-tenant-deleter` | sp | platform-devex, scrum-data-platform | scrum-data-platform | 2026-07-23 |
| `saas-mis-dip` | sc | scrum-account-and-identity-management, scrum-data-platform | fast-data, scrum-data-platform | 2026-08-25 |
| `saas-saf-dip` | sc | ds-dp-mix, scrum-data-platform | scrum-data-platform | 2026-08-26 |
| `tenant-access-controls` | sc | scrum-data-platform, scrum-platform-data-presentation | scrum-data-platform | 2026-08-20 |

## 3. DE grant, no CODEOWNERS root rule (14)

These have a DE team grant but no `*` rule declaring an owner, so PRs get no automatic reviewer. **Adding a CODEOWNERS root rule to the active ones is the clearest cleanup this inventory suggests.**

| Repo | Org | Team grants | Last push |
| --- | --- | --- | --- |
| `certification-generation-dip` | sc | stale/none — see caveats | 2026-08-26 |
| `client-management-service-dip` | sp | dipo | 2026-02-19 |
| `data-platform-playground` | sp | dipo | 2024-04-15 |
| `data-test-dip` | sp | scrum-data-governance | 2024-12-09 |
| `docker-lineage-dip` | sp | dipo | 2025-04-11 |
| `flink-connector-cassandra` | sp | dipo | 2025-04-25 |
| `iai-ops` | sp | dipo, scrum-data-governance | 2026-08-25 |
| `ida-roleinsights-dip` | sp | dipo, fast-data | 2026-08-10 |
| `identity-graph-dip` | sp | dipo | 2026-08-26 |
| `pa-data-eng-dip` | sp | scrum-data-governance | 2026-08-25 |
| `saas-airflow` | sp | dipo | 2026-07-21 |
| `saas-idn-dip-streaming-demo` | sp | fast-data | 2026-03-09 |
| `saas-mis-dip` | sp | fast-data | 2024-12-17 |
| `shared-signals-dip` | sp | dipo, fast-data | 2026-08-24 |

## 4. Platform access only — owned by other teams (26)

A DE team (almost always `dipo`) holds access because DE runs the DIP platform, but the code belongs to the product team in the CODEOWNERS column. **Route functional questions on these to the owning team, not to Data Engineering.**

| Repo | Org | Actual owner (CODEOWNERS root) | DE grant | Last push |
| --- | --- | --- | --- | --- |
| `entitlement-application-correlation-dip` | sc | team-trident | dipo | 2026-07-29 |
| `flink-apps` | sp | scrum-wasabi | dipo | 2026-05-07 |
| `gitops-iai` | sp | devops-fte-r-w | dipo | 2026-08-26 |
| `gitops-k8s` | sp | devops-fte-r-w | dipo, fast-data, scrum-data-platform | 2026-08-26 |
| `gov-violation-dip` | sc | scrum-sod | dipo | 2026-08-26 |
| `gulfstream` | sp | scrum-wasabi | dipo | 2025-10-20 |
| `ida-airolefingerprinter-dip` | sp | scrum-sage, scrum-salt | dipo, fast-data | 2026-08-26 |
| `ida-arrheuristic-dip` | sp | scrum-sage | dipo, fast-data | 2026-08-11 |
| `ida-certrecommenderfeatures-dip` | sp | scrum-sage, scrum-salt | dipo, fast-data | 2026-08-26 |
| `ida-common-dip` | sp | scrum-sage, scrum-salt | dipo, fast-data | 2026-08-24 |
| `ida-data-common` | sp | scrum-wasabi | dipo | 2023-08-03 |
| `ida-data-processing` | sp | scrum-sage, scrum-salt, scrum-tarragon, scrum-wasabi | dipo | 2026-08-26 |
| `ida-features-dip` | sp | scrum-sage | dipo | 2026-08-12 |
| `ida-lakehouse` | sp | scrum-wasabi | dipo | 2026-07-29 |
| `ida-lowsimilarityoutliers-dip` | sp | scrum-sage, scrum-salt | dipo | 2026-08-26 |
| `ida-ops` | sp | periscope, saas-ips-fr8, saas-ips-keel, saas-ips-ramp, saas-ips-sigma | dipo | 2026-08-26 |
| `ida-peergroupsingest-dip` | sp | scrum-sage, scrum-salt | dipo, fast-data | 2026-08-25 |
| `jenkins-deployment-pipelines` | sp | saas-devops-kaizen-fte | dipo | 2026-08-25 |
| `provisioningpolicyrecommender-dip` | sp | scrum-tarragon | scrum-data-governance | 2026-05-23 |
| `saas-access-profile-dip` | sc | scrum-palm | fast-data | 2026-08-25 |
| `saas-datapump` | sp | scrum-wasabi | dipo | 2026-08-21 |
| `saas-dbt-flink-core` | sp | scrum-wasabi | dipo, fast-data | 2026-06-26 |
| `saas-grafana` | sp | devops-fte-r-w, periscope | dipo | 2026-08-26 |
| `saas-pagerduty` | sp | devops-fte-r-w | dipo | 2026-01-05 |
| `sp-domain-events-materializer` | sp | scrum-platform-data-presentation | fast-data | 2025-09-16 |
| `sparsejaccard-dip` | sp | scrum-sage | dipo, fast-data | 2026-08-20 |

## 5. Deltas vs. the Components & Services page

Recorded here for whoever next refreshes that page. **No edits were made to it.**

### 5.1 DE-owned repos it does not list (15)

Almost all of it is newer `sailpoint-core` / `scrum-data-platform` work:

`saas-saf-dip` · `saas-entitlement-materializer-dip` · `saas-role-lite-materializer-dip` · `dp-entity-live-icehouse-dip` · `dp-activity-data-dip` · `data-platform-tasks` · `data-platform-tasks-dip` · `data-platform-almighty-agents` · `dependency-inference-graph` · `dp-pulp-services-dip` · `mcp-curator` · `connectivityinsights-ingress-dip` · `platform-core-dip` · `saas-data-platform-utils` · `saas-entity-topic-tenant-deleter`

It also omits two consumer DIPs now granted to `sailpoint-core/dipo`: `entitlement-application-correlation-dip` (team-trident) and `gov-violation-dip` (scrum-sod).

### 5.2 Listed repos that no longer exist (11)

All return HTTP 404: `ida-arrclassifier-dip` · `ida-arrclassifierexport-dip` · `saas-flink-common` · `ida-materializer` · `ida-peergroups-dip` · `ida-identitygraph-dip` · `ida-autorm-dip` · `privileged-entitlement-discovery-dip` · `platform-tools` · `my-sailpoint-dip` · `sailpoint/application-discovery-dip`

### 5.3 Three factual corrections

| Claim on that page | Verified reality |
| --- | --- |
| `scrum-data-platform` is an "umbrella GitHub team… **No dedicated repos**" | It has **10 repos in sailpoint and 16 in sailpoint-core**. It is where most current work lives — this is the most misleading line on the page. |
| `sp/dipo` has **44 repos** | The API returns **40**. The gap is 3 deleted repos plus `saas-workflows-dip`, now owned by `sailpoint-core/platform-forms-and-workflows`. |
| A "Cross-Org Repos" section lists 5 repos existing in both orgs | **Artifact of org transfers.** `tenant-access-controls`, `connectivityinsights-dip`, `source-onboarding-dip`, `genai-dip` and `application-discovery-dip` were moved to `sailpoint-core`; the GitHub API silently follows the rename redirect, so the old path still resolves. Only `saas-mis-dip` genuinely exists in both orgs — and the `sailpoint` copy has been dead since Dec 2024. |

### 5.4 Repos it attributes to DE that DE does not own

Verified against CODEOWNERS: `saas-machine-account-detection-dip` → `scrum-tarragon` · `ida-identity-history-transform-dip` → `scrum-sage`/`scrum-salt` · `ida-data-api` → `scrum-sage`/`scrum-salt` · `connectivityinsights-dip`, `source-onboarding-dip`, `application-discovery-dip` → `code-owners-connectivity-insights` · `genai-dip`, `saas-management-dip` → `ADI` · `role-propagation` → `scrum-lanai-palm` · `saas-nhi-dip` → `scrum-account-and-identity-management` · `saas-ciem-dip`, `cam-analytics`, `sam-cam`, `sam-cam-fed-dev` → `cam-data-engineering` · `ida-outliers-live-dip` → `scrum-sage` · `saas-kafka-artifacts` → NHI/platform-devex/ARP · `release-data` → `sailpoint-ips/ci-cd`

## 6. Housekeeping candidates

**Not archived, but no push in 12+ months** — worth an archive decision:

| Repo | Org | Last push |
| --- | --- | --- |
| `ida-data-common` | sp | 2023-08-03 |
| `data-platform-playground` | sp | 2024-04-15 |
| `data-test-dip` | sp | 2024-12-09 |
| `saas-mis-dip` | sp | 2024-12-17 |
| `docker-lineage-dip` | sp | 2025-04-11 |
| `flink-connector-cassandra` | sp | 2025-04-25 |

## 7. Method — how to reproduce

Two independent signals were unioned, then reconciled. Requires `gh` authenticated with `read:org` + `repo`.

**Signal A — team grants.** Enumerated for all eight team/org combinations (`dipo`, `scrum-data-platform`, `scrum-data-governance`, `fast-data` × `sailpoint`, `sailpoint-core`; the `sailpoint-ips` variants return 404):

```shell
gh api "/orgs/$ORG/teams/$TEAM/repos?per_page=100" --paginate \
  --jq '.[] | "\(.full_name)\t\(.role_name)\t\(.archived)\t\(.pushed_at)"'
```

**Signal B — exhaustive CODEOWNERS sweep.** GitHub code search proved _not_ exhaustive (its index missed known hits), so instead every non-archived repo in all three orgs — 1,566 of them, 1,306 with a CODEOWNERS file — was fetched directly and parsed for both the full owner set and the root `*` rule:

```shell
gh api "/orgs/$ORG/repos?per_page=100&type=all" --paginate \
  --jq '.[] | select(.archived==false) | .full_name'

# then, per repo, first hit of .github/CODEOWNERS, CODEOWNERS, docs/CODEOWNERS
gh api "/repos/$REPO/contents/$PATH" --jq '.content' | base64 -d \
  | grep -v '^[[:space:]]*#' | awk '$1=="*"' \
  | grep -oE '@[A-Za-z0-9-]+/[A-Za-z0-9._-]+'
```

Cross-checked against the Components & Services page; every discrepancy in section 5 was re-verified individually against the API.

## 8. Caveats

1. **No admin-scope reverse lookup.** The authoritative `GET /repos/{repo}/teams` endpoint needs `admin:repo`; the token used had `read:org` + `repo`. A repo owned by DE through a team outside the four enumerated _and_ with no CODEOWNERS entry would not appear. The exhaustive sweep in Signal B makes this unlikely but not impossible.

2. **Case sensitivity.** CODEOWNERS entries are not case-consistent — `@sailpoint/DIPO` and `@sailpoint/dipo` both occur. Matching must be case-insensitive or rows will be silently dropped.

3. **Redirects mask transfers.** `gh api /repos/{old-path}` succeeds for transferred repos. Always compare the returned `.full_name` to what you asked for before concluding a repo exists at a given path.

4. **`certification-generation-dip` is genuinely ambiguous.** It is active (pushed 2026-08-26), now lives in `sailpoint-core`, has an empty CODEOWNERS file, appears in no DE team grant, and its top contributors are not DE engineers — yet the Components & Services page lists it under `sp/dipo`. The team grant appears to have been dropped during the org transfer. **Someone should confirm whether DE still owns this.**

5. **Point-in-time.** Counts are as of 27 Aug 2026. Re-run section 7 rather than trusting these numbers months from now.
