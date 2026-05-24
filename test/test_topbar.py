"""test_topbar.py -- topbar event tests skipped in CI (require display)."""

import pytest


@pytest.mark.skip(reason="requires display: chart.show(block=True) with JS event dispatch")
def test_switcher_fires_event(chart):
    chart.topbar.switcher(
        "a",
        ("1", "2"),
        func=lambda c: (c.topbar["a"].value == "2", c.exit()),
    )
    chart.run_script(
        f'{chart.topbar["a"].id}.intervalElements[1].dispatchEvent(new Event("click"))'
    )
    chart.show(block=True)


@pytest.mark.skip(reason="requires display: chart.show(block=True) with JS event dispatch")
def test_button_fires_event(chart):
    chart.topbar.button(
        "a",
        "1",
        func=lambda c: (c.topbar["a"].value == "2", c.exit()),
    )
    chart.topbar["a"].set("2")
    chart.run_script(f'{chart.topbar["a"].id}.elem.dispatchEvent(new Event("click"))')
    chart.show(block=True)
