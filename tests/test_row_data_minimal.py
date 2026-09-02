"""Publishing only what the chart shows.

`export.row_data: minimal` sits between `include` and `exclude`: interactivity
survives, but the export carries no information beyond what the rendered chart
displays. That means column pruning only -- values are never rounded or
transformed, because a chart that disagrees with the warehouse is a worse
problem than the precision it leaks.

Two things carry more than the picture by default: an interactive chart inlines
its Vega spec with *every* column the query returned, encoded or not, and a
static SVG carries each row's exact values in a per-mark accessibility label.
"""

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from glyf.config import ConfigError, ExportConfig, GlyfConfig, load_config
from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

# A column the query returns but no VISUALISE role binds. Its value exists
# nowhere else, so finding it in the output means the rows were over-shipped.
UNENCODED_VALUE = "LEAK-a3f9c1"
# Values the chart *does* encode. The picture shows them, so they may be
# published; what may not be published is their exact figure in a label.
ENCODED_REGION = "Acme Holdings"
ENCODED_REVENUE = "987654321"


def test_unencoded_columns_are_not_published(tmp_path: Path) -> None:
    project = _built_project(tmp_path, row_data="minimal")

    published = _published_text(project)

    assert UNENCODED_VALUE not in published
    # The column's *name* is published: compiled SQL selects it, and compiled
    # SQL is metadata that behaves as under `include`.
    assert "secret_col" in (
        project / "target" / "glyf" / "site" / "compiled" / "revenue.sql"
    ).read_text(encoding="utf-8")


def test_the_same_column_is_published_by_default(tmp_path: Path) -> None:
    """The guard above is only meaningful if the default really does publish."""
    project = _built_project(tmp_path, row_data="include")

    assert UNENCODED_VALUE in _published_text(project)


def test_vega_datasets_carry_only_encoded_columns(tmp_path: Path) -> None:
    project = _built_project(tmp_path, row_data="minimal")

    spec = _inlined_vega_spec(project)
    (rows,) = spec["datasets"].values()

    assert rows, "the chart still has its rows -- this is pruning, not exclusion"
    assert all(set(row) == {"month", "revenue", "region"} for row in rows)
    # Values are what the warehouse returned, untouched.
    assert rows[0]["revenue"] == int(ENCODED_REVENUE)
    assert rows[0]["region"] == ENCODED_REGION


def test_interactivity_survives(tmp_path: Path) -> None:
    """The point of the mode: `exclude` would have downgraded this to a PNG."""
    project = _project(tmp_path)
    _write_chart(project)

    result = render_project(project, _config("minimal"))

    assert result.warnings == ()
    project = _finish_build(project, row_data="minimal")
    spec = _inlined_vega_spec(project)
    assert [t["field"] for t in spec["encoding"]["tooltip"]] == [
        "month",
        "revenue",
        "region",
    ]
    assert any(param.get("bind") == "legend" for param in spec["params"])


def test_svg_mark_labels_keep_field_names_and_drop_values(tmp_path: Path) -> None:
    project = _built_project(tmp_path, row_data="minimal")
    svg = (project / "target" / "glyf" / "charts" / "revenue.svg").read_text(
        encoding="utf-8"
    )

    labels = re.findall(r'aria-label="([^"]*)"', svg)

    assert "month; revenue; region" in labels, "the marks name their columns"
    assert not [label for label in labels if label.startswith("month: ")]
    assert f"revenue: {ENCODED_REVENUE}" not in svg
    assert f"region: {ENCODED_REGION}" not in svg
    # ...while the same build under `include` labels every mark with its row.
    included = _built_project(tmp_path / "include", row_data="include")
    included_svg = (
        included / "target" / "glyf" / "charts" / "revenue.svg"
    ).read_text(encoding="utf-8")
    assert f"revenue: {ENCODED_REVENUE}" in included_svg


def test_svg_still_describes_what_the_page_shows(tmp_path: Path) -> None:
    """Axes, legends and titles are text on the page; their labels stay."""
    project = _built_project(tmp_path, row_data="minimal")
    svg = (project / "target" / "glyf" / "charts" / "revenue.svg").read_text(
        encoding="utf-8"
    )

    assert "Monthly Revenue" in svg
    assert re.search(r'aria-label="[^"]*legend[^"]*region', svg, re.IGNORECASE)


