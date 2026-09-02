"""PII classification and enforcement.

A chart's query result passes through here once, after execution and before
anything reads it -- the renderer, the local data file, a dashboard filter --
so every backend is covered by the same rule. Classification is by column
name, from two sources joined together: the columns the dbt project tags as
PII in `schema.yml` on the models and sources the chart reads, and the
`privacy.pii_columns` list in `glyf.yml` for what dbt does not model.

Name matching is the documented limit. `select email as contact` produces a
column named `contact`, which no manifest tags; the `glyf.yml` list exists
for exactly that alias. Column lineage through arbitrary SQL is out of scope.

Behind the list sits a safety net: `scan_for_pii` looks at the *values* of
the columns nobody classified and says when they read like emails, phone
numbers, card numbers or social security numbers. It is fuzzy, so it warns
and never redacts on its own -- a silently redacted false positive is a wrong
chart with a clean conscience. `privacy.strict` turns the warning into a
failure for teams that would rather classify than be surprised.
"""

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass

import pyarrow as pa

from glyf.config import PrivacyConfig
from glyf.execution.result import QueryResult
from glyf.manifest.loader import DbtManifest
from glyf.manifest.resolver import RefResolution


class PiiPolicyError(ValueError):
    """Raised when a chart's result carries PII and the policy is `deny`."""


@dataclass(frozen=True)
class PiiColumn:
    name: str
    # Where the classification came from, for the message a build prints.
    origin: str


def classify_pii(
    columns: tuple[str, ...],
    resolution: RefResolution,
    manifest: DbtManifest,
    config: PrivacyConfig,
) -> tuple[PiiColumn, ...]:
    """Which of a result's columns are PII, in result order.

    Matching is case-insensitive: warehouses fold identifiers differently and
    a classification that misses `Email` because dbt wrote `email` would be
    the wrong kind of strict.
    """
    origins: dict[str, str] = {}
    for name in config.pii_columns:
        origins.setdefault(name.lower(), "listed in glyf.yml privacy.pii_columns")
    for ref in resolution.refs:
        node = manifest.node_for_ref(ref)
        if node is None:
            continue
        for column in node.pii_columns:
            origins.setdefault(
                column.lower(), f"tagged pii on {node.resource_type} {node.name}"
            )
    for source_name, table_name in resolution.sources:
        source = manifest.node_for_source(source_name, table_name)
        if source is None:
            continue
        for column in source.pii_columns:
            origins.setdefault(
                column.lower(), f"tagged pii on source {source_name}.{table_name}"
            )
    return tuple(
        PiiColumn(name=column, origin=origins[column.lower()])
        for column in columns
        if column.lower() in origins
    )


def apply_pii_policy(
    data: QueryResult,
    findings: tuple[PiiColumn, ...],
    config: PrivacyConfig,
    *,
    chart_path: str,
) -> QueryResult:
    """Fail or redact, per `privacy.on_pii`. A clean result passes through."""
    if not findings:
        return data
    if config.on_pii == "deny":
        described = "; ".join(f"'{f.name}' ({f.origin})" for f in findings)
        noun = "a PII column" if len(findings) == 1 else "PII columns"
        raise PiiPolicyError(
            f"{chart_path} returns {noun}: {described}. Drop it from the query, "
            "or set privacy.on_pii: redact to publish it masked."
        )
    return redact_columns(data, tuple(f.name for f in findings), config.redaction)


@dataclass(frozen=True)
class PiiSuspect:
    column: str
    # What the values read like: "email addresses", "phone numbers", ...
    kind: str
    matched: int
    sampled: int

    def describe(self) -> str:
        return (
            f"column '{self.column}' looks like {self.kind} "
            f"({self.matched} of {self.sampled} sampled values)"
        )


# How many non-null values of a column the scan reads, spread across the
# result rather than taken from the top, so a sorted result does not hide a
# late block of addresses.
SCAN_SAMPLE = 200


