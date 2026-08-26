
"""
SOH MODEL EVALUATION
====================

Evaluates the trained SOH prediction model using the combined NASA,
Oxford and CALCE dataset.

Input:
    processed/soh/combined_soh_dataset.csv
    processed/soh/models/best_soh_model.pkl
    processed/soh/models/feature_columns.json

Output:
    processed/soh/evaluation/
        prediction_results.csv
        dataset_wise_results.csv
        battery_wise_results.csv
        evaluation_summary.json
        actual_vs_predicted.png
        error_distribution.png
        error_by_dataset.png
        soh_prediction_by_battery.png
        residual_vs_actual.png
"""

from pathlib import Path
import json
import pickle
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    median_absolute_error,
)

warnings.filterwarnings("ignore")


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

SOH_DIR = PROJECT_DIR / "processed" / "soh"

INPUT_DATASET = SOH_DIR / "combined_soh_dataset.csv"

MODEL_DIR = SOH_DIR / "models"

MODEL_FILE = MODEL_DIR / "best_soh_model.pkl"

FEATURE_FILE = MODEL_DIR / "feature_columns.json"

EVALUATION_DIR = SOH_DIR / "evaluation"


# ============================================================
# REQUIRED COLUMNS
# ============================================================

BASE_REQUIRED_COLUMNS = [
    "Source_Dataset",
    "Battery_ID",
    "Cycle",
    "Capacity_Ah",
    "SOH_percent",
]


NUMERIC_COLUMNS = [
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
    "SOH_percent",
]


MODEL_DERIVED_FEATURES = [
    "Cycle_Normalized",
    "Capacity_Ratio",
    "Voltage_Range_V",
    "Current_Range_A",
    "Temperature_Range_C",
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_section(title):
    print()
    print("-" * 70)
    print(title)
    print("-" * 70)


def ensure_directory():
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)


def check_input_files():
    print_header("CHECKING INPUT FILES")

    files = [
        ("Combined SOH dataset", INPUT_DATASET),
        ("Best SOH model", MODEL_FILE),
        ("Feature metadata", FEATURE_FILE),
    ]

    for name, path in files:
        if not path.exists():
            raise FileNotFoundError(
                f"{name} not found:\n{path}"
            )

        print(f"[FOUND] {name}")
        print(f"        {path}")


# ============================================================
# LOAD DATA
# ============================================================

def load_dataset():
    print_header("LOADING COMBINED SOH DATASET")

    df = pd.read_csv(INPUT_DATASET)

    print(f"Rows loaded    : {len(df)}")
    print(f"Columns loaded : {len(df.columns)}")

    print()
    print("Columns:")

    for column in df.columns:
        print(f"  {column}")

    return df


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

def validate_required_columns(df):
    print_section("CHECKING REQUIRED COLUMNS")

    missing = [
        column
        for column in BASE_REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            "Missing required columns:\n"
            + "\n".join(missing)
        )

    print("[PASS] All required columns present.")


# ============================================================
# NUMERIC CONVERSION
# ============================================================

def convert_numeric_columns(df):
    print_section("CONVERTING NUMERIC COLUMNS")

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    print("Numeric conversion complete.")

    return df


# ============================================================
# BASIC VALIDATION
# ============================================================

def basic_validation(df):

    print_section("BASIC DATA VALIDATION")

    invalid_soh = (
        df["SOH_percent"].isna()
        | (df["SOH_percent"] < 0)
        | (df["SOH_percent"] > 100)
    )

    invalid_capacity = (
        df["Capacity_Ah"].isna()
        | (df["Capacity_Ah"] <= 0)
    )

    invalid_cycle = (
        df["Cycle"].isna()
        | (df["Cycle"] < 0)
    )

    invalid_battery = (
        df["Battery_ID"].isna()
        | (df["Battery_ID"].astype(str).str.strip() == "")
    )

    print(f"Invalid SOH rows      : {invalid_soh.sum()}")
    print(f"Invalid capacity rows : {invalid_capacity.sum()}")
    print(f"Invalid cycle rows    : {invalid_cycle.sum()}")
    print(f"Invalid battery rows  : {invalid_battery.sum()}")

    invalid_any = (
        invalid_soh
        | invalid_capacity
        | invalid_cycle
        | invalid_battery
    )

    if invalid_any.any():
        print()
        print(
            f"[WARNING] Removing {invalid_any.sum()} invalid rows."
        )

        df = df.loc[~invalid_any].copy()

    print()
    print(f"Rows after validation: {len(df)}")

    if len(df) == 0:
        raise RuntimeError(
            "No valid rows remain after validation."
        )

    return df


