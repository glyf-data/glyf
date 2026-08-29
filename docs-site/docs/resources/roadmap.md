# Roadmap

`glyf` stays a deterministic, static-first CLI. The current workflow is:

```bash
dbt build
glyf build
glyf serve
```

## Planned

- **Watch mode** — regenerate charts and dashboards when `.ggsql` files,
  dashboard YAML, or `glyf.yml` change.
- **Richer dashboard layout** — grid sizing and chart sizing hints beyond the
  current column tracks.
- **Publish helpers** for common static hosting targets.
- **dbt docs integration** — model, column, and source descriptions from the
  manifest shown on dashboards.
- **Lineage-aware dashboards** — which models and sources feed each chart.
- **Visual diffs and alert hooks** — dashboard output diffs in CI, and Slack or
  webhook notifications.
- **JavaScript packages** for consuming `bundle.json` in web applications.

None of these have dates. Discussion and proposals are welcome in
[GitHub Discussions](https://github.com/glyf-data/glyf/discussions).
