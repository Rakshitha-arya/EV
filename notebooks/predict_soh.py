import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


# ======================================================================
# SOH PREDICTION / INFERENCE
# ======================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

SOH_DIR = PROJECT_DIR / "processed" / "soh"
MODEL_DIR = SOH_DIR / "models"

MODEL_PATH = MODEL_DIR / "best_soh_model.pkl"
FEATURE_PATH = MODEL_DIR / "feature_columns.json"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

INPUT_PATH = SOH_DIR / "combined_soh_dataset.csv"
OUTPUT_PATH = SOH_DIR / "soh_predictions.csv"


print("=" * 70)
print("SOH PREDICTION / INFERENCE")
print("=" * 70)

print()
print("Project directory:")
print(f"  {PROJECT_DIR}")

print()
print("Model:")
print(f"  {MODEL_PATH}")

print()
print("Feature metadata:")
print(f"  {FEATURE_PATH}")

print()
print("Input dataset:")
print(f"  {INPUT_PATH}")

print()
print("Output:")
print(f"  {OUTPUT_PATH}")


# ======================================================================
# CHECK REQUIRED FILES
# ======================================================================

print()
print("=" * 70)
print("CHECKING REQUIRED FILES")
print("=" * 70)

required_files = {
    "MODEL": MODEL_PATH,
    "FEATURE METADATA": FEATURE_PATH,
    "MODEL METADATA": METADATA_PATH,
    "INPUT DATASET": INPUT_PATH,
}

for name, path in required_files.items():
    if path.exists():
        print(f"[FOUND] {name}")
        print(f"        {path}")
    else:
        print(f"[MISSING] {name}")
        print(f"          {path}")
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


# ======================================================================
# LOAD MODEL
# ======================================================================

print()
print("=" * 70)
print("LOADING TRAINED SOH MODEL")
print("=" * 70)

model = joblib.load(MODEL_PATH)

print()
print("Model loaded successfully.")
print(f"Model type: {type(model).__name__}")


# ======================================================================
# LOAD FEATURE METADATA
# ======================================================================

print()
print("=" * 70)
print("LOADING FEATURE METADATA")
print("=" * 70)

with open(FEATURE_PATH, "r", encoding="utf-8") as f:
    feature_metadata = json.load(f)

print("Feature metadata loaded.")


# ======================================================================
# EXTRACT FEATURE COLUMN LIST
# ======================================================================

if isinstance(feature_metadata, list):
    feature_columns = feature_metadata

elif isinstance(feature_metadata, dict):
    if "feature_columns" in feature_metadata:
        feature_columns = feature_metadata["feature_columns"]

    elif "features" in feature_metadata:
        feature_columns = feature_metadata["features"]

    elif "columns" in feature_metadata:
        feature_columns = feature_metadata["columns"]

    else:
        raise ValueError(
            "Could not find feature column list in feature_columns.json."
        )

else:
    raise ValueError(
        "Unsupported feature metadata format."
    )


feature_columns = list(feature_columns)

print()
print("Model feature columns:")

for i, column in enumerate(feature_columns, start=1):
    print(f"  {i:2d}. {column}")

print()
print(f"Total model features: {len(feature_columns)}")


# ======================================================================
# LOAD MODEL METADATA
# ======================================================================

print()
print("=" * 70)
print("LOADING MODEL METADATA")
print("=" * 70)

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    model_metadata = json.load(f)

print("Model metadata loaded.")

if isinstance(model_metadata, dict):
    print()
    print("Model metadata summary:")

    for key in [
        "best_model",
        "model_name",
        "MAE",
        "RMSE",
        "R2",
        "r2",
        "train_rows",
        "test_rows",
    ]:
        if key in model_metadata:
            print(f"  {key}: {model_metadata[key]}")


# ======================================================================
# LOAD INPUT DATASET
# ======================================================================

print()
print("=" * 70)
print("LOADING INPUT DATASET")
print("=" * 70)

df = pd.read_csv(INPUT_PATH)

print()
print(f"Rows loaded    : {len(df)}")
print(f"Columns loaded : {len(df.columns)}")

print()
print("Columns:")

