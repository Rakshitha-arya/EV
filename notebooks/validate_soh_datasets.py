import os
import pandas as pd
import numpy as np

# ==============================================================
# SOH DATASET VALIDATION
# ==============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOH_DIR = os.path.join(BASE_DIR, "processed", "soh")

NASA_FILE = os.path.join(SOH_DIR, "nasa_soh_features.csv")
OXFORD_FILE = os.path.join(SOH_DIR, "oxford_soh_features.csv")
CALCE_FILE = os.path.join(SOH_DIR, "calce_soh_features.csv")

print("=" * 70)
print("SOH DATASET VALIDATION")
print("=" * 70)

print()
print("SOH directory:")
print(SOH_DIR)

# --------------------------------------------------------------
# Helper
# --------------------------------------------------------------

def validate_file(name, path):
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    if not os.path.exists(path):
        print("ERROR: File not found")
        print(path)
        return None

    df = pd.read_csv(path)

    print()
    print("File:")
    print(path)

    print()
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    print()
    print("Columns:")
    for col in df.columns:
        print(" ", col)

    # ----------------------------------------------------------
    # Missing values
    # ----------------------------------------------------------

    print()
    print("-" * 70)
    print("MISSING VALUES")
    print("-" * 70)

    missing = df.isna().sum()

    for col, value in missing.items():
        pct = (value / len(df)) * 100 if len(df) else 0
        print(
            f"{col:25s} {value:8d} "
            f"({pct:7.2f}%)"
        )

    # ----------------------------------------------------------
    # Duplicate rows
    # ----------------------------------------------------------

    print()
    print("-" * 70)
    print("DUPLICATES")
    print("-" * 70)

    duplicates = df.duplicated().sum()

    print("Duplicate rows:", duplicates)

    # ----------------------------------------------------------
    # Battery count
    # ----------------------------------------------------------

    if "Battery_ID" in df.columns:
        print()
        print("-" * 70)
        print("BATTERY / CELL SUMMARY")
        print("-" * 70)

        print(
            "Unique batteries/cells:",
            df["Battery_ID"].nunique()
        )

        counts = df["Battery_ID"].value_counts().sort_index()

        for battery, count in counts.items():
            print(f"  {str(battery):15s} {count:6d} rows")

    # ----------------------------------------------------------
    # Cycle checks
    # ----------------------------------------------------------

    if "Cycle" in df.columns and "Battery_ID" in df.columns:

        print()
        print("-" * 70)
        print("CYCLE SUMMARY")
        print("-" * 70)

        cycle_counts = (
            df.groupby("Battery_ID")["Cycle"]
            .nunique()
            .sort_index()
        )

        for battery, count in cycle_counts.items():
            print(
                f"  {str(battery):15s} "
                f"{count:6d} cycles"
            )

        duplicate_cycles = (
            df.groupby(["Battery_ID", "Cycle"])
            .size()
        )

        duplicate_cycles = duplicate_cycles[
            duplicate_cycles > 1
        ]

        print()
        print(
            "Battery/cycle combinations with "
            "multiple rows:",
            len(duplicate_cycles)
        )

        if len(duplicate_cycles) > 0:
            print()
            print("First duplicate cycle records:")

            for index, count in duplicate_cycles.head(20).items():
                print(
                    f"  Battery={index[0]} "
                    f"Cycle={index[1]} "
                    f"Rows={count}"
                )

    # ----------------------------------------------------------
    # SOH checks
    # ----------------------------------------------------------

    if "SOH_percent" in df.columns:

        soh = pd.to_numeric(
            df["SOH_percent"],
            errors="coerce"
        )

        print()
        print("-" * 70)
        print("SOH CHECK")
        print("-" * 70)

        valid = soh.dropna()

        print("Valid SOH rows:", len(valid))

        if len(valid) > 0:

            print("Minimum SOH:", valid.min())
            print("Maximum SOH:", valid.max())
            print("Mean SOH:", valid.mean())

            print()
            print("SOH outside expected range 0-100%:")

            invalid = df[
                (soh < 0) |
                (soh > 100)
            ]

            print("Invalid rows:", len(invalid))

            if len(invalid) > 0:

                cols = [
                    c for c in [
                        "Battery_ID",
                        "Cycle",
                        "Capacity_Ah",
                        "SOH_percent"
                    ]
                    if c in invalid.columns
                ]

                print()
                print(
                    invalid[cols]
                    .head(20)
                    .to_string(index=False)
                )

            # --------------------------------------------------
            # Battery-wise SOH range
            # --------------------------------------------------

            if "Battery_ID" in df.columns:

                print()
                print("Battery-wise SOH:")

                summary = (
                    df.groupby("Battery_ID")["SOH_percent"]
                    .agg(
                        count="count",
                        first="first",
                        last="last",
                        minimum="min",
                        maximum="max",
                        mean="mean"
                    )
                )

                print(summary.to_string())

    # ----------------------------------------------------------
    # Capacity checks
    # ----------------------------------------------------------

    if "Capacity_Ah" in df.columns:

        capacity = pd.to_numeric(
            df["Capacity_Ah"],
            errors="coerce"
        )

        valid_capacity = capacity.dropna()

        print()
        print("-" * 70)
        print("CAPACITY CHECK")
        print("-" * 70)

        print(
            "Valid capacity rows:",
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

            print()
            print(
                "Capacity <= 0:",
                (valid_capacity <= 0).sum()
            )

    # ----------------------------------------------------------
    # Numerical feature checks
    # ----------------------------------------------------------

    numeric_columns = [
        "Voltage_Min_V",
        "Voltage_Max_V",
        "Voltage_Mean_V",
        "Voltage_Final_V",
        "Current_Min_A",
        "Current_Max_A",
        "Current_Mean_A",
        "Temperature_Min_C",
        "Temperature_Max_C",
        "Temperature_Mean_C",
        "Temperature_Final_C",
        "Discharge_Time_s"
    ]

    print()
    print("-" * 70)
    print("NUMERIC FEATURE CHECK")
    print("-" * 70)

    for col in numeric_columns:

        if col not in df.columns:
            continue

        values = pd.to_numeric(
            df[col],
            errors="coerce"
        ).dropna()

        if len(values) == 0:
            print(
                f"{col:25s} No numeric values"
            )
            continue

        print(
            f"{col:25s} "
            f"min={values.min():.6f} "
            f"max={values.max():.6f} "
            f"mean={values.mean():.6f}"
        )

    return df


# ==============================================================
# VALIDATE DATASETS
# ==============================================================

nasa = validate_file(
    "NASA",
    NASA_FILE
)

oxford = validate_file(
    "OXFORD",
    OXFORD_FILE
)

calce = validate_file(
    "CALCE",
    CALCE_FILE
)


# ==============================================================
# CROSS DATASET SUMMARY
# ==============================================================

print()
print("=" * 70)
print("CROSS-DATASET SUMMARY")
print("=" * 70)

datasets = [
    ("NASA", nasa),
    ("Oxford", oxford),
    ("CALCE", calce)
]

for name, df in datasets:

    if df is None:
        continue

    batteries = (
        df["Battery_ID"].nunique()
        if "Battery_ID" in df.columns
        else 0
    )

    cycles = (
        df.groupby("Battery_ID")["Cycle"]
        .nunique()
        .sum()
        if "Battery_ID" in df.columns
        and "Cycle" in df.columns
        else 0
    )

    print(
        f"{name:10s} "
        f"Rows={len(df):8d} "
        f"Batteries={batteries:4d} "
        f"Cycles={cycles:6d}"
    )


# ==============================================================
# FINAL
# ==============================================================

print()
print("=" * 70)
print("SOH VALIDATION COMPLETE")
print("=" * 70)

print()
print("IMPORTANT:")
print("1. SOH must normally remain within 0-100%.")
print("2. NASA duplicate battery files must be removed.")
print("3. NASA anomalous capacity/SOH records must be investigated.")
print("4. Do not train the ML model until these checks pass.")
print()