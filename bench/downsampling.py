"""Measure what a chart costs as its mark count grows, and what downsampling saves.

`glyf` is a compile-time renderer: every mark a chart draws becomes a node in
the SVG it publishes, so cost tracks marks, not rows -- until vl-convert's V8
heap runs out and takes the process with it. This harness measures both ends of
that: what the current path costs at a given row count, where it stops working,
and how much of it three downsampling strategies give back.

    uv run python bench/downsampling.py sweep      # baseline vs downsampled
    uv run python bench/downsampling.py ceiling    # where rendering stops working
    uv run python bench/downsampling.py density    # a binned scatter that keeps its counts

Nothing here is part of the test suite or of CI: it renders real charts through
the real renderer, which is slow by design. Only the table handed to
`render_chart` differs between a baseline row and a downsampled one.

The strategies, and why there are three:

`bin_mean` averages y per x bin. Smallest output, and the one to distrust: it
redraws the signal, so a noisy series loses its envelope and the y axis
silently narrows with it.

`bin_m4` keeps the first, last, highest and lowest row of each x bin -- the four
that decide what a line renderer paints in that pixel column. Every value
survives from the warehouse rather than being computed, which is why the drawn
line stays the line the full result would have drawn.

`bin_grid` bins both axes and emits one mark per occupied cell, with a count.
It shrinks a scatter as well as M4 shrinks a line, but it snaps marks to a
lattice and drops density -- a cell holding one row draws like a cell holding a
thousand. `density` renders the same table with the count encoded, which is
honest about density but is a different chart.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb
import pyarrow as pa

from glyf.config import RenderConfig
from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart, VisualiseMapping
from glyf.ggsql.renderer import render_chart

DEFAULT_OUT = Path("target/glyf/bench")
WIDTH, HEIGHT = 800, 400


# ---------------------------------------------------------------- test data

def make_scatter_data(rows: int) -> pa.Table:
    """A trend, noise around it, and four series: structure downsampling must keep."""
    return duckdb.sql(f"""
        select
            i * (100.0 / {rows})                                as x,
            sin(i * (100.0 / {rows}) / 8.0) * 25 + 50
                + (random() - 0.5) * 18
                + (i % 4) * 6                                   as y,
            'series_' || (i % 4)                                as series
        from range({rows}) t(i)
    """).to_arrow_table()


def make_line_data(rows: int) -> pa.Table:
    """A dense single series whose noise envelope is part of the picture."""
    return duckdb.sql(f"""
        select
            i                                                   as x,
            sin(i / ({rows} / 40.0)) * 30 + 50
                + (random() - 0.5) * 12                         as y
        from range({rows}) t(i)
    """).to_arrow_table()


# -------------------------------------------------------------- downsampling

def bin_mean(table: pa.Table, x: str, y: str, bins: int) -> pa.Table:
    """One mark per x bin, at the mean of its rows. Smallest, and lossy in a way
    that does not look lossy: the spread of the rows disappears into the mean."""
    arrow_table = table  # duckdb's replacement scan resolves this by name
    return duckdb.sql(f"""
        with t as (select * from arrow_table),
        bounds as (select min({x}) as x0, max({x}) as x1 from t),
        binned as (
            select
                least(floor(({x} - x0) / nullif(x1 - x0, 0) * {bins}), {bins} - 1) as bin_x,
                x0, x1, {y}
            from t, bounds
        )
        select
            x0 + (bin_x + 0.5) * (x1 - x0) / {bins} as {x},
            avg({y})                                as {y}
        from binned
        group by bin_x, x0, x1
        order by 1
    """).to_arrow_table()


def bin_m4(table: pa.Table, x: str, y: str, bins: int) -> pa.Table:
    """The first, last, highest and lowest row of each x bin: at most four marks
    per pixel column, and every one of them a row the warehouse returned."""
    arrow_table = table  # duckdb's replacement scan resolves this by name
    return duckdb.sql(f"""
        with t as (select * from arrow_table),
        bounds as (select min({x}) as x0, max({x}) as x1 from t),
        binned as (
            select
                least(floor(({x} - x0) / nullif(x1 - x0, 0) * {bins}), {bins} - 1) as bin_x,
                {x}, {y}
            from t, bounds
        ),
        agg as (
            select bin_x, min({x}) as xmin, max({x}) as xmax,
                          min({y}) as ymin, max({y}) as ymax
            from binned group by bin_x
        )
        select distinct b.{x} as {x}, b.{y} as {y}
        from binned b join agg a on b.bin_x = a.bin_x
        where b.{x} = a.xmin or b.{x} = a.xmax
           or b.{y} = a.ymin or b.{y} = a.ymax
        order by 1
    """).to_arrow_table()


def bin_grid(
    table: pa.Table, x: str, y: str, color: str | None, nx: int, ny: int
) -> pa.Table:
    """One mark per occupied cell of an nx by ny grid, at the cell centre, with
    the number of rows behind it. Marks become bounded by the grid rather than
    by the row count -- at the cost of drawing every mark on a lattice."""
    arrow_table = table  # duckdb's replacement scan resolves this by name
    group = f", {color}" if color else ""
    select_color = f"{color}," if color else ""
    return duckdb.sql(f"""
        with t as (select * from arrow_table),
        bounds as (
            select min({x}) as x0, max({x}) as x1, min({y}) as y0, max({y}) as y1 from t
        ), binned as (
            select
                {select_color}
                least(floor(({x} - x0) / nullif(x1 - x0, 0) * {nx}), {nx} - 1) as bin_x,
                least(floor(({y} - y0) / nullif(y1 - y0, 0) * {ny}), {ny} - 1) as bin_y,
                x0, x1, y0, y1
            from t, bounds
        )
        select
            {select_color}
            x0 + (bin_x + 0.5) * (x1 - x0) / {nx} as {x},
            y0 + (bin_y + 0.5) * (y1 - y0) / {ny} as {y},
            count(*)                              as n
        from binned
        group by bin_x, bin_y, x0, x1, y0, y1{group}
        order by {x}
    """).to_arrow_table()


# --------------------------------------------------------------- measurement

@dataclass
class Measure:
    case: str
    rows: int
    marks: int
    bin_ms: float
    render_ms: float
    svg_bytes: int
    png_bytes: int

    def row(self) -> str:
        return (
            f"{self.case:<30} {self.rows:>9,} {self.marks:>9,} "
            f"{self.bin_ms:>8.0f} {self.render_ms:>10.0f} "
            f"{self.svg_bytes / 1e6:>9.2f} {self.png_bytes / 1e3:>9.0f}"
        )


HEADER = (
    f"{'case':<30} {'rows':>9} {'marks':>9} "
    f"{'bin ms':>8} {'render ms':>10} {'svg MB':>9} {'png KB':>9}"
)


def spec_for(name: str, draw: str, color: str | None) -> GgsqlChart:
    visualise = [VisualiseMapping("x", "x"), VisualiseMapping("y", "y")]
    if color:
        visualise.append(VisualiseMapping(color, "color"))
    return GgsqlChart(
        path=Path(f"{name}.ggsql"),
        name=name,
        sql="select 1",
        visualise=tuple(visualise),
        draw_type=draw,
        labels={"title": name},
        config={"width": WIDTH, "height": HEIGHT},
        interactions=(),
    )


def measure(
    case: str,
    chart: GgsqlChart,
    table: pa.Table,
    source_rows: int,
    out: Path,
    bin_ms: float = 0.0,
) -> Measure:
    """Render one chart and report what it cost. Artifacts stay on disk so the
    downsampled picture can be compared against the baseline by eye -- the only
    check that catches a strategy which is small and wrong."""
    out.mkdir(parents=True, exist_ok=True)
    slug = case.replace(" ", "_").replace(",", "")
    png, svg = out / f"{slug}.png", out / f"{slug}.svg"
    for path in (png, svg):
        path.unlink(missing_ok=True)

    start = time.perf_counter()
    render_chart(
        chart,
        QueryResult.from_arrow(table),
        png,
        svg,
        RenderConfig(formats=("svg", "png"), default_width=WIDTH, default_height=HEIGHT),
    )
    render_ms = (time.perf_counter() - start) * 1000

    return Measure(
        case=case,
        rows=source_rows,
        marks=table.num_rows,
        bin_ms=bin_ms,
        render_ms=render_ms,
        svg_bytes=svg.stat().st_size if svg.exists() else 0,
        png_bytes=png.stat().st_size if png.exists() else 0,
    )


def timed(fn, *args) -> tuple[pa.Table, float]:
    start = time.perf_counter()
    result = fn(*args)
    return result, (time.perf_counter() - start) * 1000


# ---------------------------------------------------------------- subcommands

def cmd_sweep(args: argparse.Namespace) -> int:
    results: list[Measure] = []
    print(HEADER)
    print("-" * len(HEADER))

    for rows in args.rows:
        data = make_scatter_data(rows)
        chart = spec_for(f"scatter_{rows}", "scatter", "series")
        if rows <= args.baseline_limit:
            results.append(measure(f"scatter {rows:,} baseline", chart, data, rows, args.out))
            print(results[-1].row(), flush=True)
        for nx, ny in ((160, 80), (80, 40)):
            binned, ms = timed(bin_grid, data, "x", "y", "series", nx, ny)
            results.append(
                measure(f"scatter {rows:,} grid {nx}x{ny}", chart, binned, rows, args.out, ms)
            )
            print(results[-1].row(), flush=True)

        data = make_line_data(rows)
        chart = spec_for(f"line_{rows}", "line", None)
        if rows <= args.baseline_limit:
            results.append(measure(f"line {rows:,} baseline", chart, data, rows, args.out))
            print(results[-1].row(), flush=True)
        for bins in (800, 400):
            for name, fn in (("mean", bin_mean), ("m4", bin_m4)):
                binned, ms = timed(fn, data, "x", "y", bins)
                results.append(
                    measure(f"line {rows:,} {name} {bins}", chart, binned, rows, args.out, ms)
                )
                print(results[-1].row(), flush=True)

    report = args.out / "sweep.json"
    report.write_text(json.dumps([asdict(m) for m in results], indent=2), encoding="utf-8")
    print(f"\nartifacts and {report.name} under {args.out}/")
    return 0


def cmd_ceiling(args: argparse.Namespace) -> int:
    """Find the row count where rendering stops working.

    Each probe runs in its own process because the failure mode is not an
    exception: vl-convert's V8 heap aborts, which would take this one down too.
    """
    print(f"{'rows':>9}  {'result':<10} {'render ms':>10} {'svg MB':>9}")
    print("-" * 43)
    for rows in args.rows:
        probe = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()),
             "--out", str(args.out), "_probe", str(rows)],
            capture_output=True,
            text=True,
        )
        line = probe.stdout.strip().splitlines()[-1] if probe.stdout.strip() else ""
        if probe.returncode == 0 and line:
            measured = json.loads(line)
            print(
                f"{rows:>9,}  {'ok':<10} {measured['render_ms']:>10.0f} "
                f"{measured['svg_bytes'] / 1e6:>9.2f}",
                flush=True,
            )
            continue

        reason = "V8 OOM" if "out of memory" in probe.stderr else f"exit {probe.returncode}"
        print(f"{rows:>9,}  {'CRASH':<10} {reason:>10}", flush=True)
        if args.stop_on_crash:
            print("\nstopping at the first failure; pass --no-stop-on-crash to continue")
            return 0
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    """One row count, one process: the child half of `ceiling`."""
    rows = args.rows[0]
    measured = measure(
        f"probe line {rows:,}", spec_for(f"line_{rows}", "line", None),
        make_line_data(rows), rows, args.out,
    )
    print(json.dumps(asdict(measured)))
    return 0


def cmd_density(args: argparse.Namespace) -> int:
    """The binned scatter with its counts encoded, which `bin_grid` alone throws away."""
    import altair as alt

    rows = args.rows[0]
    nx, ny = 160, 80
    binned, bin_ms = timed(bin_grid, make_scatter_data(rows), "x", "y", None, nx, ny)
    print(f"{rows:,} rows -> {binned.num_rows:,} occupied cells in {bin_ms:.0f} ms")

    chart = (
        alt.Chart(binned)
        .mark_rect()
        .encode(
            x=alt.X("x", bin=alt.Bin(maxbins=nx), title="x"),
            y=alt.Y("y", bin=alt.Bin(maxbins=ny), title="y"),
            color=alt.Color("n", scale=alt.Scale(scheme="blues"), title="rows"),
        )
        .properties(width=WIDTH, height=HEIGHT, title=f"density, {rows:,} rows, {nx}x{ny} bins")
    )
    args.out.mkdir(parents=True, exist_ok=True)
    png, svg = args.out / "density.png", args.out / "density.svg"
    start = time.perf_counter()
    chart.save(svg)
    chart.save(png)
    print(
        f"render {(time.perf_counter() - start) * 1000:.0f} ms  "
        f"svg {svg.stat().st_size / 1e6:.2f} MB  png {png.stat().st_size / 1e3:.0f} KB"
    )
    print(
        "\nnote: colour now carries the count, so a density plot cannot also "
        "carry the series a scatter coloured by."
    )
    return 0


def rows_list(value: str) -> list[int]:
    return [int(part) for part in value.split(",")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where artifacts go")
    sub = parser.add_subparsers(dest="command", required=True)

    sweep = sub.add_parser("sweep", help="baseline vs downsampled, per row count")
    sweep.add_argument("--rows", type=rows_list, default=[1_000, 10_000, 100_000])
    sweep.add_argument(
        "--baseline-limit",
        type=int,
        default=500_000,
        help="skip the baseline above this row count; it crashes past ~500k",
    )
    sweep.set_defaults(func=cmd_sweep)

    ceiling = sub.add_parser("ceiling", help="find where rendering stops working")
    ceiling.add_argument(
        "--rows", type=rows_list, default=[200_000, 400_000, 500_000, 600_000, 700_000]
    )
    ceiling.add_argument("--stop-on-crash", action=argparse.BooleanOptionalAction, default=True)
    ceiling.set_defaults(func=cmd_ceiling)

    density = sub.add_parser("density", help="a binned scatter that keeps its counts")
    density.add_argument("--rows", type=rows_list, default=[100_000])
    density.set_defaults(func=cmd_density)

    probe = sub.add_parser("_probe", help=argparse.SUPPRESS)
    probe.add_argument("rows", type=rows_list)
    probe.set_defaults(func=cmd_probe)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
