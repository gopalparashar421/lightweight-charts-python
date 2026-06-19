"""test_subcharts.py — Unit tests for SubCharts API (create_subchart / SubChart).

TDD: all tests are written before implementation and must fail with
ImportError / AttributeError until the feature is implemented.
"""

from lightweight_charts.abstract import AbstractChart


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_scripts_after(chart, call):
    """Run *call*, return all run_script strings emitted after the call starts."""
    start = len(chart.win.scripts)
    call()
    return chart.win.scripts[start:]


# ---------------------------------------------------------------------------
# Test: SubChart type and full API surface
# ---------------------------------------------------------------------------


def test_create_subchart_returns_subchart_instance(chart):
    """create_subchart returns a SubChart instance."""
    from lightweight_charts.abstract import SubChart

    sub = chart.create_subchart("Price")
    assert isinstance(sub, SubChart)


def test_subchart_is_abstract_chart(chart):
    """SubChart inherits AbstractChart — full API must be available."""
    sub = chart.create_subchart("Price")
    assert isinstance(sub, AbstractChart)
    assert hasattr(sub, "create_line")
    assert hasattr(sub, "topbar")
    assert hasattr(sub, "set")
    assert hasattr(sub, "create_histogram")


# ---------------------------------------------------------------------------
# Test: run_script emission order and content
# ---------------------------------------------------------------------------


def test_create_subchart_emits_manager_creation(chart):
    """First create_subchart emits 'new Lib.SubChartManager()' exactly once."""
    scripts = _new_scripts_after(chart, lambda: chart.create_subchart("Price", main_label="Main"))
    joined = "".join(scripts)
    assert "new Lib.SubChartManager()" in joined


def test_create_subchart_emits_main_label_registration(chart):
    """First create_subchart registers the main chart with the given main_label."""
    scripts = _new_scripts_after(
        chart, lambda: chart.create_subchart("Price", main_label="Overview")
    )
    joined = "".join(scripts)
    assert "Overview" in joined


def test_create_subchart_emits_sub_label_registration(chart):
    """create_subchart registers the subchart with the given label."""
    scripts = _new_scripts_after(
        chart, lambda: chart.create_subchart("Equity Curve", main_label="Main")
    )
    joined = "".join(scripts)
    assert "Equity Curve" in joined


def test_manager_created_before_main_registration(chart):
    """SubChartManager is instantiated before main chart is registered."""
    scripts = _new_scripts_after(chart, lambda: chart.create_subchart("Price", main_label="Main"))
    joined = "\n".join(scripts)
    manager_pos = joined.find("new Lib.SubChartManager()")
    main_reg_pos = joined.find("Main")
    assert manager_pos != -1, "Manager creation not found in scripts"
    assert main_reg_pos != -1, "Main label registration not found in scripts"
    assert manager_pos < main_reg_pos, "Manager must be created before main registration"


def test_manager_not_recreated_on_second_call(chart):
    """Second create_subchart call must NOT emit 'new Lib.SubChartManager()' again."""
    chart.create_subchart("Price", main_label="Main")
    scripts = _new_scripts_after(chart, lambda: chart.create_subchart("Equity Curve"))
    joined = "".join(scripts)
    assert "new Lib.SubChartManager()" not in joined


def test_main_label_not_reregistered_on_second_call(chart):
    """main_label is silently ignored after the first call."""
    chart.create_subchart("Price", main_label="FirstLabel")
    # second call with different main_label — must not emit 'SecondLabel'
    scripts = _new_scripts_after(
        chart, lambda: chart.create_subchart("Equity", main_label="SecondLabel")
    )
    joined = "".join(scripts)
    assert "SecondLabel" not in joined


# ---------------------------------------------------------------------------
# Test: _subcharts registry
# ---------------------------------------------------------------------------


def test_subcharts_stored_in_list(chart):
    """create_subchart results are stored in chart._subcharts."""
    sub1 = chart.create_subchart("Price")
    sub2 = chart.create_subchart("Equity")
    assert hasattr(chart, "_subcharts")
    assert sub1 in chart._subcharts
    assert sub2 in chart._subcharts


def test_subcharts_list_grows_with_each_call(chart):
    """Each create_subchart call appends exactly one entry."""
    chart.create_subchart("A")
    assert len(chart._subcharts) == 1
    chart.create_subchart("B")
    assert len(chart._subcharts) == 2


# ---------------------------------------------------------------------------
# Test: regression — existing chart has no subchart state unless used
# ---------------------------------------------------------------------------


def test_fresh_chart_has_no_subcharts_attr(chart):
    """A fresh Chart must not have _subcharts or _subchart_manager_id set."""
    assert not hasattr(chart, "_subcharts")
    assert not hasattr(chart, "_subchart_manager_id")
