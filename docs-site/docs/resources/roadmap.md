import Link from '@docusaurus/Link';

# Roadmap

What is coming, what is being considered, and what has shipped. Nothing here
has a date: `glyf` has one maintainer, and an item moves when it is ready. The
order is the priority.

<p className="roadmapJump">
  Looking for what changed in a version you already have? Every release is
  written up in the <Link href="https://github.com/glyf-data/glyf/blob/main/CHANGELOG.md">changelog</Link> and
  on the <Link href="https://github.com/glyf-data/glyf/releases">releases page</Link>.
</p>

## Planned

Vote with a 👍 on the issue. The most wanted go first.

<div className="roadmapGrid">
  <Link className="roadmapCard" href="https://github.com/glyf-data/glyf/issues/137">
    <strong>Pipeline alerts</strong>
    <span>Alert conditions declared in dashboard YAML, checked against the query results at build time, and sent to Slack or a webhook.</span>
    <em>Discuss on GitHub</em>
  </Link>
  <Link className="roadmapCard" href="https://github.com/glyf-data/glyf/issues/138">
    <strong>MCP server for agents</strong>
    <span>Let an AI agent list charts, read what a chart depends on, and see the effect of a change before proposing it.</span>
    <em>Discuss on GitHub</em>
  </Link>
  <Link className="roadmapCard" href="https://github.com/glyf-data/glyf/issues/139">
    <strong>Natural-language chart edits</strong>
    <span>Describe a change in words and get a reviewed pull request: the SQL diff, a passing build, and the visual diff attached.</span>
    <em>Discuss on GitHub</em>
  </Link>
</div>

## Being considered

Not committed to. Say so in [Discussions](https://github.com/glyf-data/glyf/discussions)
if one of these would change how you work.

<ul className="roadmapList">
  <li><strong>Watch mode.</strong> Rebuild charts and dashboards when a <code>.ggsql</code> file, a dashboard or <code>glyf.yml</code> changes.</li>
  <li><strong>Dashboard templates.</strong> Ready-made layouts to start from.</li>
  <li><strong>dbt docs on dashboards.</strong> Model, column and source descriptions from the manifest, shown beside the charts they describe.</li>
  <li><strong>Lineage.</strong> Which models and sources feed each chart, and which charts a changed model touches.</li>
  <li><strong>Richer layout.</strong> Grid and chart sizing beyond column tracks.</li>
  <li><strong>Publish helpers</strong> for common static hosts.</li>
  <li><strong>JavaScript packages.</strong> React components and a client for <code>bundle.json</code> are experimental in <Link href="https://github.com/glyf-data/glyf-js">glyf-js</Link>.</li>
</ul>

<p className="roadmapAsk">
  <strong>Missing something?</strong> Describe the chart or the workflow you need.{' '}
  <Link href="https://github.com/glyf-data/glyf/issues/new?template=feature_request.yml">Open a feature request</Link>
</p>

## Shipped

<ol className="roadmapTimeline">
  <li>
    <div className="roadmapTimeline__head">
      <Link className="roadmapVersion" href="https://github.com/glyf-data/glyf/releases/tag/v0.10.0">0.10.0</Link>
      <time dateTime="2026-09-23">23 September 2026</time>
    </div>
    <strong>Table chart, KPI tile, and a diff that says what moved</strong>
    <p><code>DRAW table</code> shows a query's rows as they are, sortable on the dashboard, and <code>DRAW kpi</code> shows one number with the change against a comparison value; neither is drawn, so <code>glyf diff</code> compares their rows and shows before and after side by side. For a bar, line or area chart the diff now says what happened the way the chart draws it, <code>bars: 12 gone (Partners)</code>, and draws this build's marks over the baseline's in grey. Underneath, glyf validates the chart block itself for every chart type and reads chart SQL with a parser that reports syntax errors with a position. <Link to="/docs/guides/visualisation-syntax#table">Read the guide</Link>.</p>
  </li>
  <li>
    <div className="roadmapTimeline__head">
      <Link className="roadmapVersion" href="https://github.com/glyf-data/glyf/releases/tag/v0.9.0">0.9.0</Link>
      <time dateTime="2026-09-22">22 September 2026</time>
    </div>
    <strong>Visual diff</strong>
    <p><code>glyf diff</code> compares the charts of two builds and reports which changed, how much of each picture moved, and why: the query, the rows, the version, or the chart itself. It runs in a pull request, so a reviewer sees what a change does to the dashboards and not only the line of SQL that did it. <Link to="/docs/guides/visual-diff">Read the guide</Link>.</p>
  </li>
  <li>
    <div className="roadmapTimeline__head">
      <Link className="roadmapVersion" href="https://github.com/glyf-data/glyf/releases/tag/v0.8.0">0.8.0</Link>
      <time dateTime="2026-09-20">20 September 2026</time>
    </div>
    <strong>The same picture every build</strong>
    <p>A chart whose query left the row order undefined could draw differently on every build. glyf now orders those rows itself, and never touches a query that orders its own. Chart files are byte-identical between builds, which is what makes a visual diff exact.</p>
  </li>
  <li>
    <div className="roadmapTimeline__head">
      <Link className="roadmapVersion" href="https://github.com/glyf-data/glyf/releases/tag/v0.7.0">0.7.0</Link>
      <time dateTime="2026-09-20">20 September 2026</time>
    </div>
    <strong>Histogram, boxplot and heatmap</strong>
    <p>Three more chart types, and two example projects rebuilt on realistic data to show them. Fixed: row values left in SVG labels under <code>row_data: minimal</code>, and a starter chart from <code>glyf init</code> that failed validation.</p>
  </li>
  <li>
    <div className="roadmapTimeline__head">
      <Link className="roadmapVersion" href="https://github.com/glyf-data/glyf/releases/tag/v0.6.0">0.6.0</Link>
      <time dateTime="2026-09-03">3 September 2026</time>
    </div>
    <strong>Charts too large to draw</strong>
    <p>A chart with too many marks now fails with an error naming it, where it used to kill the build. A large line or area chart can be reduced to the marks its pixels can show, without changing the picture.</p>
  </li>
  <li>
    <div className="roadmapTimeline__head">
      <Link className="roadmapVersion" href="https://github.com/glyf-data/glyf/releases/tag/v0.5.0">0.5.0</Link>
      <time dateTime="2026-09-03">3 September 2026</time>
    </div>
    <strong>Your warehouse, and what a build publishes</strong>
    <p>Charts run on Snowflake, BigQuery, Trino and DuckDB through your dbt profile. Control over what a published site contains: row data modes, PII classification with deny or redact, a scan for unclassified personal data, and one build per audience. Every build records what it did.</p>
  </li>
  <li>
    <div className="roadmapTimeline__head">
      <Link className="roadmapVersion" href="https://github.com/glyf-data/glyf/releases/tag/v0.4.0">0.4.0</Link>
      <time dateTime="2026-08-29">29 August 2026</time>
    </div>
    <strong>Half the install</strong>
    <p>Two heavy dependencies removed, taking a clean install from 531 MB to 269 MB. Dashboard toolbar actions.</p>
  </li>
</ol>

<p className="roadmapJump">
  Earlier versions, and the full notes for these, are in the{' '}
  <Link href="https://github.com/glyf-data/glyf/blob/main/CHANGELOG.md">changelog</Link>.
</p>
