"""Keeping PII out of a chart.

Classification is the union of two sources: columns the dbt project tags as
PII in `schema.yml` (read from the manifest, on the models and sources a chart
reads) and `privacy.pii_columns` in `glyf.yml`. Enforcement happens once, on
the query result, before anything reads it -- so it covers every backend, the
local data file, and validate mode alike.

The documented limit is name matching: `select email as contact` yields a
column no manifest tags. The `glyf.yml` list exists for that alias.
"""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from typer.testing import CliRunner

from glyf.cli import app
from glyf.config import ConfigError, ExecutionConfig, GlyfConfig, PrivacyConfig, load_config
from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.execution import QueryResult
from glyf.pipeline import RenderError, render_project
from glyf.privacy import hash_value, mask_value, redact_columns, scan_for_pii
from tests.helpers import copy_basic_project

EMAIL = "jane.doe@acme.example"
PHONE = "+1-555-0100"


# --- classification ---------------------------------------------------------


def test_a_manifest_tagged_column_fails_the_build(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, "SELECT month, revenue, email")

    with pytest.raises(RenderError) as excinfo:
        render_project(project, _config())

    message = str(excinfo.value)
    assert "revenue.ggsql returns a PII column: 'email'" in message
    assert "tagged pii on model fct_orders" in message
    assert "privacy.on_pii: redact" in message


def test_a_pii_tag_counts_too(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={"phone": {"tags": ["PII"]}})
    _write_chart(project, "SELECT month, revenue, phone")

    with pytest.raises(RenderError, match="'phone' \\(tagged pii on model fct_orders\\)"):
        render_project(project, _config())


def test_a_glyf_yml_column_covers_an_alias(tmp_path: Path) -> None:
    """dbt tags `email`; the query renames it, and only glyf.yml can know."""
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, "SELECT month, revenue, email AS contact")

    render_project(project, _config())  # the alias slips past the manifest

    with pytest.raises(RenderError) as excinfo:
        render_project(project, _config(pii_columns=("contact",)))
    assert "'contact' (listed in glyf.yml privacy.pii_columns)" in str(excinfo.value)


def test_matching_ignores_case(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, 'SELECT month, revenue, email AS "Email"')

    with pytest.raises(RenderError, match="'Email'"):
        render_project(project, _config())


def test_only_the_models_a_chart_reads_classify_it(tmp_path: Path) -> None:
    """A tag on an unrelated model is that model's business."""
    project = _project(tmp_path, tagged={})
    manifest = json.loads((project / "target" / "manifest.json").read_text())
    manifest["nodes"]["model.basic.dim_customers"] = {
        "name": "dim_customers",
        "relation_name": "main.dim_customers",
        "columns": {"month": {"name": "month", "meta": {"pii": True}}},
    }
    (project / "target" / "manifest.json").write_text(json.dumps(manifest))
    _write_chart(project, "SELECT month, revenue")

    render_project(project, _config())


def test_a_clean_result_passes(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, "SELECT month, revenue")

    result = render_project(project, _config())

    assert result.charts[0].data.columns == ("month", "revenue")


def test_validate_mode_denies_with_no_rows_moved(tmp_path: Path) -> None:
    """CI catches a charted email against a `limit 0` result."""
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, "SELECT month, revenue, email")
    config = replace(_config(), execution=ExecutionConfig(mode="validate"))

    with pytest.raises(RenderError, match="returns a PII column: 'email'"):
        render_project(project, config)


def test_several_columns_are_named_together(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        tagged={"email": {"meta": {"pii": True}}, "phone": {"tags": ["pii"]}},
    )
    _write_chart(project, "SELECT month, revenue, email, phone")

    with pytest.raises(RenderError, match="returns PII columns: 'email' .*; 'phone' "):
        render_project(project, _config())


# --- redaction ---------------------------------------------------------------


def test_redact_masks_every_reader_of_the_result(tmp_path: Path) -> None:
    """The local data file, the chart and the published site all see the mask."""
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, "SELECT month, revenue, email", color="email")
    config = _config(on_pii="redact")

    result = render_project(project, config)
    generate_dashboards(project, config)
    export_site(project, config=config)

    assert result.charts[0].data.rows[0]["email"] == "j***@acme.example"
    data_json = json.loads(
        (project / "target" / "glyf" / "data" / "normalized" / "revenue.data.json").read_text()
    )
    assert data_json["rows"][0]["email"] == "j***@acme.example"
    published = _published_text(project)
    assert EMAIL not in published
    assert "j***@acme.example" in published


def test_redact_can_hash_instead(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, "SELECT month, revenue, email")

    result = render_project(project, _config(on_pii="redact", redaction="hash"))

    value = result.charts[0].data.rows[0]["email"]
    assert value == hash_value(EMAIL)
    assert EMAIL not in value


def test_mask_keeps_a_hint_and_nothing_more() -> None:
    assert mask_value("jane.doe@acme.example") == "j***@acme.example"
    assert mask_value("+1-555-0100") == "+***"
    assert mask_value(4155550100) == "4***"
    assert mask_value("") == "***"
    assert mask_value(None) is None


