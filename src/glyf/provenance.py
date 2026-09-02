"""What a build did, recorded so it can be read back.

A published artifact says almost nothing about how it came to exist. The
questions an audit asks later -- which warehouse identity ran the queries,
which dashboards were deliberately left out, whether the PII policy redacted
anything, how many rows each chart pulled -- are all known at build time and
were all thrown away.

This module collects them into one record, written to `build.json` beside the
artifacts and embedded in the local `bundle.json`. It is deliberately *not*
published by default: the record names the warehouse identity and the
selectors, which is recon material on a public site.

The record is the build describing itself. It is not evidence, and nothing
verifies it -- the same caveat the `security` block carries. A tamper-evident
history means shipping these records to an append-only log outside the
artifact, which is the pipeline's job; `--log-json` exists to feed it.
"""

import hashlib
import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from glyf import __version__
from glyf.config import GlyfConfig

BUILD_RECORD_VERSION = 1


def sql_digest(compiled_sql: str) -> str:
    """A short digest of the SQL that ran.

    Enough to notice that what ran changed, without republishing the query
    itself: on a public site the compiled SQL names warehouse tables, and a
    digest names nothing.
    """
    return hashlib.sha256(compiled_sql.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ChartRecord:
    name: str
    compiled_sql_sha256: str
    # None under validate mode, which fetches no rows rather than zero rows.
    row_count: int | None = None
    # Columns the PII policy rewrote, and how.
    redacted_columns: tuple[str, ...] = ()
    # Columns the value scan flagged but nobody classified.
    scan_warnings: tuple[dict[str, Any], ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "compiled_sql_sha256": self.compiled_sql_sha256,
            "row_count": self.row_count,
        }
        if self.redacted_columns:
            payload["redacted_columns"] = list(self.redacted_columns)
        if self.scan_warnings:
            payload["scan_warnings"] = [dict(item) for item in self.scan_warnings]
        return payload


@dataclass(frozen=True)
class BuildRecord:
    """Everything a build knows about itself."""

    built_at: str
    project: str
    glyf_version: str = __version__
    record_version: int = BUILD_RECORD_VERSION
    duration_ms: int | None = None
    # `success` or `failed`. A log of successes only is a weak audit.
    outcome: str = "success"
    error: str | None = None
    execution: dict[str, Any] = field(default_factory=dict)
    export: dict[str, Any] = field(default_factory=dict)
    privacy: dict[str, Any] = field(default_factory=dict)
    # None when the build was not restricted to a selection.
    selection: dict[str, Any] | None = None
    # The dbt run the artifacts were built from.
    dbt_manifest_generated_at: str | None = None
    charts: tuple[ChartRecord, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "record_version": self.record_version,
            "glyf_version": self.glyf_version,
            "built_at": self.built_at,
            "duration_ms": self.duration_ms,
            "outcome": self.outcome,
            "error": self.error,
            "project": self.project,
            "dbt_manifest_generated_at": self.dbt_manifest_generated_at,
            "execution": dict(self.execution),
            "export": dict(self.export),
            "privacy": dict(self.privacy),
            "selection": dict(self.selection) if self.selection is not None else None,
            "charts": {chart.name: chart.to_payload() for chart in self.charts},
        }


def build_record(
    *,
    project: str,
    built_at: str,
    config: GlyfConfig,
    charts: tuple[ChartRecord, ...],
    selectors: tuple[str, ...] | None = None,
    dashboards: tuple[str, ...] | None = None,
    dbt_manifest_generated_at: str | None = None,
    duration_ms: int | None = None,
) -> BuildRecord:
    privacy = config.privacy
    return BuildRecord(
        built_at=built_at,
        project=project,
        duration_ms=duration_ms,
        execution={
            "backend": config.execution.backend,
            # The identity the queries ran as: the warehouse's policies for it
            # are what bounded everything below.
            "target": config.execution.target,
            "mode": config.execution.mode,
            "max_rows": config.execution.max_rows,
        },
        export={"row_data": config.export.row_data},
        privacy={
            "on_pii": privacy.on_pii,
            "redaction": privacy.redaction,
            "scan": privacy.scan,
            "strict": privacy.strict,
            "pii_columns": list(privacy.pii_columns),
        },
        selection=(
            None
            if selectors is None
            else {
                "selectors": list(selectors),
                "dashboards": list(dashboards or ()),
            }
        ),
        dbt_manifest_generated_at=dbt_manifest_generated_at,
        charts=charts,
    )


def failure_record(
    *,
    project: str,
    built_at: str,
    config: GlyfConfig,
    error: str,
    selectors: tuple[str, ...] | None = None,
    duration_ms: int | None = None,
) -> BuildRecord:
    """A record for a build that did not finish.

    It carries no chart facts, because there is no artifact to describe --
    only that a build was attempted with these settings and why it stopped.
    """
    record = build_record(
        project=project,
        built_at=built_at,
        config=config,
        charts=(),
        selectors=selectors,
        duration_ms=duration_ms,
    )
    return replace(record, outcome="failed", error=error)


def append_build_event(path: Path, record: BuildRecord) -> Path:
    """Append the record to a JSON Lines log.

    One object per line, appended rather than replaced, so a single file
    accumulates the history of a project's builds and any log collector can
    read it. `glyf build` captures each step's stdout, so a stream would be
    swallowed; a file is what survives.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record.to_payload(), sort_keys=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return path


def write_build_record(path: Path, record: BuildRecord) -> Path:
    """Write the record beside the artifacts.

    `build.json` sits at the output root, which `glyf export` does not copy,
    so the record stays local unless someone deliberately publishes it.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def read_build_record(path: Path) -> dict[str, Any] | None:
    """The record a previous step wrote, or None when there is none to read."""
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return raw if isinstance(raw, dict) else None
