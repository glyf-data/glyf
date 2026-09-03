# Benchmarks

Measurements that are too slow to be tests. Nothing here runs in CI; each
command renders real charts through the real renderer, which is the point.

Artifacts are written under `target/glyf/bench/`, so a downsampled chart can be
compared against its baseline by eye. That comparison is not optional — the
cheapest downsampling strategy is also the one that quietly redraws the data,
and no file-size number catches it.

## Downsampling

```bash
uv run python bench/downsampling.py sweep      # baseline vs downsampled, per row count
uv run python bench/downsampling.py ceiling    # where rendering stops working
uv run python bench/downsampling.py density    # a binned scatter that keeps its counts
```

`glyf` is a compile-time renderer, so an SVG spends a DOM node per mark and the
cost of a chart tracks its mark count. `sweep` measures that cost against three
ways of reducing marks before the renderer sees them:

- **mean** — one mark per x bin at the mean of its rows
- **M4** — the first, last, highest and lowest row of each x bin, which are the
  four that decide what a line renderer paints in that pixel column
- **grid** — one mark per occupied cell of a 2D grid, with the row count behind it

### What it measured

Run 2026-09-03 on `v0.5.0`, macOS arm64, altair 6.1.0 / vl-convert 1.9.0 /
duckdb 1.5.2. One chart, 800x400, SVG and PNG.

100k rows:

| case | marks | bin ms | render ms | SVG MB |
| --- | --- | --- | --- | --- |
| line baseline | 100,000 | – | 2741 | 27.59 |
| line mean, 800 bins | 800 | 3 | 74 | 0.24 |
| line M4, 800 bins | 3,143 | 4 | 122 | 0.87 |
| scatter baseline | 100,000 | – | 2919 | 28.23 |
| scatter grid 160x80 | 11,549 | 4 | 348 | 3.39 |
| scatter grid 80x40 | 3,226 | 3 | 137 | 0.95 |

Binning costs one DuckDB aggregation pass — 5–17 ms for a million rows — and
output size then depends on the bin count rather than the row count: 800 bins
is 0.24 MB whether it started from 10k rows or 1M.

### Where rendering stops working

`ceiling` runs each row count in its own process, because the failure is not an
exception. A one-series line chart renders at 500k rows and aborts above it:

| rows | result | render | SVG |
| --- | --- | --- | --- |
| 200,000 | ok | 5.6 s | 55.3 MB |
| 400,000 | ok | 11.5 s | 110.7 MB |
| 500,000 | ok | 18.2 s | 138.8 MB |
| 600,000 | crash | – | – |

```
# Fatal JavaScript out of memory: Ineffective mark-compacts near heap limit
```

That is vl-convert's V8 heap, around 1.4 GB. It takes the whole process with it
— exit 133, no Python traceback, a V8 C stack trace instead.

### What the pictures show

Numbers rank the strategies; only the rendered artifacts separate them.

- **M4 is faithful.** At 100k rows it reproduces the baseline image — same
  noise envelope, same y range, same shape — at 3,143 marks instead of 100,000.
- **Mean is not.** It keeps the signal and drops the spread with it: on the test
  series the y axis silently narrowed from 14–86 to 20–80 and the envelope
  disappeared. The chart looks clean, and is not the chart the data draws.
- **Grid binning changes a scatter.** Marks snap to a lattice, visibly at
  160x80 and unmistakably at 80x40, where it stops reading as a scatter plot.
  It also drops density: a cell holding one row draws like a cell holding a
  thousand. `density` encodes the count instead, which is honest about density
  but spends the colour channel on it, so the chart can no longer carry the
  series a scatter was coloured by.
