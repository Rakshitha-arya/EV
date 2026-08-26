"""
clean_nasa_soh_dataset.py

Clean and validate the NASA SOH feature dataset.

Input:
    processed/soh/nasa_soh_features.csv

Output:
    processed/soh/nasa_soh_features_clean.csv

Main operations:
1. Load the extracted NASA SOH dataset.
2. Remove duplicate Battery_ID + Cycle records.
3. Detect invalid/anomalous capacity values.
4. Recalculate SOH independently for every battery.
5. Keep SOH strictly within 0-100%.
6. Remove invalid rows instead of clipping them.
7. Save the cleaned NASA dataset.
8. Print a detailed validation summary.

IMPORTANT:
- This script does NOT modify the original CSV.
- The original NASA file remains unchanged.
- The cleaned dataset is saved separately.
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ======================================================================
# CONFIGURATION
# ======================================================================

# Project directory:
# C:\Major project\flask_app
BASE_DIR = Path(__file__).resolve().parent.parent

# Input/output directories
SOH_DIR = BASE_DIR / "processed" / "soh"

INPUT_FILE = SOH_DIR / "nasa_soh_features.csv"
OUTPUT_FILE = SOH_DIR / "nasa_soh_features_clean.csv"

# ----------------------------------------------------------------------
# Dataset-specific cleaning limits
# ----------------------------------------------------------------------

# NASA lithium-ion battery capacities in this project are expected
# to be approximately in the range 0.5 Ah to 2.0 Ah for normal records.
#
# We use a deliberately broad upper limit so that we do not remove
# legitimate records simply because they differ slightly between
# battery groups.
MIN_CAPACITY_AH = 0.05
MAX_CAPACITY_AH = 2.10

# SOH must be physically meaningful.
MIN_SOH = 0.0
MAX_SOH = 100.0


# ======================================================================
# HELPER FUNCTIONS
# ======================================================================

def print_separator(char="=", length=70):
    print(char * length)


def print_section(title):
    print()
    print_separator()
    print(title)
    print_separator()


def safe_numeric(df, columns):
    """
    Convert selected columns to numeric values.

    Invalid values become NaN.
    """
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def calculate_soh(group):
    """
    Calculate battery-wise SOH.

    The first valid capacity for each battery is treated as 100% SOH.

        SOH = Capacity / Initial Capacity * 100

    The original capacity is preserved.
    """

    group = group.sort_values(
        by=["Cycle", "Original_Cycle_Index"],
        kind="stable"
    ).copy()

    valid_capacity = group["Capacity_Ah"].notna() & (
        group["Capacity_Ah"] > 0
    )

    if not valid_capacity.any():
        group["SOH_percent"] = np.nan
        return group

    first_capacity = group.loc[
        valid_capacity, "Capacity_Ah"
    ].iloc[0]

    group["SOH_percent"] = (
        group["Capacity_Ah"] / first_capacity
    ) * 100.0

    return group


def recalculate_all_soh(df):
    """
    Recalculate SOH independently for each battery.
    """

    cleaned_groups = []

    for battery_id, group in df.groupby(
        "Battery_ID",
        sort=False
    ):
        group = calculate_soh(group)
        cleaned_groups.append(group)

    if not cleaned_groups:
        return df.copy()

    result = pd.concat(
        cleaned_groups,
        ignore_index=True
    )

    return result


# ======================================================================
# START
# ======================================================================

print_section("NASA SOH DATASET CLEANING")

print(f"Project directory:")
print(f"  {BASE_DIR}")

print()
print("Input:")
print(f"  {INPUT_FILE}")

print()
print("Output:")
print(f"  {OUTPUT_FILE}")


# ======================================================================
# CHECK INPUT FILE
# ======================================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"\nNASA SOH input file was not found:\n{INPUT_FILE}\n\n"
        "Run fix_nasa_soh_extraction.py first."
    )


# ======================================================================
# LOAD DATA
# ======================================================================

print_section("LOADING NASA SOH DATASET")

df = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(df)}")
print(f"Columns loaded: {len(df.columns)}")

print()
print("Columns:")

for column in df.columns:
    print(f"  {column}")


# ======================================================================
# REQUIRED COLUMNS
# ======================================================================

required_columns = [
    "Dataset",
    "Battery_ID",
    "Cycle",
    "Original_Cycle_Index",
    "Capacity_Ah",
    "SOH_percent",
]

missing_required = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_required:
    raise RuntimeError(
        "\nRequired columns are missing:\n"
        + "\n".join(
            f"  {column}"
            for column in missing_required
        )
    )


# ======================================================================
# CONVERT NUMERIC COLUMNS
# ======================================================================

print_section("CONVERTING NUMERIC COLUMNS")

numeric_columns = [
    "Cycle",
    "Original_Cycle_Index",
    "Capacity_Ah",
    "SOH_percent",
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
]

df = safe_numeric(df, numeric_columns)

print("Numeric conversion complete.")


# ======================================================================
# ORIGINAL DATA SUMMARY
# ======================================================================

print_section("ORIGINAL DATASET SUMMARY")

print(f"Rows: {len(df)}")
print(f"Unique batteries: {df['Battery_ID'].nunique()}")

print()
print("Rows per battery:")

battery_counts = (
    df.groupby("Battery_ID")
    .size()
    .sort_index()
)

for battery_id, count in battery_counts.items():
    print(f"  {battery_id:<10} {count:>5} rows")


# ======================================================================
# STEP 1: REMOVE EXACT DUPLICATE ROWS
# ======================================================================

print_section("STEP 1 - REMOVING EXACT DUPLICATE ROWS")

before_exact = len(df)

df = df.drop_duplicates(
    keep="first"
).reset_index(drop=True)

removed_exact = before_exact - len(df)

print(f"Rows before: {before_exact}")
print(f"Rows after : {len(df)}")
print(f"Exact duplicate rows removed: {removed_exact}")


# ======================================================================
# STEP 2: REMOVE DUPLICATE BATTERY + CYCLE RECORDS
# ======================================================================

print_section(
    "STEP 2 - REMOVING DUPLICATE BATTERY/CYCLE RECORDS"
)

duplicate_mask = df.duplicated(
    subset=["Battery_ID", "Cycle"],
    keep=False
)

duplicate_rows = df.loc[
    duplicate_mask
].copy()

print(
    f"Rows involved in duplicate Battery_ID + Cycle "
    f"records: {len(duplicate_rows)}"
)

if len(duplicate_rows) > 0:

    duplicate_groups = (
        duplicate_rows
        .groupby(["Battery_ID", "Cycle"])
        .size()
        .reset_index(name="Rows")
        .sort_values(["Battery_ID", "Cycle"])
    )

    print()
    print("Duplicate battery/cycle groups:")

    for _, row in duplicate_groups.head(50).iterrows():
        print(
            f"  Battery={row['Battery_ID']} "
            f"Cycle={int(row['Cycle'])} "
            f"Rows={int(row['Rows'])}"
        )

    if len(duplicate_groups) > 50:
        print(
            f"  ... and "
            f"{len(duplicate_groups) - 50} more groups"
        )


# ----------------------------------------------------------------------
# Why keep the first record?
#
# Your validation showed that B0025-B0028 appear twice because the same
# batteries exist in more than one NASA folder.
#
# The duplicate files represent the same Battery_ID/Cycle combination.
#
# Therefore we keep the first occurrence and remove later copies.
# ----------------------------------------------------------------------

before_cycle_dedup = len(df)

df = df.drop_duplicates(
    subset=["Battery_ID", "Cycle"],
    keep="first"
).reset_index(drop=True)

removed_cycle_duplicates = (
    before_cycle_dedup - len(df)
)

print()
print(
    f"Battery/cycle duplicate rows removed: "
    f"{removed_cycle_duplicates}"
)

print(f"Rows remaining: {len(df)}")


# ======================================================================
# STEP 3: CHECK MISSING CAPACITY
# ======================================================================

print_section("STEP 3 - CHECKING CAPACITY VALUES")

missing_capacity = df["Capacity_Ah"].isna().sum()

nonpositive_capacity = (
    df["Capacity_Ah"] <= 0
).sum()

print(f"Missing capacity records: {missing_capacity}")
print(f"Capacity <= 0 records    : {nonpositive_capacity}")

if missing_capacity > 0:
    print()
    print("Removing rows with missing capacity.")

if nonpositive_capacity > 0:
    print()
    print("Removing rows with non-positive capacity.")


before_capacity_validity = len(df)

df = df[
    df["Capacity_Ah"].notna()
    & (df["Capacity_Ah"] > 0)
].copy()

removed_invalid_capacity = (
    before_capacity_validity - len(df)
)

print()
print(
    f"Invalid capacity rows removed: "
    f"{removed_invalid_capacity}"
)


# ======================================================================
# STEP 4: DETECT ANOMALOUS CAPACITY
# ======================================================================

print_section("STEP 4 - DETECTING ANOMALOUS CAPACITY")

print(
    f"Accepted capacity range:"
    f" {MIN_CAPACITY_AH} Ah to {MAX_CAPACITY_AH} Ah"
)

capacity_anomaly_mask = (
    (df["Capacity_Ah"] < MIN_CAPACITY_AH)
    | (df["Capacity_Ah"] > MAX_CAPACITY_AH)
)

capacity_anomalies = df.loc[
    capacity_anomaly_mask
].copy()

print()
print(
    f"Capacity anomaly rows found: "
    f"{len(capacity_anomalies)}"
)

if len(capacity_anomalies) > 0:

    print()
    print("Examples of anomalous capacity records:")

    display_columns = [
        "Battery_ID",
        "Cycle",
        "Original_Cycle_Index",
        "Capacity_Ah",
    ]

    available_display_columns = [
        column
        for column in display_columns
        if column in capacity_anomalies.columns
    ]

    print(
        capacity_anomalies[
            available_display_columns
        ]
        .head(30)
        .to_string(index=False)
    )

    if len(capacity_anomalies) > 30:
        print(
            f"\n... {len(capacity_anomalies) - 30} "
            f"additional anomalous rows."
        )


# ----------------------------------------------------------------------
# Remove anomalous capacity records.
# ----------------------------------------------------------------------

before_anomaly_removal = len(df)

df = df[
    ~capacity_anomaly_mask
].copy()

removed_capacity_anomalies = (
    before_anomaly_removal - len(df)
)

print()
print(
    f"Anomalous capacity rows removed: "
    f"{removed_capacity_anomalies}"
)

print(f"Rows remaining: {len(df)}")


# ======================================================================
# STEP 5: SORT DATA
# ======================================================================

print_section("STEP 5 - SORTING DATA")

df = df.sort_values(
    by=["Battery_ID", "Cycle"],
    kind="stable"
).reset_index(drop=True)

print("Dataset sorted by Battery_ID and Cycle.")


# ======================================================================
# STEP 6: RECALCULATE SOH
# ======================================================================

print_section("STEP 6 - RECALCULATING SOH")

print(
    "SOH is calculated independently for each battery."
)

print(
    "The first valid capacity of each battery is treated "
    "as 100% SOH."
)

df = recalculate_all_soh(df)

print("SOH recalculation complete.")


# ======================================================================
# STEP 7: CHECK SOH
# ======================================================================

print_section("STEP 7 - VALIDATING SOH")

print(
    f"SOH minimum before range filtering: "
    f"{df['SOH_percent'].min()}"
)

print(
    f"SOH maximum before range filtering: "
    f"{df['SOH_percent'].max()}"
)

invalid_soh_mask = (
    df["SOH_percent"].isna()
    | (df["SOH_percent"] <= MIN_SOH)
    | (df["SOH_percent"] > MAX_SOH)
)

invalid_soh = df.loc[
    invalid_soh_mask
].copy()

print()
print(
    f"Invalid SOH rows found: "
    f"{len(invalid_soh)}"
)

if len(invalid_soh) > 0:

    print()
    print("Examples of invalid SOH records:")

    print(
        invalid_soh[
            [
                "Battery_ID",
                "Cycle",
                "Capacity_Ah",
                "SOH_percent",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )


# ======================================================================
# STEP 8: REMOVE INVALID SOH RECORDS
# ======================================================================

print_section("STEP 8 - REMOVING INVALID SOH RECORDS")

before_soh_filter = len(df)

df = df[
    ~invalid_soh_mask
].copy()

removed_invalid_soh = (
    before_soh_filter - len(df)
)

print(
    f"Invalid SOH rows removed: "
    f"{removed_invalid_soh}"
)

print(f"Rows remaining: {len(df)}")


# ======================================================================
# STEP 9: FINAL DUPLICATE CHECK
# ======================================================================

print_section("STEP 9 - FINAL DUPLICATE CHECK")

exact_duplicates_final = df.duplicated().sum()

battery_cycle_duplicates_final = df.duplicated(
    subset=["Battery_ID", "Cycle"]
).sum()

print(
    f"Exact duplicate rows: "
    f"{exact_duplicates_final}"
)

print(
    f"Duplicate Battery_ID + Cycle rows: "
    f"{battery_cycle_duplicates_final}"
)

if exact_duplicates_final != 0:
    print(
        "\nWARNING: Exact duplicates still exist."
    )

if battery_cycle_duplicates_final != 0:
    print(
        "\nWARNING: Battery/cycle duplicates still exist."
    )


# ======================================================================
# STEP 10: FINAL MISSING VALUE CHECK
# ======================================================================

print_section("STEP 10 - FINAL MISSING VALUE CHECK")

missing_final = df.isna().sum()

missing_final = missing_final[
    missing_final > 0
]

if len(missing_final) == 0:
    print("No missing values found.")
else:
    print("Missing values found:")
    print(missing_final.to_string())


# ======================================================================
# STEP 11: FINAL SOH VALIDATION
# ======================================================================

print_section("STEP 11 - FINAL SOH VALIDATION")

final_min_soh = df["SOH_percent"].min()
final_max_soh = df["SOH_percent"].max()
final_mean_soh = df["SOH_percent"].mean()

print(
    f"Minimum SOH: {final_min_soh:.6f}%"
)

print(
    f"Maximum SOH: {final_max_soh:.6f}%"
)

print(
    f"Mean SOH   : {final_mean_soh:.6f}%"
)

final_invalid_soh = df[
    (df["SOH_percent"] <= 0)
    | (df["SOH_percent"] > 100)
].copy()

print()
print(
    f"SOH outside 0-100%: "
    f"{len(final_invalid_soh)} rows"
)

if len(final_invalid_soh) != 0:
    raise RuntimeError(
        "Final SOH validation failed. "
        "Some SOH values remain outside 0-100%."
    )


# ======================================================================
# STEP 12: CAPACITY VALIDATION
# ======================================================================

print_section("STEP 12 - FINAL CAPACITY VALIDATION")

print(
    f"Minimum capacity: "
    f"{df['Capacity_Ah'].min():.6f} Ah"
)

print(
    f"Maximum capacity: "
    f"{df['Capacity_Ah'].max():.6f} Ah"
)

print(
    f"Mean capacity: "
    f"{df['Capacity_Ah'].mean():.6f} Ah"
)

capacity_invalid_final = df[
    (df["Capacity_Ah"] <= 0)
    | (df["Capacity_Ah"] < MIN_CAPACITY_AH)
    | (df["Capacity_Ah"] > MAX_CAPACITY_AH)
]

print()
print(
    f"Capacity outside accepted range: "
    f"{len(capacity_invalid_final)} rows"
)

if len(capacity_invalid_final) != 0:
    raise RuntimeError(
        "Final capacity validation failed."
    )


# ======================================================================
# STEP 13: BATTERY SUMMARY
# ======================================================================

print_section("FINAL BATTERY SUMMARY")

battery_summary = (
    df.groupby("Battery_ID")["SOH_percent"]
    .agg(
        count="count",
        first="first",
        last="last",
        minimum="min",
        maximum="max",
        mean="mean",
    )
)

print(
    battery_summary.to_string(
        float_format=lambda x: f"{x:.4f}"
    )
)


# ======================================================================
# STEP 14: CHECK FIRST SOH FOR EVERY BATTERY
# ======================================================================

print_section(
    "CHECKING FIRST SOH OF EVERY BATTERY"
)

first_soh = (
    df.sort_values(
        ["Battery_ID", "Cycle"]
    )
    .groupby("Battery_ID")["SOH_percent"]
    .first()
)

print(
    first_soh.to_string(
        float_format=lambda x: f"{x:.4f}"
    )
)

first_soh_invalid = first_soh[
    ~np.isclose(
        first_soh,
        100.0,
        atol=1e-6
    )
]

if len(first_soh_invalid) > 0:

    print()
    print(
        "WARNING: Some batteries do not start at exactly 100% SOH:"
    )

    print(
        first_soh_invalid.to_string()
    )

else:

    print()
    print(
        "All batteries start at 100% SOH."
    )


# ======================================================================
# STEP 15: FINAL DATASET SUMMARY
# ======================================================================

print_section("FINAL CLEAN DATASET SUMMARY")

print(
    f"Rows: {len(df)}"
)

print(
    f"Batteries: {df['Battery_ID'].nunique()}"
)

print(
    f"Total battery/cycle records: "
    f"{df[['Battery_ID', 'Cycle']].drop_duplicates().shape[0]}"
)

print()
print("Rows per battery:")

final_counts = (
    df.groupby("Battery_ID")
    .size()
    .sort_index()
)

for battery_id, count in final_counts.items():
    print(
        f"  {battery_id:<10} "
        f"{count:>5} rows"
    )


# ======================================================================
# STEP 16: SAVE CLEAN DATASET
# ======================================================================

print_section("SAVING CLEAN NASA DATASET")

SOH_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# Keep a predictable column order.
preferred_columns = [
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

available_columns = [
    column
    for column in preferred_columns
    if column in df.columns
]

remaining_columns = [
    column
    for column in df.columns
    if column not in available_columns
]

df = df[
    available_columns + remaining_columns
]

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Clean dataset saved successfully:")
print(
    f"  {OUTPUT_FILE}"
)


# ======================================================================
# STEP 17: VERIFY SAVED FILE
# ======================================================================

print_section("VERIFYING SAVED FILE")

if not OUTPUT_FILE.exists():
    raise RuntimeError(
        "Output file was not created."
    )

check_df = pd.read_csv(
    OUTPUT_FILE
)

print(
    f"Saved rows: {len(check_df)}"
)

print(
    f"Saved columns: {len(check_df.columns)}"
)

print(
    f"Saved batteries: "
    f"{check_df['Battery_ID'].nunique()}"
)

print(
    f"Saved minimum SOH: "
    f"{check_df['SOH_percent'].min():.6f}%"
)

print(
    f"Saved maximum SOH: "
    f"{check_df['SOH_percent'].max():.6f}%"
)

print(
    f"Saved mean SOH: "
    f"{check_df['SOH_percent'].mean():.6f}%"
)


# ======================================================================
# FINAL CHECK
# ======================================================================

print_section("FINAL VALIDATION")

checks = {
    "No missing values": check_df.isna().sum().sum() == 0,

    "No exact duplicates":
        check_df.duplicated().sum() == 0,

    "No Battery/Cycle duplicates":
        check_df.duplicated(
            subset=["Battery_ID", "Cycle"]
        ).sum() == 0,

    "SOH > 0":
        (check_df["SOH_percent"] > 0).all(),

    "SOH <= 100":
        (check_df["SOH_percent"] <= 100).all(),

    "Capacity > 0":
        (check_df["Capacity_Ah"] > 0).all(),

    "Capacity within accepted range":
        (
            (check_df["Capacity_Ah"] >= MIN_CAPACITY_AH)
            & (check_df["Capacity_Ah"] <= MAX_CAPACITY_AH)
        ).all(),
}


all_passed = True

for check_name, passed in checks.items():

    status = "PASS" if passed else "FAIL"

    print(
        f"  [{status}] {check_name}"
    )

    if not passed:
        all_passed = False


# ======================================================================
# COMPLETION
# ======================================================================

print()

if all_passed:

    print_separator()
    print("NASA SOH CLEANING COMPLETE")
    print_separator()

    print()
    print("Clean dataset:")
    print(
        f"  {OUTPUT_FILE}"
    )

    print()
    print("The dataset is ready for the next validation/training stage.")

else:

    print_separator()
    print("NASA SOH CLEANING COMPLETED WITH VALIDATION ERRORS")
    print_separator()

    raise RuntimeError(
        "One or more final validation checks failed."
    )