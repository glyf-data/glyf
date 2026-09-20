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
~ margin_share: 31.3% of the picture moved (the rows changed)
✓ 2 changed, 6 unchanged
✓ wrote target/glyf/diff/index.html
```

`--baseline` takes a `target/glyf` directory, an exported site, or a project
that contains one.

## What it writes

Everything goes under `target/glyf/diff/`, which holds its own copies of the
images and can be uploaded as it is.

| File | For |
| --- | --- |
| `index.html` | A reviewer. Each changed chart before, after, and marked up. |
| `summary.md` | A pull request comment. One table row per changed chart. |
| `diff.json` | A script. Status, pixel counts, reasons and row changes per chart. |
| `images/` | `<chart>.before.png`, `<chart>.after.png`, `<chart>.diff.png` |

The marked-up image is the new chart faded back, with every pixel that differs
from the baseline drawn on top in one colour.

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

A numeric column is summarised by its sum. For a rate or a percentage the sum
means nothing by itself; read it as "this column moved" and look at the picture.

Row changes need both builds to have published their rows. A build under
[`export.row_data: exclude`](data-exposure.md) publishes none, and the diff
then reports the pictures alone.

## In a pull request

Build the base branch and the pull request in the same job, then compare. The
same runner draws both, so the comparison can be exact.

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
