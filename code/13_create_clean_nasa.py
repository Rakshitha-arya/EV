import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_all_batteries_SOH.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_clean_training_SOH.csv"
)

# Batteries selected for the first reliable model
SELECTED_BATTERIES = [
    "B0005",
    "B0006",
    "B0007",
    "B0018",
    "B0025",
    "B0026",
    "B0027",
    "B0028",
    "B0029",
    "B0030",
    "B0031",
    "B0032"
]

df = pd.read_csv(INPUT_FILE)

# ---------------------------------------------------------
# Select batteries
# ---------------------------------------------------------

df = df[
    df["battery_id"].isin(
        SELECTED_BATTERIES
    )
].copy()

# ---------------------------------------------------------
# Remove invalid capacity values
# ---------------------------------------------------------

df = df[
    df["capacity_Ah"] > 0
].copy()

# ---------------------------------------------------------
# Sort
# ---------------------------------------------------------

df = df.sort_values(
    ["battery_id", "cycle_number"]
).reset_index(drop=True)

# ---------------------------------------------------------
# Reference capacity
#
# Use median of first 10 discharge capacities.
# These selected batteries have stable initial regions.
# ---------------------------------------------------------

reference = (
    df.groupby("battery_id")
    ["capacity_Ah"]
    .apply(
        lambda x:
        np.median(
            x.iloc[:10]
        )
    )
)

# ---------------------------------------------------------
# Map reference capacity
# ---------------------------------------------------------

df["reference_capacity_Ah"] = (
    df["battery_id"].map(reference)
)

# ---------------------------------------------------------
# Calculate SOH
# ---------------------------------------------------------

df["SOH_percent"] = (
    df["capacity_Ah"]
    /
    df["reference_capacity_Ah"]
    * 100
)

# ---------------------------------------------------------
# Remove physically impossible SOH values
#
# We allow a small measurement variation above 100%.
# ---------------------------------------------------------

df = df[
    (df["SOH_percent"] >= 0) &
    (df["SOH_percent"] <= 105)
].copy()

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("=" * 70)
print("CLEAN NASA TRAINING DATASET")
print("=" * 70)

print("\nBatteries:")
print(
    df["battery_id"]
    .unique()
)

print(
    "\nNumber of batteries:",
    df["battery_id"].nunique()
)

print(
    "Total rows:",
    len(df)
)

print("\nRows per battery:")

print(
    df.groupby("battery_id")
    .size()
    .to_string()
)

print("\nSOH statistics:")

print(
    df["SOH_percent"]
    .describe()
)

print("\nSOH range per battery:")

print(
    df.groupby("battery_id")
    ["SOH_percent"]
    .agg(["min", "max"])
    .to_string()
)

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)
print("CLEAN DATASET CREATED")
print("=" * 70)