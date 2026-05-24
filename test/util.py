"""util.py -- legacy test utilities. CI uses conftest.py fixtures."""

import os

import pandas as pd

path = os.path.join(os.path.dirname(__file__), "../examples/1_setting_data/ohlcv.csv")

BARS = pd.read_csv(path, index_col=0)
