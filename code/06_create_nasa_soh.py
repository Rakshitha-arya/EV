import os
import pandas as pd

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_B0005_discharge.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_B0005_SOH.csv"
)

# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("=" * 70)
print("NASA B0005 - SOH DATASET CREATION")
print("=" * 70)

print("\nInput rows:", len(df))

# ---------------------------------------------------------
# Remove invalid rows
# ---------------------------------------------------------

df = df.dropna(
    subset=[
        "voltage",
        "current",
        "temperature",
        "time_seconds",
        "capacity_Ah"
    ]
)

# ---------------------------------------------------------
# Create cycle-level features
# ---------------------------------------------------------

features = []

for discharge_number, group in df.groupby("discharge_number"):

    group = group.sort_values("time_seconds")

    capacity = group["capacity_Ah"].iloc[0]

    duration = (
        group["time_seconds"].max()
        - group["time_seconds"].min()
    )

    features.append({

        "battery_id":
            group["battery_id"].iloc[0],

        "cycle_number":
            discharge_number,

        "voltage_mean":
            group["voltage"].mean(),

        "voltage_min":
            group["voltage"].min(),

        "voltage_max":
            group["voltage"].max(),

        "voltage_std":
            group["voltage"].std(),

        "current_mean":
            group["current"].mean(),

        "current_min":
            group["current"].min(),

        "current_max":
            group["current"].max(),

        "current_std":
            group["current"].std(),

        "temperature_mean":
            group["temperature"].mean(),

        "temperature_min":
            group["temperature"].min(),

        "temperature_max":
            group["temperature"].max(),

        "discharge_time_seconds":
            duration,

        "capacity_Ah":
            capacity
    })

# ---------------------------------------------------------
# Create DataFrame
# ---------------------------------------------------------

soh_df = pd.DataFrame(features)

# ---------------------------------------------------------
# Calculate SOH
# ---------------------------------------------------------

initial_capacity = soh_df["capacity_Ah"].iloc[0]

soh_df["SOH_percent"] = (
    soh_df["capacity_Ah"]
    / initial_capacity
    * 100
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

soh_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\nInitial capacity:")
print(f"{initial_capacity:.6f} Ah")

print("\nNumber of discharge cycles:")
print(len(soh_df))

print("\nFinal capacity:")
print(
    f"{soh_df['capacity_Ah'].iloc[-1]:.6f} Ah"
)

print("\nFinal SOH:")
print(
    f"{soh_df['SOH_percent'].iloc[-1]:.2f}%"
)

print("\nFirst 5 cycles:")
print(
    soh_df.head().to_string(index=False)
)

print("\nLast 5 cycles:")
print(
    soh_df.tail().to_string(index=False)
)

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)
print("SOH DATASET CREATED")
print("=" * 70)