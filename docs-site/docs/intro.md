import Link from '@docusaurus/Link';

# glyf

`glyf` is an open-source visualisation build tool for data pipelines.

It lets analytics engineers define chart queries in `.ggsql`, connect them to analytical metadata, render the results into static chart artifacts, and publish dashboards without running a BI server. The first integration reads dbt artifacts and resolves dbt `ref()` and `source()` calls from `target/manifest.json`.

Charts are written in the [ggsql](https://ggsql.org) format: a SQL query followed by a few lines (`VISUALISE`, `DRAW`, `LABEL`) saying what to draw. glyf reads that format as is, so a ggsql chart is a glyf chart and `.ggsql` files get the format's editor support, and it adds chart types and interactions of its own, listed in the [syntax guide](./guides/visualisation-syntax.md).

Use it when you want visualisations to live beside analytical code, move through code review, and produce static output for internal reporting, client delivery, or lightweight documentation.

## Who it is for

- Analytics engineers who want dashboards versioned with analytical projects.
- Developers who prefer code review, CI, and static publishing over a running BI service for lightweight reporting.
- Teams that want generated dashboard artifacts they can inspect, archive, and publish anywhere.

## How it runs

`glyf` runs beside dbt rather than inside it. Nothing runs between builds, and each command hands its output to the next:

<ol className="buildSteps">
  <li>
    <code>dbt build</code>
    <p>dbt builds the tables and writes <code>target/manifest.json</code>.</p>
  </li>
  <li>
    <code>glyf build</code>
    <p>glyf reads the manifest, resolves each <code>ref()</code> and <code>source()</code>, runs each chart's query, and writes charts, dashboards and a static site under <code>target/glyf/</code>.</p>
  </li>
  <li>
    <code>glyf serve</code>
    <p>Previews the exported site locally. Publishing it is copying a folder.</p>
  </li>
</ol>

## Where to go next

<div className="docMap">
  <Link className="docMap__start" to="/docs/get-started/quickstart">
    <strong>Quickstart</strong>
    <span>Install the CLI, scaffold a starter chart in a dbt project, and build your first dashboard.</span>
  </Link>
  <Link to="/docs/guides/visualisation-syntax">
    <strong>Visualisation syntax</strong>
    <span>The chart block of a <code>.ggsql</code> file and the eight chart types.</span>
  </Link>
  <Link to="/docs/guides/dashboard-yaml">
    <strong>Dashboard YAML</strong>
    <span>Sections, column tracks, metric tiles and filters.</span>
  </Link>
  <Link to="/docs/examples/gallery">
    <strong>Examples</strong>
    <span>Four dbt projects with their rendered dashboards.</span>
  </Link>
  <Link to="/docs/reference/cli">
    <strong>CLI reference</strong>
    <span>Every command and flag, for scripts and CI.</span>
  </Link>
  <Link to="/docs/reference/configuration">
    <strong>Configuration</strong>
    <span>Every key of <code>glyf.yml</code> and its default.</span>
  </Link>
  <Link to="/docs/guides/data-exposure">
    <strong>What a published site exposes</strong>
    <span>Which rows a dashboard ships, and how to ship fewer.</span>
  </Link>
</div>
