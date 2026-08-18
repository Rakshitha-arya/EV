import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


print("=" * 65)
print("EV DIGITAL TWIN - FINAL TUNED SOH MODEL VALIDATION")
print("=" * 65)


# ============================================================
# PATHS
# ============================================================

DATA_FILE = "processed/NASA_health_features.csv"
MODEL_FILE = "models/NASA_tuned_GradientBoosting_SOH.pkl"

PRED_FILE = "processed/NASA_final_SOH_predictions.csv"
RESULT_FILE = "processed/NASA_final_SOH_evaluation.csv"

PLOT_FILE = "results/NASA_final_actual_vs_predicted_SOH.png"
ERROR_PLOT = "results/NASA_final_SOH_prediction_error.png"

os.makedirs("processed", exist_ok=True)
os.makedirs("results", exist_ok=True)


# ============================================================
# LOAD DATA AND MODEL
# ============================================================

df = pd.read_csv(DATA_FILE)

model = joblib.load(MODEL_FILE)

print("\nDataset rows:", len(df))

print("Model loaded:")
print(MODEL_FILE)


# ============================================================
# SAME BATTERY-LEVEL TEST SET
# ============================================================

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

test_df = df[
    df["battery_id"].isin(test_batteries)
].copy()

print("\nTesting batteries:")
print(test_batteries)

print("\nTesting rows:", len(test_df))


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


# ============================================================
# PREDICTION
# ============================================================

X_test = test_df[features]
y_test = test_df[target]

predictions = model.predict(X_test)

test_df["predicted_SOH_percent"] = predictions

test_df["error_percent"] = (
    test_df["predicted_SOH_percent"]
    - test_df["SOH_percent"]
)

test_df["absolute_error_percent"] = (
    test_df["error_percent"].abs()
)


# ============================================================
# OVERALL METRICS
# ============================================================

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
print("FINAL MODEL PERFORMANCE")
print("=" * 65)

print(f"\nMAE  : {mae:.4f}%")
print(f"RMSE : {rmse:.4f}%")
print(f"R²   : {r2:.4f}")


# ============================================================
# BATTERY-WISE PERFORMANCE
# ============================================================

print("\n" + "=" * 65)
print("BATTERY-WISE PERFORMANCE")
print("=" * 65)

battery_results = []

for battery in test_batteries:

    battery_df = test_df[
        test_df["battery_id"] == battery
    ]

    battery_mae = mean_absolute_error(
        battery_df["SOH_percent"],
        battery_df["predicted_SOH_percent"]
    )

    battery_rmse = np.sqrt(
        mean_squared_error(
            battery_df["SOH_percent"],
            battery_df["predicted_SOH_percent"]
        )
    )

    battery_r2 = r2_score(
        battery_df["SOH_percent"],
        battery_df["predicted_SOH_percent"]
    )

    battery_results.append({
        "battery_id": battery,
        "cycles": len(battery_df),
        "MAE_percent": battery_mae,
        "RMSE_percent": battery_rmse,
        "R2": battery_r2
    })

    print(
        f"{battery}: "
        f"MAE = {battery_mae:.4f}% | "
        f"RMSE = {battery_rmse:.4f}% | "
        f"R² = {battery_r2:.4f}"
    )


battery_results_df = pd.DataFrame(
    battery_results
)


# ============================================================
# WORST PREDICTIONS
# ============================================================

print("\n" + "=" * 65)
print("10 WORST PREDICTIONS")
print("=" * 65)

worst = test_df.sort_values(
    "absolute_error_percent",
    ascending=False
).head(10)

print(
    worst[
        [
            "battery_id",
            "cycle_number",
            "SOH_percent",
            "predicted_SOH_percent",
            "error_percent",
            "absolute_error_percent"
        ]
    ].to_string(index=False)
)


# ============================================================
# MODEL BIAS
# ============================================================

mean_error = test_df["error_percent"].mean()

print("\n" + "=" * 65)
print("MODEL BIAS")
print("=" * 65)

print(
    f"\nMean prediction error: "
    f"{mean_error:.4f}%"
)

if mean_error > 0:
    print("Model tendency: OVER-PREDICTION")
elif mean_error < 0:
    print("Model tendency: UNDER-PREDICTION")
else:
    print("Model tendency: NO BIAS")


# ============================================================
# SAVE PREDICTIONS
# ============================================================

test_df.to_csv(
    PRED_FILE,
    index=False
)


# ============================================================
# SAVE EVALUATION SUMMARY
# ============================================================

overall_result = pd.DataFrame([
    {
        "model": "Tuned Gradient Boosting",
        "MAE_percent": mae,
        "RMSE_percent": rmse,
        "R2": r2,
        "test_rows": len(test_df),
        "test_batteries": len(test_batteries)
    }
])

overall_result.to_csv(
    RESULT_FILE,
    index=False
)


# ============================================================
# ACTUAL VS PREDICTED PLOT
# ============================================================

plt.figure(figsize=(10, 6))

for battery in test_batteries:

    battery_df = test_df[
        test_df["battery_id"] == battery
    ]

    plt.plot(
        battery_df["cycle_number"],
        battery_df["SOH_percent"],
        marker="o",
        label=f"{battery} Actual"
    )

    plt.plot(
        battery_df["cycle_number"],
        battery_df["predicted_SOH_percent"],
        linestyle="--",
        label=f"{battery} Predicted"
    )

plt.xlabel("Cycle Number")
plt.ylabel("SOH (%)")
plt.title(
    "NASA Battery SOH - Actual vs Predicted\n"
    f"Tuned Gradient Boosting | MAE = {mae:.2f}%"
)

plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    PLOT_FILE,
    dpi=300
)

plt.close()


# ============================================================
# ERROR PLOT
# ============================================================

plt.figure(figsize=(10, 6))

for battery in test_batteries:

    battery_df = test_df[
        test_df["battery_id"] == battery
    ]

    plt.plot(
        battery_df["cycle_number"],
        battery_df["error_percent"],
        marker="o",
        label=battery
    )

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel("Cycle Number")
plt.ylabel("Prediction Error (%)")
plt.title(
    "NASA Battery SOH Prediction Error"
)

plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    ERROR_PLOT,
    dpi=300
)

plt.close()


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 65)
print("FILES SAVED")
print("=" * 65)

print("\nFinal predictions:")
print(PRED_FILE)

print("\nEvaluation:")
print(RESULT_FILE)

print("\nActual vs predicted plot:")
print(PLOT_FILE)

print("\nPrediction error plot:")
print(ERROR_PLOT)

print("\n" + "=" * 65)
print("FINAL SOH MODEL VALIDATION COMPLETE")
print("=" * 65)