for column in df.columns:
    print(f"  {column}")


# ======================================================================
# BASIC INPUT VALIDATION
# ======================================================================

print()
print("=" * 70)
print("BASIC INPUT VALIDATION")
print("=" * 70)

required_base_columns = [
    "Source_Dataset",
    "Battery_ID",
    "Cycle",
    "Capacity_Ah",
]

missing_base_columns = [
    column
    for column in required_base_columns
    if column not in df.columns
]

if missing_base_columns:
    raise ValueError(
        "Missing required input columns: "
        + ", ".join(missing_base_columns)
    )

print("[PASS] Required input columns present.")


# ======================================================================
# CONVERT NUMERIC COLUMNS
# ======================================================================

print()
print("=" * 70)
print("CONVERTING NUMERIC COLUMNS")
print("=" * 70)

numeric_columns = [
    "Cycle",
    "Capacity_Ah",
    "Voltage_Min_V",
    "Voltage_Max_V",
    "Voltage_Mean_V",
    "Voltage_Final_V",
    "Current_Min_A",
    "Current_Max_A",
    "Current_Mean_A",
    "Temperature_Min_C",
    "Temperature_Max_C",
    "Temperature_Mean_C",
    "Temperature_Final_C",
    "Discharge_Time_s",
]

for column in numeric_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

print("Numeric conversion complete.")


# ======================================================================
# CREATE DERIVED FEATURES
# ======================================================================

print()
print("=" * 70)
print("CREATING MODEL FEATURES")
print("=" * 70)


# ----------------------------------------------------------------------
# Cycle_Normalized
# ----------------------------------------------------------------------

df["Cycle_Normalized"] = (
    df.groupby(
        ["Source_Dataset", "Battery_ID"]
    )["Cycle"]
    .transform(
        lambda x: (
            x - x.min()
        ) / (
            x.max() - x.min()
        )
        if x.max() != x.min()
        else 0.0
    )
)


# ----------------------------------------------------------------------
# Capacity_Ratio
# ----------------------------------------------------------------------

first_capacity = (
    df.groupby(
        ["Source_Dataset", "Battery_ID"]
    )["Capacity_Ah"]
    .transform("first")
)

df["Capacity_Ratio"] = (
    df["Capacity_Ah"] / first_capacity
)


# ----------------------------------------------------------------------
# Voltage_Range_V
# ----------------------------------------------------------------------

if (
    "Voltage_Min_V" in df.columns
    and "Voltage_Max_V" in df.columns
):
    df["Voltage_Range_V"] = (
        df["Voltage_Max_V"]
        - df["Voltage_Min_V"]
    )
else:
    df["Voltage_Range_V"] = np.nan


# ----------------------------------------------------------------------
# Current_Range_A
# ----------------------------------------------------------------------

if (
    "Current_Min_A" in df.columns
    and "Current_Max_A" in df.columns
):
    df["Current_Range_A"] = (
        df["Current_Max_A"]
        - df["Current_Min_A"]
    )
else:
    df["Current_Range_A"] = np.nan


# ----------------------------------------------------------------------
# Temperature_Range_C
# ----------------------------------------------------------------------

if (
    "Temperature_Min_C" in df.columns
    and "Temperature_Max_C" in df.columns
):
    df["Temperature_Range_C"] = (
        df["Temperature_Max_C"]
        - df["Temperature_Min_C"]
    )
else:
    df["Temperature_Range_C"] = np.nan


print("Derived features created:")
print("  Cycle_Normalized")
print("  Capacity_Ratio")
print("  Voltage_Range_V")
print("  Current_Range_A")
print("  Temperature_Range_C")


# ======================================================================
# ADD SOURCE DATASET AS MODEL FEATURE
# ======================================================================

print()
print("=" * 70)
print("PREPARING DATASET IDENTIFIER")
print("=" * 70)

if "Source_Dataset" not in df.columns:
    raise ValueError(
        "Source_Dataset column is required."
    )

print("Source_Dataset available.")


# ======================================================================
# ENSURE ALL MODEL FEATURES EXIST
# ======================================================================

print()
print("=" * 70)
print("CHECKING MODEL FEATURES")
print("=" * 70)

