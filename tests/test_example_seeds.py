"""The committed example seeds are what `examples/seed_data.py` writes.

The dashboards quote figures from this data in their metric tiles, so a seed
edited by hand, or a generator changed without being rerun, leaves an example
that contradicts itself.
"""

import importlib.util
from pathlib import Path

EXAMPLES = Path("examples")


def test_committed_seeds_match_the_generator(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "seed_data", EXAMPLES / "seed_data.py"
    )
    assert spec is not None and spec.loader is not None
    seed_data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_data)

    seed_data.main(tmp_path)

    generated = sorted(tmp_path.rglob("*.csv"))
    assert len(generated) == 6
    for path in generated:
        committed = EXAMPLES / path.relative_to(tmp_path)
        assert committed.read_text(encoding="utf-8") == path.read_text(
            encoding="utf-8"
        ), f"{committed} differs; run `uv run python examples/seed_data.py`"