def scan_for_pii(
    data: QueryResult, *, skip: tuple[str, ...] = ()
) -> tuple[PiiSuspect, ...]:
    """Unclassified string columns whose values read like PII, in column order.

    Only string columns are read: a phone number stored as an integer has
    already lost the shape the detectors look for. Columns in `skip` -- the
    ones classification already handled -- are not looked at, so a masked
    email does not trip the email detector.
    """
    table = data.to_arrow()
    skipped = {name.lower() for name in skip}
    suspects: list[PiiSuspect] = []
    for field in table.schema:
        if field.name.lower() in skipped:
            continue
        if not (pa.types.is_string(field.type) or pa.types.is_large_string(field.type)):
            continue
        values = _sample(table.column(field.name))
        if not values:
            continue
        for kind, matches, threshold in _DETECTORS:
            matched = sum(1 for value in values if matches(value))
            if matched and matched / len(values) >= threshold:
                suspects.append(
                    PiiSuspect(
                        column=field.name, kind=kind, matched=matched, sampled=len(values)
                    )
                )
                break
    return tuple(suspects)


def _sample(column: pa.ChunkedArray) -> list[str]:
    non_null = column.drop_null()
    total = len(non_null)
    if total == 0:
        return []
    if total <= SCAN_SAMPLE:
        return [str(value) for value in non_null.to_pylist()]
    step = total / SCAN_SAMPLE
    picked = non_null.take(pa.array([int(i * step) for i in range(SCAN_SAMPLE)]))
    return [str(value) for value in picked.to_pylist()]


_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
# A leading + or at least one separator: a bare run of digits is an ID until
# proven otherwise.
_PHONE = re.compile(
    r"^(\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]\d{3,4}[\s.-]?\d{3,4}$|^\+\d{10,15}$"
)
_CARD = re.compile(r"^(?:\d[ -]?){12,18}\d$")
_SSN = re.compile(r"^(\d{3})-(\d{2})-(\d{4})$")


def _is_email(value: str) -> bool:
    return _EMAIL.match(value.strip()) is not None


def _is_phone(value: str) -> bool:
    text = value.strip()
    digits = sum(ch.isdigit() for ch in text)
    return 10 <= digits <= 15 and _PHONE.match(text) is not None


def _is_card_number(value: str) -> bool:
    text = value.strip()
    if _CARD.match(text) is None:
        return False
    return _luhn(re.sub(r"[ -]", "", text))


def _luhn(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _is_ssn(value: str) -> bool:
    found = _SSN.match(value.strip())
    if found is None:
        return False
    area, group, serial = found.groups()
    # The ranges the SSA never issues.
    if area in {"000", "666"} or area.startswith("9"):
        return False
    return group != "00" and serial != "0000"


# (what it reads like, the test, the share of sampled values that must match).
# One in twenty is enough for the shapes that nothing else produces; a card
# number needs a majority because one random digit string in ten passes Luhn.
_DETECTORS: tuple[tuple[str, Callable[[str], bool], float], ...] = (
    ("email addresses", _is_email, 0.05),
    ("social security numbers", _is_ssn, 0.05),
    ("phone numbers", _is_phone, 0.05),
    ("card numbers", _is_card_number, 0.5),
)


def redact_columns(
    data: QueryResult, columns: tuple[str, ...], method: str
) -> QueryResult:
    """The result with the named columns rewritten as redacted strings.

    Nulls stay null. Every other value becomes a string, whatever it was:
    a masked phone number is text, not a number.
    """
    redact = mask_value if method == "mask" else hash_value
    table = data.to_arrow()
    for name in columns:
        index = table.schema.get_field_index(name)
        values = [redact(value) for value in table.column(index).to_pylist()]
        table = table.set_column(index, name, pa.array(values, type=pa.string()))
    return QueryResult.from_arrow(table)


def mask_value(value: object) -> str | None:
    """`jane@acme.com` -> `j***@acme.com`; anything else keeps its first character."""
    if value is None:
        return None
    text = str(value)
    if "@" in text:
        local, _, domain = text.partition("@")
        return f"{local[:1]}***@{domain}"
    return f"{text[:1]}***"


def hash_value(value: object) -> str | None:
    """A short, stable digest: equal values stay equal, nothing else survives.

    Unsalted, so a low-entropy value (an email someone can guess) is not
    hidden from anyone willing to hash their guess. This keeps a key
    groupable; it does not keep it secret.
    """
    if value is None:
        return None
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
