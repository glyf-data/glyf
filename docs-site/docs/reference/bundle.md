# Bundle Manifest

Every glyf build writes a JSON manifest that lists the dashboards and charts it
produced and where their artifacts live. It is the contract between a glyf
build and anything that consumes it — Glyf Studio, the planned JavaScript
packages, or an application of your own that fetches the exported site.

```json title="target/glyf/site/bundle.json"
{
  "bundle_version": "1",
  "glyf_version": "0.4.0",
  "project": "basic",
  "mode": "public_site",
  "generated_at": "2026-08-30T10:38:38Z"
}
```

## The two manifests

| Manifest | `mode` | Written by | Paths are relative to |
| --- | --- | --- | --- |
| `target/glyf/bundle.json` | `local_artifact` | `glyf dashboard` | `target/glyf/` |
| `target/glyf/site/bundle.json` | `public_site` | `glyf export` | the site root |

`glyf build` runs both steps, so it writes both. They share one schema; the
public one omits the internal artifacts described under
[What the public manifest changes](#what-the-public-manifest-changes).

Every path in a manifest is relative to the directory that manifest sits in, so
an application can resolve artifacts against the URL it fetched the manifest
from without knowing anything about the project layout.

## Versioning

`bundle_version` is the only field a consumer must read before anything else.
It is a string, and it is `"1"` today.

Within a version:

- Fields may be **added**. A consumer must ignore fields it does not recognise.
- Existing field names, types and meanings **do not change**.
- Optional fields (`interactions`, `filters[].source`) may be absent, and
  nullable fields may be `null`. Both are part of the contract, not a defect.

Removing a field, renaming one, or changing what an existing field means
requires a new `bundle_version`. A consumer that does not recognise the version
it reads should stop rather than guess.

`glyf_version` and `generated_at` describe the build, not the format. They are
informational: do not branch on them.

## Top-level fields

| Field | Type | Description |
| --- | --- | --- |
| `bundle_version` | string | Schema version of this document. `"1"`. |
| `glyf_version` | string | The glyf release that wrote it, for diagnostics. |
| `project` | string | The dbt project directory name. |
| `mode` | string | `local_artifact` or `public_site`. |
| `generated_at` | string \| null | Build time, ISO 8601 UTC (`2026-08-30T10:38:38Z`). See [generated_at](#generated_at). |
| `paths` | object | Where each kind of artifact lives. |
| `security` | object | What this manifest exposes. |
| `charts` | object | Chart name → [chart entry](#charts). |
| `dashboards` | object | Dashboard name → [dashboard entry](#dashboards). |

Keys are sorted and the file ends with a newline, so manifests diff cleanly
between builds.

### `generated_at`

`glyf dashboard` records the build timestamp. `glyf export` does not have one of
its own, so it inherits the timestamp from the local manifest; if that manifest
is missing, it falls back to the modification time of the generated
`index.html`. When neither exists the field is `null`, so treat it as nullable.

### `paths`

| Field | Type | Description |
| --- | --- | --- |
| `index` | string | The generated index page. |
| `dashboards` | string | Directory of rendered dashboard pages. |
| `charts` | string | Directory of chart metadata, SVG and PNG artifacts. |
| `compiled` | string | Directory of compiled SQL. |
| `assets` | string | Directory of CSS and other static assets. |
| `data` | object | **Local manifests only.** `normalized` and `vega` directories. |

### `security`

| Field | Type | Description |
| --- | --- | --- |
| `public_export` | boolean | Whether this manifest describes a public export. |
| `internal_artifacts_included` | boolean | Whether the artifacts it points at include internal ones. |
| `internal_artifacts` | array of strings | Which directories those are. Empty in a public manifest. |
| `browser_visible_data` | string | Prose note on what publishing the described site exposes to a browser. |
| `row_data` | string | **Optional.** `"minimal"` when the site was built with `export.row_data: minimal`, `"excluded"` under `export.row_data: exclude`; absent otherwise. |

## `build`

**Optional.** The build provenance record: what this artifact contains and how
it was made. Present in the local manifest, and in a published one only under
`export.provenance: public` — it names the warehouse identity the queries ran
as and the selectors that narrowed the build, which is recon material on a
public site. The same record is written to `target/glyf/build.json`, which
`glyf export` never copies.

| Field | Type | Description |
| --- | --- | --- |
| `record_version` | number | Schema version of the record. `1`. |
| `built_at` | string | When the render ran, ISO 8601 UTC. |
| `duration_ms` | number | How long the render took. |
| `outcome` | string | `"success"`, or `"failed"` in an event log. |
| `error` | string \| null | Why a failed build stopped. `null` on success. |
| `project` | string | The project directory's name. |
| `dbt_manifest_generated_at` | string \| null | `metadata.generated_at` from the dbt manifest: which dbt run the artifacts were built from. |
| `execution` | object | `backend`, `target`, `mode`, `max_rows`. `target` names the warehouse identity. |
| `export` | object | `row_data`. |
| `privacy` | object | `on_pii`, `redaction`, `scan`, `strict`, `pii_columns`. |
| `selection` | object \| null | `selectors` and the `dashboards` they matched; `null` when the build was not restricted. |
| `charts` | object | Keyed by chart name; see below. |

### `build.charts[]`

| Field | Type | Description |
| --- | --- | --- |
| `compiled_sql_sha256` | string | First 16 hex characters of the compiled SQL's digest. Enough to notice that what ran changed, without republishing the query. |
| `row_count` | number \| null | Rows the query returned. `null` under validate mode, which fetches no rows — that is not zero rows. |
| `redacted_columns` | array of strings | **Optional.** Columns the PII policy rewrote. |
| `scan_warnings` | array of objects | **Optional.** What the value scan flagged: `column`, `kind`, `matched`, `sampled`. |

The record is the build describing itself. Like `security`, it is descriptive:
nothing verifies it, and it is not evidence. A tamper-evident history means
shipping these records somewhere append-only, which is what `--log-json` is
for.

## `charts`

An object keyed by chart name — the `.ggsql` file's stem, and the same name a
dashboard's `charts` list refers to.

| Field | Type | Description |
| --- | --- | --- |
| `title` | string \| null | The chart's `LABEL title`, if it has one. |
| `chart_type` | string \| null | The `DRAW` type: `line`, `bar`, `scatter`, `pie`, and so on. |
| `fields` | object | `x` and `y`, the column names bound to those roles. |
| `artifacts` | object | See below. |
| `interactions` | array of strings | **Optional.** Present only when the chart declares `INTERACT`. |

### `charts[].artifacts`

Every value is a path or `null`; the keys are always present.

| Field | Public manifest | Description |
| --- | --- | --- |
| `metadata` | path | The chart's own JSON metadata file. |
| `png` | path | Rendered PNG. |
| `svg` | path | Rendered SVG. |
| `compiled_sql` | path | The compiled SQL behind the chart. |
| `data` | always `null` | Normalised chart data. Local manifests only. |
| `vega` | always `null` | Vega specification. Local manifests only, and only for charts with interactions. |

Check for `null`, not for a missing key: `data` and `vega` stay in a public
manifest and are set to `null` rather than being removed.

Under `export.row_data: exclude` (see
[the configuration reference](./configuration.md#publishing-without-the-rows)),
`svg` and `compiled_sql` are `null` too, because those files are not published.
`security.row_data` is then `"excluded"`, which is the field to branch on if a
consumer needs to know whether row data exists at all. Under
`export.row_data: minimal` every artifact path is present as usual and
`security.row_data` is `"minimal"`: the SVG and any inlined Vega spec carry
only the columns the chart encodes.

## `dashboards`

An object keyed by dashboard name — the `name` in its YAML.

| Field | Type | Description |
| --- | --- | --- |
| `title` | string | Display title. |
| `description` | string \| null | Optional description. |
| `path` | string | The rendered dashboard page. |
| `theme` | string | Resolved dashboard theme, falling back to the project default. |
| `chart_theme` | string | Resolved chart theme, or `auto`. |
| `tags` | array of strings | Dashboard tags. |
| `charts` | array of strings | Chart names, in display order. Keys into `charts`. |
| `filters` | array of objects | See below. |
| `source` | string | The dashboard's YAML file, relative to the project root. |

### `dashboards[].filters`

| Field | Type | Description |
| --- | --- | --- |
| `field` | string | Label shown in the dashboard's control row. |
| `values` | array of strings | The filter's values, always resolved. |
| `source` | object | **Optional.** Present when the YAML used `source(chart, field)`; records the `chart` and `field` the values came from. |

`values` is populated either way — a consumer that only renders the controls can
ignore `source` entirely.

## What the public manifest changes

| | `local_artifact` | `public_site` |
| --- | --- | --- |
| `paths.data` | present | omitted |
| `security.public_export` | `false` | `true` |
| `security.internal_artifacts_included` | `true` | `false` |
| `security.internal_artifacts` | `["data/normalized", "data/vega"]` | `[]` |
| `charts[].artifacts.data` | path | `null` |
| `charts[].artifacts.vega` | path, when the chart has interactions | `null` |

Nothing else differs. The public manifest does not *reference* the normalised
data or the Vega specs that stay under `target/glyf/`.

That is a statement about the manifest, not about the site. The dashboard pages
published alongside it still carry the chart rows — inline in a Vega
specification for an interactive chart, and in an SVG's per-mark labels
otherwise. Withholding the paths does not withhold the data. See
[what a published site exposes](../guides/data-exposure.md), and
`export.row_data: exclude` if the site should carry no rows at all.

## A complete public manifest

```json title="target/glyf/site/bundle.json"
{
  "bundle_version": "1",
  "charts": {
    "revenue": {
      "artifacts": {
        "compiled_sql": "compiled/revenue.sql",
        "data": null,
        "metadata": "charts/revenue.json",
        "png": "charts/revenue.png",
        "svg": "charts/revenue.svg",
        "vega": null
      },
      "chart_type": "line",
      "fields": {
        "x": "month",
        "y": "revenue"
      },
      "interactions": [
        "tooltip",
        "zoom"
      ],
      "title": "Monthly Revenue"
    }
  },
  "dashboards": {
    "executive": {
      "chart_theme": "auto",
      "charts": [
        "revenue"
      ],
      "description": "Key business metrics generated from dbt models.",
      "filters": [
        {
          "field": "region",
          "source": {
            "chart": "revenue",
            "field": "month"
          },
          "values": [
            "2026-01",
            "2026-02",
            "2026-03",
            "2026-04"
          ]
        },
        {
          "field": "focus",
          "values": [
            "revenue",
            "margin"
          ]
        }
      ],
      "path": "dashboards/executive.html",
      "source": "dashboards/executive.yml",
      "tags": [
        "finance",
        "executive",
        "demo"
      ],
      "theme": "light",
      "title": "Executive Dashboard"
    }
  },
  "generated_at": "2026-08-30T10:38:38Z",
  "glyf_version": "0.4.0",
  "mode": "public_site",
  "paths": {
    "assets": "assets/",
    "charts": "charts/",
    "compiled": "compiled/",
    "dashboards": "dashboards/",
    "index": "index.html"
  },
  "project": "basic",
  "security": {
    "browser_visible_data": "Public exports include rendered dashboard HTML and public chart artifacts. Embedded app packages may intentionally expose Vega specs to the browser.",
    "internal_artifacts": [],
    "internal_artifacts_included": false,
    "public_export": true
  }
}
```

## Reading it from an application

```js
const base = "https://analytics.example.com/glyf/product_analytics/";
const bundle = await fetch(base + "bundle.json").then((r) => r.json());

if (bundle.bundle_version !== "1") {
  throw new Error(`unsupported bundle_version ${bundle.bundle_version}`);
}

const chart = bundle.charts["revenue"];
document.querySelector("img").src = base + chart.artifacts.svg;
```

[Embedded analytics](../integrations/embedded-analytics.md) covers publishing
the site the manifest describes.
