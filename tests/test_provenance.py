"""Recording what a build did.

A published artifact says almost nothing about how it came to exist. The
record answers the one audit question glyf can answer: what went into this
artifact and how was it built. The other three -- which queries ran, who
opened the dashboard, who copied the numbers out -- belong to the warehouse,
the edge, and nobody respectively.

The record is deliberately not published by default: it names the warehouse
identity and the selectors.
"""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyf.cli import app
from glyf.config import (
    ConfigError,
    ExecutionConfig,
    ExportConfig,
    GlyfConfig,
    PrivacyConfig,
    load_config,
)
from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.manifest.loader import load_manifest
from glyf.pipeline import render_project
from glyf.provenance import sql_digest
from tests.helpers import copy_basic_project

runner = CliRunner()

EMAIL = "jane.doe@acme.example"


# --- what the record says -----------------------------------------------------


def test_the_record_names_the_identity_the_queries_ran_as(tmp_path: Path) -> None:
    """The whole point: the role behind this target bounded what is in here."""
    project = _project(tmp_path)
    config = replace(
        GlyfConfig(),
        execution=ExecutionConfig(backend="duckdb", target="finance", max_rows=500),
    )

    record = render_project(project, config).build.to_payload()

    assert record["execution"] == {
        "backend": "duckdb",
        "target": "finance",
        "mode": "full",
        "max_rows": 500,
    }
    assert record["outcome"] == "success"
    assert record["error"] is None
    assert record["project"] == "basic"
    assert record["duration_ms"] >= 0


def test_the_record_counts_the_rows_each_chart_pulled(tmp_path: Path) -> None:
    project = _project(tmp_path)

    record = render_project(project).build.to_payload()

    assert record["charts"]["revenue"]["row_count"] == 2


def test_the_record_digests_the_sql_rather_than_repeating_it(tmp_path: Path) -> None:
    """A digest notices that what ran changed without naming the tables."""
    project = _project(tmp_path)

    before = render_project(project).build.to_payload()
    _write_chart(project, "SELECT month, revenue, email")
    after = render_project(project).build.to_payload()

    digest = before["charts"]["revenue"]["compiled_sql_sha256"]
    assert len(digest) == 16
    assert "fct_orders" not in digest
    assert after["charts"]["revenue"]["compiled_sql_sha256"] != digest


def test_the_record_says_what_the_privacy_policy_did(tmp_path: Path) -> None:
    project = _project(tmp_path, tag_email=True)
    _write_chart(project, "SELECT month, revenue, email")
    config = replace(
        GlyfConfig(), privacy=PrivacyConfig(on_pii="redact", redaction="hash")
    )

    record = render_project(project, config).build.to_payload()

    assert record["privacy"]["on_pii"] == "redact"
    assert record["privacy"]["redaction"] == "hash"
    assert record["charts"]["revenue"]["redacted_columns"] == ["email"]