# ============================================================
# DUPLICATE CHECK
# ============================================================

def remove_duplicates(df):

    print_section("CHECKING DUPLICATES")

    before = len(df)

    df = df.drop_duplicates().copy()

    exact_removed = before - len(df)

    print(
        f"Exact duplicate rows removed: "
        f"{exact_removed}"
    )

    before = len(df)

    df = df.drop_duplicates(
        subset=[
            "Source_Dataset",
            "Battery_ID",
            "Cycle",
        ],
        keep="first",
    ).copy()

    grouped_removed = before - len(df)

    print(
        f"Dataset/Battery/Cycle duplicate "
        f"rows removed: {grouped_removed}"
    )

    print(f"Rows remaining: {len(df)}")

    return df


# ============================================================
# FEATURE CREATION
# ============================================================

def create_model_features(df):

    print_section("CREATING MODEL FEATURES")

    df = df.copy()

    # --------------------------------------------------------
    # Cycle normalized within each battery
    # --------------------------------------------------------

    max_cycle = (
        df.groupby(
            ["Source_Dataset", "Battery_ID"]
        )["Cycle"]
        .transform("max")
    )

    max_cycle = max_cycle.replace(0, 1)

    df["Cycle_Normalized"] = (
        df["Cycle"] / max_cycle
    )

    # --------------------------------------------------------
    # Capacity ratio
    # --------------------------------------------------------

    first_capacity = (
        df.sort_values(
            [
                "Source_Dataset",
                "Battery_ID",
                "Cycle",
            ]
        )
        .groupby(
            ["Source_Dataset", "Battery_ID"]
        )["Capacity_Ah"]
        .transform("first")
    )

    first_capacity = first_capacity.replace(0, np.nan)

    df["Capacity_Ratio"] = (
        df["Capacity_Ah"] / first_capacity
    )

    # --------------------------------------------------------
    # Voltage range
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Current range
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Temperature range
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Prevent invalid infinity values
    # --------------------------------------------------------

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True,
    )

    print("Derived features recreated:")
    print("  Cycle_Normalized")
    print("  Capacity_Ratio")
    print("  Voltage_Range_V")
    print("  Current_Range_A")
    print("  Temperature_Range_C")

    return df


# ============================================================
# FEATURE AVAILABILITY
# ============================================================

def print_feature_availability(df):

    print_section("FEATURE AVAILABILITY")

    features = [
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
        "Cycle_Normalized",
        "Capacity_Ratio",
        "Voltage_Range_V",
        "Current_Range_A",
        "Temperature_Range_C",
        "Source_Dataset",
    ]

    total = len(df)

    for feature in features:

        if feature not in df.columns:
            count = 0
        else:
            count = df[feature].notna().sum()

        percentage = (
            100.0 * count / total
            if total > 0
            else 0
        )

        print(
            f"{feature:<30}"
            f"{count:>5}/{total:<5}"
            f" ({percentage:>6.2f}%)"
        )


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    print_section("LOADING TRAINED SOH MODEL")

    with open(MODEL_FILE, "rb") as file:
        model = pickle.load(file)

    print(f"Model type: {type(model).__name__}")

    return model


# ============================================================
# LOAD FEATURE METADATA
# ============================================================

