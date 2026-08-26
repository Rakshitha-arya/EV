
"""
======================================================================
NASA SOH TRAINING DATASET SELECTION
======================================================================

Purpose:
    Create a reliable NASA SOH dataset for ML training.

Primary NASA batteries:
    B0005
    B0006
    B0007
    B0018

These batteries provide long, consistent degradation trajectories.

Input:
    processed/soh/nasa_soh_features.csv

Output:
    processed/soh/nasa_soh_training.csv

======================================================================
"""

from pathlib import Path
import pandas as pd
import numpy as np


# =====================================================================
# PROJECT PATHS
# =====================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "processed"
    / "soh"
    / "nasa_soh_features.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "processed"
    / "soh"
    / "nasa_soh_training.csv"
)


# =====================================================================
# CONFIGURATION
# =====================================================================

# Primary reliable NASA batteries
SELECTED_BATTERIES = [
    "B0005",
    "B0006",
    "B0007",
    "B0018",
]

# Expected SOH range
MIN_SOH = 0.0
MAX_SOH = 100.0

# Capacity must be positive
MIN_CAPACITY = 0.0


# =====================================================================
# HEADER
# =====================================================================

print()
print("=" * 70)
print("NASA SOH TRAINING DATASET SELECTION")
print("=" * 70)

print()
print("Project directory:")
print(f"  {BASE_DIR}")

print()
print("Input:")
print(f"  {INPUT_FILE}")

print()
print("Output:")
print(f"  {OUTPUT_FILE}")


# =====================================================================
# CHECK INPUT
# =====================================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"\nNASA input file not found:\n{INPUT_FILE}"
    )


# =====================================================================
# LOAD DATA
# =====================================================================

print()
print("=" * 70)
print("LOADING NASA DATASET")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print()
print(f"Rows loaded: {len(df)}")
print(f"Columns loaded: {len(df.columns)}")

print()
print("Columns:")

for column in df.columns:
    print(f"  {column}")


# =====================================================================
# CHECK REQUIRED COLUMNS
# =====================================================================

REQUIRED_COLUMNS = [
    "Dataset",
    "Battery_ID",
    "Cycle",
    "Original_Cycle_Index",
    "Capacity_Ah",
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
    "Discharge_Time_s",
    "SOH_percent",
]

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in df.columns
]

if missing_columns:
    raise RuntimeError(
        "\nMissing required columns:\n"
        + "\n".join(f"  {c}" for c in missing_columns)
    )


# =====================================================================
# NUMERIC CONVERSION
# =====================================================================

print()
print("=" * 70)
print("CONVERTING NUMERIC COLUMNS")
print("=" * 70)

NUMERIC_COLUMNS = [
    "Cycle",
    "Original_Cycle_Index",
    "Capacity_Ah",
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
    "Discharge_Time_s",
    "SOH_percent",
]

for column in NUMERIC_COLUMNS:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

print()
print("Numeric conversion complete.")


# =====================================================================
# ORIGINAL BATTERY SUMMARY
# =====================================================================

print()
print("=" * 70)
print("ORIGINAL NASA BATTERY SUMMARY")
print("=" * 70)

battery_summary = (
    df.groupby("Battery_ID")
    .size()
    .sort_index()
)

print()
print(f"Total batteries: {df['Battery_ID'].nunique()}")

print()

for battery, count in battery_summary.items():
    print(f"  {battery:<12} {count:>5} rows")


# =====================================================================
# SELECT PRIMARY BATTERIES
# =====================================================================

print()
print("=" * 70)
print("SELECTING PRIMARY TRAINING BATTERIES")
print("=" * 70)

print()
print("Selected batteries:")

for battery in SELECTED_BATTERIES:
    print(f"  {battery}")


# Check availability
available_batteries = set(
    df["Battery_ID"]
    .dropna()
    .astype(str)
    .unique()
)

missing_selected = [
    battery
    for battery in SELECTED_BATTERIES
    if battery not in available_batteries
]

if missing_selected:
    raise RuntimeError(
        "\nSelected NASA batteries not found:\n"
        + "\n".join(f"  {b}" for b in missing_selected)
    )


# =====================================================================
# FILTER BATTERIES
# =====================================================================

