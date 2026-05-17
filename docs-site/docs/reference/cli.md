# CLI Reference

The CLI entry point is:

```bash
dbt-charts
```

When working from this repository, use:

```bash
uv run dbt-charts
```

## Commands

| Command | Purpose |
| --- | --- |
| `dbt-charts doctor` | Check whether a project is ready for dbt-charts workflows. |
| `dbt-charts list` | List discovered ggsql project files. |
| `dbt-charts validate` | Validate discovered files and manifest refs. |
| `dbt-charts render` | Generate compiled SQL and chart artifacts. |
| `dbt-charts dashboard` | Generate static dashboard HTML from rendered chart artifacts. |
| `dbt-charts export` | Copy generated outputs into a publish-ready static site folder. |
| `dbt-charts serve` | Serve the generated static dashboard site locally. |

## Shared options

Most commands support:

| Option | Description |
| --- | --- |
| `--project-dir`, `--project`, `-p` | Path to a dbt project. Defaults to the current directory. |
| `--config` | Path to `dbt_charts.yml`. Defaults to `PROJECT/dbt_charts.yml` if present. |

## Common workflow

```bash
uv run dbt-charts doctor --project-dir examples/simple_dbt
uv run dbt-charts list --project-dir examples/simple_dbt
uv run dbt-charts validate --project-dir examples/simple_dbt
uv run dbt-charts render --project-dir examples/simple_dbt
uv run dbt-charts dashboard --project-dir examples/simple_dbt
uv run dbt-charts export --project-dir examples/simple_dbt --clean --zip
```

## `export` options

| Option | Description |
| --- | --- |
| `--clean` | Delete the previous site export before copying. |
| `--zip` | Create `target/ggsql/dbt-charts-site.zip`. |

## `serve` options

| Option | Description |
| --- | --- |
| `--host` | Host interface to bind. Defaults to `127.0.0.1`. |
| `--port` | Port to bind. Defaults to `8000`. Use `0` to choose an available port. |

Preview a generated dashboard:

```bash
uv run dbt-charts serve --project-dir examples/simple_dbt
uv run dbt-charts serve --project-dir examples/simple_dbt --host 127.0.0.1 --port 8080
```