def load_feature_metadata():

    print_section("LOADING FEATURE METADATA")

    with open(FEATURE_FILE, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    if isinstance(metadata, list):
        features = metadata

    elif isinstance(metadata, dict):

        if "feature_columns" in metadata:
            features = metadata["feature_columns"]

        elif "features" in metadata:
            features = metadata["features"]

        elif "columns" in metadata:
            features = metadata["columns"]

        else:
            raise RuntimeError(
                "Could not find feature columns "
                "inside feature_columns.json."
            )

    else:
        raise RuntimeError(
            "Unsupported feature metadata format."
        )

    if not isinstance(features, list):
        raise RuntimeError(
            "Feature metadata is not a list."
        )

    print("Features loaded from metadata:")

    for index, feature in enumerate(features, start=1):
        print(f"{index:>4}. {feature}")

    return features


# ============================================================
# PREPARE MODEL INPUT
# ============================================================

def prepare_model_input(df, feature_columns):

    print_section("PREPARING MODEL INPUT")

    missing_features = [
        feature
        for feature in feature_columns
        if feature not in df.columns
    ]

    if missing_features:
        raise RuntimeError(
            "The following model features are missing:\n"
            + "\n".join(missing_features)
        )

    X = df[feature_columns].copy()

    print(f"Model input rows    : {len(X)}")
    print(f"Model input columns : {len(X.columns)}")

    return X


# ============================================================
# MODEL PREPROCESSING CHECK
# ============================================================

def check_model_preprocessing(model, feature_columns):

    print_section("CHECKING MODEL PREPROCESSING")

    print("Model object:")
    print(f"  {type(model).__name__}")

    if "Source_Dataset" in feature_columns:

        print(
            "  Source_Dataset is included as a model feature."
        )

        if hasattr(model, "named_steps"):

            print(
                "  Saved model contains pipeline steps:"
            )

            for name in model.named_steps:
                print(f"    - {name}")

        else:

            print(
                "  [WARNING] Model does not expose "
                "named pipeline steps."
            )


# ============================================================
# GENERATE PREDICTIONS
# ============================================================

def generate_predictions(model, X):

    print_section("GENERATING SOH PREDICTIONS")

    print("Running model prediction...")

    predictions = model.predict(X)

    predictions = np.asarray(
        predictions,
        dtype=float,
    )

    outside = (
        (predictions < 0)
        | (predictions > 100)
    )

    outside_count = int(outside.sum())

    if outside_count > 0:

        print(
            f"[WARNING] {outside_count} predictions "
            f"were outside 0-100% and clipped."
        )

        predictions = np.clip(
            predictions,
            0,
            100,
        )

    else:

        print(
            "[PASS] All predictions within 0-100%."
        )

    print("Prediction complete.")

    print(
        f"Prediction minimum : "
        f"{predictions.min():.6f}%"
    )

    print(
        f"Prediction maximum : "
        f"{predictions.max():.6f}%"
    )

    print(
        f"Prediction mean    : "
        f"{predictions.mean():.6f}%"
    )

    return predictions


# ============================================================
# OVERALL METRICS
# ============================================================

def calculate_overall_metrics(
    actual,
    predicted,
):

    mae = mean_absolute_error(
        actual,
        predicted,
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predicted,
        )
    )

    r2 = r2_score(
        actual,
        predicted,
    )

    median_ae = median_absolute_error(
        actual,
        predicted,
    )

    errors = predicted - actual

    maximum_error = np.max(
        np.abs(errors)
    )

    mean_error = np.mean(errors)

    return {
        "Samples": int(len(actual)),
        "MAE_percent": float(mae),
        "RMSE_percent": float(rmse),
        "R2": float(r2),
        "Median_AE_percent": float(median_ae),
        "Maximum_Error_percent": float(
            maximum_error
        ),
        "Mean_Error_percent": float(
            mean_error
        ),
    }


# ============================================================
# DATASET-WISE EVALUATION
# ============================================================

