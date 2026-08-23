import os
import pandas as pd
import numpy as np

# ============================================================
# VALIDATE STANDARDIZED BATTERY DATASETS
# ============================================================

BASE_DIR = r"C:\Major project\flask_app"

STANDARDIZED_DIR = os.path.join(
    BASE_DIR,
    "processed",
    "standardized"
)

FILES = {
    "CALCE": os.path.join(
        STANDARDIZED_DIR,
        "calce_standardized.csv"
    ),
    "NASA": os.path.join(
        STANDARDIZED_DIR,
        "nasa_standardized.csv"
    ),
    "Oxford": os.path.join(
        STANDARDIZED_DIR,
        "oxford_standardized.csv"
    )
}

print("=" * 70)
print("STANDARDIZED DATASET VALIDATION")
print("=" * 70)

print()
print("Directory:")
print(STANDARDIZED_DIR)


# ============================================================
# COMMON COLUMNS
# ============================================================

EXPECTED_COLUMNS = [
    "Dataset",
    "Battery_ID",
    "Cycle",
    "Time",
    "Voltage",
    "Current",
    "Temperature",
    "Capacity_Ah"
]


# ============================================================
# VALIDATE EACH DATASET
# ============================================================

all_data = {}

for dataset_name, filepath in FILES.items():

    print()
    print("=" * 70)
    print(dataset_name)
    print("=" * 70)

    if not os.path.exists(filepath):
        print("ERROR: File not found")
        print(filepath)
        continue

    df = pd.read_csv(filepath)

    all_data[dataset_name] = df

    print()
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    print()
    print("COLUMN CHECK")

    for column in EXPECTED_COLUMNS:

        if column in df.columns:
            print(f"  [OK]      {column}")
        else:
            print(f"  [MISSING] {column}")

    # --------------------------------------------------------
    # Dataset value
    # --------------------------------------------------------

    print()
    print("Dataset labels:")

    if "Dataset" in df.columns:
        print(df["Dataset"].value_counts(dropna=False).to_string())

    # --------------------------------------------------------
    # Battery count
    # --------------------------------------------------------

    print()
    print("Battery/Cell count:")

    if "Battery_ID" in df.columns:
        print(
            "Unique batteries/cells:",
            df["Battery_ID"].nunique()
        )

    # --------------------------------------------------------
    # Actual cycles per battery
    # --------------------------------------------------------

    print()
    print("CYCLES PER BATTERY/CELL")

    if (
        "Battery_ID" in df.columns
        and "Cycle" in df.columns
    ):

        cycle_summary = (
            df.groupby("Battery_ID")["Cycle"]
            .nunique()
            .sort_index()
        )

        for battery, count in cycle_summary.items():
            print(
                f"  {str(battery):<12} "
                f"{count:>6} cycles"
            )

        print()
        print(
            "Total battery/cell cycle records:",
            cycle_summary.sum()
        )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    print()
    print("MISSING VALUES")

    missing = df[EXPECTED_COLUMNS].isna().sum()

    for column, count in missing.items():

        percentage = (
            count / len(df) * 100
            if len(df) > 0
            else 0
        )

        print(
            f"  {column:<15} "
            f"{count:>10} "
            f"({percentage:>7.2f}%)"
        )

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    print()
    print("DUPLICATES")

    duplicate_count = df.duplicated().sum()

    print(
        "Duplicate rows:",
        duplicate_count
    )

    # --------------------------------------------------------
    # Numeric ranges
    # --------------------------------------------------------

    print()
    print("NUMERIC RANGES")

    numeric_columns = [
        "Time",
        "Voltage",
        "Current",
        "Temperature",
        "Capacity_Ah"
    ]

    for column in numeric_columns:

        if column not in df.columns:
            continue

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if len(values) == 0:

            print(
                f"  {column:<15} "
                "No numeric values"
            )

            continue

        print(
            f"  {column:<15} "
            f"min={values.min():.6f} "
            f"max={values.max():.6f} "
            f"mean={values.mean():.6f}"
        )

    # --------------------------------------------------------
    # Capacity information
    # --------------------------------------------------------

    print()
    print("CAPACITY CHECK")

    if "Capacity_Ah" in df.columns:

        capacity = pd.to_numeric(
            df["Capacity_Ah"],
            errors="coerce"
        )

        valid_capacity = capacity.dropna()

        print(
            "Valid Capacity_Ah rows:",
            len(valid_capacity)
        )

        if len(valid_capacity) > 0:

            print(
                "Minimum capacity:",
                valid_capacity.min()
            )

            print(
                "Maximum capacity:",
                valid_capacity.max()
            )

            print(
                "Mean capacity:",
                valid_capacity.mean()
            )

    # --------------------------------------------------------
    # Voltage information
    # --------------------------------------------------------

    print()
    print("VOLTAGE CHECK")

    voltage = pd.to_numeric(
        df["Voltage"],
        errors="coerce"
    ).dropna()

    if len(voltage) > 0:

        print(
            "Valid voltage rows:",
            len(voltage)
        )

        print(
            "Minimum voltage:",
            voltage.min()
        )

        print(
            "Maximum voltage:",
            voltage.max()
        )

    # --------------------------------------------------------
    # Current information
    # --------------------------------------------------------

    print()
    print("CURRENT CHECK")

    current = pd.to_numeric(
        df["Current"],
        errors="coerce"
    ).dropna()

    print(
        "Valid current rows:",
        len(current)
    )

    if len(current) > 0:

        print(
            "Minimum current:",
            current.min()
        )

        print(
            "Maximum current:",
            current.max()
        )

    # --------------------------------------------------------
    # Temperature information
    # --------------------------------------------------------

    print()
    print("TEMPERATURE CHECK")

    temperature = pd.to_numeric(
        df["Temperature"],
        errors="coerce"
    ).dropna()

    print(
        "Valid temperature rows:",
        len(temperature)
    )

    if len(temperature) > 0:

        print(
            "Minimum temperature:",
            temperature.min()
        )

        print(
            "Maximum temperature:",
            temperature.max()
        )


# ============================================================
# CROSS-DATASET SUMMARY
# ============================================================

print()
print("=" * 70)
print("CROSS-DATASET SUMMARY")
print("=" * 70)

print()

for dataset_name, df in all_data.items():

    print(
        f"{dataset_name:<10} "
        f"Rows={len(df):>10} "
        f"Batteries={df['Battery_ID'].nunique():>4}"
    )


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)

print()
print("IMPORTANT:")
print("Do not calculate SOH from this validation script.")
print("The next step will determine the correct capacity")
print("source and SOH method separately for CALCE, NASA")
print("and Oxford.")

print()