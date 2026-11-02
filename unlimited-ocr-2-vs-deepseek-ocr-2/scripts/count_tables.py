"""Load every HTML table in each file with pandas and print its shape: count_tables.py FILE..."""
import re
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

for path in map(Path, sys.argv[1:]):
    tables = re.findall(r"<table>.*?</table>", path.read_text(), re.S)
    shapes = [pd.read_html(StringIO(table))[0].shape for table in tables]
    print(f"{path}: {len(shapes)} DataFrame(s) {shapes}")
