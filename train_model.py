import pandas as pd
import numpy as np
import pickle
import json
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# Create models folder
os.makedirs("models", exist_ok=True)

# Load Real Dataset
df = pd.read_csv("dataset/uci_student_performance.csv")

# Create Pass/Fail target
df["result"] = (df["G3"] >= 10).astype(int)

# Remove target-related leakage columns
X = df.drop(columns=["G3", "result", "G1", "G2"])
y = df["result"]

# Identify columns
categorical_cols = X.select_dtypes(
    include=["object"]
).columns.tolist()

numerical_cols = X.select_dtypes(
    exclude=["object"]
).columns.tolist()

# Preprocessing
numeric_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("num", numeric_transformer, numerical_cols),
    ("cat", categorical_transformer, categorical_cols)
])

# Train Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Models
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=42
    ),

    "Decision Tree": DecisionTreeClassifier(
        criterion="entropy",
        max_depth=5,
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42
    )
}

results = {}

for name, model in models.items():

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", model)
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(
        y_test, predictions, zero_division=0
    )
    recall = recall_score(
        y_test, predictions, zero_division=0
    )
    f1 = f1_score(
        y_test, predictions, zero_division=0
    )

    results[name] = {
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1 * 100, 2),
        "confusion_matrix": confusion_matrix(
            y_test, predictions
        ).tolist()
    }

    # Save trained model
    filename = name.lower().replace(" ", "_") + ".pkl"

    with open(f"models/{filename}", "wb") as file:
        pickle.dump(pipeline, file)

    print("\n", name)
    print("Accuracy:", round(accuracy * 100, 2), "%")
    print(classification_report(
        y_test, predictions,
        target_names=["Fail", "Pass"],
        zero_division=0
    ))

# Save Results
with open("models/model_results.json", "w") as file:
    json.dump(results, file, indent=4)

# Save feature information
with open("models/feature_columns.json", "w") as file:
    json.dump(X.columns.tolist(), file, indent=4)

print("\n================================")
print("REAL DATASET MODEL TRAINING DONE")
print("Total Records:", len(df))
print("Training Records:", len(X_train))
print("Testing Records:", len(X_test))
print("================================")