missing_features = [
    column
    for column in feature_columns
    if column not in df.columns
]

if missing_features:
    print()
    print("Missing model features:")

    for column in missing_features:
        print(f"  {column}")

    raise ValueError(
        "Input data does not contain all required model features."
    )

print("[PASS] All model features are present.")


# ======================================================================
# CREATE FEATURE DATAFRAME
# ======================================================================

print()
print("=" * 70)
print("CREATING INFERENCE FEATURE MATRIX")
print("=" * 70)

X = df[feature_columns].copy()

print()
print(f"Feature rows   : {len(X)}")
print(f"Feature columns: {len(X.columns)}")


# ======================================================================
# HANDLE CATEGORICAL DATASET FEATURE
# ======================================================================

print()
print("=" * 70)
print("ENCODING SOURCE DATASET")
print("=" * 70)

if "Source_Dataset" in X.columns:

    source_mapping = {
        "CALCE": 0,
        "NASA": 1,
        "Oxford": 2,
    }

    X["Source_Dataset"] = (
        X["Source_Dataset"]
        .map(source_mapping)
    )

    unknown_sources = X["Source_Dataset"].isna().sum()

    if unknown_sources > 0:
        raise ValueError(
            f"Unknown Source_Dataset values found: "
            f"{unknown_sources}"
        )

    print("Source_Dataset encoded:")
    print("  CALCE  -> 0")
    print("  NASA   -> 1")
    print("  Oxford -> 2")


# ======================================================================
# HANDLE NUMERIC VALUES
# ======================================================================

print()
print("=" * 70)
print("PREPARING NUMERIC FEATURES")
print("=" * 70)

for column in X.columns:
    if column != "Source_Dataset":
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce"
        )


# ======================================================================
# MISSING VALUE HANDLING
# ======================================================================

print()
print("=" * 70)
print("CHECKING FEATURE MISSING VALUES")
print("=" * 70)

missing_before = X.isna().sum()

missing_total = int(
    missing_before.sum()
)

print()
print(f"Total missing feature values: {missing_total}")

if missing_total > 0:

    print()
    print("Missing values by feature:")

    for column, count in missing_before.items():
        if count > 0:
            percentage = (
                count / len(X)
            ) * 100

            print(
                f"  {column:30s}"
                f"{count:6d}"
                f" ({percentage:6.2f}%)"
            )

    print()
    print(
        "Missing feature values are expected "
        "for Oxford/CALCE because those datasets "
        "do not contain all NASA electrical/thermal measurements."
    )

    print()
    print(
        "Filling missing numeric values with training-compatible "
        "column medians."
    )

    for column in X.columns:

        if X[column].isna().any():

            median_value = X[column].median()

            if pd.isna(median_value):
                raise ValueError(
                    f"Cannot calculate median for feature: {column}"
                )

            X[column] = X[column].fillna(
                median_value
            )

            print(
                f"  {column}: "
                f"filled with median "
                f"{median_value:.6f}"
            )


# ======================================================================
# FINAL FEATURE VALIDATION
# ======================================================================

print()
print("=" * 70)
print("FINAL FEATURE VALIDATION")
print("=" * 70)

remaining_missing = int(
    X.isna().sum().sum()
)

if remaining_missing != 0:
    raise RuntimeError(
        "Missing values remain in inference feature matrix."
    )

if not np.isfinite(
    X.to_numpy(dtype=float)
).all():
    raise RuntimeError(
        "Non-finite values detected in inference features."
    )

print("[PASS] No missing feature values.")
print("[PASS] No non-finite feature values.")


# ======================================================================
# FEATURE ORDER VALIDATION
# ======================================================================

print()
print("=" * 70)
print("VALIDATING FEATURE ORDER")
print("=" * 70)

if list(X.columns) != feature_columns:
    raise RuntimeError(
        "Feature column order does not match training metadata."
    )

print("[PASS] Feature order matches training metadata.")


# ======================================================================
# RUN PREDICTION
# ======================================================================

print()
print("=" * 70)
print("RUNNING SOH PREDICTION")
print("=" * 70)

print("Generating predictions...")

