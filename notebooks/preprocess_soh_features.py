"""
preprocess_soh_features.py

EV Digital Twin
SOH Model Preprocessing

Input:
    processed/soh/combined_soh_dataset.csv

Outputs:
    processed/soh/soh_preprocessed_train.csv
    processed/soh/soh_preprocessed_test.csv
    processed/soh/soh_train_metadata.csv
    processed/soh/soh_test_metadata.csv
    processed/soh/soh_feature_names.csv
    processed/soh/soh_preprocessor.joblib

Important:
- Splits data by battery, NOT by individual rows.
- Does not invent physical measurements.
- Missing NASA-specific features in Oxford/CALCE are handled
  through training-set imputation.
- Missingness indicators are retained.
- SOH_percent is the prediction target.
"""

from pathlib import Path
import sys
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================================
# CONFIGURATION
# ============================================================================

RANDOM_STATE = 42
TEST_SIZE = 0.20

PROJECT_DIR = Path(__file__).resolve().parents[1]
SOH_DIR = PROJECT_DIR / "processed" / "soh"

INPUT_FILE = SOH_DIR / "combined_soh_dataset.csv"

TRAIN_OUTPUT = SOH_DIR / "soh_preprocessed_train.csv"
TEST_OUTPUT = SOH_DIR / "soh_preprocessed_test.csv"

TRAIN_METADATA_OUTPUT = SOH_DIR / "soh_train_metadata.csv"
TEST_METADATA_OUTPUT = SOH_DIR / "soh_test_metadata.csv"

FEATURE_NAMES_OUTPUT = SOH_DIR / "soh_feature_names.csv"
PREPROCESSOR_OUTPUT = SOH_DIR / "soh_preprocessor.joblib"


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_subheader(title):
    print()
    print("-" * 70)
    print(title)
    print("-" * 70)


def fail(message):
    print()
    print("[ERROR]")
    print(message)
    print()
    sys.exit(1)


# ============================================================================
# REQUIRED SCHEMA
# ============================================================================

