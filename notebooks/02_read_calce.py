from pathlib import Path
import pandas as pd

DATASET_FOLDER = (
    Path(__file__).resolve().parents[2]
    / "datasets"
    / "CALCE"
    / "CS2"
    / "CS2_35"
)

# Use the first Excel file
files = sorted(DATASET_FOLDER.glob("*.xlsx"))

if not files:
    print("ERROR: No Excel files found.")
    exit()

file = files[0]

print("=" * 70)
print("CALCE CS2-35 CHANNEL DATA INSPECTION")
print("=" * 70)

print("\nFile:")
print(file.name)

# Read the actual measurement sheet WITHOUT assuming a header
df = pd.read_excel(
    file,
    sheet_name="Channel_1-008",
    header=None
)

print("\nShape:")
print(df.shape)

print("\nFirst 15 rows:")
print(df.head(15).to_string())

print("\n" + "=" * 70)
print("DATA TYPES")
print("=" * 70)

print(df.dtypes)

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)