def test_the_record_keeps_the_scan_warnings(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write_chart(project, "SELECT month, revenue, email AS contact")

    record = render_project(project).build.to_payload()

    assert record["charts"]["revenue"]["scan_warnings"] == [
        {"column": "contact", "kind": "email addresses", "matched": 2, "sampled": 2}
    ]


def test_the_record_says_which_dashboards_were_left_out(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _write_second_dashboard(project)

    record = render_project(project, select=("tag:hr",)).build.to_payload()

    assert record["selection"] == {"selectors": ["tag:hr"], "dashboards": ["people"]}


def test_an_unrestricted_build_records_no_selection(tmp_path: Path) -> None:
    project = _project(tmp_path)

    assert render_project(project).build.to_payload()["selection"] is None


def test_the_record_names_the_dbt_run_it_was_built_from(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _set_manifest_generated_at(project, "2026-09-02T10:00:00.000000Z")

    record = render_project(project).build.to_payload()

    assert record["dbt_manifest_generated_at"] == "2026-09-02T10:00:00.000000Z"
    assert load_manifest(project / "target" / "manifest.json").generated_at is not None


def test_a_manifest_without_a_timestamp_records_none(tmp_path: Path) -> None:
    project = _project(tmp_path)

    assert render_project(project).build.to_payload()["dbt_manifest_generated_at"] is None


def test_validate_mode_records_no_row_count(tmp_path: Path) -> None:
    """A validate run fetches no rows. That is not zero rows."""
    project = _project(tmp_path)
    config = replace(GlyfConfig(), execution=ExecutionConfig(mode="validate"))

    record = render_project(project, config).build.to_payload()

    assert record["execution"]["mode"] == "validate"
    assert record["charts"]["revenue"]["row_count"] is None
    assert record["charts"]["revenue"]["compiled_sql_sha256"] == sql_digest(
        (project / "target" / "glyf" / "compiled" / "revenue.sql").read_text().strip()
    )


# --- where the record goes ----------------------------------------------------


def test_the_record_is_written_beside_the_artifacts_and_not_published(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)

    result = runner.invoke(app, ["build", "--project", str(project)])

    assert result.exit_code == 0, result.output
    output = project / "target" / "glyf"
    assert (output / "build.json").exists()
    assert not (output / "site" / "build.json").exists()


def test_the_local_manifest_carries_it_and_the_public_one_does_not(
    tmp_path: Path,
) -> None:
    """It names the warehouse identity and the selectors."""
    project = _project(tmp_path)
    _build(project, GlyfConfig())

    local = json.loads((project / "target" / "glyf" / "bundle.json").read_text())
    public = json.loads(
        (project / "target" / "glyf" / "site" / "bundle.json").read_text()
    )

    assert local["build"]["outcome"] == "success"
    assert "build" not in public


def test_publishing_the_record_is_opt_in(tmp_path: Path) -> None:
    project = _project(tmp_path)
    config = replace(GlyfConfig(), export=ExportConfig(provenance="public"))

    _build(project, config)

    public = json.loads(
        (project / "target" / "glyf" / "site" / "bundle.json").read_text()
    )
    assert public["build"]["charts"]["revenue"]["row_count"] == 2


def test_adding_the_block_does_not_change_the_bundle_version(tmp_path: Path) -> None:
    """The documented contract allows added fields; consumers ignore what they don't know."""
    project = _project(tmp_path)
    _build(project, GlyfConfig())

    local = json.loads((project / "target" / "glyf" / "bundle.json").read_text())

    assert local["bundle_version"] == "1"


# --- the event log ------------------------------------------------------------


def test_the_log_appends_one_line_per_build(tmp_path: Path) -> None:
    project = _project(tmp_path)
    log = tmp_path / "logs" / "builds.jsonl"

    for _ in range(2):
        result = runner.invoke(
            app, ["build", "--project", str(project), "--log-json", str(log)]
        )
        assert result.exit_code == 0, result.output

    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert all(json.loads(line)["outcome"] == "success" for line in lines)


def test_a_failed_build_is_logged_too(tmp_path: Path) -> None:
    """A log of successes only is a weak audit."""
    project = _project(tmp_path, tag_email=True)
    _write_chart(project, "SELECT month, revenue, email")
    log = tmp_path / "builds.jsonl"

    result = runner.invoke(
        app, ["build", "--project", str(project), "--log-json", str(log)]
    )

    assert result.exit_code == 1
    (event,) = [json.loads(line) for line in log.read_text().strip().splitlines()]
    assert event["outcome"] == "failed"
    assert "returns a PII column: 'email'" in event["error"]
    assert event["charts"] == {}
    # ...and the settings the attempt ran with are still recorded.
    assert event["privacy"]["on_pii"] == "deny"


def test_no_log_file_means_no_log(tmp_path: Path) -> None:
    project = _project(tmp_path)

    runner.invoke(app, ["build", "--project", str(project)])

    assert not list(tmp_path.rglob("*.jsonl"))


# --- configuration ------------------------------------------------------------


def test_provenance_mode_loads_from_glyf_yml(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "export:\n  provenance: public\n", encoding="utf-8"
    )

    config = load_config(tmp_path)

    assert config.export.provenance == "public"
    assert config.export.publishes_provenance
    assert not ExportConfig().publishes_provenance


def test_an_unknown_provenance_mode_is_named(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "export:\n  provenance: sometimes\n", encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="'export.provenance' must be one of local, public"):
        load_config(tmp_path)


# --- helpers ------------------------------------------------------------------


def _project(tmp_path: Path, *, tag_email: bool = False) -> Path:
    project = copy_basic_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        f"month,revenue,email\n2026-01,100,{EMAIL}\n2026-02,200,{EMAIL}\n",
        encoding="utf-8",
    )
    _write_chart(project, "SELECT month, revenue")
    if tag_email:
        path = project / "target" / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["nodes"]["model.basic.fct_orders"]["columns"] = {
            "email": {"name": "email", "meta": {"pii": True}}
        }
        path.write_text(json.dumps(manifest), encoding="utf-8")
    return project


def _write_chart(project: Path, select: str) -> None:
    (project / "visualisations" / "revenue.ggsql").write_text(
        f"{select}\nFROM {{{{ ref('fct_orders') }}}}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW bar\nLABEL title => 'Revenue'\n",
        encoding="utf-8",
    )


def _write_second_dashboard(project: Path) -> None:
    (project / "visualisations" / "headcount.ggsql").write_text(
        "SELECT month, revenue\nFROM {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW bar\nLABEL title => 'Headcount'\n",
        encoding="utf-8",
    )
    (project / "dashboards" / "people.yml").write_text(
        "name: people\ntitle: People\ntags:\n  - hr\n\ncharts:\n  - headcount\n",
        encoding="utf-8",
    )


def _set_manifest_generated_at(project: Path, value: str) -> None:
    path = project / "target" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["metadata"] = {"generated_at": value}
    path.write_text(json.dumps(manifest), encoding="utf-8")


def _build(project: Path, config: GlyfConfig) -> None:
    render_project(project, config)
    generate_dashboards(project, config)
    export_site(project, config=config)
