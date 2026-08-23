import os
import pandas as pd

BASE_DIR = r"C:\Major project\flask_app"

FILES = [
    os.path.join(
        BASE_DIR,
        "processed",
        "calce"
    ),
    os.path.join(
        BASE_DIR,
        "processed",
        "calce_measurements.csv"
    ),
]

print("=" * 70)
print("CALCE PROCESSED DATA INSPECTION")
print("=" * 70)

for path in FILES:

    print()
    print("-" * 70)
    print("PATH:")
    print(path)

    if os.path.isdir(path):

        print("Directory found")

        for root, dirs, files in os.walk(path):

            for file in files:

                print(
                    os.path.join(root, file)
                )

    elif os.path.isfile(path):

        print("CSV file found")

        df = pd.read_csv(path)

        print()
        print("Rows:", len(df))
        print("Columns:", len(df.columns))

        print()
        print("Columns:")
        for col in df.columns:
            print(" ", col)

        print()
        print("First 5 rows:")
        print(df.head().to_string())

        print()
        print("Missing values:")
        print(df.isna().sum().to_string())

print()
print("=" * 70)
print("CALCE INSPECTION COMPLETE")
print("=" * 70)