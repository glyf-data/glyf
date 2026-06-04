from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.dashboard.artifacts import (
    ChartArtifact,
    ChartArtifactError,
    load_chart_artifact,
)


@dataclass
class MacroContext:
    project_root: Path
    config: GlyfConfig
    strict: bool = True
    _artifacts: dict[str, ChartArtifact] = field(default_factory=dict)

    def chart_artifact(self, chart: str) -> ChartArtifact | None:
        chart_name = _required_chart_name(chart)
        artifact = self._artifacts.get(chart_name)
        if artifact is None:
            try:
                artifact = load_chart_artifact(self.project_root, chart_name, self.config)
            except ChartArtifactError:
                if self.strict:
                    raise
                return None
            self._artifacts[chart_name] = artifact
        return artifact

    def chart_fields(self, chart: str) -> tuple[str, ...]:
        artifact = self.chart_artifact(chart)
        if artifact is None:
            return ("value",)
        return artifact.data.fields

    def chart_rows(self, chart: str) -> tuple[dict[str, object], ...]:
        artifact = self.chart_artifact(chart)
        if artifact is None:
            return ({"value": 0},)
        return artifact.data.rows

    def chart_values(self, chart: str, field: str) -> tuple[object, ...]:
        field_name = self._required_field(chart, field)
        values: list[object] = []
        for row in self.chart_rows(chart):
            value = row.get(field_name)
            if value is not None:
                values.append(value)
        if not values:
            if not self.strict:
                return (0,)
            raise ValueError(
                f"chart '{chart}' field '{field_name}' does not contain any values"
            )
        return tuple(values)

    def distinct_values(self, chart: str, field: str) -> tuple[object, ...]:
        values = self.chart_values(chart, field)
        distinct: list[object] = []
        seen: set[str] = set()
        for value in values:
            marker = repr(value)
            if marker in seen:
                continue
            seen.add(marker)
            distinct.append(value)
        return tuple(distinct)

    def latest_value(self, chart: str, field: str) -> object:
        values = self.chart_values(chart, field)
        return values[-1]

    def source(self, chart: str, field: str) -> tuple[object, ...]:
        return self.distinct_values(chart, field)

    def _required_field(self, chart: str, field: str) -> str:
        field_name = str(field).strip()
        if not field_name:
            raise ValueError("expected 'field' to be a non-empty string")
        available = self.chart_fields(chart)
        if not self.strict and available == ("value",):
            return field_name
        if field_name not in available:
            fields = ", ".join(available)
            raise ValueError(
                f"chart '{chart}' does not expose field '{field_name}'"
                + (f"; available fields: {fields}" if fields else "")
            )
        return field_name


def _required_chart_name(chart: str) -> str:
    chart_name = str(chart).strip()
    if not chart_name:
        raise ValueError("expected 'chart' to be a non-empty string")
    return chart_name
