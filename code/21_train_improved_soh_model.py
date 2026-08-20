import os
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_health_features.csv"
)

TRAIN_BATTERIES = [
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

TEST_BATTERIES = [
    "B0030",
    "B0031",
    "B0032"
]

MODEL_FILE = os.path.join(
    BASE_DIR,
    "models",
    "NASA_Improved_RandomForest_SOH.pkl"
)

PREDICTION_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_Improved_SOH_predictions.csv"
)

print("=" * 65)
print("EV DIGITAL TWIN - IMPROVED SOH MODEL")
print("=" * 65)

# --------------------------------------------------
# Load dataset
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

df = df.sort_values(
    ["battery_id", "cycle_number"]
).reset_index(drop=True)

# --------------------------------------------------
# Features
# IMPORTANT: no target/capacity-derived leakage
# --------------------------------------------------

FEATURES = [
    "cycle_number",
    "ambient_temperature",

    "voltage_mean",
    "voltage_min",
    "voltage_max",
    "voltage_std",

    "current_mean",
    "current_min",
    "current_max",
    "current_std",

    "temperature_mean",
    "temperature_min",
    "temperature_max",

    "discharge_time_seconds",

    "voltage_change",
    "voltage_range",

    "current_range",

    "temperature_range",
    "temperature_change",

    "discharge_time_change",
    "discharge_time_change_percent"
]

TARGET = "SOH_percent"

# --------------------------------------------------
# Remove missing values
# --------------------------------------------------

df = df.dropna(
    subset=FEATURES + [TARGET]
).reset_index(drop=True)

# --------------------------------------------------
# Battery-level split
# --------------------------------------------------

train = df[
    df["battery_id"].isin(TRAIN_BATTERIES)
].copy()

test = df[
    df["battery_id"].isin(TEST_BATTERIES)
].copy()

X_train = train[FEATURES]
y_train = train[TARGET]

X_test = test[FEATURES]
y_test = test[TARGET]

print("\nTraining batteries:")
print(TRAIN_BATTERIES)

print("\nTesting batteries:")
print(TEST_BATTERIES)

print("\nTraining rows:", len(train))
print("Testing rows:", len(test))

print("\nNumber of features:", len(FEATURES))

# --------------------------------------------------
# Train model
# --------------------------------------------------

print("\nTraining Random Forest...")

model = RandomForestRegressor(
    n_estimators=500,
    max_depth=12,
    min_samples_leaf=2,
    max_features="sqrt",
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train,
    y_train
)

print("Training complete.")

# --------------------------------------------------
# Prediction
# --------------------------------------------------

predictions = model.predict(X_test)

# --------------------------------------------------
# Metrics
# --------------------------------------------------

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)

r2 = r2_score(
    y_test,
    predictions
)

print("\n" + "=" * 65)
print("IMPROVED MODEL PERFORMANCE")
print("=" * 65)

print(f"\nMAE  : {mae:.4f}%")
print(f"RMSE : {rmse:.4f}%")
print(f"R²   : {r2:.4f}")

# --------------------------------------------------
# Prediction table
# --------------------------------------------------

result = test[
    ["battery_id", "cycle_number", "SOH_percent"]
].copy()

result["predicted_SOH_percent"] = predictions

result["absolute_error_percent"] = (
    abs(
        result["SOH_percent"] -
        result["predicted_SOH_percent"]
    )
)

result["error_percent"] = (
    result["predicted_SOH_percent"] -
    result["SOH_percent"]
)

# --------------------------------------------------
# Battery-wise performance
# --------------------------------------------------

print("\n" + "=" * 65)
print("BATTERY-WISE PERFORMANCE")
print("=" * 65)

for battery in TEST_BATTERIES:

    battery_result = result[
        result["battery_id"] == battery
    ]

    battery_mae = mean_absolute_error(
        battery_result["SOH_percent"],
        battery_result["predicted_SOH_percent"]
    )

    print(
        f"{battery}: "
        f"MAE = {battery_mae:.4f}%"
    )

# --------------------------------------------------
# Feature importance
# --------------------------------------------------

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n" + "=" * 65)
print("MODEL FEATURE IMPORTANCE")
print("=" * 65)

for _, row in importance.iterrows():

    print(
        f"{row['feature']:35s} "
        f"{row['importance']:.6f}"
    )

# --------------------------------------------------
# Save model
# --------------------------------------------------

joblib.dump(
    model,
    MODEL_FILE
)

result.to_csv(
    PREDICTION_FILE,
    index=False
)

print("\nModel saved to:")
print(MODEL_FILE)

print("\nPredictions saved to:")
print(PREDICTION_FILE)

print("\n" + "=" * 65)
print("IMPROVED SOH MODEL COMPLETE")
print("=" * 65)