training_df = df[
    df["Battery_ID"].astype(str).isin(
        SELECTED_BATTERIES
    )
].copy()

print()
print(f"Rows after battery selection: {len(training_df)}")


# =====================================================================
# REMOVE EXACT DUPLICATES
# =====================================================================

print()
print("=" * 70)
print("REMOVING EXACT DUPLICATES")
print("=" * 70)

before = len(training_df)

training_df = training_df.drop_duplicates()

after = len(training_df)

print()
print(f"Rows before: {before}")
print(f"Rows after : {after}")
print(f"Duplicates removed: {before - after}")


# =====================================================================
# REMOVE BATTERY/CYCLE DUPLICATES
# =====================================================================

print()
print("=" * 70)
print("CHECKING BATTERY/CYCLE DUPLICATES")
print("=" * 70)

duplicate_mask = training_df.duplicated(
    subset=["Battery_ID", "Cycle"],
    keep=False
)

duplicate_count = int(duplicate_mask.sum())

print()
print(
    f"Rows involved in Battery_ID + Cycle duplicates: "
    f"{duplicate_count}"
)

if duplicate_count > 0:

    print()
    print("Duplicate records:")

    print(
        training_df.loc[
            duplicate_mask,
            ["Battery_ID", "Cycle", "Capacity_Ah", "SOH_percent"]
        ]
        .sort_values(["Battery_ID", "Cycle"])
        .head(20)
        .to_string(index=False)
    )

    # Keep the first record for each battery/cycle
    training_df = (
        training_df
        .sort_values(
            ["Battery_ID", "Cycle"]
        )
        .drop_duplicates(
            subset=["Battery_ID", "Cycle"],
            keep="first"
        )
    )

print()
print(
    f"Rows after Battery/Cycle duplicate handling: "
    f"{len(training_df)}"
)


# =====================================================================
# REMOVE MISSING VALUES
# =====================================================================

print()
print("=" * 70)
print("CHECKING MISSING VALUES")
print("=" * 70)

missing_before = int(training_df.isna().sum().sum())

print()
print(f"Missing values before cleaning: {missing_before}")

if missing_before > 0:

    print()
    print("Missing values by column:")

    missing_table = (
        training_df.isna()
        .sum()
        .loc[lambda x: x > 0]
    )

    print(missing_table.to_string())

    training_df = training_df.dropna(
        subset=[
            "Battery_ID",
            "Cycle",
            "Capacity_Ah",
            "SOH_percent",
        ]
    )

print()
print(
    f"Missing values after required-field cleaning: "
    f"{training_df.isna().sum().sum()}"
)


# =====================================================================
# CAPACITY VALIDATION
# =====================================================================

print()
print("=" * 70)
print("CAPACITY VALIDATION")
print("=" * 70)

invalid_capacity = (
    training_df["Capacity_Ah"] <= MIN_CAPACITY
)

invalid_capacity_count = int(
    invalid_capacity.sum()
)

print()
print(
    f"Capacity <= {MIN_CAPACITY}: "
    f"{invalid_capacity_count}"
)

if invalid_capacity_count > 0:
    training_df = training_df[
        ~invalid_capacity
    ].copy()


# =====================================================================
# SOH VALIDATION
# =====================================================================

print()
print("=" * 70)
print("SOH VALIDATION")
print("=" * 70)

print()
print(
    f"SOH before validation:"
)

print(
    f"  Minimum: "
    f"{training_df['SOH_percent'].min():.6f}%"
)

print(
    f"  Maximum: "
    f"{training_df['SOH_percent'].max():.6f}%"
)

invalid_soh = (
    (training_df["SOH_percent"] <= MIN_SOH)
    |
    (training_df["SOH_percent"] > MAX_SOH)
)

invalid_soh_count = int(
    invalid_soh.sum()
)

print()
print(
    f"SOH outside 0-100%: "
    f"{invalid_soh_count}"
)

