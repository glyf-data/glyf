"""The chart's own account of a change: which marks moved, said in its terms."""

from glyf.diff.overlay import MarkChange, _mark_change, compact


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


def test_a_rescaled_y_axis_is_said_before_the_marks() -> None:
    before = {("jan", None): 50_000.0, ("feb", None): 60_000.0}
    after = {("jan", None): 50_000.0, ("feb", None): 400_000.0}

    marks = _mark_change("bar", before, after, x_order=["jan", "feb"])

    assert (marks.y_before, marks.y_after) == ((0.0, 60_000.0), (0.0, 400_000.0))
    assert marks.y_rescaled
    assert marks.describe_axes() == "y axis 0–60k → 0–400k"
    assert marks.describe() == "bars: 1 higher"


def test_a_small_shift_is_not_a_rescale() -> None:
    before = {("jan", None): 100.0, ("feb", None): 95.0}
    after = {("jan", None): 105.0, ("feb", None): 95.0}

    marks = _mark_change("line", before, after, x_order=["jan", "feb"])

    assert not marks.y_rescaled
    assert marks.describe_axes() is None


def test_stacked_marks_span_their_totals_and_negatives_go_below_zero() -> None:
    before = {("jan", "a"): 10.0, ("jan", "b"): 20.0, ("feb", "a"): -5.0}
    after = {("jan", "a"): 10.0, ("jan", "b"): 20.0, ("feb", "a"): -40.0}

    stacked = _mark_change("bar", before, after, x_order=["jan", "feb"], stacked=True)
    lines = _mark_change("line", before, after, x_order=["jan", "feb"])

    assert (stacked.y_before, stacked.y_after) == ((-5.0, 30.0), (-40.0, 30.0))
    assert stacked.describe_axes() == "y axis -5–30 → -40–30"
    assert lines.y_before == (-5.0, 20.0), "a line reaches its own value"


def test_x_categories_one_build_lacks_are_named() -> None:
    before = {("jan", None): 1.0, ("feb", None): 1.0}
    after = {("feb", None): 1.0, ("mar", None): 1.0}

    marks = _mark_change("bar", before, after, x_order=["jan", "feb", "mar"])

    assert (marks.x_gone, marks.x_new) == (("jan",), ("mar",))
    assert marks.describe_axes() == "x axis: mar added, jan dropped"


def test_compact_numbers_read_like_axis_labels() -> None:
    assert [compact(v) for v in (0, 28.5, 950, 60_000, 1_250_000, 2e9, -4_000)] == [
        "0", "28.5", "950", "60k", "1.25M", "2B", "-4k",
    ]
