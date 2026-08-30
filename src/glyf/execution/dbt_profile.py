"""Resolve a dbt project's connection profile.

`glyf` executes the SQL dbt's models are built from, so it should connect the
way dbt does: by reading `profiles.yml`. This module resolves which profile and
target a project uses and hands back the target's settings. It opens no
connection -- see ARCHITECTURE.md for where that is going.

Only `env_var()` is honoured from dbt's templating. Profiles use it constantly
for credentials, and supporting it is what makes a real `profiles.yml` usable;
supporting the rest of Jinja would mean reimplementing dbt's context, so
anything else fails loudly instead of silently rendering as empty.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml
from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

# Keys whose values must never reach a log, an error message or `glyf doctor`.
_SECRET_KEY_PATTERN = re.compile(
    r"pass|secret|token|key|credential|auth", re.IGNORECASE
)
# Keys the pattern catches that name a location or a method, not a secret, and
# that `glyf doctor` should be able to show.
_SECRET_KEY_EXCEPTIONS = frozenset(
    {"keyfile", "key_file", "private_key_path", "authenticator", "authentication"}
)

_REDACTED = "***"

# A rendered scalar that is plainly a number becomes one: `port: "{{ env_var(
# 'PGPORT') }}"` should reach a driver as 5432, not "5432". Deliberately narrow
# -- YAML would also read "no" as False, which would quietly corrupt a password.
_NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")


class DbtProfileError(ValueError):
    """Raised when a dbt profile cannot be resolved."""


@dataclass(frozen=True)
class DbtProfile:
    """A resolved dbt target: which warehouse, and how to reach it."""

    name: str
    target: str
    type: str
    config: Mapping[str, Any]
    profiles_path: Path

    def redacted(self) -> dict[str, Any]:
        """The target's settings with credentials masked, safe to display."""
        return {key: _redact(key, value) for key, value in self.config.items()}


def load_dbt_profile(
    project_root: Path,
    *,
    profiles_dir: Path | None = None,
    target: str | None = None,
) -> DbtProfile:
    """Resolve the profile `project_root` uses, and the target within it.

    `profiles_dir` and `target` override the project's own choices; both are
    surfaced as glyf config so a project can render against a target dbt did
    not build with.
    """
    profile_name = _profile_name(project_root)
    profiles_path = _find_profiles(project_root, profiles_dir)
    document = _load_profiles(profiles_path)

    profile = document.get(profile_name)
    if not isinstance(profile, dict):
        known = ", ".join(sorted(str(key) for key in document)) or "none"
        raise DbtProfileError(
            f"{profiles_path}: no profile named '{profile_name}'. Found: {known}"
        )

    outputs = profile.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise DbtProfileError(
            f"{profiles_path}: profile '{profile_name}' defines no outputs"
        )

    target_name = target or os.environ.get("DBT_TARGET") or profile.get("target")
    if not isinstance(target_name, str) or not target_name:
        raise DbtProfileError(
            f"{profiles_path}: profile '{profile_name}' has no target; "
            "set one in profiles.yml or with execution.target"
        )

    output = outputs.get(target_name)
    if not isinstance(output, dict):
        known = ", ".join(sorted(str(key) for key in outputs))
        raise DbtProfileError(
            f"{profiles_path}: profile '{profile_name}' has no target "
            f"'{target_name}'. Found: {known}"
        )

    rendered = _render_values(output, profiles_path)
    adapter = rendered.get("type")
    if not isinstance(adapter, str) or not adapter:
        raise DbtProfileError(
            f"{profiles_path}: target '{target_name}' of profile "
            f"'{profile_name}' has no 'type'"
        )

    return DbtProfile(
        name=profile_name,
        target=target_name,
        type=adapter,
        config=rendered,
        profiles_path=profiles_path,
    )


