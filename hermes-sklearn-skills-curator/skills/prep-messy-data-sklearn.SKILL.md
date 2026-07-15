---
name: prep-messy-data-sklearn
description: Prepare messy real-world data (missing values, categoricals, string numbers) for scikit-learn
---

# Prep messy data for sklearn

How to get a messy dataset ready for a scikit-learn model:
1. Load the CSV with pandas and inspect dtypes.
2. Convert string-formatted numbers (commas) to numeric.
3. Impute missing values (median for numeric).
4. Encode categorical features.
5. Fit and score the model.
