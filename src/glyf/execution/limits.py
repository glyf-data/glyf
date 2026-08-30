"""Bound what a chart query returns.

Two callers, one mechanism. Validate mode asks for no rows at all, so that CI
can prove a query still runs and binds its columns without paying for the data.
A full build with `execution.max_rows` set asks for one row more than the cap,
so that exceeding it can be detected and reported rather than silently drawn.

The bound is applied in SQL rather than by discarding rows after the fact, so
the warehouse sends less over the wire. It bounds transfer and render time; it
does not bound what the warehouse scans, and an aggregate is computed in full
whatever limit follows it.
"""

from __future__ import annotations

SUBQUERY_ALIAS = "glyf_limited"


def wrap_row_limit(sql: str, limit: int) -> str:
    """Return `sql` bounded to at most `limit` rows.

    The original query becomes a subquery, so a trailing `order by`, `group by`
    or comment cannot swallow the limit that follows it.
    """
    if limit < 0:
        raise ValueError("row limit must not be negative")

    inner = sql.strip().rstrip(";").rstrip()
    return f"select * from (\n{inner}\n) as {SUBQUERY_ALIAS} limit {limit}"
