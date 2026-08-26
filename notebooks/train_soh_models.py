"""
train_soh_models.py

Train and compare SOH prediction models using the prepared combined
NASA + Oxford + CALCE dataset.

Input:
    processed/soh/combined_soh_dataset.csv

Outputs:
    processed/soh/models/
        soh_model_results.csv
        best_soh_model.pkl
        feature_columns.json
        model_metadata.json
        model_comparison.csv

The script:
1. Loads the combined dataset.
2. Removes invalid target rows.
3. Creates useful cycle/degradation features.
4. Handles dataset-specific missing sensor features.
5. Splits data by battery/cell to avoid data leakage.
6. Trains several regression models.
7. Evaluates MAE, RMSE and R².
8. Saves the best model and metadata.
"""

from pathlib import Path
import json
import pickle
import warnings

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor


warnings.filterwarnings("ignore")


# ============================================================
# PROJECT PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

SOH_DIR = PROJECT_DIR / "processed" / "soh"

INPUT_FILE = SOH_DIR / "combined_soh_dataset.csv"
MODEL_DIR = SOH_DIR / "models"

MODEL_RESULTS_FILE = MODEL_DIR / "soh_model_results.csv"
MODEL_COMPARISON_FILE = MODEL_DIR / "model_comparison.csv"
BEST_MODEL_FILE = MODEL_DIR / "best_soh_model.pkl"
FEATURE_COLUMNS_FILE = MODEL_DIR / "feature_columns.json"
MODEL_METADATA_FILE = MODEL_DIR / "model_metadata.json"


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_COLUMN = "SOH_percent"

GROUP_COLUMN = "Battery_ID"

DATASET_COLUMN = "Source_Dataset"

RANDOM_STATE = 42


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

BASE_NUMERIC_FEATURES = [
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


DERIVED_NUMERIC_FEATURES = [
    "Cycle_Normalized",
    "Capacity_Ratio",
    "Voltage_Range_V",
    "Current_Range_A",
    "Temperature_Range_C",
]


CATEGORICAL_FEATURES = [
    "Source_Dataset",
]


# ============================================================
# PRINT HELPERS
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


# ============================================================
# PATH VALIDATION
# ============================================================

def check_paths():
    print_header("SOH MODEL TRAINING")

    print("Project directory:")
    print(f"  {PROJECT_DIR}")

    print()
    print("Input:")
    print(f"  {INPUT_FILE}")

    print()
    print("Output directory:")
    print(f"  {MODEL_DIR}")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"\nInput dataset not found:\n{INPUT_FILE}\n"
            "Run prepare_combined_soh_dataset.py first."
        )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("[FOUND] Combined SOH dataset")


# ============================================================
# LOAD DATA
# ============================================================

