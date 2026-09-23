# Visual Diff

`glyf diff` compares the charts of this build with the charts of an earlier
one and reports what changed: which charts, how much of each picture moved,
and why.

A change to a dbt model can move a number on a dashboard without touching any
file a reviewer would think to open. The SQL diff shows one line. The visual
diff shows that a department disappeared from four charts and bookings fell by
a tenth.

## Run it

```bash
glyf build                              # the build to keep as a baseline
cp -R target/glyf /tmp/baseline

# ...change a model, a chart, or the data...

dbt build
glyf build
glyf diff --baseline /tmp/baseline
```

```text
~ bookings_trend: 6.1% of the picture moved (the rows changed)
    sum of bookings 1,079,700 → 974,000 (-9.8%)
~ margin_share: 31.3% of the picture moved (the rows changed)
    rows 4 → 3
    gone from department: Partners
    sum of gross_margin 503,700 → 446,500 (-11.4%)
✓ 2 changed, 6 unchanged
✓ wrote target/glyf/diff/index.html
```

Each changed chart is followed by what moved in its rows, so the CI log tells
the story without downloading the report.

`--baseline` takes a `target/glyf` directory, an exported site, or a project
that contains one.

## What it writes

Everything goes under `target/glyf/diff/`, which holds its own copies of the
images and can be uploaded as it is.

| File | For |
| --- | --- |
| `index.html` | A reviewer. Each changed chart before, after, and what moved. |
| `summary.md` | A pull request comment. One table row per changed chart. |
| `diff.json` | A script. Status, pixel counts, reasons, mark changes and row changes per chart. |
| `images/` | `<chart>.before.png`, `<chart>.after.png`, `<chart>.overlay.png`, `<chart>.diff.png` |