def test_compiled_sql_and_svg_are_published(tmp_path: Path) -> None:
    """Compiled SQL is metadata, not data; it behaves as under `include`."""
    project = _built_project(tmp_path, row_data="minimal")
    site = project / "target" / "glyf" / "site"

    assert (site / "compiled" / "revenue.sql").exists()
    assert (site / "charts" / "revenue.svg").exists()
    assert (site / "charts" / "revenue.png").exists()
    dashboard = (site / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert "glyf-source-sql" in dashboard, "the SQL drawer is not withheld"


def test_the_local_data_file_keeps_every_column(tmp_path: Path) -> None:
    """Pruning is for the published chart; the person who ran the build keeps the rows."""
    project = _built_project(tmp_path, row_data="minimal")
    data_json = (
        project / "target" / "glyf" / "data" / "normalized" / "revenue.data.json"
    )

    payload = json.loads(data_json.read_text(encoding="utf-8"))

    assert "secret_col" in payload["fields"]
    assert not list((project / "target" / "glyf" / "site").rglob("*.data.json"))


def test_the_public_manifest_reports_the_mode(tmp_path: Path) -> None:
    project = _built_project(tmp_path, row_data="minimal")
    site = project / "target" / "glyf" / "site"

    bundle = json.loads((site / "bundle.json").read_text(encoding="utf-8"))

    assert bundle["security"]["row_data"] == "minimal"
    artifacts = bundle["charts"]["revenue"]["artifacts"]
    assert artifacts["svg"] == "charts/revenue.svg"
    assert artifacts["compiled_sql"] == "compiled/revenue.sql"
    assert bundle["charts"]["revenue"]["interactions"] == ["tooltip", "zoom", "legend_filter"]


def test_minimal_loads_from_glyf_yml(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "export:\n  row_data: minimal\n", encoding="utf-8"
    )

    config = load_config(tmp_path)

    assert config.export.row_data == "minimal"
    assert config.export.prunes_row_data
    assert not config.export.excludes_row_data


def test_an_unknown_mode_names_the_accepted_ones(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "export:\n  row_data: partial\n", encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="exclude, include, minimal"):
        load_config(tmp_path)


def _config(row_data: str) -> GlyfConfig:
    return replace(GlyfConfig(), export=ExportConfig(row_data=row_data))


def _project(tmp_path: Path) -> Path:
    project = copy_basic_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        "month,region,revenue,secret_col\n"
        f"2026-01,{ENCODED_REGION},{ENCODED_REVENUE},{UNENCODED_VALUE}\n",
        encoding="utf-8",
    )
    return project


def _write_chart(project: Path) -> None:
    (project / "visualisations" / "revenue.ggsql").write_text(
        "SELECT month, region, revenue, secret_col\n"
        "FROM {{ ref('fct_orders') }}\n"
        "\n"
        "VISUALISE month AS x, revenue AS y, region AS color\n"
        "DRAW bar\n"
        "LABEL title => 'Monthly Revenue'\n"
        "INTERACT tooltip, zoom, legend_filter\n",
        encoding="utf-8",
    )


def _finish_build(project: Path, *, row_data: str) -> Path:
    config = _config(row_data)
    generate_dashboards(project, config)
    export_site(project, config=config)
    return project


def _built_project(tmp_path: Path, *, row_data: str) -> Path:
    project = _project(tmp_path)
    _write_chart(project)
    render_project(project, _config(row_data))
    return _finish_build(project, row_data=row_data)


def _published_text(project: Path) -> str:
    """Everything under site/ that a browser or a curl could read as text."""
    site = project / "target" / "glyf" / "site"
    chunks = []
    for path in sorted(site.rglob("*")):
        if path.is_file() and path.suffix not in {".png", ".ttf", ".zip"}:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def _inlined_vega_spec(project: Path) -> dict:
    dashboard = (
        project / "target" / "glyf" / "site" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="chart-revenue-spec">(.*?)</script>',
        dashboard,
        re.DOTALL,
    )
    assert match is not None, "the interactive chart inlines its spec"
    return json.loads(match.group(1))

