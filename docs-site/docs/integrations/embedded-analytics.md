# Embedded Analytics

Use this when a product application should show charts built by the same
pipeline that runs `glyf`, without that application running `glyf` itself.

## The contract: `bundle.json`

`glyf build` (or `glyf export`) writes a static site with a manifest at its
root:

```text
target/glyf/site/
  bundle.json
  charts/
  dashboards/
  compiled/
  assets/
```

`bundle.json` lists every exported dashboard and chart, with the paths of the
SVG and PNG artifacts, dashboard pages, and compiled SQL. An application reads
the manifest, looks up a chart by name, and shows the artifact it points at.
Nothing in the site depends on a server.

Every field, and the rule for what may change within a `bundle_version`, is in
the [bundle manifest reference](../reference/bundle.md).

## Publish the site

Copy `target/glyf/site/` anywhere the application can fetch static files:
Cloudflare Pages, S3 and CloudFront, R2, an internal static server, or the
application's own public folder.

```text
https://analytics.example.com/glyf/product_analytics/bundle.json
/analytics/glyf/product_analytics/bundle.json
```

## What the public bundle omits

The exported `bundle.json` is meant to be published. It does not reference the
normalised chart data or the Vega specs that `glyf dashboard` keeps under
`target/glyf/`, and copied chart metadata has those paths removed. The
[reference](../reference/bundle.md#what-the-public-manifest-changes) lists the
differences field by field.

The manifest omits those *paths*; the exported dashboards still carry the chart
rows in their HTML.

## Draw charts live: `export.embed`

A picture is enough for a report. An application that wants tooltips, zoom,
its own theme or filters needs the chart's Vega specification, which the
public site withholds by default. Opt in:

```yaml title="glyf.yml"
export:
  embed: true
```

`glyf export` then publishes each drawn chart's spec at
`charts/<name>.vega.json`, `bundle.json` points `charts[].artifacts.vega` at
it, and `security.embedded_specs` is `true`. A spec carries the rows the chart
was drawn from, the same rows the dashboard pages already inline, so combine
it with `export.row_data: minimal` to publish only the columns each chart
encodes. It cannot be combined with `row_data: exclude`, which publishes no
rows. If the published site should contain no row data, build it
with `export.row_data: exclude`. [What a published site
exposes](../guides/data-exposure.md) covers what that changes. If an
application needs interactive Vega rendering or row-level access control,
serve a scoped bundle from your own backend rather than publishing the
internal artifacts.

## JavaScript packages

[glyf-js](https://github.com/glyf-data/glyf-js) reads `bundle.json` and draws
the charts in your application: live from the published Vega specs, with
tooltips, your theme and palette, KPI tiles, tables and the dashboard's
filters.

```bash
npm install @glyf-data/react     # React
npm install @glyf-data/embed     # any page, no framework
```

```tsx
import "@glyf-data/embed/style.css";
import { GlyfChart, GlyfFilters, GlyfProvider } from "@glyf-data/react";

export function Insights() {
  return (
    <GlyfProvider bundleUrl="/glyf/bundle.json" theme="dark">
      <GlyfFilters dashboard="insights" />
      <GlyfChart name="spend_by_model" />
    </GlyfProvider>
  );
}
```

[clanker.glyfdata.com](https://clanker.glyfdata.com) is a customer-facing page
built this way, from `examples/clanker_insights`. Without `export.embed` the
packages fall back to the SVG each chart was rendered as.
