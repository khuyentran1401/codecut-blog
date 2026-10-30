import numpy as np
import polars as pl

masked_tips = np.ma.array([3.75, 0.0, 3.0], mask=[False, True, False])
tips = pl.Series("tip_amount", masked_tips)

print(tips.to_list())
print(repr(tips.to_numpy(masked=True)))
