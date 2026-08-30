"""Guard the documentation against drift.

The 2026-08-29 docs review found two bugs by hand: a macro call the macro's
signature rejects, and a dashboard example that had quietly lost the `filters:`
block it existed to demonstrate. Prose is invisible to CI, so this module makes
the documented examples executable:

1. every dashboard YAML block in the docs loads through `glyf.dashboard.loader`
2. every macro expression in those blocks resolves against the real macros
3. blocks a page presents as a shipped example file are identical to that file
4. every documented `glyf.yml` loads through `glyf.config`

Blocks are routed by shape, so nothing in the docs needs an annotation: a block
whose top-level keys are dashboard keys is checked, and one whose keys are not
-- a GitHub Actions workflow, a `glyf.yml` -- is not a dashboard example and is
left to its own check. A block that is deliberately invalid can opt out with an
HTML comment on the line above its fence; see `docs-site/README.md`.
"""

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pytest
import yaml

from glyf.config import GlyfConfig, load_config
from glyf.dashboard.loader import load_dashboard
from glyf.dashboard.macros.context import MacroContext
from glyf.dashboard.macros.registry import (
    DashboardMacroRegistry,
    resolve_dashboard_components,
)

DOCS = Path("docs-site/docs")

SKIP_MARKER = "glyf-docs: skip"

# Top-level keys of a dashboard spec. A YAML block outside this vocabulary is
# not a dashboard example.
DASHBOARD_KEYS = frozenset(
    {
        "name",
        "title",
        "description",
        "tags",
        "theme",
        "chart_theme",
        "charts",
        "layout",
        "sections",
        "groups",
        "filters",
        "summary",
        "toolbar",
    }
)

# Keys that make a block loadable on its own; a fragment without one of them is
# spliced into a host spec before loading.
BODY_KEYS = frozenset({"charts", "sections", "groups"})

# Some blocks document a single item of a section rather than a dashboard, so
# they are spliced one level deeper. Without this they would load as a
# dashboard with an unknown top-level key, which the loader ignores -- the block
# would pass while its macro was never evaluated.
ITEM_KEYS = frozenset(
    {
        "chart",
        "component",
        "markdown",
        "metric",
        "title",
        "text",
        "label",
        "value",
        "note",
        "width",
    }
)
ITEM_MARKERS = frozenset({"chart", "component", "markdown", "metric"})

# Top-level keys of a `glyf.yml`. These blocks are checked too, by loading them
# through `glyf.config` rather than the dashboard loader.
CONFIG_KEYS = frozenset(
    {
        "visualisations_path",
        "dashboards_path",
        "output_path",
        "compiled_path",
        "charts_path",
        "dashboards_output_path",
        "site_path",
        "execution",
        "render",
        "dashboard",
    }
)

# Pages whose YAML blocks are deliberately not dashboard specs. Kept explicit so
# that a block which stops looking like a dashboard -- a misspelled top-level
# key, say -- fails `test_every_yaml_block_is_accounted_for` instead of quietly
# dropping out of the checks above.
NON_DASHBOARD_PAGES = frozenset(
    {
        "integrations/github-actions.md",  # a GitHub Actions workflow
    }
)

# Pages that present a block as an example project's file, and the file itself.
SHIPPED_BLOCKS = {
    "examples/product-analytics.md": "examples/product_analytics/dashboards/product.yml",
    "examples/finance-metrics.md": "examples/finance_metrics/dashboards/finance.yml",
}

# Floors, so a moved docs tree or a renamed fence language makes these tests
# fail instead of quietly checking nothing.
MINIMUM_DASHBOARD_BLOCKS = 20
MINIMUM_MACRO_BLOCKS = 8
MINIMUM_CONFIG_BLOCKS = 2


@dataclass(frozen=True)
class Block:
    page: Path
    line: int
    lang: str
    text: str

    @property
    def id(self) -> str:
        return f"{self.page.relative_to(DOCS)}:{self.line}"


def _blocks(path: Path) -> Iterator[Block]:
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("```") or len(line) <= 3:
            index += 1
            continue
        preceding = lines[index - 1] if index else ""
        lang = line[3:].split(maxsplit=1)[0]
        start = index + 1
        end = start
        while end < len(lines) and not lines[end].startswith("```"):
            end += 1
        if SKIP_MARKER not in preceding:
            yield Block(path, start + 1, lang, "\n".join(lines[start:end]))
        index = end + 1


def _yaml_blocks() -> list[Block]:
    return [
        block
        for path in sorted(DOCS.rglob("*.md"))
        for block in _blocks(path)
        if block.lang in {"yaml", "yml"}
    ]


def _keys(block: Block) -> frozenset[str]:
    document = yaml.safe_load(block.text)
    if not isinstance(document, dict):
        return frozenset()
    return frozenset(str(key) for key in document)


def _shape(block: Block) -> str | None:
    """How to load the block: as a spec, a dashboard fragment, or a section item."""
    keys = _keys(block)
    if not keys:
        return None
    if keys & ITEM_MARKERS and keys <= ITEM_KEYS:
        return "item"
    if keys <= DASHBOARD_KEYS:
        return "dashboard"
    if keys <= CONFIG_KEYS:
        return "config"
    return None


def _dashboard_blocks() -> list[Block]:
    """YAML blocks documenting a dashboard spec, a fragment of one, or an item."""
    return [block for block in _yaml_blocks() if _shape(block) in {"dashboard", "item"}]


