import pandas as pd
import numpy as np
from lightweight_charts import Chart

np.random.seed(3)
dates = pd.date_range('2024-01-01', periods=50, freq='1D')
values = 200 + np.cumsum(np.random.randn(50))
df = pd.DataFrame({'time': dates, 'value': values})

chart = Chart()
line = chart.create_line(name='Line', color='#7B68EE')
line.set(df)

# Attach a custom primitive using a raw JS object that implements
# the ISeriesPrimitive interface.  Replace the body with your own
# plugin constructor (e.g. 'new Lib.Plugins.MyPlugin({})').
primitive = line.attach_primitive(
    '({'
    '  attached: function() {},'
    '  detached: function() {},'
    '  updateAllViews: function() {},'
    '  paneViews: function() { return []; },'
    '})'
)

chart.fit()
chart.show(block=True)
