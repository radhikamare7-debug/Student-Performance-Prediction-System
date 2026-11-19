import pandas as pd

# Load UCI Dataset
df = pd.read_csv("dataset/uci_student_performance.csv")

print("\n========== DATASET INFORMATION ==========")

print("\nDataset Shape:")
print(df.shape)

print("\nMissing Values:")
print(df.isnull().sum())

print("\nFinal Grade Statistics:")
print(df["G3"].describe())

print("\nPass/Fail Distribution:")
df["result"] = df["G3"].apply(
    lambda marks: "Pass" if marks >= 10 else "Fail"
)

print(df["result"].value_counts())

print("\nFirst 10 Student Records:")
print(df[["studytime", "absences", "G1", "G2", "G3", "result"]].head(10))

print("\nDataset Check Completed!")