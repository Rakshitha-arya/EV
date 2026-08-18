"""
EV DIGITAL TWIN - SOH PREDICTION
STEP 25

Uses the exact features stored in the trained model.
"""

import os
import joblib
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "models/NASA_tuned_GradientBoosting_SOH.pkl"

DATA_PATH = "processed/NASA_health_features.csv"

OUTPUT_PATH = "processed/NASA_digital_twin_SOH.csv"

TEST_BATTERIES = [
    "B0030",
    "B0031",
    "B0032"
]


# ============================================================
# HEADER
# ============================================================

print("=" * 65)
print("EV DIGITAL TWIN - SOH PREDICTION")
print("=" * 65)


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(MODEL_PATH):
    print("\nERROR: Model not found:")
    print(MODEL_PATH)
    raise SystemExit(1)

if not os.path.exists(DATA_PATH):
    print("\nERROR: Dataset not found:")
    print(DATA_PATH)
    raise SystemExit(1)


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading trained model...")

model = joblib.load(MODEL_PATH)

print("Model loaded:")
print(MODEL_PATH)


# ============================================================
# SHOW EXACT MODEL FEATURES
# ============================================================

if hasattr(model, "feature_names_in_"):

    MODEL_FEATURES = list(model.feature_names_in_)

else:

    print("\nERROR:")
    print("The saved model does not contain feature names.")

    raise SystemExit(1)


print("\nExact features expected by model:")

for i, feature in enumerate(MODEL_FEATURES, start=1):
    print(f"{i:2d}. {feature}")


print("\nNumber of model features:", len(MODEL_FEATURES))


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading health-feature dataset...")

df = pd.read_csv(DATA_PATH)

print("Rows loaded:", len(df))


# ============================================================
# CHECK DATA FEATURES
# ============================================================

missing_features = [
    feature
    for feature in MODEL_FEATURES
    if feature not in df.columns
]

if missing_features:

    print("\nERROR: Dataset is missing model features:")

    for feature in missing_features:
        print(" -", feature)

    raise SystemExit(1)


# ============================================================
# SELECT TEST BATTERIES
# ============================================================

df_test = df[
    df["battery_id"].isin(TEST_BATTERIES)
].copy()

print("\nTesting batteries:")
print(TEST_BATTERIES)

print("\nTesting rows:", len(df_test))


# ============================================================
# REMOVE MISSING VALUES
# ============================================================

before = len(df_test)

df_test = df_test.dropna(
    subset=MODEL_FEATURES
).copy()

after = len(df_test)

print(
    "Rows after feature validation:",
    after
)

if after == 0:

    print("\nERROR: No usable rows remain.")

    raise SystemExit(1)


# ============================================================
# PREPARE MODEL INPUT
# ============================================================

X_test = df_test[MODEL_FEATURES].copy()


# ============================================================
# PREDICT
# ============================================================

print("\nRunning SOH prediction...")

predicted_soh = model.predict(X_test)


# ============================================================
# LIMIT DISPLAY RANGE
# ============================================================

df_test["predicted_SOH_percent"] = np.clip(
    predicted_soh,
    0,
    100
)


# ============================================================
# HEALTH CLASSIFICATION
# ============================================================

def classify_health(soh):

    if soh >= 80:
        return "HEALTHY"

    elif soh >= 60:
        return "MODERATE"

    else:
        return "POOR"


df_test["battery_health"] = (
    df_test["predicted_SOH_percent"]
    .apply(classify_health)
)


# ============================================================
# ERROR
# ============================================================

df_test["prediction_error_percent"] = (
    df_test["predicted_SOH_percent"]
    - df_test["SOH_percent"]
)

df_test["absolute_error_percent"] = (
    df_test["prediction_error_percent"]
    .abs()
)


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_COLUMNS = [
    "battery_id",
    "cycle_number",
    "SOH_percent",
    "predicted_SOH_percent",
    "prediction_error_percent",
    "absolute_error_percent",
    "battery_health"
]

result = df_test[OUTPUT_COLUMNS].copy()


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# PERFORMANCE
# ============================================================

mae = result[
    "absolute_error_percent"
].mean()

rmse = np.sqrt(
    (
        result["prediction_error_percent"] ** 2
    ).mean()
)


print("\n" + "=" * 65)
print("DIGITAL TWIN PERFORMANCE")
print("=" * 65)

print(f"\nMAE  : {mae:.4f}%")
print(f"RMSE : {rmse:.4f}%")


# ============================================================
# BATTERY-WISE STATUS
# ============================================================

print("\n" + "=" * 65)
print("DIGITAL TWIN BATTERY STATUS")
print("=" * 65)

for battery in TEST_BATTERIES:

    battery_data = result[
        result["battery_id"] == battery
    ]

    if battery_data.empty:
        continue

    latest = battery_data.iloc[-1]

    print("\nBattery:", battery)

    print(
        "Latest cycle:",
        int(latest["cycle_number"])
    )

    print(
        "Actual SOH:",
        f"{latest['SOH_percent']:.2f}%"
    )

    print(
        "Predicted SOH:",
        f"{latest['predicted_SOH_percent']:.2f}%"
    )

    print(
        "Health:",
        latest["battery_health"]
    )


# ============================================================
# HEALTH COUNTS
# ============================================================

print("\n" + "=" * 65)
print("HEALTH SUMMARY")
print("=" * 65)

print(
    "\nHealthy:",
    (result["battery_health"] == "HEALTHY").sum()
)

print(
    "Moderate:",
    (result["battery_health"] == "MODERATE").sum()
)

print(
    "Poor:",
    (result["battery_health"] == "POOR").sum()
)


# ============================================================
# SAVE COMPLETE
# ============================================================

print("\nResults saved to:")
print(OUTPUT_PATH)

print("\n" + "=" * 65)
print("DIGITAL TWIN SOH PREDICTION COMPLETE")
print("=" * 65)