"What moved" is the chart drawn over its old self: the new marks in colour,
the baseline's marks in grey behind them, and a box around every category
whose value moved. A series the new build dropped stays in the legend with
nothing under it. See [what moved, in the chart's terms](#what-moved-in-the-charts-terms).
The `diff.png` is the older, pixel-level view: the new chart faded back with
every differing pixel drawn in one colour. The report shows it for a chart the
overlay cannot draw.

## How a chart is judged

Two PNGs with the same bytes are the same chart, and most comparisons end
there. glyf [orders the rows](visualisation-syntax.md#row-order) a query leaves
unordered, so a rebuild of unchanged data produces the same file.

When the bytes differ, the two images are compared pixel by pixel. A chart
counts as changed when any pixel differs. Two options loosen that:

| Option | Meaning |
| --- | --- |
| `--threshold` | Percentage of a chart's pixels that may differ before it counts as changed. Default `0`. |
| `--tolerance` | How far a colour channel may move, out of 255, before a pixel counts as changed. Default `0`. |

Leave both at zero when the two builds were rendered on the same machine. Raise
`--threshold` when they were not: different machines rasterise fonts
differently, and that moves a few pixels in every chart with text in it.

## Why a chart changed

Each changed chart carries the reasons the two builds can account for, from
`build.json` and the published rows:

| Reason | Evidence |
| --- | --- |
| the query changed | The compiled SQL has a different hash. |
| the rows changed | The row count, the columns, a column's sum, or a column's set of values differs. |
| glyf `a` -> `b` | The two builds were made by different versions. |
| the same rows came back in a different order | No value differs, only which row came first. The query's `ORDER BY` leaves ties; see [Row order](visualisation-syntax.md#row-order). |
| the chart definition changed | None of the above: what is left is the `DRAW` type, a label, the size, or an interaction. |

The row changes are listed in plain terms:

```text
rows 48 → 36
gone from department: Partners
sum of expenses 576,000 → 527,500 (-8.4%)
```

## What moved, in the chart's terms

A pixel comparison says where the picture differs and cannot say why: a bar
that shrank lights up at its old height and its new one, a line that lost six
months re-spreads across the axis and lights up twice. So for a bar, line or
area chart, glyf compares the two builds' rows the way the chart draws them,
one mark per x value and series, and reports what it finds first:

```text
~ expenses_by_department: 50.8% of the picture moved (the rows changed)
    bars: 12 gone (Partners)
    rows 48 → 36
    gone from department: Partners
    sum of expenses 576,000 → 527,500 (-8.4%)
```

`bars: 12 gone (Partners)` means twelve bars that the baseline drew have no
counterpart in this build, all of them in the Partners series. The other
counts are `new`, `higher` and `lower`. A line or area chart says `points`.

The report draws the same thing: this build's marks in colour, the baseline's
in grey behind them, and a magenta box around each x value where a mark went,
appeared or changed height. In the example above every month is boxed, and
the grey outline above each stack is the total the baseline had.

This needs both builds' rows and a chart with a category on x. A scatter has
a number on x, so there is nothing to box; a histogram bins and a boxplot
summarises its own rows; a heatmap has no height to compare and a pie no
axis. Those, and a build under `export.row_data: exclude`, show the
pixel-level picture instead.

A numeric column is summarised by its sum. For a rate or a percentage the sum
means nothing by itself; read it as "this column moved" and look at the picture.

Row changes need both builds to have published their rows. A build under
[`export.row_data: exclude`](data-exposure.md) publishes none, and the diff
then reports the pictures alone.

A [table](visualisation-syntax.md#table) has no picture. Its HTML fragment is
written from its rows and nothing else, so it is byte-stable the way a PNG is,
and a fragment that differs is a table that changed. There is no percentage
and no threshold for it: `glyf diff` says `the table changed`, gives the row
changes above, and the report shows the two tables side by side. In
`diff.json` a table's entry carries `"table": true`, no pixel counts, and a
`fragments` object pointing at `fragments/<name>.before.html` and
`fragments/<name>.after.html`. A [kpi](visualisation-syntax.md#kpi) is
treated the same way: `glyf diff` says `the value changed`, the entry
carries `"kpi": true`, and the report shows the two tiles side by side.

## In a pull request

Build the base branch and the pull request in the same job, then compare. The
same runner draws both, so the comparison can be exact.

Before the build, [`glyf impact`](../reference/cli.md#impact) answers the
question a reviewer asks first: a pull request that changes `fct_finance`
reaches which charts? `glyf impact fct_finance` lists them with their
dashboards, and `glyf impact fct_finance.margin` narrows it to the charts that
name the column, saying which only might. The diff then says what moved in
them.

```yaml title=".github/workflows/visual-diff.yml"
name: visual diff

on: pull_request

permissions:
  contents: read
  pull-requests: write

jobs:
  visual-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          path: head
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          path: base

      - uses: astral-sh/setup-uv@v5
      - name: Install glyf and dbt
        run: |
          uv tool install glyf-core
          uv tool install dbt-core --with dbt-duckdb

      - name: Build both sides
        run: |
          for side in base head; do
            (cd "$side" && dbt build && glyf build)
          done

      - name: Compare
        run: |
          cd head
          glyf diff --baseline ../base
          cat target/glyf/diff/summary.md >> "$GITHUB_STEP_SUMMARY"

      - uses: actions/upload-artifact@v4
        with:
          name: visual-diff
          path: head/target/glyf/diff

      - name: Comment on the pull request
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --repo "$GITHUB_REPOSITORY" \
            --body-file head/target/glyf/diff/summary.md
```

A pull request from a fork gets a read-only token and cannot comment. The
summary is still written to the run page by the `Compare` step.

Building the base needs the base's models. Against a warehouse, give the two
builds their own dbt targets so that neither overwrites the other's tables.
glyf's own repository runs this workflow against its example projects; see
[`visual-diff.yml`](https://github.com/glyf-data/glyf/blob/main/.github/workflows/visual-diff.yml).

Add `--fail-on-change` to make the step exit 1 when any chart changed, was
added or was removed. That suits a branch where the dashboards must not move,
such as a refactor.
