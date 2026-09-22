"""Which SQL dialect a project's charts are written in.

The parser reads each chart's SQL for the ORDER BY rule and for a syntax
warning, and a warehouse's SQL differs at the edges. The dialect follows the
warehouse the charts run on: the dbt profile's target type for the `dbt`
backend, DuckDB for the DuckDB backends, generic SQL otherwise. It is only
ever a hint, so a profile that cannot be read falls back to generic rather
than failing here; the executor reports that problem, with its own message.
"""

from __future__ import annotations

from pathlib import Path

from glyf.config import ExecutionConfig
from glyf.execution.dbt_profile import DbtProfileError, load_dbt_profile

GENERIC = "generic"


def sql_dialect(project_root: Path, execution: ExecutionConfig) -> str:
    if execution.backend.startswith("duckdb"):
        return "duckdb"
    if execution.backend != "dbt":
        return GENERIC
    try:
        profile = load_dbt_profile(
            project_root,
            profiles_dir=execution.profiles_dir,
            target=execution.target,
        )
    except (DbtProfileError, OSError, ValueError):
        return GENERIC
    return profile.type if profile.type in ("duckdb", "snowflake", "bigquery") else GENERIC
