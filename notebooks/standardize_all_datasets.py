import os
import pandas as pd
import numpy as np

# ============================================================
# STANDARDIZE ALL BATTERY DATASETS
# ============================================================

BASE_DIR = r"C:\Major project\flask_app"
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

CALCE_FILE = os.path.join(
    PROCESSED_DIR,
    "calce_cs2_all_cells.csv"
)

NASA_FILE = os.path.join(
    PROCESSED_DIR,
    "nasa",
    "nasa_measurements.csv"
)

OXFORD_FILE = os.path.join(
    PROCESSED_DIR,
    "oxford",
    "oxford_measurements.csv"
)

OUTPUT_DIR = os.path.join(
    PROCESSED_DIR,
    "standardized"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("BATTERY DATASET STANDARDIZATION")
print("=" * 70)

print()
print("Processed directory:")
print(PROCESSED_DIR)

# ============================================================
# COMMON COLUMN ORDER
# ============================================================

COMMON_COLUMNS = [
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
# CALCE
# ============================================================

print()
print("=" * 70)
print("CALCE")
print("=" * 70)

if not os.path.exists(CALCE_FILE):
    print("ERROR: CALCE file not found:")
    print(CALCE_FILE)
    raise SystemExit(1)

calce = pd.read_csv(CALCE_FILE)

print()
print("Input rows:", len(calce))
print("Input columns:")
for col in calce.columns:
    print(" ", col)

calce["Dataset"] = "CALCE"

# CALCE should already contain Battery and Cycle information.
# Detect common possible column names.

if "Battery_ID" not in calce.columns:

    if "Battery" in calce.columns:
        calce["Battery_ID"] = calce["Battery"]

    elif "Cell" in calce.columns:
        calce["Battery_ID"] = calce["Cell"]

    else:
        calce["Battery_ID"] = "CALCE"

# Ensure required columns exist.
for col in COMMON_COLUMNS:

    if col not in calce.columns:
        calce[col] = np.nan

calce = calce[COMMON_COLUMNS]

calce_output = os.path.join(
    OUTPUT_DIR,
    "calce_standardized.csv"
)

calce.to_csv(
    calce_output,
    index=False
)

print()
print("Standardized CALCE rows:", len(calce))
print("Saved:")
print(calce_output)


# ============================================================
# NASA
# ============================================================

print()
print("=" * 70)
print("NASA")
print("=" * 70)

if not os.path.exists(NASA_FILE):
    print("ERROR: NASA file not found:")
    print(NASA_FILE)
    raise SystemExit(1)

nasa = pd.read_csv(NASA_FILE)

print()
print("Input rows:", len(nasa))
print("Input columns:")
for col in nasa.columns:
    print(" ", col)

nasa["Dataset"] = "NASA"

# NASA already uses Battery_ID.
if "Battery_ID" not in nasa.columns:
    raise ValueError(
        "NASA dataset does not contain Battery_ID"
    )

# Make sure all common columns exist.
for col in COMMON_COLUMNS:

    if col not in nasa.columns:
        nasa[col] = np.nan

nasa = nasa[COMMON_COLUMNS]

nasa_output = os.path.join(
    OUTPUT_DIR,
    "nasa_standardized.csv"
)

nasa.to_csv(
    nasa_output,
    index=False
)

print()
print("Standardized NASA rows:", len(nasa))
print("Saved:")
print(nasa_output)


# ============================================================
# OXFORD
# ============================================================

print()
print("=" * 70)
print("OXFORD")
print("=" * 70)

if not os.path.exists(OXFORD_FILE):
    print("ERROR: Oxford file not found:")
    print(OXFORD_FILE)
    raise SystemExit(1)

oxford = pd.read_csv(OXFORD_FILE)

print()
print("Input rows:", len(oxford))
print("Input columns:")
for col in oxford.columns:
    print(" ", col)

oxford["Dataset"] = "Oxford"

# Oxford uses Cell_ID.
if "Battery_ID" not in oxford.columns:

    if "Cell_ID" in oxford.columns:
        oxford["Battery_ID"] = oxford["Cell_ID"]

    else:
        raise ValueError(
            "Oxford dataset does not contain Cell_ID"
        )

# Oxford has Charge_mAh rather than Capacity_Ah.
# DO NOT treat instantaneous charge as battery capacity.
#
# Capacity_Ah will remain NaN at this stage.
#
# This will be calculated later from appropriate
# discharge/capacity measurements.

if "Capacity_Ah" not in oxford.columns:
    oxford["Capacity_Ah"] = np.nan

# Oxford extraction currently has no current column.
if "Current" not in oxford.columns:
    oxford["Current"] = np.nan

# Oxford already has Voltage, Temperature, Time.
for col in COMMON_COLUMNS:

    if col not in oxford.columns:
        oxford[col] = np.nan

oxford = oxford[COMMON_COLUMNS]

oxford_output = os.path.join(
    OUTPUT_DIR,
    "oxford_standardized.csv"
)

oxford.to_csv(
    oxford_output,
    index=False
)

print()
print("Standardized Oxford rows:", len(oxford))
print("Saved:")
print(oxford_output)


# ============================================================
# COMBINE DATASETS
# ============================================================

print()
print("=" * 70)
print("COMBINING DATASETS")
print("=" * 70)

combined = pd.concat(
    [
        calce,
        nasa,
        oxford
    ],
    ignore_index=True
)

combined_output = os.path.join(
    OUTPUT_DIR,
    "all_battery_measurements.csv"
)

combined.to_csv(
    combined_output,
    index=False
)

print()
print("Combined rows:", len(combined))
print("Combined columns:")

for col in combined.columns:
    print(" ", col)


# ============================================================
# DATASET SUMMARY
# ============================================================

print()
print("=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

print()

summary = (
    combined
    .groupby("Dataset")
    .agg(
        Rows=("Dataset", "size"),
        Batteries=("Battery_ID", "nunique"),
        Cycles=("Cycle", "nunique")
    )
    .reset_index()
)

print(summary.to_string(index=False))


# ============================================================
# BATTERY SUMMARY
# ============================================================

print()
print("=" * 70)
print("BATTERY SUMMARY")
print("=" * 70)

battery_summary = (
    combined
    .groupby(
        ["Dataset", "Battery_ID"]
    )
    .agg(
        Rows=("Dataset", "size"),
        Cycles=("Cycle", "nunique")
    )
    .reset_index()
)

print()
print(
    battery_summary.to_string(index=False)
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("STANDARDIZATION COMPLETE")
print("=" * 70)

print()
print("CALCE standardized:")
print(calce_output)

print()
print("NASA standardized:")
print(nasa_output)

print()
print("Oxford standardized:")
print(oxford_output)

print()
print("Combined standardized dataset:")
print(combined_output)

print()
print("TOTAL MEASUREMENT ROWS:", len(combined))

print()
print("=" * 70)