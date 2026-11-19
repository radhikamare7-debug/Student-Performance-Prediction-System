import pandas as pd
from ucimlrepo import fetch_ucirepo

print("Downloading UCI Student Performance Dataset...")

# Fetch real dataset
student_data = fetch_ucirepo(id=320)

# Features and target
X = student_data.data.features
y = student_data.data.targets

# Combine features and target
df = pd.concat([X, y], axis=1)

# Save dataset
df.to_csv(
    "dataset/uci_student_performance.csv",
    index=False
)

print("\nDataset Downloaded Successfully!")

print("Dataset Shape:", df.shape)

print("\nFirst 5 Records:")
print(df.head())

print("\nDataset Columns:")
print(df.columns.tolist())