def calculate_dataset_metrics(df):

    print_section("DATASET-WISE EVALUATION")

    records = []

    for dataset, group in df.groupby(
        "Source_Dataset"
    ):

        actual = group["SOH_percent"].to_numpy()

        predicted = group[
            "Predicted_SOH_percent"
        ].to_numpy()

        mae = mean_absolute_error(
            actual,
            predicted,
        )

        rmse = np.sqrt(
            mean_squared_error(
                actual,
                predicted,
            )
        )

        r2 = r2_score(
            actual,
            predicted,
        )

        print()
        print(dataset)

        print(
            f"  Samples : {len(group)}"
        )

        print(
            f"  MAE     : {mae:.6f}%"
        )

        print(
            f"  RMSE    : {rmse:.6f}%"
        )

        print(
            f"  R2      : {r2:.6f}"
        )

        records.append(
            {
                "Source_Dataset": dataset,
                "Samples": len(group),
                "MAE_percent": mae,
                "RMSE_percent": rmse,
                "R2": r2,
            }
        )

    return pd.DataFrame(records)


# ============================================================
# BATTERY-WISE EVALUATION
# ============================================================

def calculate_battery_metrics(df):

    print_section("BATTERY-WISE EVALUATION")

    records = []

    grouped = df.groupby(
        [
            "Source_Dataset",
            "Battery_ID",
        ]
    )

    for (
        dataset,
        battery,
    ), group in grouped:

        actual = group[
            "SOH_percent"
        ].to_numpy()

        predicted = group[
            "Predicted_SOH_percent"
        ].to_numpy()

        mae = mean_absolute_error(
            actual,
            predicted,
        )

        rmse = np.sqrt(
            mean_squared_error(
                actual,
                predicted,
            )
        )

        # R2 is undefined for a single sample.
        if len(group) > 1:
            try:
                r2 = r2_score(
                    actual,
                    predicted,
                )
            except Exception:
                r2 = np.nan
        else:
            r2 = np.nan

        print(
            f"{dataset:<8} "
            f"{battery:<10} "
            f"n={len(group):<4} "
            f"MAE={mae:.4f}% "
            f"RMSE={rmse:.4f}% "
            f"R2={r2:.6f}"
            if not np.isnan(r2)
            else
            f"{dataset:<8} "
            f"{battery:<10} "
            f"n={len(group):<4} "
            f"MAE={mae:.4f}% "
            f"RMSE={rmse:.4f}% "
            f"R2=N/A"
        )

        records.append(
            {
                "Source_Dataset": dataset,
                "Battery_ID": battery,
                "Samples": len(group),
                "MAE_percent": mae,
                "RMSE_percent": rmse,
                "R2": r2,
            }
        )

    return pd.DataFrame(records)


# ============================================================
# CREATE PREDICTION RESULTS
# ============================================================

def create_prediction_results(
    df,
    predictions,
):

    print_section("CREATING PREDICTION RESULTS")

    results = df.copy()

    # --------------------------------------------------------
    # IMPORTANT:
    # Create prediction columns BEFORE any plotting.
    # --------------------------------------------------------

    results[
        "Predicted_SOH_percent"
    ] = predictions

    results[
        "Prediction_Error_percent"
    ] = (
        results["Predicted_SOH_percent"]
        - results["SOH_percent"]
    )

    results[
        "Absolute_Error_percent"
    ] = (
        results["Prediction_Error_percent"]
        .abs()
    )

    # Additional useful error columns
    results[
        "Squared_Error"
    ] = (
        results["Prediction_Error_percent"]
        ** 2
    )

    output_file = (
        EVALUATION_DIR
        / "prediction_results.csv"
    )

    results.to_csv(
        output_file,
        index=False,
    )

    print(
        "Prediction results saved:"
    )

    print(f"  {output_file}")

    return results


# ============================================================
# WORST PREDICTIONS
# ============================================================

def print_worst_predictions(df):

    print_section("WORST PREDICTION CASES")

    required = [
        "Source_Dataset",
        "Battery_ID",
        "Cycle",
        "SOH_percent",
        "Predicted_SOH_percent",
        "Prediction_Error_percent",
        "Absolute_Error_percent",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            "Prediction results missing columns:\n"
            + "\n".join(missing)
        )

    worst = (
        df.sort_values(
            "Absolute_Error_percent",
            ascending=False,
        )
        .head(25)
    )

    print(
        worst[required]
        .to_string(index=False)
    )


