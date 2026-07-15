---
name: sklearn-debug-v2
description: Debug and fix common issues with scikit-learn models in data science workflows
tags:
  - data-science
  - ml
  - pandas
  - debugging
---

# sklearn-debug-v2

This skill describes how to debug and fix common issues with scikit-learn models in data science workflows, especially when dealing with real-world messy datasets.

## Common Issues Addressed

1. **String columns with numeric values**: Handling fields like "1,200" that need to be converted to numeric
2. **Categorical features**: Encoding categorical variables using LabelEncoder for machine learning compatibility  
3. **Missing data**: Properly handling NaN values in numerical columns
4. **Data type mismatches**: Ensuring all input data is in the correct format for ML algorithms

## Typical Workflow

1. Read and inspect the dataset with `df.head()` and `df.dtypes`
2. Identify string columns containing numeric data (like "1,200")
3. Convert these to proper numeric types using `.str.replace(',', '').astype(float)`
4. Handle missing values appropriately (median/mean imputation)
5. Encode categorical variables using LabelEncoder
6. Prepare features and target for model training
7. Fit the model and evaluate performance

## Example Code Pattern

```python
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import numpy as np

df = pd.read_csv("data.csv")

# Convert string columns with commas to numeric
df['numeric_column'] = df['numeric_column'].str.replace(',', '').astype(float)

# Handle missing values
median_value = df['numeric_column'].median()
df['numeric_column'] = df['numeric_column'].fillna(median_value)

# Encode categorical features
label_encoder = LabelEncoder()
df['categorical_column_encoded'] = label_encoder.fit_transform(df['categorical_column'])

# Prepare features and target
X = df.drop(columns=['target'])
y = df['target']

model = LogisticRegression(max_iter=1000)
model.fit(X, y)
print("Accuracy:", model.score(X, y))
```

## Key Tips

- Always check data types before feeding into ML models
- Handle missing values explicitly rather than letting them cause errors
- Use LabelEncoder for simple categorical encoding in binary classification problems
- Ensure all columns are the correct data type before fitting models