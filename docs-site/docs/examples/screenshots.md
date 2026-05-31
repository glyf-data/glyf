# Screenshots

Screenshots keep the examples gallery grounded in real generated output.

Use this checklist when refreshing docs assets so every image shows output produced by glyf, not generic product artwork.

## Gallery banner assets

The gallery uses wide `1200x675` banner assets so cards stay aligned across desktop and mobile layouts.

| Asset | Source output | Rendered dashboard |
| --- | --- | --- |
| `simple-dbt-banner.svg` | `examples/simple_dbt` | `/dashboards/simple-dbt/dashboards/executive.html` |
| `sales-dashboard-banner.svg` | `examples/sales_dashboard` | `/dashboards/sales-dashboard/dashboards/sales.html` |
| `product-analytics-banner.svg` | `examples/product_analytics` | `/dashboards/product-analytics/dashboards/product.html` |
| `finance-metrics-banner.svg` | `examples/finance_metrics` | `/dashboards/finance-metrics/dashboards/finance.html` |

## Capture guidelines

- Use generated `glyf` output.
- Prefer wide rectangle previews that fit gallery cards.
- Replace the current banner SVG files with real `1200x675` screenshots when captured.
- Avoid screenshots with local file paths, private data, or unstable timestamps.
- Keep light and dark mode screenshots if both modes are visually meaningful.
- Store assets under `docs-site/static/img/examples/`.

## Refresh workflow

Generate the source outputs first:

```bash
task dashboard-ci EXAMPLE_PROJECT=examples/simple_dbt
task dashboard-ci EXAMPLE_PROJECT=examples/sales_dashboard
task dashboard-ci EXAMPLE_PROJECT=examples/product_analytics
task dashboard-ci EXAMPLE_PROJECT=examples/finance_metrics
```

Copy the exported sites into the documentation static tree:

```bash
docs-site/static/dashboards/simple-dbt/
docs-site/static/dashboards/sales-dashboard/
docs-site/static/dashboards/product-analytics/
docs-site/static/dashboards/finance-metrics/
```

Normalize preview banners to `1200x675` before committing them.