def _config_blocks() -> list[Block]:
    """YAML blocks documenting a `glyf.yml`, wherever they appear."""
    return [block for block in _yaml_blocks() if _shape(block) == "config"]


def _macro_blocks() -> list[Block]:
    return [block for block in _dashboard_blocks() if "{{" in block.text]


def _python_macros(page: Path) -> str | None:
    """The `macros.py` a page documents, if it documents one."""
    for block in _blocks(page):
        if block.lang == "python" and "def " in block.text:
            return block.text
    return None


def _as_dashboard(block: Block, directory: Path) -> Path:
    """Write the block as a loadable spec, splicing a host around a fragment.

    The block's own text is spliced in verbatim rather than re-serialised, so
    what gets loaded is what the page actually shows.
    """
    keys = _keys(block)
    path = directory / "docs_probe.yml"

    if _shape(block) == "item":
        item = textwrap.indent(block.text, " " * 8).lstrip()
        path.write_text(
            "name: docs_probe\ntitle: Docs probe\n"
            f"sections:\n  - items:\n      - {item}\n",
            encoding="utf-8",
        )
        return path

    header = []
    if "name" not in keys:
        header.append("name: docs_probe")
    if "title" not in keys:
        header.append("title: Docs probe")
    if not keys & BODY_KEYS:
        header.append("charts:\n  - revenue")
    path.write_text("\n".join([*header, block.text]) + "\n", encoding="utf-8")
    return path


def _registry(page: Path, directory: Path) -> DashboardMacroRegistry:
    """Built-in macros, plus whichever project macros the page's block belongs to.

    Deliberately not pooled across pages: `guides/dashboard-macros.md` teaches a
    simplified `activation_health`, while `examples/product_analytics` ships a
    richer one, so pooling would check each page against the wrong macro. A page
    showing a shipped file resolves against that example project; any other page
    resolves against the `macros.py` it documents itself.
    """
    shipped = SHIPPED_BLOCKS.get(str(page.relative_to(DOCS)))
    if shipped is not None:
        dashboards_dir = Path(shipped).parent
        context = MacroContext(
            project_root=dashboards_dir.parent,
            config=GlyfConfig(),
            strict=False,
        )
        return DashboardMacroRegistry.from_project(dashboards_dir, context)

    macros = _python_macros(page)
    if macros is not None:
        (directory / "macros.py").write_text(macros, encoding="utf-8")
    context = MacroContext(project_root=directory, config=GlyfConfig(), strict=False)
    return DashboardMacroRegistry.from_project(directory, context)


@pytest.mark.parametrize("block", _dashboard_blocks(), ids=lambda block: block.id)
def test_dashboard_yaml_blocks_load(block: Block, tmp_path: Path) -> None:
    load_dashboard(_as_dashboard(block, tmp_path))


@pytest.mark.parametrize("block", _macro_blocks(), ids=lambda block: block.id)
def test_dashboard_macro_expressions_resolve(block: Block, tmp_path: Path) -> None:
    dashboard = load_dashboard(_as_dashboard(block, tmp_path))
    resolve_dashboard_components(dashboard, _registry(block.page, tmp_path))


@pytest.mark.parametrize("page,shipped", sorted(SHIPPED_BLOCKS.items()))
def test_example_pages_show_the_shipped_file(page: str, shipped: str) -> None:
    """A parse check cannot catch a block that has quietly lost a section, so
    pages that claim to show a shipped file are compared against it."""
    documented = [
        block for block in _blocks(DOCS / page) if block.lang in {"yaml", "yml"}
    ]
    assert len(documented) == 1, f"{page}: expected one YAML block"
    expected = Path(shipped).read_text(encoding="utf-8").strip()
    assert documented[0].text.strip() == expected, (
        f"{page} no longer matches {shipped}; update the page or the example"
    )


@pytest.mark.parametrize("block", _config_blocks(), ids=lambda block: block.id)
def test_documented_glyf_yml_blocks_load(block: Block, tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(block.text + "\n", encoding="utf-8")

    load_config(tmp_path)


@pytest.mark.parametrize("block", _yaml_blocks(), ids=lambda block: block.id)
def test_every_yaml_block_is_accounted_for(block: Block) -> None:
    """No block may fall between the checks.

    Routing by shape means a block that stops looking like a dashboard stops
    being checked, which is the drift it is meant to catch. So every YAML block
    in the docs must be a dashboard spec, on the short list of pages that hold
    other YAML, or explicitly marked to skip.
    """
    if str(block.page.relative_to(DOCS)) in NON_DASHBOARD_PAGES:
        return
    keys = _keys(block)
    assert keys, f"{block.id}: not a YAML mapping"
    assert _shape(block) is not None, (
        f"{block.id}: keys {sorted(keys)} are not a dashboard, a section item "
        "or a glyf.yml. Fix the block, add its page to NON_DASHBOARD_PAGES, or mark it "
        f"with an HTML comment containing '{SKIP_MARKER}'."
    )


def test_the_docs_are_actually_being_checked() -> None:
    """Without floors, a moved docs tree would make every test above vacuous."""
    assert DOCS.is_dir(), "docs-site/docs is missing"
    assert len(_dashboard_blocks()) >= MINIMUM_DASHBOARD_BLOCKS
    assert len(_macro_blocks()) >= MINIMUM_MACRO_BLOCKS
    assert len(_config_blocks()) >= MINIMUM_CONFIG_BLOCKS
    for shipped in SHIPPED_BLOCKS.values():
        assert Path(shipped).exists(), f"{shipped} is gone"
