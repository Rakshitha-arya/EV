import os
import pandas as pd

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_clean_training_SOH.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "processed"
)

TRAIN_FILE = os.path.join(
    OUTPUT_DIR,
    "NASA_train_SOH.csv"
)

TEST_FILE = os.path.join(
    OUTPUT_DIR,
    "NASA_test_SOH.csv"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

# --------------------------------------------------
# BATTERY-LEVEL SPLIT
# --------------------------------------------------

train_batteries = [
    "B0005",
    "B0006",
    "B0007",
    "B0018",
    "B0025",
    "B0026",
    "B0027",
    "B0028",
    "B0029"
]

test_batteries = [
    "B0030",
    "B0031",
    "B0032"
]

train_df = df[
    df["battery_id"].isin(train_batteries)
].copy()

test_df = df[
    df["battery_id"].isin(test_batteries)
].copy()

# --------------------------------------------------
# SORT
# --------------------------------------------------

train_df = train_df.sort_values(
    ["battery_id", "cycle_number"]
)

test_df = test_df.sort_values(
    ["battery_id", "cycle_number"]
)

# --------------------------------------------------
# SAVE
# --------------------------------------------------

train_df.to_csv(
    TRAIN_FILE,
    index=False
)

test_df.to_csv(
    TEST_FILE,
    index=False
)

# --------------------------------------------------
# REPORT
# --------------------------------------------------

print("=" * 60)
print("NASA BATTERY-LEVEL TRAIN / TEST SPLIT")
print("=" * 60)

print("\nTraining batteries:")
print(train_batteries)

print("\nTesting batteries:")
print(test_batteries)

print("\nTraining rows:")
print(len(train_df))

print("\nTesting rows:")
print(len(test_df))

print("\nTraining battery counts:")
print(train_df["battery_id"].value_counts().sort_index())

print("\nTesting battery counts:")
print(test_df["battery_id"].value_counts().sort_index())

print("\nTraining SOH range:")
print(
    train_df["SOH_percent"].min(),
    "to",
    train_df["SOH_percent"].max()
)

print("\nTesting SOH range:")
print(
    test_df["SOH_percent"].min(),
    "to",
    test_df["SOH_percent"].max()
)

print("\nSaved training dataset:")
print(TRAIN_FILE)

print("\nSaved testing dataset:")
print(TEST_FILE)

print("\n" + "=" * 60)
print("SPLIT COMPLETE")
print("=" * 60)