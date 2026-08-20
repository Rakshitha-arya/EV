import os
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TRAIN_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_train_SOH.csv"
)

TEST_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_test_SOH.csv"
)

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "NASA_RandomForest_SOH.pkl"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

# --------------------------------------------------
# FEATURES
# --------------------------------------------------

features = [
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
    "capacity_Ah"
]

target = "SOH_percent"

X_train = train_df[features]
y_train = train_df[target]

X_test = test_df[features]
y_test = test_df[target]

# --------------------------------------------------
# MODEL
# --------------------------------------------------

model = RandomForestRegressor(
    n_estimators=300,
    max_depth=12,
    min_samples_split=4,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

print("=" * 60)
print("EV DIGITAL TWIN - SOH MODEL TRAINING")
print("=" * 60)

print("\nTraining rows:", len(X_train))
print("Testing rows:", len(X_test))

print("\nFeatures:")
for feature in features:
    print("  -", feature)

# --------------------------------------------------
# TRAIN
# --------------------------------------------------

print("\nTraining Random Forest...")

model.fit(X_train, y_train)

print("Training complete.")

# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

y_pred = model.predict(X_test)

# --------------------------------------------------
# METRICS
# --------------------------------------------------

mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) ** 0.5
r2 = r2_score(y_test, y_pred)

print("\n" + "=" * 60)
print("MODEL PERFORMANCE")
print("=" * 60)

print(f"\nMAE  : {mae:.4f}%")
print(f"RMSE : {rmse:.4f}%")
print(f"R²   : {r2:.4f}")

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------

joblib.dump(
    {
        "model": model,
        "features": features
    },
    MODEL_FILE
)

print("\nModel saved to:")
print(MODEL_FILE)

# --------------------------------------------------
# SAMPLE PREDICTIONS
# --------------------------------------------------

results = test_df[
    ["battery_id", "cycle_number", "SOH_percent"]
].copy()

results["predicted_SOH_percent"] = y_pred

results["absolute_error_percent"] = (
    results["SOH_percent"]
    - results["predicted_SOH_percent"]
).abs()

print("\nFirst 20 predictions:")
print(
    results.head(20).to_string(index=False)
)

print("\nAverage absolute error:")
print(
    results["absolute_error_percent"].mean()
)

print("\n" + "=" * 60)
print("SOH MODEL TRAINING COMPLETE")
print("=" * 60)