predicted_soh = model.predict(X)

predicted_soh = np.asarray(
    predicted_soh,
    dtype=float
)

print("Prediction complete.")


# ======================================================================
# CLIP PREDICTIONS TO VALID SOH RANGE
# ======================================================================

print()
print("=" * 70)
print("VALIDATING PREDICTED SOH")
print("=" * 70)

raw_min = float(
    np.min(predicted_soh)
)

raw_max = float(
    np.max(predicted_soh)
)

print(
    f"Raw prediction minimum: "
    f"{raw_min:.6f}%"
)

print(
    f"Raw prediction maximum: "
    f"{raw_max:.6f}%"
)

outside_range = (
    (predicted_soh < 0)
    | (predicted_soh > 100)
)

outside_count = int(
    outside_range.sum()
)

print(
    f"Predictions outside 0-100%: "
    f"{outside_count}"
)

if outside_count > 0:
    print(
        "Clipping predictions to the physically valid "
        "0-100% SOH range."
    )

    predicted_soh = np.clip(
        predicted_soh,
        0.0,
        100.0
    )

else:
    print(
        "All predictions already fall inside "
        "the valid 0-100% range."
    )


# ======================================================================
# CREATE OUTPUT DATAFRAME
# ======================================================================

print()
print("=" * 70)
print("CREATING PREDICTION OUTPUT")
print("=" * 70)

prediction_df = df[
    [
        "Source_Dataset",
        "Battery_ID",
        "Cycle",
        "Capacity_Ah",
    ]
].copy()

if "SOH_percent" in df.columns:
    prediction_df[
        "Actual_SOH_percent"
    ] = pd.to_numeric(
        df["SOH_percent"],
        errors="coerce"
    )

prediction_df[
    "Predicted_SOH_percent"
] = predicted_soh

prediction_df[
    "SOH_Error_percent"
] = (
    prediction_df["Predicted_SOH_percent"]
    - prediction_df["Actual_SOH_percent"]
)


prediction_df[
    "Absolute_SOH_Error_percent"
] = (
    prediction_df["SOH_Error_percent"]
    .abs()
)


# ======================================================================
# SORT OUTPUT
# ======================================================================

prediction_df = prediction_df.sort_values(
    by=[
        "Source_Dataset",
        "Battery_ID",
        "Cycle",
    ]
).reset_index(drop=True)


# ======================================================================
# SAVE PREDICTIONS
# ======================================================================

print()
print("=" * 70)
print("SAVING SOH PREDICTIONS")
print("=" * 70)

prediction_df.to_csv(
    OUTPUT_PATH,
    index=False
)

print()
print("Prediction file saved successfully:")
print(f"  {OUTPUT_PATH}")


# ======================================================================
# PREDICTION SUMMARY
# ======================================================================

print()
print("=" * 70)
print("PREDICTION SUMMARY")
print("=" * 70)

print()
print(
    f"Prediction rows : "
    f"{len(prediction_df)}"
)

print(
    f"Minimum predicted SOH : "
    f"{prediction_df['Predicted_SOH_percent'].min():.6f}%"
)

print(
    f"Maximum predicted SOH : "
    f"{prediction_df['Predicted_SOH_percent'].max():.6f}%"
)

print(
    f"Mean predicted SOH    : "
    f"{prediction_df['Predicted_SOH_percent'].mean():.6f}%"
)


# ======================================================================
# ERROR SUMMARY
# ======================================================================

if "Actual_SOH_percent" in prediction_df.columns:

    valid_actual = (
        prediction_df["Actual_SOH_percent"]
        .notna()
    )

    if valid_actual.any():

        mae = (
            prediction_df.loc[
                valid_actual,
                "Absolute_SOH_Error_percent"
            ].mean()
        )

        rmse = np.sqrt(
            np.mean(
                prediction_df.loc[
                    valid_actual,
                    "SOH_Error_percent"
                ] ** 2
            )
        )

        print()
        print(
            f"Prediction MAE  : "
            f"{mae:.6f}%"
        )

        print(
            f"Prediction RMSE : "
            f"{rmse:.6f}%"
        )


# ======================================================================
# BATTERY-WISE PREDICTION SUMMARY
# ======================================================================

