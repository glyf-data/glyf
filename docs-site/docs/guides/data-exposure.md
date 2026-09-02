# What a Published Site Exposes

A glyf site is static files. There is no server between a reader and the
artifacts, so whatever those artifacts contain is readable by anyone who can
reach them. That is the point — it is why a glyf dashboard costs nothing to host
— and it means the question worth asking before publishing is not *who can see
this page* but *what is in it*.

By default, a published site contains the data behind its charts.

## What a default export contains

| Published file | Carries |
| --- | --- |
| `dashboards/*.html` | The rows. See below — twice over, and not obviously. |
| `charts/*.svg` | Every row: vector marks carry their values in accessibility labels. |
| `charts/*.png` | The picture only. A raster image has no machine-readable values. |
| `charts/*.json` | Chart metadata: title, type, the column names bound to x and y. |
| `compiled/*.sql` | The chart's SQL, including fully-qualified `database.schema.table` names. |
| `bundle.json` | No rows. Column names, and any filter values resolved at build time. |

Two of those deserve spelling out, because neither is visible from reading the
dashboard.

**An interactive chart publishes its whole result set.** A chart with an
`INTERACT` clause is re-rendered in the browser, which means its Vega-Lite
specification is inlined into the page — and that specification carries the rows
in a `datasets` block:

```json
"datasets": {"data-eee936f3": [{"bookings": 79000, "month": "2026-03"}, ...]}
```

**A static chart publishes its rows too.** An SVG describes every mark, and each
mark carries an accessibility label containing the values it was drawn from:

```html
<path aria-label="Sessions: 6610; plan: Pro; sessions: 6610" ...>
```

With `embed_charts: true` — the default — that SVG is inlined into the dashboard
page, so the values are in the HTML whether or not the chart is interactive.

**Filters can publish a column's distinct values.** A filter written as
`values: source(chart, field)` is resolved at build time by reading the chart's
rows, so the resulting list is a `SELECT DISTINCT` of that column. Filtering on
`region` publishes your regions; filtering on `customer_name` publishes your
customers.

**Compiled SQL names your warehouse tables.** `site/compiled/*.sql` is published
whether or not the dashboard shows it. `dashboard.show_compiled_sql: false`
removes the drawer from the page; the files remain, at a predictable URL.

## Publishing only what the chart shows

```yaml title="glyf.yml"
export:
  row_data: minimal
```

This keeps every chart as it is — interactive charts stay interactive — and
strips what the picture does not show. An interactive chart's `datasets` block
is pruned to the columns its `VISUALISE` clause encodes, so a query that
selects `customer_id` alongside the two columns it plots no longer publishes
`customer_id`. An SVG mark's accessibility label keeps the field names and
drops the values: `plan; sessions` rather than `plan: Pro; sessions: 6610`.

| Published file | Carries under `minimal` |
| --- | --- |
| `dashboards/*.html` | Encoded columns only, in the inlined Vega spec; SVG labels without values. |
| `charts/*.svg` | The picture, and which columns each mark came from. |
| `charts/*.png` | The picture only. |
| `charts/*.json` | Chart metadata, as before. |
| `compiled/*.sql` | The chart's SQL, as before — it is metadata, not data. |
| `bundle.json` | As before, plus `security.row_data: "minimal"`. |

Values are never rounded or otherwise transformed. A chart whose numbers
disagree with the warehouse is a worse problem than the precision an exact
value reveals, so the mode prunes columns and touches nothing else. What it
guarantees: **a `minimal` export contains no information beyond what the
rendered chart displays.** The encoded values are still there — Vega needs them
to draw — but they are the values the pixels already reveal.

A `source(chart, field)` filter is resolved as usual. It names a column
explicitly, so its distinct values are something you asked to publish.

## Publishing without the rows

```yaml title="glyf.yml"
export:
  row_data: exclude
```

This publishes rendered PNG images and nothing else: no SVG, no Vega
specification, no compiled SQL, no SQL drawer, and no filter values resolved out
of chart rows. An `INTERACT` chart becomes a static image, and the build says
which chart was downgraded. The full behaviour is in the
[configuration reference](../reference/configuration.md#publishing-without-the-rows).

What still gets published is what you wrote: dashboard titles and descriptions,
markdown blocks, hand-written filter lists, chart titles, and whatever your
macros render. A macro that computes a headline number from the data publishes
that number — the mode withholds the rows, not the conclusions drawn from them.

## What glyf does not do

**glyf has no access control.** Nothing in a glyf artifact authenticates a
reader or restricts what they see. If a dashboard should only be visible to some
people, that has to come from where you host it: a private bucket, an
identity-aware proxy, a VPN, or a static host with authentication.

**`toolbar.visibility` is a label, not a control.** Setting it to `private`
draws a padlock icon and a badge on the page. It changes nothing about what is
exported: a dashboard marked private is published byte-for-byte identically to
one marked public.

**The `security` block in `bundle.json` is descriptive.** It reports what the
build did — whether internal artifacts were included, and whether row data was
excluded — so a consumer can inspect it. Nothing reads it back or enforces it.

**Interactive dashboards load Vega from a CDN.** A dashboard containing an
`INTERACT` chart fetches `vega`, `vega-lite` and `vega-embed` from
`cdn.jsdelivr.net` at page load, so a reader's browser contacts a third party.
`export.row_data: exclude` removes those scripts along with the specs they
render.

## A checklist before publishing

1. Would you be comfortable handing someone the rows behind every chart? If not,
   set `export.row_data: exclude`, or aggregate further in the chart's SQL.
   If the plotted values are fine but the query selects more columns than it
   plots, `export.row_data: minimal` publishes only the plotted ones.
2. Do the compiled queries reveal schema or table names you would rather not
   expose?
3. Does any `source()` filter read a column of names, emails or identifiers?
4. Does a macro or a markdown block quote a specific figure that should not be
   public?
5. Is the bucket or host actually restricted to the audience you intend?
