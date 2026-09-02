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
"""

import hashlib
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
