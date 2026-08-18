import os
import pandas as pd

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
    "NASA_clean_SOH.csv"
)

print("=" * 70)
print("NASA SOH DATA QUALITY CHECK")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print("\nOriginal rows:", len(df))
print("Original batteries:", df["battery_id"].nunique())

# ---------------------------------------------------------
# 1. Remove exact duplicate rows
# ---------------------------------------------------------

before = len(df)

df = df.drop_duplicates()

print(
    "\nDuplicate rows removed:",
    before - len(df)
)

# ---------------------------------------------------------
# 2. Remove duplicate battery/cycle combinations
# ---------------------------------------------------------

before = len(df)

df = df.drop_duplicates(
    subset=["battery_id", "cycle_number"],
    keep="first"
)

print(
    "Duplicate battery-cycle rows removed:",
    before - len(df)
)

# ---------------------------------------------------------
# 3. Sort
# ---------------------------------------------------------

df = df.sort_values(
    ["battery_id", "cycle_number"]
).reset_index(drop=True)

# ---------------------------------------------------------
# 4. Recalculate SOH
# ---------------------------------------------------------

df["SOH_percent"] = (
    df.groupby("battery_id")["capacity_Ah"]
    .transform(
        lambda x: (
            x / x.iloc[0]
        ) * 100
    )
)

# ---------------------------------------------------------
# 5. Show suspicious batteries
# ---------------------------------------------------------

summary = (
    df.groupby("battery_id")
    .agg(
        cycles=("cycle_number", "count"),
        min_capacity=("capacity_Ah", "min"),
        max_capacity=("capacity_Ah", "max"),
        min_soh=("SOH_percent", "min"),
        max_soh=("SOH_percent", "max")
    )
)

print("\nBattery quality summary:")
print(summary.to_string())

# ---------------------------------------------------------
# 6. Identify suspicious batteries
# ---------------------------------------------------------

suspicious = summary[
    (summary["min_soh"] < 50) |
    (summary["max_soh"] > 110) |
    (summary["cycles"] < 10)
]

print("\n" + "=" * 70)
print("SUSPICIOUS BATTERIES")
print("=" * 70)

print(suspicious.to_string())

# ---------------------------------------------------------
# IMPORTANT:
# Don't delete suspicious batteries automatically.
# Save them separately for investigation.
# ---------------------------------------------------------

suspicious_ids = suspicious.index.tolist()

df_suspicious = df[
    df["battery_id"].isin(suspicious_ids)
]

df_valid = df[
    ~df["battery_id"].isin(suspicious_ids)
]

# ---------------------------------------------------------
# Save valid and suspicious datasets
# ---------------------------------------------------------

VALID_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_valid_SOH.csv"
)

SUSPICIOUS_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_suspicious_SOH.csv"
)

df_valid.to_csv(
    VALID_FILE,
    index=False
)

df_suspicious.to_csv(
    SUSPICIOUS_FILE,
    index=False
)

print("\nValid batteries:")
print(df_valid["battery_id"].nunique())

print("\nValid cycles:")
print(len(df_valid))

print("\nSuspicious batteries:")
print(df_suspicious["battery_id"].nunique())

print("\nSuspicious cycles:")
print(len(df_suspicious))

print("\nValid dataset:")
print(VALID_FILE)

print("\nSuspicious dataset:")
print(SUSPICIOUS_FILE)

print("\n" + "=" * 70)
print("QUALITY CHECK COMPLETE")
print("=" * 70)