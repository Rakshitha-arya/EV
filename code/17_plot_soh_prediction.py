import os
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from sklearn.metrics import mean_absolute_error

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TEST_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_test_SOH.csv"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "models",
    "NASA_RandomForest_SOH.pkl"
)

RESULT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_SOH_predictions.csv"
)

RESULT_DIR = os.path.join(
    BASE_DIR,
    "results"
)

os.makedirs(RESULT_DIR, exist_ok=True)

PLOT_FILE = os.path.join(
    RESULT_DIR,
    "NASA_actual_vs_predicted_SOH.png"
)

# --------------------------------------------------
# LOAD
# --------------------------------------------------

test_df = pd.read_csv(TEST_FILE)

saved = joblib.load(MODEL_FILE)

model = saved["model"]
features = saved["features"]

X_test = test_df[features]
y_test = test_df["SOH_percent"]

# --------------------------------------------------
# PREDICT
# --------------------------------------------------

y_pred = model.predict(X_test)

# --------------------------------------------------
# RESULTS
# --------------------------------------------------

results = test_df[
    ["battery_id", "cycle_number", "SOH_percent"]
].copy()

results["predicted_SOH_percent"] = y_pred

results["error_percent"] = (
    results["predicted_SOH_percent"]
    - results["SOH_percent"]
)

results["absolute_error_percent"] = (
    results["error_percent"].abs()
)

results.to_csv(
    RESULT_FILE,
    index=False
)

mae = mean_absolute_error(
    y_test,
    y_pred
)

# --------------------------------------------------
# PLOT
# --------------------------------------------------

plt.figure(figsize=(12, 7))

for battery in sorted(
    results["battery_id"].unique()
):

    battery_data = results[
        results["battery_id"] == battery
    ]

    plt.plot(
        battery_data["cycle_number"],
        battery_data["SOH_percent"],
        label=f"{battery} Actual"
    )

    plt.plot(
        battery_data["cycle_number"],
        battery_data["predicted_SOH_percent"],
        "--",
        label=f"{battery} Predicted"
    )

plt.xlabel("Cycle Number")
plt.ylabel("SOH (%)")
plt.title(
    f"NASA Battery SOH: Actual vs Predicted\nMAE = {mae:.2f}%"
)

plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    PLOT_FILE,
    dpi=300
)

plt.close()

print("=" * 60)
print("SOH PREDICTION VISUALIZATION")
print("=" * 60)

print("\nMAE:")
print(f"{mae:.4f}%")

print("\nPrediction file:")
print(RESULT_FILE)

print("\nPlot saved to:")
print(PLOT_FILE)

print("\n" + "=" * 60)
print("VISUALIZATION COMPLETE")
print("=" * 60)