REQUIRED_COLUMNS = [
    "Source_Dataset",
    "Battery_ID",
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


FEATURE_COLUMNS = [
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


# ============================================================================
# MAIN
# ============================================================================

def main():

    warnings.filterwarnings(
        "ignore",
        category=FutureWarning,
    )

    print_header("SOH MODEL PREPROCESSING")

    print("Project directory:")
    print(f"  {PROJECT_DIR}")

    print()
    print("SOH directory:")
    print(f"  {SOH_DIR}")

    print()
    print("Input:")
    print(f"  {INPUT_FILE}")

    print()
    print("Outputs:")
    print(f"  {TRAIN_OUTPUT}")
    print(f"  {TEST_OUTPUT}")
    print(f"  {TRAIN_METADATA_OUTPUT}")
    print(f"  {TEST_METADATA_OUTPUT}")
    print(f"  {FEATURE_NAMES_OUTPUT}")
    print(f"  {PREPROCESSOR_OUTPUT}")

    # ========================================================================
    # CHECK INPUT
    # ========================================================================

    print_header("CHECKING INPUT DATASET")

    if not INPUT_FILE.exists():
        fail(
            "Combined SOH dataset was not found:\n"
            f"  {INPUT_FILE}\n\n"
            "Run prepare_combined_soh_dataset.py first."
        )

    print("[FOUND]")
    print(f"  {INPUT_FILE}")

    # ========================================================================
    # LOAD DATA
    # ========================================================================

    print_header("LOADING COMBINED SOH DATASET")

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows loaded   : {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    print()
    print("Columns:")

    for column in df.columns:
        print(f"  {column}")

    # ========================================================================
    # SCHEMA VALIDATION
    # ========================================================================

    print_header("VALIDATING INPUT SCHEMA")

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        fail(
            "Required columns are missing:\n"
            + "\n".join(f"  - {column}" for column in missing_columns)
        )

    print("[PASS] All required columns present.")

    # ========================================================================
    # DATASET SUMMARY
    # ========================================================================

    print_header("INPUT DATASET SUMMARY")

    print(f"Rows           : {len(df)}")
    print(f"Datasets       : {df['Source_Dataset'].nunique()}")
    print(f"Batteries      : {df['Battery_ID'].nunique()}")
    print(
        f"SOH minimum    : {df['SOH_percent'].min():.6f}%"
    )
    print(
        f"SOH maximum    : {df['SOH_percent'].max():.6f}%"
    )
    print(
        f"SOH mean       : {df['SOH_percent'].mean():.6f}%"
    )

    print()
    print("Rows by dataset:")

    dataset_counts = df["Source_Dataset"].value_counts().sort_index()

    for dataset, count in dataset_counts.items():
        print(f"  {dataset:<12} {count:>6} rows")

    # ========================================================================
    # NUMERIC CONVERSION
    # ========================================================================

    print_header("CONVERTING NUMERIC FEATURES")

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
        "SOH_percent",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    print("Numeric conversion complete.")

    # ========================================================================
    # BASIC VALIDATION
    # ========================================================================

    print_header("BASIC DATA VALIDATION")

    missing_required = df[
        [
            "Source_Dataset",
            "Battery_ID",
            "Cycle",
            "Capacity_Ah",
            "SOH_percent",
        ]
    ].isna().sum()

    print("Required-field missing values:")

    required_missing_total = 0

    for column, count in missing_required.items():

        print(f"  {column:<20} {count}")

        required_missing_total += int(count)

    if required_missing_total > 0:
        fail(
            "Required fields contain missing values.\n"
            "The combined dataset should be corrected before preprocessing."
        )

    print()
    print("[PASS] No missing required fields.")

    # ========================================================================
    # SOH VALIDATION
    # ========================================================================

    print_header("SOH TARGET VALIDATION")

    invalid_soh = (
        (df["SOH_percent"] <= 0)
        | (df["SOH_percent"] > 100)
        | (~np.isfinite(df["SOH_percent"]))
    )

    invalid_soh_count = int(invalid_soh.sum())

    print(f"Invalid SOH records: {invalid_soh_count}")

    if invalid_soh_count > 0:

        print()
        print("Examples:")

        print(
            df.loc[
                invalid_soh,
                [
                    "Source_Dataset",
                    "Battery_ID",
                    "Cycle",
                    "SOH_percent",
                ],
            ].head(10).to_string(index=False)
        )

        fail("Invalid SOH values detected.")

    print("[PASS] All SOH values are within 0-100%.")

    # ========================================================================
    # CAPACITY VALIDATION
    # ========================================================================

    print_header("CAPACITY VALIDATION")

    invalid_capacity = (
        (df["Capacity_Ah"] <= 0)
        | (~np.isfinite(df["Capacity_Ah"]))
    )

    invalid_capacity_count = int(
        invalid_capacity.sum()
    )

    print(
        f"Invalid capacity records: "
        f"{invalid_capacity_count}"
    )

    if invalid_capacity_count > 0:
        fail(
            "Non-positive or invalid Capacity_Ah values detected."
        )

    print("[PASS] All capacities are positive.")

    # ========================================================================
    # DUPLICATE VALIDATION
    # ========================================================================

    print_header("DUPLICATE VALIDATION")

    exact_duplicates = int(
        df.duplicated().sum()
    )

    battery_cycle_duplicates = int(
        df.duplicated(
            subset=[
                "Source_Dataset",
                "Battery_ID",
                "Cycle",
            ]
        ).sum()
    )

    print(
        f"Exact duplicate rows: "
        f"{exact_duplicates}"
    )

    print(
        "Duplicate "
        "Source_Dataset + Battery_ID + Cycle rows: "
        f"{battery_cycle_duplicates}"
    )

    if exact_duplicates > 0:
        fail(
            "Exact duplicate rows detected."
        )

    if battery_cycle_duplicates > 0:
        fail(
            "Duplicate dataset/battery/cycle records detected."
        )

    print("[PASS] No duplicates.")

    # ========================================================================
    # BATTERY SUMMARY
    # ========================================================================

    print_header("BATTERY SUMMARY")

    battery_summary = (
        df.groupby(
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        )["SOH_percent"]
        .agg(
            [
                "count",
                "min",
                "max",
                "mean",
            ]
        )
    )

    print(
        battery_summary.to_string()
    )

    # ========================================================================
    # SORT
    # ========================================================================

    print_header("SORTING DATA")

    df = df.sort_values(
        by=[
            "Source_Dataset",
            "Battery_ID",
            "Cycle",
        ]
    ).reset_index(drop=True)

    print(
        "Dataset sorted by Source_Dataset, "
        "Battery_ID and Cycle."
    )

    # ========================================================================
    # GROUP-BASED TRAIN/TEST SPLIT
    # ========================================================================

    print_header("CREATING BATTERY-LEVEL TRAIN/TEST SPLIT")

    print(
        "Important:"
    )

    print(
        "Rows from the same battery must not appear "
        "in both training and testing data."
    )

    print(
        "Therefore the split is performed using Battery_ID "
        "within each source dataset."
    )

    # ------------------------------------------------------------------------
    # Create globally unique battery group
    #
    # Battery_ID values such as B0005, Cell1 and CS2_35 are unique in
    # their datasets, but prefixing with Source_Dataset makes the grouping
    # explicit and prevents accidental collisions.
    # ------------------------------------------------------------------------

    df["_Battery_Group"] = (
        df["Source_Dataset"].astype(str)
        + "__"
        + df["Battery_ID"].astype(str)
    )

    unique_groups = (
        df["_Battery_Group"]
        .drop_duplicates()
        .tolist()
    )

    print()
    print(
        f"Total battery groups: "
        f"{len(unique_groups)}"
    )

    if len(unique_groups) < 2:
        fail(
            "At least two battery groups are required "
            "for a train/test split."
        )

    # ------------------------------------------------------------------------
    # GroupShuffleSplit
    # ------------------------------------------------------------------------

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    train_indices, test_indices = next(
        splitter.split(
            df,
            groups=df["_Battery_Group"],
        )
    )

    train_df = df.iloc[
        train_indices
    ].copy()

    test_df = df.iloc[
        test_indices
    ].copy()

    # ========================================================================
    # SPLIT SUMMARY
    # ========================================================================

    print_subheader("SPLIT RESULT")

    print(
        f"Training rows : {len(train_df)}"
    )

    print(
        f"Testing rows  : {len(test_df)}"
    )

    print(
        f"Training percentage: "
        f"{len(train_df) / len(df) * 100:.2f}%"
    )

    print(
        f"Testing percentage : "
        f"{len(test_df) / len(df) * 100:.2f}%"
    )

    train_groups = set(
        train_df["_Battery_Group"]
    )

    test_groups = set(
        test_df["_Battery_Group"]
    )

    overlap = train_groups.intersection(
        test_groups
    )

    print()
    print(
        f"Training battery groups: "
        f"{len(train_groups)}"
    )

    print(
        f"Testing battery groups : "
        f"{len(test_groups)}"
    )

    print(
        f"Battery groups in both sets: "
        f"{len(overlap)}"
    )

    if overlap:
        fail(
            "Battery leakage detected. "
            "Some batteries occur in both train and test."
        )

    print(
        "[PASS] No battery-level leakage."
    )

    # ========================================================================
    # TRAIN / TEST BATTERY LISTS
    # ========================================================================

    print_subheader("TRAINING BATTERIES")

    train_batteries = (
        train_df[
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        )
    )

    for _, row in train_batteries.iterrows():

        print(
            f"  {row['Source_Dataset']:<10} "
            f"{row['Battery_ID']}"
        )

    print_subheader("TESTING BATTERIES")

    test_batteries = (
        test_df[
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        )
    )

    for _, row in test_batteries.iterrows():

        print(
            f"  {row['Source_Dataset']:<10} "
            f"{row['Battery_ID']}"
        )

    # ========================================================================
    # FEATURE / TARGET SEPARATION
    # ========================================================================

    print_header("SEPARATING FEATURES AND TARGET")

    missing_feature_columns = [
        column
        for column in FEATURE_COLUMNS
        if column not in df.columns
    ]

    if missing_feature_columns:
        fail(
            "Expected feature columns are missing:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing_feature_columns
            )
        )

    X_train = train_df[
        FEATURE_COLUMNS
    ].copy()

    X_test = test_df[
        FEATURE_COLUMNS
    ].copy()

    y_train = train_df[
        "SOH_percent"
    ].copy()

    y_test = test_df[
        "SOH_percent"
    ].copy()

    print(
        f"Feature columns: {len(FEATURE_COLUMNS)}"
    )

    print()
    print("Features:")

    for feature in FEATURE_COLUMNS:
        print(f"  {feature}")

    print()
    print(
        "Target: SOH_percent"
    )

    # ========================================================================
    # MISSING VALUE ANALYSIS
    # ========================================================================

    print_header("MISSING FEATURE ANALYSIS")

    train_missing = X_train.isna().sum()
    test_missing = X_test.isna().sum()

    print(
        "Training missing values:"
    )

    for column in FEATURE_COLUMNS:

        count = int(
            train_missing[column]
        )

        percentage = (
            count / len(X_train) * 100
        )

        print(
            f"  {column:<25} "
            f"{count:>5} "
            f"({percentage:>6.2f}%)"
        )

    print()
    print(
        "Testing missing values:"
    )

    for column in FEATURE_COLUMNS:

        count = int(
            test_missing[column]
        )

        percentage = (
            count / len(X_test) * 100
        )

        print(
            f"  {column:<25} "
            f"{count:>5} "
            f"({percentage:>6.2f}%)"
        )

    print()
    print(
        "Missing values are expected for NASA-specific "
        "features in Oxford/CALCE records."
    )

    print(
        "They will be handled by the preprocessing pipeline."
    )

    # ========================================================================
    # BUILD PREPROCESSOR
    # ========================================================================

    print_header("BUILDING PREPROCESSING PIPELINE")

    print(
        "Numerical preprocessing:"
    )

    print(
        "  1. Median imputation"
    )

    print(
        "  2. Missing-value indicators"
    )

    print(
        "  3. Standard scaling"
    )

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=True,
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                FEATURE_COLUMNS,
            )
        ],
        remainder="drop",
    )

    # ========================================================================
    # FIT ONLY ON TRAINING DATA
    # ========================================================================

    print_header(
        "FITTING PREPROCESSOR ON TRAINING DATA ONLY"
    )

    print(
        "The preprocessing pipeline is fitted ONLY "
        "using the training set."
    )

    print(
        "The test set is transformed afterward."
    )

    print(
        "This prevents preprocessing leakage."
    )

    X_train_processed = preprocessor.fit_transform(
        X_train
    )

    X_test_processed = preprocessor.transform(
        X_test
    )

    # Convert sparse matrix if necessary
    if hasattr(
        X_train_processed,
        "toarray",
    ):
        X_train_processed = (
            X_train_processed.toarray()
        )

    if hasattr(
        X_test_processed,
        "toarray",
    ):
        X_test_processed = (
            X_test_processed.toarray()
        )

    X_train_processed = np.asarray(
        X_train_processed
    )

    X_test_processed = np.asarray(
        X_test_processed
    )

    print(
        "Preprocessing complete."
    )

    print()
    print(
        f"Processed training shape: "
        f"{X_train_processed.shape}"
    )

    print(
        f"Processed testing shape : "
        f"{X_test_processed.shape}"
    )

    # ========================================================================
    # GET PROCESSED FEATURE NAMES
    # ========================================================================

    print_header("GENERATING PROCESSED FEATURE NAMES")

    try:

        processed_feature_names = (
            preprocessor.get_feature_names_out()
        )

        processed_feature_names = [
            str(name)
            for name in processed_feature_names
        ]

    except Exception:

        # Fallback if older sklearn version
        processed_feature_names = []

        for feature in FEATURE_COLUMNS:
            processed_feature_names.append(
                f"numeric__{feature}"
            )

        # Missing indicator names
        for feature in FEATURE_COLUMNS:

            if (
                train_missing[feature] > 0
            ):
                processed_feature_names.append(
                    f"numeric__missingindicator_{feature}"
                )

    print(
        f"Processed feature count: "
        f"{len(processed_feature_names)}"
    )

    print()
    print(
        "Processed features:"
    )

    for index, feature in enumerate(
        processed_feature_names,
        start=1,
    ):

        print(
            f"  {index:>3}. {feature}"
        )

    # ========================================================================
    # BUILD OUTPUT DATAFRAMES
    # ========================================================================

    print_header(
        "CREATING MODEL-READY DATASETS"
    )

    train_processed_df = pd.DataFrame(
        X_train_processed,
        columns=processed_feature_names,
    )

    test_processed_df = pd.DataFrame(
        X_test_processed,
        columns=processed_feature_names,
    )

    train_processed_df[
        "SOH_percent"
    ] = y_train.to_numpy()

    test_processed_df[
        "SOH_percent"
    ] = y_test.to_numpy()

    print(
        f"Training output shape: "
        f"{train_processed_df.shape}"
    )

    print(
        f"Testing output shape : "
        f"{test_processed_df.shape}"
    )

    # ========================================================================
    # METADATA
    # ========================================================================

    print_header("CREATING METADATA")

    metadata_columns = [
        "Source_Dataset",
        "Battery_ID",
        "Cycle",
        "Capacity_Ah",
        "SOH_percent",
    ]

    train_metadata = train_df[
        metadata_columns
    ].copy()

    test_metadata = test_df[
        metadata_columns
    ].copy()

    print(
        "Metadata retained separately "
        "for traceability."
    )

    # ========================================================================
    # FEATURE NAMES TABLE
    # ========================================================================

    feature_names_df = pd.DataFrame(
        {
            "Feature_Index": range(
                1,
                len(
                    processed_feature_names
                ) + 1,
            ),
            "Feature_Name":
                processed_feature_names,
        }
    )

    # ========================================================================
    # OUTPUT DIRECTORY
    # ========================================================================

    SOH_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================================
    # SAVE TRAINING DATA
    # ========================================================================

    print_header(
        "SAVING PREPROCESSED TRAINING DATA"
    )

    train_processed_df.to_csv(
        TRAIN_OUTPUT,
        index=False,
    )

    print(
        f"Saved:\n  {TRAIN_OUTPUT}"
    )

    # ========================================================================
    # SAVE TEST DATA
    # ========================================================================

    print_header(
        "SAVING PREPROCESSED TEST DATA"
    )

    test_processed_df.to_csv(
        TEST_OUTPUT,
        index=False,
    )

    print(
        f"Saved:\n  {TEST_OUTPUT}"
    )

    # ========================================================================
    # SAVE METADATA
    # ========================================================================

    print_header(
        "SAVING METADATA"
    )

    train_metadata.to_csv(
        TRAIN_METADATA_OUTPUT,
        index=False,
    )

    test_metadata.to_csv(
        TEST_METADATA_OUTPUT,
        index=False,
    )

    print(
        f"Training metadata:\n"
        f"  {TRAIN_METADATA_OUTPUT}"
    )

    print(
        f"Testing metadata:\n"
        f"  {TEST_METADATA_OUTPUT}"
    )

    # ========================================================================
    # SAVE FEATURE NAMES
    # ========================================================================

    print_header(
        "SAVING FEATURE NAME MAPPING"
    )

    feature_names_df.to_csv(
        FEATURE_NAMES_OUTPUT,
        index=False,
    )

    print(
        f"Saved:\n  {FEATURE_NAMES_OUTPUT}"
    )

    # ========================================================================
    # SAVE PREPROCESSOR
    # ========================================================================

    print_header(
        "SAVING PREPROCESSING PIPELINE"
    )

    joblib.dump(
        preprocessor,
        PREPROCESSOR_OUTPUT,
    )

    print(
        f"Saved:\n  {PREPROCESSOR_OUTPUT}"
    )

    # ========================================================================
    # VERIFY SAVED FILES
    # ========================================================================

    print_header(
        "VERIFYING SAVED FILES"
    )

    output_files = [
        TRAIN_OUTPUT,
        TEST_OUTPUT,
        TRAIN_METADATA_OUTPUT,
        TEST_METADATA_OUTPUT,
        FEATURE_NAMES_OUTPUT,
        PREPROCESSOR_OUTPUT,
    ]

    for output_file in output_files:

        if output_file.exists():

            size_kb = (
                output_file.stat().st_size
                / 1024
            )

            print(
                f"[PASS] "
                f"{output_file.name:<40} "
                f"{size_kb:>10.2f} KB"
            )

        else:

            print(
                f"[FAIL] "
                f"{output_file.name}"
            )

            fail(
                "One or more output files were not created."
            )

    # ========================================================================
    # RELOAD CSV FILES
    # ========================================================================

    print_header(
        "RELOADING SAVED DATASETS"
    )

    saved_train = pd.read_csv(
        TRAIN_OUTPUT
    )

    saved_test = pd.read_csv(
        TEST_OUTPUT
    )

    saved_train_metadata = pd.read_csv(
        TRAIN_METADATA_OUTPUT
    )

    saved_test_metadata = pd.read_csv(
        TEST_METADATA_OUTPUT
    )

    print(
        f"Saved training rows: "
        f"{len(saved_train)}"
    )

    print(
        f"Saved testing rows : "
        f"{len(saved_test)}"
    )

    print(
        f"Saved training metadata rows: "
        f"{len(saved_train_metadata)}"
    )

    print(
        f"Saved testing metadata rows: "
        f"{len(saved_test_metadata)}"
    )

    # ========================================================================
    # FINAL VALIDATION
    # ========================================================================

    print_header(
        "FINAL PREPROCESSING VALIDATION"
    )

    validation_passed = True

    # ------------------------------------------------------------------------
    # Row preservation
    # ------------------------------------------------------------------------

    expected_train_rows = len(train_df)
    expected_test_rows = len(test_df)

    if len(saved_train) != expected_train_rows:

        print(
            "[FAIL] Training row count changed."
        )

        validation_passed = False

    else:

        print(
            "[PASS] Training row count preserved."
        )

    if len(saved_test) != expected_test_rows:

        print(
            "[FAIL] Testing row count changed."
        )

        validation_passed = False

    else:

        print(
            "[PASS] Testing row count preserved."
        )

    # ------------------------------------------------------------------------
    # Target validation
    # ------------------------------------------------------------------------

    train_target_invalid = (
        saved_train["SOH_percent"].isna().sum()
        > 0
        or
        (saved_train["SOH_percent"] <= 0).any()
        or
        (saved_train["SOH_percent"] > 100).any()
    )

    test_target_invalid = (
        saved_test["SOH_percent"].isna().sum()
        > 0
        or
        (saved_test["SOH_percent"] <= 0).any()
        or
        (saved_test["SOH_percent"] > 100).any()
    )

    if train_target_invalid:

        print(
            "[FAIL] Invalid training SOH target."
        )

        validation_passed = False

    else:

        print(
            "[PASS] Training SOH target valid."
        )

    if test_target_invalid:

        print(
            "[FAIL] Invalid testing SOH target."
        )

        validation_passed = False

    else:

        print(
            "[PASS] Testing SOH target valid."
        )

    # ------------------------------------------------------------------------
    # NaN validation
    # ------------------------------------------------------------------------

    train_feature_columns = [
        column
        for column in saved_train.columns
        if column != "SOH_percent"
    ]

    test_feature_columns = [
        column
        for column in saved_test.columns
        if column != "SOH_percent"
    ]

    train_nan_count = int(
        saved_train[
            train_feature_columns
        ].isna().sum().sum()
    )

    test_nan_count = int(
        saved_test[
            test_feature_columns
        ].isna().sum().sum()
    )

    if train_nan_count > 0:

        print(
            "[FAIL] NaN values remain "
            "in training features."
        )

        validation_passed = False

    else:

        print(
            "[PASS] No NaN values in training features."
        )

    if test_nan_count > 0:

        print(
            "[FAIL] NaN values remain "
            "in testing features."
        )

        validation_passed = False

    else:

        print(
            "[PASS] No NaN values in testing features."
        )

    # ------------------------------------------------------------------------
    # Infinite values
    # ------------------------------------------------------------------------

    train_numeric = saved_train[
        train_feature_columns
    ].to_numpy()

    test_numeric = saved_test[
        test_feature_columns
    ].to_numpy()

    train_inf = int(
        np.isinf(train_numeric).sum()
    )

    test_inf = int(
        np.isinf(test_numeric).sum()
    )

    if train_inf > 0:

        print(
            "[FAIL] Infinite training feature values."
        )

        validation_passed = False

    else:

        print(
            "[PASS] No infinite training values."
        )

    if test_inf > 0:

        print(
            "[FAIL] Infinite testing feature values."
        )

        validation_passed = False

    else:

        print(
            "[PASS] No infinite testing values."
        )

    # ------------------------------------------------------------------------
    # Battery leakage
    # ------------------------------------------------------------------------

    train_meta_groups = set(
        train_metadata.apply(
            lambda row:
            f"{row['Source_Dataset']}__"
            f"{row['Battery_ID']}",
            axis=1,
        )
    )

    test_meta_groups = set(
        test_metadata.apply(
            lambda row:
            f"{row['Source_Dataset']}__"
            f"{row['Battery_ID']}",
            axis=1,
        )
    )

    metadata_overlap = (
        train_meta_groups
        .intersection(
            test_meta_groups
        )
    )

    if metadata_overlap:

        print(
            "[FAIL] Battery leakage found "
            "between train/test."
        )

        validation_passed = False

    else:

        print(
            "[PASS] No battery leakage."
        )

    # ------------------------------------------------------------------------
    # Metadata row preservation
    # ------------------------------------------------------------------------

    if (
        len(saved_train_metadata)
        != len(saved_train)
    ):

        print(
            "[FAIL] Training metadata row count mismatch."
        )

        validation_passed = False

    else:

        print(
            "[PASS] Training metadata aligned."
        )

    if (
        len(saved_test_metadata)
        != len(saved_test)
    ):

        print(
            "[FAIL] Testing metadata row count mismatch."
        )

        validation_passed = False

    else:

        print(
            "[PASS] Testing metadata aligned."
        )

    # ========================================================================
    # FINAL STATISTICS
    # ========================================================================

    print_header(
        "PREPROCESSED DATASET SUMMARY"
    )

    print(
        f"Training rows      : {len(saved_train)}"
    )

    print(
        f"Testing rows       : {len(saved_test)}"
    )

    print(
        f"Processed features : "
        f"{len(train_feature_columns)}"
    )

    print(
        f"Training batteries : "
        f"{len(train_meta_groups)}"
    )

    print(
        f"Testing batteries  : "
        f"{len(test_meta_groups)}"
    )

    print()
    print(
        f"Training SOH range : "
        f"{saved_train['SOH_percent'].min():.6f}% "
        f"- "
        f"{saved_train['SOH_percent'].max():.6f}%"
    )

    print(
        f"Testing SOH range  : "
        f"{saved_test['SOH_percent'].min():.6f}% "
        f"- "
        f"{saved_test['SOH_percent'].max():.6f}%"
    )

    # ========================================================================
    # FINAL RESULT
    # ========================================================================

    if not validation_passed:

        print_header(
            "PREPROCESSING FAILED"
        )

        raise RuntimeError(
            "Final preprocessing validation failed. "
            "Do not proceed to ML training."
        )

    print_header(
        "SOH PREPROCESSING COMPLETE"
    )

    print(
        "All preprocessing and validation checks passed."
    )

    print()
    print(
        "Training dataset:"
    )

    print(
        f"  {TRAIN_OUTPUT}"
    )

    print()
    print(
        "Testing dataset:"
    )

    print(
        f"  {TEST_OUTPUT}"
    )

    print()
    print(
        "Training metadata:"
    )

    print(
        f"  {TRAIN_METADATA_OUTPUT}"
    )

    print()
    print(
        "Testing metadata:"
    )

    print(
        f"  {TEST_METADATA_OUTPUT}"
    )

    print()
    print(
        "Feature names:"
    )

    print(
        f"  {FEATURE_NAMES_OUTPUT}"
    )

    print()
    print(
        "Preprocessor:"
    )

    print(
        f"  {PREPROCESSOR_OUTPUT}"
    )

    print()
    print(
        "The SOH data is ready for the model-training stage."
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()