def load_dataset():
    print_header("LOADING COMBINED SOH DATASET")

    df = pd.read_csv(INPUT_FILE)

    print()
    print(f"Rows loaded    : {len(df)}")
    print(f"Columns loaded : {len(df.columns)}")

    print()
    print("Columns:")

    for column in df.columns:
        print(f"  {column}")

    required_columns = [
        DATASET_COLUMN,
        GROUP_COLUMN,
        "Cycle",
        "Capacity_Ah",
        TARGET_COLUMN,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise RuntimeError(
            "Required columns are missing:\n"
            + "\n".join(f"  {x}" for x in missing_columns)
        )

    return df


# ============================================================
# NUMERIC CONVERSION
# ============================================================

def convert_numeric_columns(df):
    print_header("CONVERTING NUMERIC COLUMNS")

    numeric_columns = [
        column
        for column in BASE_NUMERIC_FEATURES + [TARGET_COLUMN]
        if column in df.columns
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    print("Numeric conversion complete.")

    return df


# ============================================================
# BASIC VALIDATION
# ============================================================

def validate_basic_data(df):
    print_header("BASIC DATA VALIDATION")

    print(f"Rows before validation: {len(df)}")

    invalid_target = (
        df[TARGET_COLUMN].isna()
        | (df[TARGET_COLUMN] < 0)
        | (df[TARGET_COLUMN] > 100)
    )

    invalid_capacity = (
        df["Capacity_Ah"].isna()
        | (df["Capacity_Ah"] <= 0)
    )

    invalid_cycle = (
        df["Cycle"].isna()
        | (df["Cycle"] < 0)
    )

    invalid_group = (
        df[GROUP_COLUMN].isna()
        | (df[GROUP_COLUMN].astype(str).str.strip() == "")
    )

    invalid_rows = (
        invalid_target
        | invalid_capacity
        | invalid_cycle
        | invalid_group
    )

    print()
    print(f"Invalid SOH rows       : {invalid_target.sum()}")
    print(f"Invalid capacity rows  : {invalid_capacity.sum()}")
    print(f"Invalid cycle rows     : {invalid_cycle.sum()}")
    print(f"Invalid battery rows   : {invalid_group.sum()}")

    if invalid_rows.sum() > 0:
        print()
        print(
            f"Removing {invalid_rows.sum()} invalid rows."
        )

        df = df.loc[~invalid_rows].copy()

    print()
    print(f"Rows after validation: {len(df)}")

    if len(df) == 0:
        raise RuntimeError(
            "No valid rows remain after validation."
        )

    return df


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):
    print_header("REMOVING DUPLICATES")

    exact_before = len(df)

    df = df.drop_duplicates().copy()

    exact_removed = exact_before - len(df)

    print(f"Exact duplicate rows removed: {exact_removed}")

    key_columns = [
        DATASET_COLUMN,
        GROUP_COLUMN,
        "Cycle",
    ]

    duplicate_mask = df.duplicated(
        subset=key_columns,
        keep="first",
    )

    duplicate_count = int(duplicate_mask.sum())

    print(
        "Dataset/Battery/Cycle duplicate rows removed: "
        f"{duplicate_count}"
    )

    if duplicate_count > 0:
        df = df.loc[~duplicate_mask].copy()

    print(f"Rows remaining: {len(df)}")

    return df


# ============================================================
# CREATE DERIVED FEATURES
# ============================================================

def create_features(df):
    print_header("CREATING MODEL FEATURES")

    df = df.copy()

    # --------------------------------------------------------
    # Cycle normalized within each battery
    # --------------------------------------------------------

    max_cycle = (
        df.groupby(
            [DATASET_COLUMN, GROUP_COLUMN]
        )["Cycle"]
        .transform("max")
    )

    df["Cycle_Normalized"] = np.where(
        max_cycle > 0,
        df["Cycle"] / max_cycle,
        0.0,
    )

    # --------------------------------------------------------
    # Capacity ratio
    #
    # Capacity / initial battery capacity
    # --------------------------------------------------------

    initial_capacity = (
        df.sort_values(
            [DATASET_COLUMN, GROUP_COLUMN, "Cycle"]
        )
        .groupby(
            [DATASET_COLUMN, GROUP_COLUMN]
        )["Capacity_Ah"]
        .transform("first")
    )

    df["Capacity_Ratio"] = np.where(
        initial_capacity > 0,
        df["Capacity_Ah"] / initial_capacity,
        np.nan,
    )

    # --------------------------------------------------------
    # Voltage range
    # --------------------------------------------------------

    if {
        "Voltage_Min_V",
        "Voltage_Max_V",
    }.issubset(df.columns):

        df["Voltage_Range_V"] = (
            df["Voltage_Max_V"]
            - df["Voltage_Min_V"]
        )

    else:
        df["Voltage_Range_V"] = np.nan

    # --------------------------------------------------------
    # Current range
    # --------------------------------------------------------

    if {
        "Current_Min_A",
        "Current_Max_A",
    }.issubset(df.columns):

        df["Current_Range_A"] = (
            df["Current_Max_A"]
            - df["Current_Min_A"]
        )

    else:
        df["Current_Range_A"] = np.nan

    # --------------------------------------------------------
    # Temperature range
    # --------------------------------------------------------

    if {
        "Temperature_Min_C",
        "Temperature_Max_C",
    }.issubset(df.columns):

        df["Temperature_Range_C"] = (
            df["Temperature_Max_C"]
            - df["Temperature_Min_C"]
        )

    else:
        df["Temperature_Range_C"] = np.nan

    print("Derived features created:")

    for column in DERIVED_NUMERIC_FEATURES:
        print(f"  {column}")

    return df


# ============================================================
# FEATURE AVAILABILITY
# ============================================================

def print_feature_availability(df):
    print_header("FEATURE AVAILABILITY")

    feature_columns = (
        BASE_NUMERIC_FEATURES
        + DERIVED_NUMERIC_FEATURES
    )

    for column in feature_columns:

        if column not in df.columns:
            print(
                f"{column:30s} MISSING COLUMN"
            )
            continue

        available = df[column].notna().sum()
        total = len(df)

        percentage = (
            available / total * 100
            if total > 0
            else 0
        )

        print(
            f"{column:30s}"
            f"{available:5d}/{total:<5d}"
            f"({percentage:7.2f}%)"
        )


# ============================================================
# GROUP-AWARE TRAIN/TEST SPLIT
# ============================================================

def create_group_split(df):
    print_header("CREATING BATTERY-WISE TRAIN/TEST SPLIT")

    groups = (
        df[
            [DATASET_COLUMN, GROUP_COLUMN]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    print()
    print(
        f"Total battery/cell groups: {len(groups)}"
    )

    if len(groups) < 4:
        raise RuntimeError(
            "Too few battery/cell groups for a "
            "meaningful train/test split."
        )

    # --------------------------------------------------------
    # Deterministic group split.
    #
    # We deliberately keep complete batteries/cells together.
    # This prevents cycle-level leakage.
    # --------------------------------------------------------

    rng = np.random.RandomState(RANDOM_STATE)

    shuffled_indices = rng.permutation(len(groups))

    test_group_count = max(
        1,
        int(round(len(groups) * 0.25))
    )

    test_indices = shuffled_indices[
        :test_group_count
    ]

    train_indices = shuffled_indices[
        test_group_count:
    ]

    train_groups = groups.iloc[
        train_indices
    ].copy()

    test_groups = groups.iloc[
        test_indices
    ].copy()

    train_keys = set(
        zip(
            train_groups[DATASET_COLUMN],
            train_groups[GROUP_COLUMN],
        )
    )

    test_keys = set(
        zip(
            test_groups[DATASET_COLUMN],
            test_groups[GROUP_COLUMN],
        )
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    overlap = train_keys.intersection(test_keys)

    if overlap:
        raise RuntimeError(
            "Battery/cell leakage detected between "
            "training and testing groups."
        )

    train_mask = [
        (
            dataset,
            battery
        ) in train_keys
        for dataset, battery in zip(
            df[DATASET_COLUMN],
            df[GROUP_COLUMN],
        )
    ]

    test_mask = [
        (
            dataset,
            battery
        ) in test_keys
        for dataset, battery in zip(
            df[DATASET_COLUMN],
            df[GROUP_COLUMN],
        )
    ]

    train_df = df.loc[
        train_mask
    ].copy()

    test_df = df.loc[
        test_mask
    ].copy()

    print()
    print("Training groups:")

    for _, row in train_groups.sort_values(
        [DATASET_COLUMN, GROUP_COLUMN]
    ).iterrows():

        print(
            f"  {row[DATASET_COLUMN]:8s} "
            f"{row[GROUP_COLUMN]}"
        )

    print()
    print("Testing groups:")

    for _, row in test_groups.sort_values(
        [DATASET_COLUMN, GROUP_COLUMN]
    ).iterrows():

        print(
            f"  {row[DATASET_COLUMN]:8s} "
            f"{row[GROUP_COLUMN]}"
        )

    print()
    print(
        f"Training rows: {len(train_df)}"
    )

    print(
        f"Testing rows : {len(test_df)}"
    )

    if len(train_df) == 0 or len(test_df) == 0:
        raise RuntimeError(
            "Train/test split produced an empty dataset."
        )

    return train_df, test_df, train_groups, test_groups


# ============================================================
# PREPROCESSOR
# ============================================================

def create_preprocessor(feature_columns):
    numeric_features = [
        column
        for column in feature_columns
        if column != DATASET_COLUMN
    ]

    categorical_features = [
        DATASET_COLUMN
    ]

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_features,
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_features,
            ),
        ],
        remainder="drop",
    )

    return preprocessor


# ============================================================
# MODEL DEFINITIONS
# ============================================================

def create_models():
    models = {

        "Ridge": Ridge(
            alpha=1.0
        ),

        "RandomForest": RandomForestRegressor(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),

        "ExtraTrees": ExtraTreesRegressor(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),

        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=250,
            learning_rate=0.03,
            max_depth=3,
            min_samples_leaf=3,
            random_state=RANDOM_STATE,
        ),

        "KNN": KNeighborsRegressor(
            n_neighbors=8,
            weights="distance",
            p=2,
        ),
    }

    return models


