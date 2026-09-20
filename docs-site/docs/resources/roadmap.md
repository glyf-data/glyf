# Roadmap

`glyf` stays a deterministic, static-first CLI. The current workflow is:

```bash
dbt build
glyf build
glyf serve
```

## Recently shipped

- **[Visual diff](../guides/visual-diff.md)**: `glyf diff` compares two builds
  and reports which charts changed, how much of each picture moved, and why.
  It runs in a pull request.
- **Reproducible charts**: a rebuild of unchanged data produces the same bytes,
  which is what makes the diff exact.
- **Histogram, boxplot and heatmap** chart types.

## Planned

- **Watch mode**: regenerate charts and dashboards when `.ggsql` files,
  dashboard YAML, or `glyf.yml` change.
- **Richer dashboard layout**: grid sizing and chart sizing hints beyond the
  current column tracks.
- **Publish helpers** for common static hosting targets.
- **dbt docs integration**: model, column, and source descriptions from the
  manifest shown on dashboards.
- **Lineage-aware dashboards**: which models and sources feed each chart.
- **Alert hooks**: Slack or webhook notifications when a value on a dashboard
  crosses a threshold.
- **JavaScript packages** for consuming `bundle.json` in web applications.
  Experimental React components are in
  [glyf-js](https://github.com/glyf-data/glyf-js).

None of these have dates. Discussion and proposals are welcome in
[GitHub Discussions](https://github.com/glyf-data/glyf/discussions).