def test_hash_is_stable_and_keeps_distinctness() -> None:
    assert hash_value("a") == hash_value("a")
    assert hash_value("a") != hash_value("b")
    assert len(hash_value("a")) == 16
    assert hash_value(None) is None


def test_redaction_keeps_nulls_and_the_other_columns() -> None:
    data = QueryResult.from_records(
        ("id", "phone", "email"),
        (
            {"id": 1, "phone": PHONE, "email": EMAIL},
            {"id": 2, "phone": None, "email": None},
        ),
    )

    redacted = redact_columns(data, ("phone", "email"), "mask")

    assert redacted.columns == ("id", "phone", "email")
    assert redacted.rows == (
        {"id": 1, "phone": "+***", "email": "j***@acme.example"},
        {"id": 2, "phone": None, "email": None},
    )


# --- the value scan ----------------------------------------------------------


def test_an_unclassified_email_column_warns(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={})
    _write_chart(project, "SELECT month, revenue, email AS contact")

    result = render_project(project, _config())

    assert result.warnings == (
        "visualisations/revenue.ggsql column 'contact' looks like email addresses "
        "(2 of 2 sampled values) but is not classified as PII. Tag it in "
        "schema.yml or list it in privacy.pii_columns",
    )
    # A warning, not a rewrite: the values are exactly what the query returned.
    assert result.charts[0].data.rows[0]["contact"] == EMAIL


def test_the_scan_never_redacts(tmp_path: Path) -> None:
    """Even with redaction on, a fuzzy match only ever warns."""
    project = _project(tmp_path, tagged={})
    _write_chart(project, "SELECT month, revenue, email AS contact")

    result = render_project(project, _config(on_pii="redact"))

    assert len(result.warnings) == 1
    assert result.charts[0].data.rows[0]["contact"] == EMAIL


def test_strict_turns_the_warning_into_a_failure(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={})
    _write_chart(project, "SELECT month, revenue, email AS contact")

    with pytest.raises(RenderError, match=r"looks like email addresses .* \(privacy.strict\)"):
        render_project(project, _config(strict=True))


def test_a_classified_column_is_not_scanned(tmp_path: Path) -> None:
    """Classification owns it; a masked email must not trip the email detector."""
    project = _project(tmp_path, tagged={"email": {"meta": {"pii": True}}})
    _write_chart(project, "SELECT month, revenue, email")

    result = render_project(project, _config(on_pii="redact"))

    assert result.warnings == ()


def test_the_scan_can_be_switched_off(tmp_path: Path) -> None:
    project = _project(tmp_path, tagged={})
    _write_chart(project, "SELECT month, revenue, email AS contact")

    result = render_project(project, _config(scan=False))

    assert result.warnings == ()


def test_validate_mode_has_no_values_to_scan(tmp_path: Path) -> None:
    """`limit 0` moves no rows, so only the classification runs in CI."""
    project = _project(tmp_path, tagged={})
    _write_chart(project, "SELECT month, revenue, email AS contact")
    config = replace(_config(), execution=ExecutionConfig(mode="validate"))

    result = render_project(project, config)

    assert result.warnings == ()


def test_glyf_build_prints_the_warning_without_verbose(tmp_path: Path) -> None:
    """A warning nobody sees is a silent downgrade."""
    project = _project(tmp_path, tagged={})
    _write_chart(project, "SELECT month, revenue, email AS contact")

    result = CliRunner().invoke(app, ["build", "--project", str(project)])

    assert result.exit_code == 0, result.output
    assert "! visualisations/revenue.ggsql column 'contact' looks like email" in result.output
    assert "✓ rendered chart artifacts" in result.output


@pytest.mark.parametrize(
    ("kind", "values"),
    [
        ("email addresses", ["jane@acme.example", "j.doe+x@mail.example.org"]),
        ("phone numbers", ["+1-555-010-0123", "(415) 555-0100", "+14155550100"]),
        ("card numbers", ["4111 1111 1111 1111", "5500-0000-0000-0004"]),
        ("social security numbers", ["123-45-6789", "078-05-1120"]),
    ],
)
def test_each_detector_names_what_it_saw(kind: str, values: list[str]) -> None:
    data = _strings("v", values)

    (suspect,) = scan_for_pii(data)

    assert suspect.kind == kind
    assert suspect.column == "v"
    assert (suspect.matched, suspect.sampled) == (len(values), len(values))


@pytest.mark.parametrize(
    "values",
    [
        ["2026-01-15", "2026-02-15"],  # dates are not phone numbers
        ["4155550100", "2125550199"],  # bare digits are IDs until proven otherwise
        ["4111111111111112", "4111111111111113"],  # fails Luhn
        ["000-45-6789", "900-45-6789", "123-00-6789", "123-45-0000"],  # never issued
        ["North", "South", "j***@acme.example"],  # a masked value is not an address
        ["x@y", "not an email", ""],
    ],
)
def test_lookalikes_do_not_warn(values: list[str]) -> None:
    assert scan_for_pii(_strings("v", values)) == ()


