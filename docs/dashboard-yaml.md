# Dashboard YAML

Dashboard configs live in `dashboards/`.

```yaml
name: executive
title: Executive Dashboard
description: Key business metrics generated from dbt models.

charts:
  - revenue
  - revenue_by_region_bar
  - revenue_share_pie
```

## Fields

- `name`: output filename stem.
- `title`: dashboard page title.
- `description`: optional intro text.
- `charts`: list of `.ggsql` chart names without the extension.
- `layout`: optional placeholder for future layout support.

Generated HTML is written to:

```text
target/ggsql/dashboards/<name>.html
```

The dashboard index is written to:

```text
target/ggsql/index.html
```
