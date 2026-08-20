import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_clean_training_SOH.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_health_features.csv"
)

print("=" * 65)
print("NASA SOH - HEALTH FEATURE ENGINEERING")
print("=" * 65)

df = pd.read_csv(INPUT_FILE)

# --------------------------------------------------
# Sort correctly
# --------------------------------------------------

df = df.sort_values(
    ["battery_id", "cycle_number"]
).reset_index(drop=True)

# --------------------------------------------------
# Capacity-based health features
# --------------------------------------------------

df["capacity_change"] = (
    df.groupby("battery_id")["capacity_Ah"]
    .diff()
)

df["capacity_change_percent"] = (
    df["capacity_change"]
    / df["reference_capacity_Ah"]
    * 100
)

df["capacity_retention_percent"] = (
    df["capacity_Ah"]
    / df["reference_capacity_Ah"]
    * 100
)

# --------------------------------------------------
# Voltage health features
# --------------------------------------------------

df["voltage_change"] = (
    df.groupby("battery_id")["voltage_mean"]
    .diff()
)

df["voltage_range"] = (
    df["voltage_max"] -
    df["voltage_min"]
)

# --------------------------------------------------
# Current features
# --------------------------------------------------

df["current_range"] = (
    df["current_max"] -
    df["current_min"]
)

# --------------------------------------------------
# Temperature features
# --------------------------------------------------

df["temperature_range"] = (
    df["temperature_max"] -
    df["temperature_min"]
)

df["temperature_change"] = (
    df.groupby("battery_id")["temperature_mean"]
    .diff()
)

# --------------------------------------------------
# Discharge time change
# --------------------------------------------------

df["discharge_time_change"] = (
    df.groupby("battery_id")["discharge_time_seconds"]
    .diff()
)

df["discharge_time_change_percent"] = (
    df["discharge_time_change"]
    / df["discharge_time_seconds"]
    * 100
)

# --------------------------------------------------
# Rolling capacity trend
# --------------------------------------------------

df["capacity_rolling_mean_5"] = (
    df.groupby("battery_id")["capacity_Ah"]
    .transform(
        lambda x: x.rolling(
            window=5,
            min_periods=1
        ).mean()
    )
)

df["capacity_rolling_std_5"] = (
    df.groupby("battery_id")["capacity_Ah"]
    .transform(
        lambda x: x.rolling(
            window=5,
            min_periods=1
        ).std()
    )
)

# --------------------------------------------------
# Rolling SOH trend
# --------------------------------------------------

df["SOH_rolling_mean_5"] = (
    df.groupby("battery_id")["SOH_percent"]
    .transform(
        lambda x: x.rolling(
            window=5,
            min_periods=1
        ).mean()
    )
)

# --------------------------------------------------
# Remove infinities
# --------------------------------------------------

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

# Keep rows usable by ML
df = df.dropna().reset_index(drop=True)

# --------------------------------------------------
# Save
# --------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nOriginal dataset rows:", 1020)
print("Rows after feature creation:", len(df))

print("\nNew health features:")

new_features = [
    "capacity_change",
    "capacity_change_percent",
    "capacity_retention_percent",
    "voltage_change",
    "voltage_range",
    "current_range",
    "temperature_range",
    "temperature_change",
    "discharge_time_change",
    "discharge_time_change_percent",
    "capacity_rolling_mean_5",
    "capacity_rolling_std_5",
    "SOH_rolling_mean_5"
]

for feature in new_features:
    print("  -", feature)

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 65)
print("HEALTH FEATURE ENGINEERING COMPLETE")
print("=" * 65)