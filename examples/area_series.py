import pandas as pd
import numpy as np
from lightweight_charts import Chart

# Generate synthetic price data
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=100, freq='1D')
prices = 100 + np.cumsum(np.random.randn(100))
df = pd.DataFrame({'time': dates, 'value': prices})

if __name__ == '__main__':
    chart = Chart()
    area = chart.create_area(
        name='value',
        top_color='rgba(33, 150, 243, 0.4)',
        bottom_color='rgba(33, 150, 243, 0.0)',
        line_color='#2196F3',
        line_width=2,
    )
    area.set(df)
    chart.fit()
    chart.show(block=True)
