# Where to Run Builds

`dbt run` executes inside the warehouse: the SQL goes in, the tables stay
there. `glyf build` is different in a way that is easy to miss. It runs each
chart's query and **pulls the result rows to wherever the command is running**,
because drawing a chart needs the numbers. Where you run it is therefore a
data-movement decision, not just a scheduling one.

## What leaves the warehouse

A full build moves, for every chart, the complete result of its query — every
row and every selected column — over the network to the machine running glyf.
On a laptop that is your laptop. On a GitHub-hosted runner it is a virtual
machine GitHub owns: the rows transit and sit on infrastructure outside your
warehouse's control boundary, however briefly. For a public repository they
also sit in a workflow artifact anyone can download.

That is real egress. Whether it matters depends on the data and on what your
warehouse's boundary is supposed to guarantee, but it should be a decision
rather than a side effect of copying a workflow.

## The split: validate in CI, build inside the perimeter

glyf's execution modes were built for exactly this division:

| | Runs where | Moves | Proves |
| --- | --- | --- | --- |
| `glyf build --validate` | CI, on any runner | **zero rows** — each query is wrapped in `limit 0` | every query still runs, binds the columns its chart draws, and returns no [PII column](../reference/configuration.md#keeping-pii-out-of-a-chart) |
| `glyf build` | inside the perimeter | every chart's result | the dashboards, from live data |

A pull request asks whether the SQL still works, not what the numbers are this
morning. Validate mode answers that with no data moved: it writes the compiled
SQL and stops, no images, no data files, no export. It runs the PII policy
too, since a `limit 0` result still has its columns — "someone charted emails"
fails in CI with nothing fetched.

`dbt compile` is what produces the manifest glyf reads, and it needs a
warehouse connection for introspection but moves no table rows either. So the
CI job is:

```yaml title=".github/workflows/glyf-validate.yml"
name: glyf validate

on:
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --all-groups
      - run: uv run dbt compile --profiles-dir .
        env:
          DBT_ENV_SECRET_PASSWORD: ${{ secrets.WAREHOUSE_PASSWORD }}
      - run: uv run glyf build --validate
```

Nothing here uploads an artifact, because nothing here produced one.

Full builds run where the data is already allowed to be: an Airflow (or
Dagster, or cron) task on infrastructure inside the perimeter, or a
[self-hosted runner](https://docs.github.com/en/actions/hosting-your-own-runners)
in the same network. The shape is the same as the local workflow —
`dbt build`, `glyf build`, upload `target/glyf/site/` — with two rules about
the credential it runs under:

1. **A service role scoped to the marts the dashboards need.** Not the role a
   data engineer uses; not one that can read raw or staging layers. This is
   the primary control — glyf inherits the role's view and never widens it —
   so the role ceiling is what decides what can end up in an artifact at all.
2. **Short-lived credentials over long-lived secrets.** Prefer the platform's
   workload identity (GitHub Actions OIDC to a cloud role, an Airflow
   connection backed by a secrets manager, Snowflake key-pair auth with a
   rotated key) over a password pasted into a secret store and forgotten. The
   [dbt backend](./dbt-integration.md#execution) reads whatever `profiles.yml`
   resolves at run time, so the credential only has to exist for the length
   of the job.

The repository's own
[example workflow](../integrations/github-actions.md) does run a full build on
a GitHub-hosted runner. That is fine for what it builds — a DuckDB example
whose "warehouse" is a seed file checked into the same repository — and it is
not the pattern for a warehouse-backed project.

## Publishing only from the pipeline

A local build is the development loop: edit a `.ggsql` file, run
`glyf build`, look at the page. It produces an artifact that reflects *your*
warehouse view, on *your* machine, and it should stop there. Publishing — the
copy of `site/` to the bucket or host people read from — happens from the
pipeline, under the service role, and nowhere else.

The reasons are the same as for any deployable: the pipeline's output is
reproducible from a commit, it was built with the intended role rather than
whichever human ran it, and there is a log of what was published when. With
dashboards there is a third: a laptop build may contain rows that the service
role could not have read, and a bucket is a poor place to discover that.

## Building one artifact per audience

A published dashboard is a static file: one materialised view of the data,
identical for everyone who opens it. There is no per-viewer filtering inside
it and there cannot be. When two audiences may see different numbers, the
static-native answer is two artifacts, each built as the audience that will
read it.

```bash
glyf build --target finance --select tag:finance --output-dir artifacts/finance
glyf build --target exec    --select tag:exec    --output-dir artifacts/exec
```

Each flag does one thing, and only the first is a privacy control.

### `--target` names the identity, not the destination

`--target` is dbt's word: it selects one of the named blocks under `outputs`
in `profiles.yml`, and that block says which warehouse user or role the
queries run as.

<!-- glyf-docs: skip — a dbt profiles.yml, dbt's file rather than a glyf spec -->
```yaml title="~/.dbt/profiles.yml"
analytics:
  target: finance        # the default when nobody passes --target
  outputs:
    finance:             # <- what `--target finance` selects
      type: trino
      user: svc-glyf-finance
    exec:
      type: trino
      user: svc-glyf-exec
```

The warehouse then applies its own access control to that identity: an Open
Policy Agent or Ranger rule on Trino, a masking or row-access policy on
Snowflake, column-level security and IAM on BigQuery. None of that is
configured in dbt or in glyf — it is administered wherever the data lives, and
it applies to every client that connects, glyf included.

**That is where the restriction comes from.** A build running as
`svc-glyf-finance` receives only what that identity is allowed to read, so its
artifacts cannot contain anything more. glyf never widens access; it inherits
the ceiling of the credential it was given. It follows that per-audience
builds do nothing at all if every target connects as the same role — the
feature has teeth only where the warehouse policies exist.

`--target` requires `execution.backend: dbt`. With any other backend the
target would be ignored, and a build that silently ran as the wrong identity
is worse than one that refuses.

### `--select` decides which dashboards get built

A selector is `tag:NAME`, `name:NAME`, or a bare dashboard name, and it may be
repeated for a union. The build produces the matching dashboards and exactly
the charts they reference:

```yaml title="dashboards/executive.yml"
name: executive
title: Executive Dashboard
tags:
  - exec
```

This matters for more than tidiness. A chart whose table an audience's role
cannot read does not come back empty — the query fails, and a failed chart
fails the build. The audience that should not see a dashboard must not build
it. A selector that matches no dashboard is an error rather than an empty
site.

### `--output-dir` keeps the results apart

It writes `compiled/`, `charts/`, `dashboards/` and `site/` beneath the
directory you name, so one audience's build does not overwrite another's. It
is staging, not a boundary: a directory controls nothing, and what keeps the
two artifacts separate in the end is publishing them to different places
behind different access groups.

Within one output directory, a build always describes itself: artifacts from
a previous, wider build are removed rather than left to be published
alongside. Even so, give each audience its own directory — reusing one and
relying on the pruning is a single mistake away from the wrong thing.

### Putting it together

The pipeline runs the loop and publishes each result to its own location:

```bash
for audience in finance exec; do
  glyf build \
    --target "$audience" \
    --select "tag:$audience" \
    --output-dir "artifacts/$audience"
  aws s3 sync "artifacts/$audience/site" "s3://dashboards-$audience/" --delete
done
```

Each bucket is then fronted by the access group for that audience, as below.
The warehouse decides what each artifact could contain; the edge decides who
can open it.

## Storing the artifacts

A glyf site is a snapshot of query results at build time, rendered. It is
data, and the store it lands in should be treated the way the warehouse is —
not the way a marketing site's bucket is.

**Object storage with a policy, not a public bucket.** Block public access,
grant the pipeline role write and the edge read, and encrypt at rest with a
key you control (SSE-KMS on S3, CMEK on GCS) so that access to the bucket is
not the same as access to the bytes.

**An edge that authenticates.** The artifact contains no access control of its
own — [`toolbar.visibility: private` is a label](./data-exposure.md#what-glyf-does-not-do)
— so the edge is where "who may open this" lives. The patterns that fit static
files:

- **CloudFront with origin access control**, so the bucket is reachable only
  through the distribution, plus **signed cookies or signed URLs** issued by
  something that knows who the viewer is. Signed cookies suit a dashboard,
  which loads a page and then its chart files.
- **An identity-aware proxy** in front of any static host: Cloudflare Access,
  Google IAP, or your own. This is how glyf's own documentation was gated
  during its beta.
- A **VPN or private network** when the readers are already inside one.

**Versioning and a lifecycle.** Every build is a point-in-time copy of the
data. Bucket versioning keeps the history a "what did the dashboard say last
Tuesday" question needs; a lifecycle rule bounds how long old snapshots of
sensitive data persist. Decide the retention deliberately — a bucket that
keeps every build forever is a growing archive of your warehouse.

**Compiled SQL is recon material on a public site.** `site/compiled/*.sql`
carries fully-qualified table names and any literals in `WHERE` clauses; it is
published by default because it is metadata rather than data, which is the
right default for an internal site. On a public one, `export.row_data: exclude`
withholds it and `dashboard.show_compiled_sql: false` removes the drawer.

## Checklist

1. Does CI run `glyf build --validate`, and only that?
2. Does the full build run inside the perimeter, under a service role granted
   the marts and nothing else?
3. Is that credential short-lived, or at least rotated and stored in a secrets
   manager?
4. Does anything publish from a laptop? It should not.
5. Is the bucket private, encrypted with your key, and reachable only through
   an authenticating edge?
6. Is there a retention rule for old builds?
