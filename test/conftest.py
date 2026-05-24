"""
conftest.py — pytest session configuration.

- Ensures the working directory is set to test/ so that relative paths
  used by existing tests (e.g. "drawings.json") resolve correctly.
- Exposes shared fixtures (BARS, chart) used across test modules.
"""

import os

import pandas as pd
import pytest

from lightweight_charts import Chart

# ---------------------------------------------------------------------------
# Working-directory fixture
# ---------------------------------------------------------------------------

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(_TEST_DIR, "..", "examples", "1_setting_data", "ohlcv.csv")


@pytest.fixture(scope="session", autouse=True)
def change_to_test_dir():
    """Change cwd to test/ for the duration of the session so that relative
    file paths used in tests (e.g. drawings.json) resolve correctly."""
    original = os.getcwd()
    os.chdir(_TEST_DIR)
    yield
    os.chdir(original)


# ---------------------------------------------------------------------------
# Shared data fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def bars():
    """Load the OHLCV sample CSV once per test session.

    index_col=0 drops the spurious 'Unnamed: 0' index column so tests that
    check column names are not affected by CSV formatting artifacts.
    """
    return pd.read_csv(_DATA_PATH, index_col=0)


# ---------------------------------------------------------------------------
# Chart fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def chart():
    """Create a Chart instance (no window shown) and tear it down after each test."""
    c = Chart(100, 100, 800, 100)
    yield c
    c.exit()