print()
print("=" * 70)
print("BATTERY-WISE PREDICTION SUMMARY")
print("=" * 70)

battery_summary = (
    prediction_df
    .groupby(
        [
            "Source_Dataset",
            "Battery_ID",
        ]
    )
    .agg(
        Records=(
            "Predicted_SOH_percent",
            "count"
        ),
        First_Predicted_SOH=(
            "Predicted_SOH_percent",
            "first"
        ),
        Last_Predicted_SOH=(
            "Predicted_SOH_percent",
            "last"
        ),
        Minimum_Predicted_SOH=(
            "Predicted_SOH_percent",
            "min"
        ),
        Maximum_Predicted_SOH=(
            "Predicted_SOH_percent",
            "max"
        ),
        Mean_Predicted_SOH=(
            "Predicted_SOH_percent",
            "mean"
        ),
    )
    .round(4)
)

print()
print(battery_summary.to_string())


# ======================================================================
# VERIFY SAVED FILE
# ======================================================================

print()
print("=" * 70)
print("VERIFYING SAVED PREDICTION FILE")
print("=" * 70)

saved_df = pd.read_csv(
    OUTPUT_PATH
)

print()
print(
    f"Saved rows    : "
    f"{len(saved_df)}"
)

print(
    f"Saved columns : "
    f"{len(saved_df.columns)}"
)

print(
    f"Saved batteries: "
    f"{saved_df['Battery_ID'].nunique()}"
)

print(
    f"Saved datasets : "
    f"{saved_df['Source_Dataset'].nunique()}"
)


# ======================================================================
# FINAL VALIDATION
# ======================================================================

print()
print("=" * 70)
print("FINAL PREDICTION VALIDATION")
print("=" * 70)

checks = []

# Rows
row_check = (
    len(saved_df) == len(prediction_df)
)

checks.append(
    ("Prediction row count preserved", row_check)
)

# Missing predictions
missing_prediction_check = (
    saved_df["Predicted_SOH_percent"]
    .notna()
    .all()
)

checks.append(
    ("No missing predictions", missing_prediction_check)
)

# SOH lower bound
soh_lower_check = (
    saved_df["Predicted_SOH_percent"] >= 0
).all()

checks.append(
    ("Predicted SOH >= 0", soh_lower_check)
)

# SOH upper bound
soh_upper_check = (
    saved_df["Predicted_SOH_percent"] <= 100
).all()

checks.append(
    ("Predicted SOH <= 100", soh_upper_check)
)

# Finite values
finite_check = np.isfinite(
    saved_df["Predicted_SOH_percent"]
    .to_numpy(dtype=float)
).all()

checks.append(
    ("Predictions are finite", finite_check)
)

# Required columns
required_output_columns = [
    "Source_Dataset",
    "Battery_ID",
    "Cycle",
    "Capacity_Ah",
    "Predicted_SOH_percent",
]

required_output_check = all(
    column in saved_df.columns
    for column in required_output_columns
)

checks.append(
    ("Required prediction columns present",
     required_output_check)
)


all_passed = True

for description, passed in checks:

    if passed:
        print(
            f"  [PASS] {description}"
        )

    else:
        print(
            f"  [FAIL] {description}"
        )

        all_passed = False


if not all_passed:
    raise RuntimeError(
        "Final prediction validation failed."
    )


# ======================================================================
# FINAL MESSAGE
# ======================================================================

print()
print("=" * 70)
print("SOH PREDICTION / INFERENCE COMPLETE")
print("=" * 70)

print()
print("Model:")
print(
    f"  {MODEL_PATH}"
)

print()
print("Prediction output:")
print(
    f"  {OUTPUT_PATH}"
)

print()
print(
    f"Rows predicted : "
    f"{len(prediction_df)}"
)

print(
    f"Datasets       : "
    f"{prediction_df['Source_Dataset'].nunique()}"
)

print(
    f"Battery groups : "
    f"{prediction_df['Battery_ID'].nunique()}"
)

print()
print(
    "The trained SOH model successfully generated "
    "predictions for the combined dataset."
)

print()
print("=" * 70)