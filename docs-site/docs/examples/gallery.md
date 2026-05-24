import Link from '@docusaurus/Link';

# Examples Gallery

Each example is a small dbt project with seeds, models, ggsql visualisations, and dashboard YAML.

## Gallery

<div className="exampleGallery">
  <article className="exampleCard">
    <Link to="pathname:///dashboards/simple-dbt/dashboards/executive.html">
      <img src="/img/examples/simple-dbt-banner.svg" alt="Simple dbt dashboard screenshot placeholder" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="simple-dbt.md">Simple dbt</a></h3>
      <p>Learning the shortest path from dbt project to dashboard.</p>
      <p><strong>Includes:</strong> Revenue charts, dashboard YAML, local DuckDB profile.</p>
      <p><strong>Rendered output:</strong> <Link to="pathname:///dashboards/simple-dbt/dashboards/executive.html">Executive Dashboard</Link></p>
    </div>
  </article>

  <article className="exampleCard">
    <Link to="pathname:///dashboards/sales-dashboard/dashboards/sales.html">
      <img src="/img/examples/sales-dashboard-banner.svg" alt="Sales dashboard screenshot placeholder" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="sales-dashboard.md">Sales Dashboard</a></h3>
      <p>Reporting patterns for revenue by time, channel, and region.</p>
      <p><strong>Includes:</strong> Line, bar, and regional charts.</p>
      <p><strong>Rendered output:</strong> <Link to="pathname:///dashboards/sales-dashboard/dashboards/sales.html">Sales Dashboard</Link></p>
    </div>
  </article>

  <article className="exampleCard">
    <Link to="pathname:///dashboards/product-analytics/dashboards/product.html">
      <img src="/img/examples/product-analytics-banner.svg" alt="Product analytics screenshot placeholder" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="product-analytics.md">Product Analytics</a></h3>
      <p>Product usage and activation metrics by plan.</p>
      <p><strong>Includes:</strong> Area, bar, and scatter examples.</p>
      <p><strong>Rendered output:</strong> <Link to="pathname:///dashboards/product-analytics/dashboards/product.html">Product Analytics</Link></p>
    </div>
  </article>

  <article className="exampleCard">
    <Link to="pathname:///dashboards/finance-metrics/dashboards/finance.html">
      <img src="/img/examples/finance-metrics-banner.svg" alt="Finance metrics screenshot placeholder" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="finance-metrics.md">Finance Metrics</a></h3>
      <p>Finance KPI dashboard patterns for bookings, expenses, and margin.</p>
      <p><strong>Includes:</strong> Bookings, expense, and margin charts.</p>
      <p><strong>Rendered output:</strong> <Link to="pathname:///dashboards/finance-metrics/dashboards/finance.html">Finance Metrics</Link></p>
    </div>
  </article>
</div>

See [Screenshots](screenshots.md) for the committed banner assets and refresh steps.

## Run an example

From an example directory:

```bash
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
```

Open:

```text
target/ggsql/site/index.html
```

## Use examples as templates

Copy the shape, not necessarily the data:

- Keep dbt models under `models/`.
- Keep chart SQL under `visualisations/`.
- Keep dashboard definitions under `dashboards/`.
- Keep `glyf.yml` at the project root for repeatable local and CI commands.
