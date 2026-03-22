import pandas as pd
import numpy as np
from lightweight_charts import Chart

np.random.seed(7)
dates = pd.date_range('2024-01-01', periods=60, freq='1H')
values = 150 + np.cumsum(np.random.randn(60))
df = pd.DataFrame({'time': dates, 'value': values})

chart = Chart()
line = chart.create_line(name='Animated', color='#FF6B6B', last_price_animation='continuous')
line.set(df)
chart.fit()
chart.show(block=True)
