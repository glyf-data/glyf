from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    css_file: str = "dashboard.css"
    variables_file: str | None = None


DEFAULT_THEME = Theme(name="light")
