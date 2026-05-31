import Link from '@docusaurus/Link';

# Examples Gallery

Each example is a small dbt project with seeds, models, ggsql visualisations, and dashboard YAML.

## Gallery

<div className="exampleGallery">
  <article className="exampleCard">
    <Link to="pathname:///dashboards/simple-dbt/dashboards/executive.html">
      <img src="/img/examples/simple-dbt-banner.svg" alt="Simple dbt dashboard preview banner" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="https://github.com/kannandreams/glyf/tree/main/examples/simple_dbt">Simple dbt</a></h3>
      <p>Learning the shortest path from dbt project to dashboard.</p>
      <p><strong>Includes:</strong> Revenue charts, dashboard YAML, local DuckDB profile.</p>
      <p className="exampleCard__links">
        <Link to="/docs/examples/simple-dbt">Docs</Link>
        <Link to="pathname:///dashboards/simple-dbt/dashboards/executive.html">Rendered dashboard</Link>
        <a href="https://github.com/kannandreams/glyf/tree/main/examples/simple_dbt">Source project</a>
      </p>
    </div>
  </article>

  <article className="exampleCard">
    <Link to="pathname:///dashboards/sales-dashboard/dashboards/sales.html">
      <img src="/img/examples/sales-dashboard-banner.svg" alt="Sales dashboard preview banner" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="https://github.com/kannandreams/glyf/tree/main/examples/sales_dashboard">Sales Dashboard</a></h3>
      <p>Reporting patterns for revenue by time, channel, and region.</p>
      <p><strong>Includes:</strong> Line, bar, and regional charts.</p>
      <p className="exampleCard__links">
        <Link to="/docs/examples/sales-dashboard">Docs</Link>
        <Link to="pathname:///dashboards/sales-dashboard/dashboards/sales.html">Rendered dashboard</Link>
        <a href="https://github.com/kannandreams/glyf/tree/main/examples/sales_dashboard">Source project</a>
      </p>
    </div>
  </article>

  <article className="exampleCard">
    <Link to="pathname:///dashboards/product-analytics/dashboards/product.html">
      <img src="/img/examples/product-analytics-banner.svg" alt="Product analytics dashboard preview banner" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="https://github.com/kannandreams/glyf/tree/main/examples/product_analytics">Product Analytics</a></h3>
      <p>Product usage and activation metrics by plan.</p>
      <p><strong>Includes:</strong> Area, bar, and scatter examples.</p>
      <p className="exampleCard__links">
        <Link to="/docs/examples/product-analytics">Docs</Link>
        <Link to="pathname:///dashboards/product-analytics/dashboards/product.html">Rendered dashboard</Link>
        <a href="https://github.com/kannandreams/glyf/tree/main/examples/product_analytics">Source project</a>
      </p>
    </div>
  </article>

  <article className="exampleCard">
    <Link to="pathname:///dashboards/finance-metrics/dashboards/finance.html">
      <img src="/img/examples/finance-metrics-banner.svg" alt="Finance metrics dashboard preview banner" />
    </Link>
    <div className="exampleCard__body">
      <h3><a href="https://github.com/kannandreams/glyf/tree/main/examples/finance_metrics">Finance Metrics</a></h3>
      <p>Finance KPI dashboard patterns for bookings, expenses, and margin.</p>
      <p><strong>Includes:</strong> Bookings, expense, and margin charts.</p>
      <p className="exampleCard__links">
        <Link to="/docs/examples/finance-metrics">Docs</Link>
        <Link to="pathname:///dashboards/finance-metrics/dashboards/finance.html">Rendered dashboard</Link>
        <a href="https://github.com/kannandreams/glyf/tree/main/examples/finance_metrics">Source project</a>
      </p>
    </div>
  </article>
</div>

## Run an example

From an example directory:

```bash
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf build --zip
uv run glyf serve
```

Open:

```text
http://127.0.0.1:8000
```

## Use examples as templates

Copy the shape, not necessarily the data:

- Keep dbt models under `models/`.
- Keep chart SQL under `visualisations/`.
- Keep dashboard definitions under `dashboards/`.
- Keep `glyf.yml` at the project root for repeatable local and CI commands.
