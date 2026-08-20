import os
import pandas as pd
import numpy as np

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

import joblib


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_health_features.csv"
)

RESULT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_model_comparison.csv"
)

BEST_MODEL_FILE = os.path.join(
    BASE_DIR,
    "models",
    "NASA_best_SOH_model.pkl"
)

PREDICTION_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_best_SOH_predictions.csv"
)


# ============================================================
# BATTERY SPLIT
# ============================================================

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


# ============================================================
# LEAKAGE-FREE FEATURES
# ============================================================

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


# ============================================================
# START
# ============================================================

print("=" * 65)
print("EV DIGITAL TWIN - SOH MODEL COMPARISON")
print("=" * 65)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

df = df.sort_values(
    ["battery_id", "cycle_number"]
).reset_index(drop=True)


# Remove rows with missing feature values

df = df.dropna(
    subset=FEATURES + [TARGET]
).reset_index(drop=True)


print("\nTotal usable rows:", len(df))


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

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


print("\nTraining rows:", len(train))
print("Testing rows :", len(test))

print("\nTraining batteries:")
print(TRAIN_BATTERIES)

print("\nTesting batteries:")
print(TEST_BATTERIES)


# ============================================================
# MODELS
# ============================================================

models = {

    "Random Forest": RandomForestRegressor(
        n_estimators=500,
        max_depth=12,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1
    ),

    "Extra Trees": ExtraTreesRegressor(
        n_estimators=500,
        max_depth=12,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1
    ),

    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=3,
        min_samples_leaf=3,
        loss="huber",
        random_state=42
    )
}


# ============================================================
# TRAIN AND EVALUATE
# ============================================================

results = []

prediction_tables = {}


for name, model in models.items():

    print("\n" + "=" * 65)
    print("TRAINING:", name)
    print("=" * 65)

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

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

    print("\nPerformance:")
    print(f"MAE  : {mae:.4f}%")
    print(f"RMSE : {rmse:.4f}%")
    print(f"R²   : {r2:.4f}")


    # --------------------------------------------------------
    # Battery-wise MAE
    # --------------------------------------------------------

    temp = test[
        ["battery_id", "cycle_number", "SOH_percent"]
    ].copy()

    temp["predicted_SOH_percent"] = predictions

    temp["absolute_error_percent"] = abs(
        temp["SOH_percent"] -
        temp["predicted_SOH_percent"]
    )

    print("\nBattery-wise MAE:")

    battery_maes = {}

    for battery in TEST_BATTERIES:

        battery_data = temp[
            temp["battery_id"] == battery
        ]

        battery_mae = mean_absolute_error(
            battery_data["SOH_percent"],
            battery_data["predicted_SOH_percent"]
        )

        battery_maes[battery] = battery_mae

        print(
            f"{battery}: "
            f"{battery_mae:.4f}%"
        )


    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    results.append({

        "model": name,

        "MAE_percent": mae,

        "RMSE_percent": rmse,

        "R2": r2,

        "B0030_MAE": battery_maes["B0030"],

        "B0031_MAE": battery_maes["B0031"],

        "B0032_MAE": battery_maes["B0032"]
    })


    prediction_tables[name] = temp


# ============================================================
# COMPARISON TABLE
# ============================================================

comparison = pd.DataFrame(
    results
)

comparison = comparison.sort_values(
    "MAE_percent"
).reset_index(drop=True)


print("\n" + "=" * 65)
print("MODEL COMPARISON")
print("=" * 65)

print(
    comparison.to_string(
        index=False
    )
)


# ============================================================
# BEST MODEL
# ============================================================

best_name = comparison.iloc[0]["model"]

best_model = models[best_name]

best_predictions = prediction_tables[
    best_name
]


print("\n" + "=" * 65)
print("BEST MODEL")
print("=" * 65)

print("\nSelected model:")
print(best_name)

print(
    f"\nBest MAE : "
    f"{comparison.iloc[0]['MAE_percent']:.4f}%"
)

print(
    f"Best RMSE: "
    f"{comparison.iloc[0]['RMSE_percent']:.4f}%"
)

print(
    f"Best R²  : "
    f"{comparison.iloc[0]['R2']:.4f}"
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

if hasattr(best_model, "feature_importances_"):

    importance = pd.DataFrame({

        "feature": FEATURES,

        "importance":
            best_model.feature_importances_
    })

    importance = importance.sort_values(
        "importance",
        ascending=False
    )

    print("\n" + "=" * 65)
    print("BEST MODEL FEATURE IMPORTANCE")
    print("=" * 65)

    for _, row in importance.iterrows():

        print(
            f"{row['feature']:35s} "
            f"{row['importance']:.6f}"
        )


# ============================================================
# SAVE
# ============================================================

comparison.to_csv(
    RESULT_FILE,
    index=False
)

best_predictions.to_csv(
    PREDICTION_FILE,
    index=False
)

joblib.dump(
    best_model,
    BEST_MODEL_FILE
)


print("\n" + "=" * 65)
print("FILES SAVED")
print("=" * 65)

print("\nModel comparison:")
print(RESULT_FILE)

print("\nBest model:")
print(BEST_MODEL_FILE)

print("\nBest predictions:")
print(PREDICTION_FILE)

print("\n" + "=" * 65)
print("MODEL COMPARISON COMPLETE")
print("=" * 65)