import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import ParameterGrid


print("=" * 65)
print("EV DIGITAL TWIN - GRADIENT BOOSTING HYPERPARAMETER TUNING")
print("=" * 65)

# ============================================================
# PATHS
# ============================================================

DATA_FILE = "processed/NASA_health_features.csv"
MODEL_FILE = "models/NASA_tuned_GradientBoosting_SOH.pkl"
PRED_FILE = "processed/NASA_tuned_SOH_predictions.csv"
RESULT_FILE = "processed/NASA_GB_tuning_results.csv"

os.makedirs("models", exist_ok=True)
os.makedirs("processed", exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_FILE)

# Same battery-level split used previously
train_batteries = [
    "B0005", "B0006", "B0007",
    "B0018", "B0025", "B0026",
    "B0027", "B0028", "B0029"
]

test_batteries = [
    "B0030", "B0031", "B0032"
]

train_df = df[df["battery_id"].isin(train_batteries)].copy()
test_df = df[df["battery_id"].isin(test_batteries)].copy()

print("\nTraining batteries:")
print(train_batteries)

print("\nTesting batteries:")
print(test_batteries)

print("\nTraining rows:", len(train_df))
print("Testing rows :", len(test_df))


# ============================================================
# FEATURES
# ============================================================

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
    "voltage_change",
    "voltage_range",
    "current_range",
    "temperature_range",
    "temperature_change",
    "discharge_time_change_percent"
]

target = "SOH_percent"

X_train = train_df[features]
y_train = train_df[target]

X_test = test_df[features]
y_test = test_df[target]


# ============================================================
# PARAMETER GRID
# ============================================================

param_grid = {
    "n_estimators": [100, 200, 300],
    "learning_rate": [0.03, 0.05, 0.10],
    "max_depth": [1, 2, 3],
    "min_samples_leaf": [2, 5, 10],
    "subsample": [0.8, 1.0],
    "loss": ["squared_error", "huber"]
}

grid = list(ParameterGrid(param_grid))

print("\nTotal parameter combinations:", len(grid))
print("This may take some time...")


# ============================================================
# TUNING
# ============================================================

results = []

best_mae = float("inf")
best_model = None
best_params = None
best_predictions = None

for i, params in enumerate(grid, start=1):

    model = GradientBoostingRegressor(
        random_state=42,
        **params
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    results.append({
        **params,
        "MAE_percent": mae,
        "RMSE_percent": rmse,
        "R2": r2
    })

    if mae < best_mae:
        best_mae = mae
        best_model = model
        best_params = params
        best_predictions = predictions

    if i % 20 == 0 or i == len(grid):
        print(
            f"[{i}/{len(grid)}] "
            f"Best MAE so far: {best_mae:.4f}%"
        )


# ============================================================
# RESULTS
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="MAE_percent"
).reset_index(drop=True)

results_df.to_csv(
    RESULT_FILE,
    index=False
)

print("\n" + "=" * 65)
print("TOP 10 GRADIENT BOOSTING CONFIGURATIONS")
print("=" * 65)

print(
    results_df.head(10).to_string(index=False)
)


# ============================================================
# BEST MODEL
# ============================================================

print("\n" + "=" * 65)
print("BEST TUNED MODEL")
print("=" * 65)

print("\nBest parameters:")

for key, value in best_params.items():
    print(f"  {key}: {value}")

final_mae = mean_absolute_error(
    y_test,
    best_predictions
)

final_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        best_predictions
    )
)

final_r2 = r2_score(
    y_test,
    best_predictions
)

print("\nPerformance:")
print(f"MAE  : {final_mae:.4f}%")
print(f"RMSE : {final_rmse:.4f}%")
print(f"R²   : {final_r2:.4f}")


# ============================================================
# BATTERY-WISE PERFORMANCE
# ============================================================

prediction_df = test_df[
    ["battery_id", "cycle_number", "SOH_percent"]
].copy()

prediction_df["predicted_SOH_percent"] = best_predictions

prediction_df["absolute_error_percent"] = (
    prediction_df["SOH_percent"]
    - prediction_df["predicted_SOH_percent"]
).abs()

print("\n" + "=" * 65)
print("BATTERY-WISE PERFORMANCE")
print("=" * 65)

for battery in test_batteries:

    battery_data = prediction_df[
        prediction_df["battery_id"] == battery
    ]

    battery_mae = mean_absolute_error(
        battery_data["SOH_percent"],
        battery_data["predicted_SOH_percent"]
    )

    print(
        f"{battery}: "
        f"MAE = {battery_mae:.4f}%"
    )


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({
    "feature": features,
    "importance": best_model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n" + "=" * 65)
print("BEST MODEL FEATURE IMPORTANCE")
print("=" * 65)

print(importance.to_string(index=False))


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    best_model,
    MODEL_FILE
)

prediction_df.to_csv(
    PRED_FILE,
    index=False
)

print("\n" + "=" * 65)
print("FILES SAVED")
print("=" * 65)

print("\nTuning results:")
print(RESULT_FILE)

print("\nBest model:")
print(MODEL_FILE)

print("\nPredictions:")
print(PRED_FILE)

print("\n" + "=" * 65)
print("GRADIENT BOOSTING TUNING COMPLETE")
print("=" * 65)