if invalid_soh_count > 0:

    print()
    print(
        "WARNING: Invalid SOH records detected."
    )

    print()
    print(
        training_df.loc[
            invalid_soh,
            [
                "Battery_ID",
                "Cycle",
                "Capacity_Ah",
                "SOH_percent",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    training_df = training_df[
        ~invalid_soh
    ].copy()


# =====================================================================
# SORT DATA
# =====================================================================

print()
print("=" * 70)
print("SORTING TRAINING DATA")
print("=" * 70)

training_df = (
    training_df
    .sort_values(
        ["Battery_ID", "Cycle"]
    )
    .reset_index(drop=True)
)

print()
print("Dataset sorted by Battery_ID and Cycle.")


# =====================================================================
# RECALCULATE SOH
# =====================================================================

print()
print("=" * 70)
print("RECALCULATING BATTERY-WISE SOH")
print("=" * 70)

print()
print(
    "SOH is calculated independently for each battery."
)

print(
    "The first valid capacity of each battery is "
    "treated as 100% SOH."
)


def calculate_battery_soh(group):

    group = group.sort_values(
        "Cycle"
    ).copy()

    first_capacity = group[
        "Capacity_Ah"
    ].iloc[0]

    if (
        pd.isna(first_capacity)
        or first_capacity <= 0
    ):
        group["SOH_percent"] = np.nan

    else:
        group["SOH_percent"] = (
            group["Capacity_Ah"]
            / first_capacity
            * 100.0
        )

    return group


training_df = (
    training_df
    .groupby(
        "Battery_ID",
        group_keys=False
    )
    .apply(
        calculate_battery_soh
    )
    .reset_index(drop=True)
)

print()
print("SOH recalculation complete.")


# =====================================================================
# FINAL SOH VALIDATION
# =====================================================================

print()
print("=" * 70)
print("FINAL SOH VALIDATION")
print("=" * 70)

training_df = training_df[
    training_df["SOH_percent"].notna()
].copy()

invalid_soh = (
    (training_df["SOH_percent"] <= 0)
    |
    (training_df["SOH_percent"] > 100)
)

print()
print(
    f"SOH minimum: "
    f"{training_df['SOH_percent'].min():.6f}%"
)

print(
    f"SOH maximum: "
    f"{training_df['SOH_percent'].max():.6f}%"
)

print(
    f"SOH mean: "
    f"{training_df['SOH_percent'].mean():.6f}%"
)

print()
print(
    f"Invalid SOH records: "
    f"{invalid_soh.sum()}"
)

if invalid_soh.any():

    print()
    print("Removing invalid SOH records...")

    training_df = training_df[
        ~invalid_soh
    ].copy()


# =====================================================================
# CHECK FIRST SOH OF EACH BATTERY
# =====================================================================

print()
print("=" * 70)
print("CHECKING FIRST SOH OF EACH BATTERY")
print("=" * 70)

first_soh = (
    training_df
    .sort_values(
        ["Battery_ID", "Cycle"]
    )
    .groupby("Battery_ID")
    ["SOH_percent"]
    .first()
)

print()

print(
    first_soh
    .to_string(
        float_format=lambda x: f"{x:.4f}"
    )
)

first_soh_ok = np.allclose(
    first_soh.values,
    100.0,
    atol=1e-6
)

print()

if first_soh_ok:
    print(
        "All selected batteries start at 100% SOH."
    )
else:
    print(
        "WARNING: Some batteries do not start at 100% SOH."
    )


# =====================================================================
# FINAL DUPLICATE CHECK
# =====================================================================

print()
print("=" * 70)
print("FINAL DUPLICATE CHECK")
print("=" * 70)

exact_duplicates = int(
    training_df.duplicated().sum()
)

battery_cycle_duplicates = int(
    training_df.duplicated(
        subset=["Battery_ID", "Cycle"]
    ).sum()
)

print()
print(
    f"Exact duplicate rows: "
    f"{exact_duplicates}"
)

print(
    f"Battery/Cycle duplicate rows: "
    f"{battery_cycle_duplicates}"
)


# =====================================================================
# FINAL SUMMARY
# =====================================================================

print()
print("=" * 70)
print("FINAL NASA TRAINING DATASET SUMMARY")
print("=" * 70)

print()
print(
    f"Rows: {len(training_df)}"
)

print(
    f"Batteries: "
    f"{training_df['Battery_ID'].nunique()}"
)

print(
    f"Total battery/cycle records: "
    f"{len(training_df)}"
)

print()
print("Rows per battery:")

final_counts = (
    training_df
    .groupby("Battery_ID")
    .size()
    .sort_index()
)

for battery, count in final_counts.items():
    print(
        f"  {battery:<12} {count:>5} rows"
    )


# =====================================================================
# BATTERY SOH SUMMARY
# =====================================================================

print()
print("=" * 70)
print("BATTERY-WISE SOH SUMMARY")
print("=" * 70)

soh_summary = (
    training_df
    .groupby("Battery_ID")["SOH_percent"]
    .agg(
        count="count",
        first="first",
        last="last",
        minimum="min",
        maximum="max",
        mean="mean",
    )
)

print()

print(
    soh_summary.to_string(
        float_format=lambda x: f"{x:.4f}"
    )
)


# =====================================================================
# CAPACITY SUMMARY
# =====================================================================

print()
print("=" * 70)
print("CAPACITY SUMMARY")
print("=" * 70)

print()
print(
    f"Minimum capacity: "
    f"{training_df['Capacity_Ah'].min():.6f} Ah"
)

print(
    f"Maximum capacity: "
    f"{training_df['Capacity_Ah'].max():.6f} Ah"
)

print(
    f"Mean capacity: "
    f"{training_df['Capacity_Ah'].mean():.6f} Ah"
)


# =====================================================================
# FINAL VALIDATION
# =====================================================================

print()
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

checks = {
    "No missing values":
        not training_df.isna().any().any(),

    "No exact duplicates":
        training_df.duplicated().sum() == 0,

    "No Battery/Cycle duplicates":
        training_df.duplicated(
            subset=["Battery_ID", "Cycle"]
        ).sum() == 0,

    "SOH > 0":
        (training_df["SOH_percent"] > 0).all(),

    "SOH <= 100":
        (training_df["SOH_percent"] <= 100).all(),

    "Capacity > 0":
        (training_df["Capacity_Ah"] > 0).all(),

    "Four primary batteries present":
        set(SELECTED_BATTERIES).issubset(
            set(training_df["Battery_ID"])
        ),
}

all_passed = True

for check_name, passed in checks.items():

    if passed:
        print(f"  [PASS] {check_name}")

    else:
        print(f"  [FAIL] {check_name}")
        all_passed = False


# =====================================================================
# SAVE DATASET
# =====================================================================

print()
print("=" * 70)
print("SAVING NASA TRAINING DATASET")
print("=" * 70)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

training_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Training dataset saved successfully:")
print(f"  {OUTPUT_FILE}")


# =====================================================================
# VERIFY SAVED FILE
# =====================================================================

print()
print("=" * 70)
print("VERIFYING SAVED FILE")
print("=" * 70)

if not OUTPUT_FILE.exists():
    raise RuntimeError(
        "Output file was not created."
    )

saved_df = pd.read_csv(
    OUTPUT_FILE
)

print()
print(
    f"Saved rows: "
    f"{len(saved_df)}"
)

print(
    f"Saved columns: "
    f"{len(saved_df.columns)}"
)

print(
    f"Saved batteries: "
    f"{saved_df['Battery_ID'].nunique()}"
)

print(
    f"Saved minimum SOH: "
    f"{saved_df['SOH_percent'].min():.6f}%"
)

print(
    f"Saved maximum SOH: "
    f"{saved_df['SOH_percent'].max():.6f}%"
)

print(
    f"Saved mean SOH: "
    f"{saved_df['SOH_percent'].mean():.6f}%"
)


# =====================================================================
# COMPLETION
# =====================================================================

print()
print("=" * 70)

if all_passed:

    print("NASA SOH TRAINING DATASET CREATION COMPLETE")
    print("=" * 70)

    print()
    print("Primary batteries:")
    for battery in SELECTED_BATTERIES:
        print(f"  {battery}")

    print()
    print("Output:")
    print(f"  {OUTPUT_FILE}")

    print()
    print(
        "The dataset is ready for the next feature/training stage."
    )

else:

    print("NASA SOH TRAINING DATASET CREATED WITH WARNINGS")
    print("=" * 70)

    print()
    print(
        "Review the [FAIL] checks before ML training."
    )

print()