# ============================================================
# PLOT 1 - ACTUAL VS PREDICTED
# ============================================================

def plot_actual_vs_predicted(df):

    print_section("PLOT: ACTUAL VS PREDICTED SOH")

    actual = df[
        "SOH_percent"
    ].to_numpy()

    predicted = df[
        "Predicted_SOH_percent"
    ].to_numpy()

    fig, ax = plt.subplots(
        figsize=(8, 7)
    )

    ax.scatter(
        actual,
        predicted,
        alpha=0.65,
        s=25,
    )

    minimum = min(
        actual.min(),
        predicted.min(),
    )

    maximum = max(
        actual.max(),
        predicted.max(),
    )

    ax.plot(
        [minimum, maximum],
        [minimum, maximum],
        linestyle="--",
    )

    ax.set_xlabel(
        "Actual SOH (%)"
    )

    ax.set_ylabel(
        "Predicted SOH (%)"
    )

    ax.set_title(
        "Actual vs Predicted SOH"
    )

    ax.grid(
        True,
        alpha=0.3,
    )

    fig.tight_layout()

    output = (
        EVALUATION_DIR
        / "actual_vs_predicted.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {output}")


# ============================================================
# PLOT 2 - ERROR DISTRIBUTION
# ============================================================

def plot_error_distribution(df):

    print_section("PLOT: ERROR DISTRIBUTION")

    # --------------------------------------------------------
    # FIX FOR PREVIOUS ERROR
    #
    # Never assume the error column exists.
    # Calculate it if necessary.
    # --------------------------------------------------------

    if (
        "Prediction_Error_percent"
        not in df.columns
    ):

        if (
            "Predicted_SOH_percent"
            not in df.columns
        ):

            raise RuntimeError(
                "Cannot create error distribution. "
                "Predicted_SOH_percent is missing."
            )

        if (
            "SOH_percent"
            not in df.columns
        ):

            raise RuntimeError(
                "Cannot create error distribution. "
                "SOH_percent is missing."
            )

        df = df.copy()

        df[
            "Prediction_Error_percent"
        ] = (
            df["Predicted_SOH_percent"]
            - df["SOH_percent"]
        )

    errors = pd.to_numeric(
        df["Prediction_Error_percent"],
        errors="coerce",
    ).dropna()

    if len(errors) == 0:
        raise RuntimeError(
            "No valid prediction errors available "
            "for error distribution plot."
        )

    fig, ax = plt.subplots(
        figsize=(9, 6)
    )

    ax.hist(
        errors,
        bins=40,
        alpha=0.75,
        edgecolor="black",
    )

    ax.axvline(
        0,
        linestyle="--",
    )

    ax.set_xlabel(
        "Prediction Error (%)"
    )

    ax.set_ylabel(
        "Frequency"
    )

    ax.set_title(
        "SOH Prediction Error Distribution"
    )

    ax.grid(
        True,
        alpha=0.3,
    )

    fig.tight_layout()

    output = (
        EVALUATION_DIR
        / "error_distribution.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {output}")


# ============================================================
# PLOT 3 - ERROR BY DATASET
# ============================================================

def plot_error_by_dataset(df):

    print_section("PLOT: ERROR BY DATASET")

    required = [
        "Source_Dataset",
        "Absolute_Error_percent",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            "Missing columns for dataset error plot:\n"
            + "\n".join(missing)
        )

    datasets = sorted(
        df["Source_Dataset"]
        .dropna()
        .unique()
    )

    values = []

    labels = []

    for dataset in datasets:

        data = df.loc[
            df["Source_Dataset"] == dataset,
            "Absolute_Error_percent",
        ].dropna()

        if len(data) > 0:
            values.append(data.to_numpy())
            labels.append(dataset)

    if not values:
        raise RuntimeError(
            "No error data available for dataset plot."
        )

    fig, ax = plt.subplots(
        figsize=(9, 6)
    )

    ax.boxplot(
        values,
        labels=labels,
    )

    ax.set_xlabel(
        "Dataset"
    )

    ax.set_ylabel(
        "Absolute Error (%)"
    )

    ax.set_title(
        "SOH Prediction Error by Dataset"
    )

    ax.grid(
        True,
        alpha=0.3,
    )

    fig.tight_layout()

    output = (
        EVALUATION_DIR
        / "error_by_dataset.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {output}")


