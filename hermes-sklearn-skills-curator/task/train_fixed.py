import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np

df = pd.read_csv("data.csv")

# Clean the annual_spend_usd column - remove commas and convert to numeric
df['annual_spend_usd'] = df['annual_spend_usd'].str.replace(',', '').astype(float)

# Handle missing values in annual_spend_usd by filling with median
df['annual_spend_usd'] = df['annual_spend_usd'].fillna(df['annual_spend_usd'].median())

# Encode categorical variables properly
# For respondent_region, we'll use one-hot encoding
X = pd.get_dummies(df.drop(columns=["converted"]), columns=['respondent_region'], drop_first=True)
y = df["converted"]

# Convert target variable to numeric: yes -> 1, no -> 0
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)

model = LogisticRegression(max_iter=1000)
model.fit(X, y)

print("Accuracy:", model.score(X, y))
