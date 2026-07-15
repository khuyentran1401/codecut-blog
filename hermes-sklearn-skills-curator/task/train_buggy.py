import pandas as pd
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("data.csv")

X = df.drop(columns=["converted"])
y = df["converted"]

model = LogisticRegression(max_iter=1000)
model.fit(X, y)

print("Accuracy:", model.score(X, y))