# ============================================================
# PLOT 4 - SOH PREDICTION BY BATTERY
# ============================================================

def plot_soh_prediction_by_battery(df):

    print_section(
        "PLOT: SOH PREDICTION BY BATTERY"
    )

    grouped = df.groupby(
        [
            "Source_Dataset",
            "Battery_ID",
        ]
    )

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    plotted = False

    for (
        dataset,
        battery,
    ), group in grouped:

        group = group.sort_values(
            "Cycle"
        )

        label = (
            f"{dataset}-{battery}"
        )

        ax.plot(
            group["Cycle"],
            group["SOH_percent"],
            linewidth=1.5,
            alpha=0.7,
        )

        ax.plot(
            group["Cycle"],
            group["Predicted_SOH_percent"],
            linestyle="--",
            linewidth=1.2,
            alpha=0.7,
        )

        plotted = True

    if not plotted:
        plt.close(fig)
        raise RuntimeError(
            "No battery prediction data available."
        )

    ax.set_xlabel(
        "Cycle"
    )

    ax.set_ylabel(
        "SOH (%)"
    )

    ax.set_title(
        "Actual and Predicted SOH by Battery"
    )

    ax.grid(
        True,
        alpha=0.3,
    )

    fig.tight_layout()

    output = (
        EVALUATION_DIR
        / "soh_prediction_by_battery.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {output}")


# ============================================================
# PLOT 5 - RESIDUAL VS ACTUAL
# ============================================================

