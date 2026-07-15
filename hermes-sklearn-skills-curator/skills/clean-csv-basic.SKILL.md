---
name: clean-csv-basic
description: Clean a messy CSV for scikit-learn - handle missing values and non-numeric columns
---

# Clean CSV (basic)

Steps to prepare a messy CSV for a scikit-learn model:
1. Read with pandas.
2. Fill missing numeric values with the median.
3. Label-encode categorical columns.
4. Train the model.
