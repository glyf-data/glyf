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

Copy `target/glyf/site/` anywhere the application can fetch static files —
Cloudflare Pages, S3 and CloudFront, R2, an internal static server, or the
application's own public folder:

```text
https://analytics.example.com/glyf/product_analytics/bundle.json
/analytics/glyf/product_analytics/bundle.json
```

## What the public bundle omits

The exported `bundle.json` is meant to be published. It does not reference the
normalised chart data or the Vega specs that `glyf dashboard` keeps under
`target/glyf/`, and copied chart metadata has those paths removed. The
[reference](../reference/bundle.md#what-the-public-manifest-changes) lists the
differences field by field. If an
application needs interactive Vega rendering or row-level access control,
serve a scoped bundle from your own backend rather than publishing the
internal artifacts.

## JavaScript packages

Client and React packages that consume `bundle.json` directly are on the
[roadmap](../resources/roadmap.md); they are not published yet. Until then,
read the manifest with `fetch` and render the SVG or PNG it points to.