def test_a_card_number_column_needs_a_majority() -> None:
    """One random digit string in ten passes Luhn, so a few hits in an ID column are noise."""
    ids = [f"{n:016d}" for n in range(1000, 1040)]  # some of these pass Luhn by chance
    assert scan_for_pii(_strings("order_id", ids)) == ()

    mostly_cards = ["4111 1111 1111 1111"] * 30 + ids[:10]
    (suspect,) = scan_for_pii(_strings("payment", mostly_cards))
    assert suspect.kind == "card numbers"


def test_one_address_in_twenty_free_text_values_is_enough() -> None:
    notes = ["fine"] * 19 + ["call jane@acme.example"]  # not a match: the whole value must be one
    assert scan_for_pii(_strings("note", notes)) == ()

    notes = ["fine"] * 19 + ["jane@acme.example"]
    (suspect,) = scan_for_pii(_strings("note", notes))
    assert (suspect.matched, suspect.sampled) == (1, 20)


def test_sampling_reads_across_the_result_not_just_the_top() -> None:
    values = ["fine"] * 5000 + ["jane@acme.example"] * 5000

    (suspect,) = scan_for_pii(_strings("note", values))

    assert suspect.sampled == 200
    assert suspect.matched == 100


def test_only_string_columns_are_scanned() -> None:
    data = QueryResult.from_records(
        ("n", "s"), tuple({"n": 4111111111111111, "s": "4111 1111 1111 1111"} for _ in range(3))
    )

    (suspect,) = scan_for_pii(data)

    assert suspect.column == "s"


def test_scan_and_strict_load_from_glyf_yml(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "privacy:\n  scan: false\n  strict: true\n", encoding="utf-8"
    )

    config = load_config(tmp_path)

    assert (config.privacy.scan, config.privacy.strict) == (False, True)
    assert (PrivacyConfig().scan, PrivacyConfig().strict) == (True, False)


# --- configuration -----------------------------------------------------------


def test_privacy_loads_from_glyf_yml(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "privacy:\n"
        "  pii_columns: [email, phone, email]\n"
        "  on_pii: redact\n"
        "  redaction: hash\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.privacy == PrivacyConfig(
        pii_columns=("email", "phone"), on_pii="redact", redaction="hash"
    )


def test_privacy_defaults_to_deny(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text("privacy:\n  pii_columns: [email]\n", encoding="utf-8")

    config = load_config(tmp_path)

    assert config.privacy.on_pii == "deny"
    assert config.privacy.redaction == "mask"
    assert GlyfConfig().privacy == PrivacyConfig()


@pytest.mark.parametrize(
    ("yaml", "message"),
    [
        ("privacy: nope\n", "'privacy' must be a mapping"),
        ("privacy:\n  pii_columns: email\n", "'privacy.pii_columns' must be a list"),
        ("privacy:\n  pii_columns: [1]\n", "'privacy.pii_columns' must be a list"),
        ("privacy:\n  on_pii: warn\n", "'privacy.on_pii' must be one of deny, redact"),
        ("privacy:\n  redaction: rot13\n", "'privacy.redaction' must be one of hash, mask"),
    ],
)
def test_invalid_privacy_config_is_named(tmp_path: Path, yaml: str, message: str) -> None:
    (tmp_path / "glyf.yml").write_text(yaml, encoding="utf-8")

    with pytest.raises(ConfigError, match=message):
        load_config(tmp_path)


# --- helpers -----------------------------------------------------------------


def _config(
    *,
    pii_columns: tuple[str, ...] = (),
    on_pii: str = "deny",
    redaction: str = "mask",
    scan: bool = True,
    strict: bool = False,
) -> GlyfConfig:
    return replace(
        GlyfConfig(),
        privacy=PrivacyConfig(
            pii_columns=pii_columns,
            on_pii=on_pii,
            redaction=redaction,
            scan=scan,
            strict=strict,
        ),
    )


def _strings(name: str, values: list[str]) -> QueryResult:
    return QueryResult.from_records((name,), tuple({name: value} for value in values))


def _project(tmp_path: Path, *, tagged: dict[str, dict[str, object]]) -> Path:
    """The basic project with contact columns, tagged as the test says."""
    project = copy_basic_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        f"month,revenue,email,phone\n2026-01,100,{EMAIL},{PHONE}\n2026-02,200,{EMAIL},{PHONE}\n",
        encoding="utf-8",
    )
    manifest_path = project / "target" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["nodes"]["model.basic.fct_orders"]["columns"] = {
        name: {"name": name, **spec} for name, spec in tagged.items()
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return project


def _write_chart(project: Path, select: str, *, color: str | None = None) -> None:
    visualise = "month AS x, revenue AS y"
    if color:
        visualise += f", {color} AS color"
    (project / "visualisations" / "revenue.ggsql").write_text(
        f"{select}\nFROM {{{{ ref('fct_orders') }}}}\n\n"
        f"VISUALISE {visualise}\nDRAW bar\nLABEL title => 'Revenue'\nINTERACT tooltip\n",
        encoding="utf-8",
    )


def _published_text(project: Path) -> str:
    site = project / "target" / "glyf" / "site"
    return "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(site.rglob("*"))
        if path.is_file() and path.suffix not in {".png", ".ttf", ".zip"}
    )