def profiles_search_path(
    project_root: Path,
    profiles_dir: Path | None = None,
) -> tuple[Path, ...]:
    """Where `profiles.yml` is looked for, in order. Mirrors dbt's own order."""
    if profiles_dir is not None:
        return (Path(profiles_dir).expanduser() / "profiles.yml",)

    candidates = []
    from_env = os.environ.get("DBT_PROFILES_DIR")
    if from_env:
        candidates.append(Path(from_env).expanduser() / "profiles.yml")
    candidates.append(project_root / "profiles.yml")
    candidates.append(Path.home() / ".dbt" / "profiles.yml")
    return tuple(candidates)


def _profile_name(project_root: Path) -> str:
    path = project_root / "dbt_project.yml"
    if not path.exists():
        raise DbtProfileError(f"{path} not found; is this a dbt project?")

    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise DbtProfileError(f"{path}: {exc}") from exc

    if document is None:
        raise DbtProfileError(f"{path} is empty; a dbt project must set 'profile:'")
    if not isinstance(document, dict):
        raise DbtProfileError(f"{path}: expected a mapping")

    name = document.get("profile")
    if not isinstance(name, str) or not name:
        raise DbtProfileError(f"{path}: no 'profile' key")
    return name


def _find_profiles(project_root: Path, profiles_dir: Path | None) -> Path:
    searched = profiles_search_path(project_root, profiles_dir)
    for candidate in searched:
        if candidate.exists():
            return candidate
    locations = ", ".join(str(candidate) for candidate in searched)
    raise DbtProfileError(f"No profiles.yml found. Looked in: {locations}")


def _load_profiles(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        # dbt renders before parsing, so a profile may hold Jinja that YAML
        # cannot read unquoted. Render leniently just to get a parseable
        # document; the selected target's values are rendered strictly after.
        document = yaml.safe_load(_render_text(text, path, strict=False))

    if not isinstance(document, dict):
        raise DbtProfileError(f"{path}: expected a mapping of profiles")
    return document


def _render_values(output: Mapping[str, Any], path: Path) -> dict[str, Any]:
    return {str(key): _render_value(value, path) for key, value in output.items()}


def _render_value(value: Any, path: Path) -> Any:
    if isinstance(value, str):
        return _coerce(_render_text(value, path, strict=True))
    if isinstance(value, dict):
        return {str(key): _render_value(item, path) for key, item in value.items()}
    if isinstance(value, list):
        return [_render_value(item, path) for item in value]
    return value


def _render_text(text: str, path: Path, *, strict: bool) -> str:
    if "{{" not in text:
        return text

    environment = SandboxedEnvironment(undefined=StrictUndefined)
    template = environment.from_string(text)
    try:
        return template.render(env_var=_env_var(strict=strict))
    except DbtProfileError:
        raise
    except Exception as exc:
        raise DbtProfileError(
            f"{path}: could not render {_summarise(text)}: {exc}. "
            "Only env_var() is supported in profiles.yml."
        ) from exc


def _env_var(*, strict: bool):
    def env_var(name: str, default: str | None = None) -> str:
        value = os.environ.get(name)
        if value is not None:
            return value
        if default is not None:
            return default
        if not strict:
            return ""
        raise DbtProfileError(
            f"Environment variable '{name}' is not set and has no default"
        )

    return env_var


def _coerce(value: str) -> Any:
    return yaml.safe_load(value) if _NUMERIC.match(value.strip()) else value


def _redact(key: str, value: Any) -> Any:
    """Mask a secret whole.

    The name is checked before the type, so an inline credential document --
    BigQuery's `keyfile_json`, say -- is masked entirely rather than walked into
    and partly published.
    """
    if key.lower() not in _SECRET_KEY_EXCEPTIONS and _SECRET_KEY_PATTERN.search(key):
        return _REDACTED
    if isinstance(value, dict):
        return {str(item): _redact(str(item), inner) for item, inner in value.items()}
    return value


def _summarise(text: str) -> str:
    """Describe a template without quoting a value that may hold a secret."""
    single_line = " ".join(text.split())
    return f"'{single_line}'" if len(single_line) <= 40 else "a templated value"