# ============================================================
# EVALUATION
# ============================================================

def calculate_metrics(y_true, y_pred):

    mae = mean_absolute_error(
        y_true,
        y_pred,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            y_pred,
        )
    )

    r2 = r2_score(
        y_true,
        y_pred,
    )

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2),
    }


# ============================================================
# TRAIN MODELS
# ============================================================

def train_models(
    train_df,
    test_df,
    feature_columns,
):
    print_header("TRAINING SOH MODELS")

    X_train = train_df[
        feature_columns
    ].copy()

    y_train = train_df[
        TARGET_COLUMN
    ].copy()

    X_test = test_df[
        feature_columns
    ].copy()

    y_test = test_df[
        TARGET_COLUMN
    ].copy()

    models = create_models()

    results = []

    trained_models = {}

    for model_name, model in models.items():

        print_section(
            f"TRAINING {model_name}"
        )

        preprocessor = create_preprocessor(
            feature_columns
        )

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor,
                ),
                (
                    "model",
                    model,
                ),
            ]
        )

        print("Fitting model...")

        pipeline.fit(
            X_train,
            y_train,
        )

        print("Prediction...")

        predictions = pipeline.predict(
            X_test
        )

        # ----------------------------------------------------
        # Safety clipping
        # ----------------------------------------------------

        predictions = np.clip(
            predictions,
            0,
            100,
        )

        metrics = calculate_metrics(
            y_test,
            predictions,
        )

        print()
        print(
            f"MAE  : {metrics['MAE']:.6f}"
        )

        print(
            f"RMSE : {metrics['RMSE']:.6f}"
        )

        print(
            f"R2   : {metrics['R2']:.6f}"
        )

        result = {
            "Model": model_name,
            "MAE": metrics["MAE"],
            "RMSE": metrics["RMSE"],
            "R2": metrics["R2"],
            "Train_Rows": len(train_df),
            "Test_Rows": len(test_df),
            "Train_Groups": train_df[
                [DATASET_COLUMN, GROUP_COLUMN]
            ].drop_duplicates().shape[0],
            "Test_Groups": test_df[
                [DATASET_COLUMN, GROUP_COLUMN]
            ].drop_duplicates().shape[0],
        }

        results.append(result)

        trained_models[
            model_name
        ] = pipeline

    results_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Best model:
    # Lowest RMSE, then lowest MAE, then highest R2
    # --------------------------------------------------------

    results_df = results_df.sort_values(
        by=[
            "RMSE",
            "MAE",
            "R2",
        ],
        ascending=[
            True,
            True,
            False,
        ],
    ).reset_index(drop=True)

    return (
        results_df,
        trained_models,
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results_df):
    print_header("MODEL COMPARISON")

    print(
        results_df.to_string(
            index=False
        )
    )

    results_df.to_csv(
        MODEL_RESULTS_FILE,
        index=False,
    )

    results_df.to_csv(
        MODEL_COMPARISON_FILE,
        index=False,
    )

    print()
    print(
        "Model comparison saved:"
    )

    print(
        f"  {MODEL_RESULTS_FILE}"
    )


