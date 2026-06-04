# Embedded Analytics

Use embedded analytics when you want a product application to display charts
built by the same data pipeline that runs Glyf.

The workflow is:

```text
glyf export
  writes target/glyf/site/

target/glyf/site/bundle.json
  describes exported dashboards and chart artifacts

@glyf/react
  loads bundle.json and renders charts by name
```

## Build the Glyf Site

Run dbt first, then build and export the Glyf artifacts:

```bash
dbt build
glyf build
```

The exported site is written to:

```text
target/glyf/site/
  bundle.json
  charts/
  dashboards/
  compiled/
  assets/
```

`bundle.json` is the artifact contract. It tells external tools where chart
metadata, SVG/PNG files, dashboard pages, and compiled SQL live.

## Publish the Artifacts

Publish `target/glyf/site` anywhere your application can read static files:

- Cloudflare Pages
- S3 and CloudFront
- R2
- an internal static server
- your app's `public/analytics/glyf` folder

For example:

```text
https://analytics.company.com/glyf/product_analytics/bundle.json
```

or inside a React app public folder:

```text
/analytics/glyf/product_analytics/bundle.json
```

## Render in React

Install the JavaScript packages in the application repo:

```bash
npm install @glyf/client @glyf/react
```

Then point `GlyfProvider` at the published bundle:

```tsx
import { GlyfProvider, GlyfChart } from "@glyf/react";

export function AnalyticsPanel() {
  return (
    <GlyfProvider bundleUrl="/analytics/glyf/product_analytics/bundle.json">
      <GlyfChart name="activation_by_plan" />
    </GlyfProvider>
  );
}
```

The first version renders exported SVG/PNG chart artifacts through an image
element. That keeps public embeds simple and avoids exposing internal normalized
data or Vega specs.

## Security Note

Public Glyf exports are intentionally public-safe:

- `target/glyf/site/bundle.json` does not reference internal normalized data.
- `target/glyf/site/bundle.json` does not reference Vega specs.
- copied chart metadata removes internal data and Vega paths.

If a future app needs interactive Vega rendering or row-level access control,
serve a scoped bundle from your backend or Glyf Cloud instead of publishing raw
interactive artifacts directly.
