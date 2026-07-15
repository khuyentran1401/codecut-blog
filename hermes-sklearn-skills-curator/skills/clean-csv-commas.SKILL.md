---
name: clean-csv-commas
description: Fix CSV columns where numbers are stored as strings with commas before sklearn
---

# Clean CSV (comma numbers)

Preparing a messy CSV for scikit-learn when numbers have commas:
1. Read with pandas.
2. Strip commas and convert string-numbers to float.
3. Impute missing numeric values with the median.
4. Encode categorical columns for the model.
