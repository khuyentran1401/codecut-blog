---
name: Data Cleaning for Machine Learning
category: data-science
description: Process of cleaning and preparing data for machine learning models, especially when dealing with mixed data types and formatting issues.
---

# Data Cleaning for Machine Learning

## Overview
This skill outlines the process of cleaning and preparing data for machine learning models, especially when dealing with mixed data types and formatting issues.

## Key Steps

1. **Inspect Data Types**
   - Check column data types using `df.dtypes`
   - Identify non-numeric columns that need encoding

2. **Handle Text-to-Numeric Conversion** 
   - Remove special characters (commas, dollar signs)
   - Convert empty strings to NaN
   - Cast to appropriate numeric dtypes

3. **Encode Categorical Variables**
   - Use `LabelEncoder` or `OneHotEncoder`
   - Transform string categories to numeric representations

4. **Handle Missing Values**
   - Identify missing data patterns
   - Fill using mean, median, mode, or forward/backward fill strategies

5. **Feature Selection** 
   - Remove non-numeric columns that can't be directly used
   - Select only appropriate features for training

## Common Issues and Solutions

### String Numbers with Commas
```python
df['column'] = df['column'].str.replace(',', '').replace('', np.nan).astype(float)
```

### Categorical Encoding
```python
from sklearn.preprocessing import LabelEncoder
label_encoder = LabelEncoder()
df['encoded_column'] = label_encoder.fit_transform(df['original_column'])
```

### Handling Missing Data
```python
X = X.fillna(X.mean())  # or median, mode, etc.
```

## Best Practices
- Always inspect data before machine learning
- Preserve original data when possible 
- Use appropriate encoding strategies for different column types
- Validate that all features are numeric before model training