"""The chart's own account of a change: which marks moved, said in its terms."""

from glyf.diff.overlay import MarkChange, _mark_change


def test_marks_are_counted_per_x_and_series() -> None:
    before = {("jan", "a"): 1.0, ("jan", "b"): 2.0, ("feb", "a"): 3.0, ("mar", "a"): 5.0}
    after = {("jan", "a"): 1.0, ("jan", "b"): 4.0, ("feb", "a"): 2.0, ("apr", "c"): 9.0}

    marks = _mark_change("bar", before, after, x_order=["jan", "feb", "mar", "apr"])

    assert (marks.gone, marks.new, marks.higher, marks.lower) == (1, 1, 1, 1)
    assert marks.gone_series == ()  # 'a' still has bars elsewhere
    assert marks.new_series == ("c",)
    assert marks.changed_x == ("jan", "feb", "mar", "apr")


def test_a_series_is_gone_only_when_none_of_its_marks_remain() -> None:
    before = {("jan", "a"): 1.0, ("feb", "a"): 2.0, ("jan", "b"): 1.0}
    after = {("jan", "b"): 1.0}

    marks = _mark_change("bar", before, after, x_order=["jan", "feb"])

    assert marks.gone_series == ("a",)
    assert marks.describe() == "bars: 2 gone (a)"


def test_describe_uses_the_charts_noun_and_names_a_few_series() -> None:
    assert MarkChange("line", higher=2, lower=1).describe() == "points: 2 higher, 1 lower"
    assert MarkChange("bar").describe() == "bars: unchanged"
    many = MarkChange("bar", gone=6, gone_series=("a", "b", "c", "d", "e", "f"))
    assert many.describe() == "bars: 6 gone (a, b, c, d and 2 more)"
