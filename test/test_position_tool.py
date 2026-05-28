"""test_position_tool.py — unit tests for PositionTool quantity validation."""

import pytest
from lightweight_charts.plugins.position_tool import PositionTool


def test_quantity_zero_raises():
    """quantity=0 must raise ValueError."""
    with pytest.raises(ValueError, match="quantity"):
        PositionTool._validate(100.0, 95.0, 110.0, quantity=0)


def test_quantity_negative_raises():
    """quantity < 0 must raise ValueError."""
    with pytest.raises(ValueError, match="quantity"):
        PositionTool._validate(100.0, 95.0, 110.0, quantity=-5)


def test_quantity_none_passes():
    """quantity=None must not raise."""
    PositionTool._validate(100.0, 95.0, 110.0, quantity=None)


def test_quantity_positive_passes():
    """quantity > 0 must not raise."""
    PositionTool._validate(100.0, 95.0, 110.0, quantity=100)