# ============================================================
# SAVE BEST MODEL
# ============================================================

def save_best_model(
    results_df,
    trained_models,
    feature_columns,
    train_groups,
    test_groups,
):
    print_header("SAVING BEST SOH MODEL")

    best_model_name = (
        results_df.iloc[0]["Model"]
    )

    best_model = trained_models[
        best_model_name
    ]

    with open(
        BEST_MODEL_FILE,
        "wb",
    ) as file:
        pickle.dump(
            best_model,
            file,
        )

    # --------------------------------------------------------
    # Feature metadata
    # --------------------------------------------------------

    feature_metadata = {
        "feature_columns": feature_columns,
        "target_column": TARGET_COLUMN,
        "dataset_column": DATASET_COLUMN,
        "group_column": GROUP_COLUMN,
    }

    with open(
        FEATURE_COLUMNS_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            feature_metadata,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # Model metadata
    # --------------------------------------------------------

    best_row = results_df.iloc[0]

    train_group_records = (
        train_groups
        .sort_values(
            [
                DATASET_COLUMN,
                GROUP_COLUMN,
            ]
        )
        .to_dict(
            orient="records"
        )
    )

    test_group_records = (
        test_groups
        .sort_values(
            [
                DATASET_COLUMN,
                GROUP_COLUMN,
            ]
        )
        .to_dict(
            orient="records"
        )
    )

    metadata = {
        "best_model": best_model_name,
        "target_column": TARGET_COLUMN,

        "input_dataset": str(
            INPUT_FILE
        ),

        "model_file": str(
            BEST_MODEL_FILE
        ),

        "feature_columns": feature_columns,

        "metrics": {
            "MAE": float(
                best_row["MAE"]
            ),
            "RMSE": float(
                best_row["RMSE"]
            ),
            "R2": float(
                best_row["R2"]
            ),
        },

        "training_rows": int(
            best_row["Train_Rows"]
        ),

        "testing_rows": int(
            best_row["Test_Rows"]
        ),

        "training_groups": train_group_records,

        "testing_groups": test_group_records,

        "random_state": RANDOM_STATE,
    }

    with open(
        MODEL_METADATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )

    print()
    print(
        f"Best model: {best_model_name}"
    )

    print()
    print(
        f"Model saved:"
    )

    print(
        f"  {BEST_MODEL_FILE}"
    )

    print()
    print(
        "Feature metadata saved:"
    )

    print(
        f"  {FEATURE_COLUMNS_FILE}"
    )

    print()
    print(
        "Model metadata saved:"
    )

    print(
        f"  {MODEL_METADATA_FILE}"
    )

    return best_model_name


# ============================================================
# FINAL MODEL VALIDATION
# ============================================================

def final_validation(
    df,
    results_df,
    best_model_name,
):
    print_header("FINAL MODEL TRAINING VALIDATION")

    checks = []

    # --------------------------------------------------------
    # Dataset checks
    # --------------------------------------------------------

    check = (
        len(df) > 0
    )

    checks.append(
        (
            "Dataset contains rows",
            check,
        )
    )

    check = (
        df[TARGET_COLUMN]
        .notna()
        .all()
    )

    checks.append(
        (
            "No missing SOH",
            check,
        )
    )

    check = (
        (
            df[TARGET_COLUMN] >= 0
        )
        & (
            df[TARGET_COLUMN] <= 100
        )
    ).all()
    
    checks.append(
        (
            "SOH within 0-100%",
            check,
        )
    )

    # --------------------------------------------------------
    # Model checks
    # --------------------------------------------------------

    check = (
        len(results_df) > 0
    )

    checks.append(
        (
            "At least one model trained",
            check,
        )
    )

    check = (
        best_model_name
        in results_df["Model"].values
    )

    checks.append(
        (
            "Best model exists",
            check,
        )
    )

    # --------------------------------------------------------
    # Metrics checks
    # --------------------------------------------------------

    best_row = results_df[
        results_df["Model"]
        == best_model_name
    ].iloc[0]

    check = np.isfinite(
        best_row["MAE"]
    )

    checks.append(
        (
            "Best model MAE valid",
            check,
        )
    )

    check = np.isfinite(
        best_row["RMSE"]
    )

    checks.append(
        (
            "Best model RMSE valid",
            check,
        )
    )

    check = np.isfinite(
        best_row["R2"]
    )

    checks.append(
        (
            "Best model R2 valid",
            check,
        )
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
            "Final model training validation failed."
        )

    print()
    print(
        "All final model validation checks passed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    check_paths()

    df = load_dataset()

    df = convert_numeric_columns(
        df
    )

    df = validate_basic_data(
        df
    )

    df = remove_duplicates(
        df
    )

    df = create_features(
        df
    )

    print_feature_availability(
        df
    )

    train_df, test_df, train_groups, test_groups = (
        create_group_split(df)
    )

    feature_columns = [
        column
        for column in (
            BASE_NUMERIC_FEATURES
            + DERIVED_NUMERIC_FEATURES
        )
        if column in df.columns
    ]

    # Dataset identifier is included as a categorical feature.
    feature_columns.append(
        DATASET_COLUMN
    )

    print_header("FINAL MODEL FEATURE SET")

    for index, column in enumerate(
        feature_columns,
        start=1,
    ):
        print(
            f"{index:3d}. {column}"
        )

    print()
    print(
        f"Total model features: "
        f"{len(feature_columns)}"
    )

    results_df, trained_models = train_models(
        train_df=train_df,
        test_df=test_df,
        feature_columns=feature_columns,
    )

    save_results(
        results_df
    )

    best_model_name = save_best_model(
        results_df=results_df,
        trained_models=trained_models,
        feature_columns=feature_columns,
        train_groups=train_groups,
        test_groups=test_groups,
    )

    final_validation(
        df=df,
        results_df=results_df,
        best_model_name=best_model_name,
    )

    print_header(
        "SOH MODEL TRAINING COMPLETE"
    )

    best_row = results_df.iloc[0]

    print()
    print(
        f"Best model : {best_model_name}"
    )

    print(
        f"MAE        : "
        f"{best_row['MAE']:.6f}"
    )

    print(
        f"RMSE       : "
        f"{best_row['RMSE']:.6f}"
    )

    print(
        f"R2         : "
        f"{best_row['R2']:.6f}"
    )

    print()
    print(
        "Input dataset:"
    )

    print(
        f"  {INPUT_FILE}"
    )

    print()
    print(
        "Saved model:"
    )

    print(
        f"  {BEST_MODEL_FILE}"
    )

    print()
    print(
        "Saved model comparison:"
    )

    print(
        f"  {MODEL_RESULTS_FILE}"
    )

    print()
    print(
        "Saved feature metadata:"
    )

    print(
        f"  {FEATURE_COLUMNS_FILE}"
    )

    print()
    print(
        "Saved model metadata:"
    )

    print(
        f"  {MODEL_METADATA_FILE}"
    )

    print()
    print(
        "The SOH model is ready for the next "
        "prediction/inference stage."
    )


if __name__ == "__main__":
    main()