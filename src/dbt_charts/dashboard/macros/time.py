from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def now(format: str = "%Y-%m-%d %H:%M", timezone: str | None = None) -> str:
    if not isinstance(format, str) or not format:
        raise ValueError("expected 'format' to be a non-empty string")

    if timezone is None:
        current = datetime.now().astimezone()
    else:
        if not isinstance(timezone, str) or not timezone:
            raise ValueError("expected 'timezone' to be a non-empty string")
        try:
            current = datetime.now(ZoneInfo(timezone))
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {timezone}") from exc
    return current.strftime(format)