def plot_residual_vs_actual(df):

    print_section(
        "PLOT: RESIDUAL VS ACTUAL SOH"
    )

    required = [
        "SOH_percent",
        "Prediction_Error_percent",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            "Missing residual plot columns:\n"
            + "\n".join(missing)
        )

    plot_df = df[
        required
    ].dropna()

    fig, ax = plt.subplots(
        figsize=(9, 6)
    )

    ax.scatter(
        plot_df["SOH_percent"],
        plot_df[
            "Prediction_Error_percent"
        ],
        alpha=0.6,
        s=25,
    )

    ax.axhline(
        0,
        linestyle="--",
    )

    ax.set_xlabel(
        "Actual SOH (%)"
    )

    ax.set_ylabel(
        "Prediction Error (%)"
    )

    ax.set_title(
        "Prediction Residual vs Actual SOH"
    )

    ax.grid(
        True,
        alpha=0.3,
    )

    fig.tight_layout()

    output = (
        EVALUATION_DIR
        / "residual_vs_actual.png"
    )

    fig.savefig(
        output,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {output}")


# ============================================================
# SAVE METADATA
# ============================================================

def save_evaluation_summary(
    overall_metrics,
    dataset_metrics,
    battery_metrics,
):

    summary = {
        "evaluation_type": (
            "Combined SOH model evaluation"
        ),
        "input_dataset": str(
            INPUT_DATASET
        ),
        "model_file": str(
            MODEL_FILE
        ),
        "overall_metrics": (
            overall_metrics
        ),
        "dataset_count": int(
            len(dataset_metrics)
        ),
        "battery_count": int(
            len(battery_metrics)
        ),
    }

    output = (
        EVALUATION_DIR
        / "evaluation_summary.json"
    )

    with open(
        output,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=4,
        )

    print(
        f"Evaluation summary saved:\n  {output}"
    )


# ============================================================
# SAVE METRIC TABLES
# ============================================================

def save_metric_tables(
    dataset_metrics,
    battery_metrics,
):

    dataset_output = (
        EVALUATION_DIR
        / "dataset_wise_results.csv"
    )

    battery_output = (
        EVALUATION_DIR
        / "battery_wise_results.csv"
    )

    dataset_metrics.to_csv(
        dataset_output,
        index=False,
    )

    battery_metrics.to_csv(
        battery_output,
        index=False,
    )

    print(
        f"Dataset-wise results saved:\n"
        f"  {dataset_output}"
    )

    print(
        f"Battery-wise results saved:\n"
        f"  {battery_output}"
    )


# ============================================================
# FINAL VALIDATION
# ============================================================

def final_validation(
    df,
    overall_metrics,
):

    print_section(
        "FINAL EVALUATION VALIDATION"
    )

    checks = []

    # Dataset rows
    check = len(df) > 0

    checks.append(check)

    print(
        f"  [{'PASS' if check else 'FAIL'}] "
        f"Dataset contains rows"
    )

    # Required actual values
    check = (
        df["SOH_percent"]
        .notna()
        .all()
    )

    checks.append(check)

    print(
        f"  [{'PASS' if check else 'FAIL'}] "
        f"No missing actual SOH"
    )

    # Required predictions
    check = (
        df["Predicted_SOH_percent"]
        .notna()
        .all()
    )

    checks.append(check)

    print(
        f"  [{'PASS' if check else 'FAIL'}] "
        f"No missing predictions"
    )

    # Prediction range
    check = (
        (df["Predicted_SOH_percent"] >= 0)
        & (
            df["Predicted_SOH_percent"]
            <= 100
        )
    ).all()

    checks.append(check)

    print(
        f"  [{'PASS' if check else 'FAIL'}] "
        f"Predictions within 0-100%"
    )

    # Error column
    check = (
        "Prediction_Error_percent"
        in df.columns
    )

    checks.append(check)

    print(
        f"  [{'PASS' if check else 'FAIL'}] "
        f"Prediction error column present"
    )

    # Metrics
    check = (
        np.isfinite(
            overall_metrics[
                "MAE_percent"
            ]
        )
        and np.isfinite(
            overall_metrics[
                "RMSE_percent"
            ]
        )
        and np.isfinite(
            overall_metrics[
                "R2"
            ]
        )
    )

    checks.append(check)

    print(
        f"  [{'PASS' if check else 'FAIL'}] "
        f"Evaluation metrics valid"
    )

    if not all(checks):
        raise RuntimeError(
            "Final evaluation validation failed."
        )

    print()
    print(
        "All final evaluation validation "
        "checks passed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print_header(
        "SOH MODEL EVALUATION"
    )

    print(
        f"Project directory:\n"
        f"  {PROJECT_DIR}"
    )

    print(
        f"\nInput dataset:\n"
        f"  {INPUT_DATASET}"
    )

    print(
        f"\nModel:\n"
        f"  {MODEL_FILE}"
    )

    print(
        f"\nEvaluation directory:\n"
        f"  {EVALUATION_DIR}"
    )

    # --------------------------------------------------------
    # Setup
    # --------------------------------------------------------

    ensure_directory()

    check_input_files()

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    df = load_dataset()

    validate_required_columns(df)

    df = convert_numeric_columns(df)

    df = basic_validation(df)

    df = remove_duplicates(df)

    # --------------------------------------------------------
    # Create features
    # --------------------------------------------------------

    df = create_model_features(df)

    print_feature_availability(df)

    # --------------------------------------------------------
    # Load model and metadata
    # --------------------------------------------------------

    model = load_model()

    feature_columns = (
        load_feature_metadata()
    )

    # --------------------------------------------------------
    # Prepare model input
    # --------------------------------------------------------

    X = prepare_model_input(
        df,
        feature_columns,
    )

    check_model_preprocessing(
        model,
        feature_columns,
    )

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    predictions = generate_predictions(
        model,
        X,
    )

    # --------------------------------------------------------
    # Actual SOH
    # --------------------------------------------------------

    actual = df[
        "SOH_percent"
    ].to_numpy()

    # --------------------------------------------------------
    # Overall metrics
    # --------------------------------------------------------

    overall_metrics = (
        calculate_overall_metrics(
            actual,
            predictions,
        )
    )

    print_section(
        "OVERALL MODEL EVALUATION"
    )

    print(
        f"Samples       : "
        f"{overall_metrics['Samples']}"
    )

    print(
        f"MAE           : "
        f"{overall_metrics['MAE_percent']:.6f}%"
    )

    print(
        f"RMSE          : "
        f"{overall_metrics['RMSE_percent']:.6f}%"
    )

    print(
        f"R2            : "
        f"{overall_metrics['R2']:.6f}"
    )

    print(
        f"Median AE     : "
        f"{overall_metrics['Median_AE_percent']:.6f}%"
    )

    print(
        f"Maximum Error : "
        f"{overall_metrics['Maximum_Error_percent']:.6f}%"
    )

    print(
        f"Mean Error    : "
        f"{overall_metrics['Mean_Error_percent']:.6f}%"
    )

    # --------------------------------------------------------
    # CREATE RESULTS DATAFRAME
    #
    # IMPORTANT:
    # This happens BEFORE dataset-wise evaluation
    # and BEFORE every plotting function.
    # --------------------------------------------------------

    results_df = create_prediction_results(
        df,
        predictions,
    )

    # --------------------------------------------------------
    # Dataset-wise metrics
    # --------------------------------------------------------

    dataset_metrics = (
        calculate_dataset_metrics(
            results_df
        )
    )

    # --------------------------------------------------------
    # Battery-wise metrics
    # --------------------------------------------------------

    battery_metrics = (
        calculate_battery_metrics(
            results_df
        )
    )

    # --------------------------------------------------------
    # Save metric tables
    # --------------------------------------------------------

    save_metric_tables(
        dataset_metrics,
        battery_metrics,
    )

    # --------------------------------------------------------
    # Worst cases
    # --------------------------------------------------------

    print_worst_predictions(
        results_df
    )

    # --------------------------------------------------------
    # Plots
    #
    # All plots receive results_df, which contains:
    #
    # SOH_percent
    # Predicted_SOH_percent
    # Prediction_Error_percent
    # Absolute_Error_percent
    #
    # This fixes the previous KeyError.
    # --------------------------------------------------------

    plot_actual_vs_predicted(
        results_df
    )

    plot_error_distribution(
        results_df
    )

    plot_error_by_dataset(
        results_df
    )

    plot_soh_prediction_by_battery(
        results_df
    )

    plot_residual_vs_actual(
        results_df
    )

    # --------------------------------------------------------
    # Save evaluation summary
    # --------------------------------------------------------

    save_evaluation_summary(
        overall_metrics,
        dataset_metrics,
        battery_metrics,
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    final_validation(
        results_df,
        overall_metrics,
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print_header(
        "SOH MODEL EVALUATION COMPLETE"
    )

    print(
        f"Overall MAE  : "
        f"{overall_metrics['MAE_percent']:.6f}%"
    )

    print(
        f"Overall RMSE : "
        f"{overall_metrics['RMSE_percent']:.6f}%"
    )

    print(
        f"Overall R2   : "
        f"{overall_metrics['R2']:.6f}"
    )

    print()
    print(
        "Evaluation files saved in:"
    )

    print(
        f"  {EVALUATION_DIR}"
    )

    print()
    print(
        "Generated files:"
    )

    output_files = [
        "prediction_results.csv",
        "dataset_wise_results.csv",
        "battery_wise_results.csv",
        "evaluation_summary.json",
        "actual_vs_predicted.png",
        "error_distribution.png",
        "error_by_dataset.png",
        "soh_prediction_by_battery.png",
        "residual_vs_actual.png",
    ]

    for filename in output_files:
        print(f"  {filename}")

    print()
    print(
        "The SOH model evaluation completed successfully."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()