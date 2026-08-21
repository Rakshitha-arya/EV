from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "calce_cs2_35_processed.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "calce_cs2_35_soh.csv"
)

print("=" * 70)
print("CALCE CS2-35 SOH CHECK")
print("=" * 70)

# --------------------------------------------------
# READ PROCESSED DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("\nInput file:")
print(INPUT_FILE)

print("\nRows:", len(df))

# --------------------------------------------------
# CHECK CAPACITY VALUES
# --------------------------------------------------

print("\nCapacity values:")
print(
    df[
        [
            "Cycle",
            "Discharge_Capacity_Ah"
        ]
    ].head(10).to_string(index=False)
)

# --------------------------------------------------
# IMPORTANT:
# The previous preprocessing used cumulative
# discharge capacity. We therefore calculate
# cycle-to-cycle capacity using the difference.
# --------------------------------------------------

df["Cycle_Discharge_Capacity_Ah"] = (
    df["Discharge_Capacity_Ah"].diff()
)

# The first cycle does not have a previous cycle.
# Use its measured capacity as the first capacity.
df.loc[
    df.index[0],
    "Cycle_Discharge_Capacity_Ah"
] = df.loc[
    df.index[0],
    "Discharge_Capacity_Ah"
]

# --------------------------------------------------
# REMOVE INVALID VALUES
# --------------------------------------------------

df = df[
    df["Cycle_Discharge_Capacity_Ah"] > 0
].copy()

# --------------------------------------------------
# CALCULATE SOH
# --------------------------------------------------

REFERENCE_CAPACITY_AH = 1.10

df["SOH_percent"] = (
    df["Cycle_Discharge_Capacity_Ah"]
    / REFERENCE_CAPACITY_AH
) * 100

# --------------------------------------------------
# LIMIT OBVIOUSLY INVALID VALUES
# --------------------------------------------------

df = df[
    (df["SOH_percent"] > 0) &
    (df["SOH_percent"] <= 120)
].copy()

# --------------------------------------------------
# SAVE
# --------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

print("\n" + "=" * 70)
print("CORRECTED SOH")
print("=" * 70)

print("\nFirst 10 cycles:")

print(
    df[
        [
            "Cycle",
            "Cycle_Discharge_Capacity_Ah",
            "SOH_percent"
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print("\nLast 10 cycles:")

print(
    df[
        [
            "Cycle",
            "Cycle_Discharge_Capacity_Ah",
            "SOH_percent"
        ]
    ]
    .tail(10)
    .to_string(index=False)
)

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)
print("SOH CHECK COMPLETE")
print("=" * 70)