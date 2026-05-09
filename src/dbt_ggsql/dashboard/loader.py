from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Dashboard:
    path: Path
    name: str
    title: str
    charts: tuple[str, ...]


def load_dashboard(path: Path) -> Dashboard:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError("invalid YAML") from exc

    if not isinstance(raw, dict):
        raise ValueError("expected a YAML mapping")

    name = raw.get("name")
    title = raw.get("title", name)
    charts = raw.get("charts", [])

    if not isinstance(name, str) or not name:
        raise ValueError("expected non-empty 'name'")
    if not isinstance(title, str) or not title:
        raise ValueError("expected non-empty 'title'")
    if not isinstance(charts, list) or not all(isinstance(item, str) for item in charts):
        raise ValueError("expected 'charts' to be a list of chart names")

    return Dashboard(path=path, name=name, title=title, charts=tuple(charts))
