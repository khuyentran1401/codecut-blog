"""Catch a column lost in a merged table: compare the sum of the 12 Reserve Bank
rows of Table G.10 with its Total row. check_totals.py MARKDOWN_FILE"""
import re
import sys
from io import StringIO

import pandas as pd

BANKS = ["Boston", "New York", "Philadelphia", "Cleveland", "Richmond", "Atlanta",
         "Chicago", "St. Louis", "Minneapolis", "Kansas City", "Dallas", "San Francisco"]

html = re.findall(r"<table>.*?</table>", open(sys.argv[1]).read(), re.S)[0]
table = pd.read_html(StringIO(html), thousands=",")[0]
table = table.set_index(table.columns[0])

banks = table.loc[BANKS].apply(pd.to_numeric, errors="coerce")
total = pd.to_numeric(table.loc["Total"], errors="coerce")
check = pd.DataFrame({"sum of banks": banks.sum(min_count=1), "Total row": total})
check["missing"] = banks.isna().sum()
print(check.tail(4).to_string())
