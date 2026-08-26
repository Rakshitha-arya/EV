from pathlib import Path
import pandas as pd
import numpy as np


# ======================================================================
# CONFIGURATION
# ======================================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
SOH_DIR = PROJECT_DIR / "processed" / "soh"

NASA_FILE = SOH_DIR / "nasa_soh_training.csv"
OXFORD_FILE = SOH_DIR / "oxford_soh_features.csv"
CALCE_FILE = SOH_DIR / "calce_soh_features.csv"

OUTPUT_FILE = SOH_DIR / "combined_soh_dataset.csv"


# ======================================================================
# COMMON FEATURE SCHEMA
# ======================================================================

COMMON_COLUMNS = [
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


NASA_FEATURE_COLUMNS = [
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


# ======================================================================
# UTILITY FUNCTIONS
# ======================================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def check_file(path, name):
    if path.exists():
        print(f"[FOUND] {name}")
        print(f"        {path}")
        return True

    print(f"[MISSING] {name}")
    print(f"          {path}")
    return False


def convert_numeric_columns(df):
    numeric_columns = [
        "Cycle",
        "Capacity_Ah",
        "Capacity_mAh",
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
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def validate_required_columns(df, dataset_name):
    required = [
        "Battery_ID",
        "Cycle",
        "SOH_percent",
    ]

    if "Capacity_Ah" not in df.columns and "Capacity_mAh" not in df.columns:
        raise ValueError(
            f"{dataset_name}: Capacity_Ah or Capacity_mAh is required."
        )

    for column in required:
        if column not in df.columns:
            raise ValueError(
                f"{dataset_name}: required column missing: {column}"
            )


def standardize_capacity(df, dataset_name):
    """
    Creates Capacity_Ah consistently.

    NASA:
        Capacity_Ah already exists.

    Oxford:
        Capacity_mAh -> Capacity_Ah.

    CALCE:
        Capacity_Ah already exists.
    """

    if "Capacity_Ah" in df.columns:
        df["Capacity_Ah"] = pd.to_numeric(
            df["Capacity_Ah"],
            errors="coerce"
        )

    elif "Capacity_mAh" in df.columns:
        df["Capacity_mAh"] = pd.to_numeric(
            df["Capacity_mAh"],
            errors="coerce"
        )

        df["Capacity_Ah"] = (
            df["Capacity_mAh"] / 1000.0
        )

    else:
        raise ValueError(
            f"{dataset_name}: capacity column not available."
        )

    return df


def align_feature_columns(df, dataset_name):
    """
    Adds feature columns that are unavailable in a dataset as NaN.

    These NaNs are intentional and must not be replaced by
    artificial measurements.
    """

    for column in NASA_FEATURE_COLUMNS:
        if column not in df.columns:
            df[column] = np.nan

            print(
                f"{dataset_name}: added missing feature "
                f"'{column}' as NaN"
            )

    return df


def prepare_dataset(df, dataset_name):
    df = df.copy()

    # Dataset identifier
    df["Source_Dataset"] = dataset_name

    # Numeric conversion
    df = convert_numeric_columns(df)

    # Required fields
    validate_required_columns(
        df,
        dataset_name
    )

    # Capacity
    df = standardize_capacity(
        df,
        dataset_name
    )

    # Add common missing features
    df = align_feature_columns(
        df,
        dataset_name
    )

    # Ensure SOH numeric
    df["SOH_percent"] = pd.to_numeric(
        df["SOH_percent"],
        errors="coerce"
    )

    # Ensure Cycle numeric
    df["Cycle"] = pd.to_numeric(
        df["Cycle"],
        errors="coerce"
    )

    # Battery ID string
    df["Battery_ID"] = (
        df["Battery_ID"]
        .astype(str)
        .str.strip()
    )

    # Select common columns
    df = df[COMMON_COLUMNS].copy()

    return df


# ======================================================================
# MAIN
# ======================================================================

def main():

    print_header(
        "COMBINED SOH DATASET PREPARATION"
    )

    print("Project directory:")
    print(f"  {PROJECT_DIR}")

    print()
    print("SOH directory:")
    print(f"  {SOH_DIR}")

    print()
    print("Input files:")
    print(f"  NASA   : {NASA_FILE}")
    print(f"  Oxford : {OXFORD_FILE}")
    print(f"  CALCE  : {CALCE_FILE}")

    print()
    print("Output:")
    print(f"  {OUTPUT_FILE}")

    # ==================================================================
    # CHECK INPUT FILES
    # ==================================================================

    print_header("CHECKING INPUT FILES")

    files_ok = True

    if not check_file(NASA_FILE, "NASA"):
        files_ok = False

    if not check_file(OXFORD_FILE, "OXFORD"):
        files_ok = False

    if not check_file(CALCE_FILE, "CALCE"):
        files_ok = False

    if not files_ok:
        raise FileNotFoundError(
            "One or more required input files are missing."
        )

    # ==================================================================
    # LOAD NASA
    # ==================================================================

    print_header(
        "LOADING NASA TRAINING DATASET"
    )

    nasa = pd.read_csv(NASA_FILE)

    print()
    print("NASA")
    print("-" * 70)
    print(f"Rows       : {len(nasa)}")
    print(
        f"Columns    : {len(nasa.columns)}"
    )
    print(
        f"Batteries  : {nasa['Battery_ID'].nunique()}"
    )

    nasa["SOH_percent"] = pd.to_numeric(
        nasa["SOH_percent"],
        errors="coerce"
    )

    print(
        f"SOH range  : "
        f"{nasa['SOH_percent'].min():.6f}% - "
        f"{nasa['SOH_percent'].max():.6f}%"
    )

    print()
    print("NASA columns:")

    for column in nasa.columns:
        print(f"  {column}")

    # ==================================================================
    # LOAD OXFORD
    # ==================================================================

    print_header(
        "LOADING OXFORD DATASET"
    )

    oxford = pd.read_csv(OXFORD_FILE)

    print()
    print("OXFORD")
    print("-" * 70)
    print(f"Rows       : {len(oxford)}")
    print(
        f"Columns    : {len(oxford.columns)}"
    )
    print(
        f"Batteries  : {oxford['Battery_ID'].nunique()}"
    )

    oxford["SOH_percent"] = pd.to_numeric(
        oxford["SOH_percent"],
        errors="coerce"
    )

    print(
        f"SOH range  : "
        f"{oxford['SOH_percent'].min():.6f}% - "
        f"{oxford['SOH_percent'].max():.6f}%"
    )

    print()
    print("Oxford columns:")

    for column in oxford.columns:
        print(f"  {column}")

    # ==================================================================
    # LOAD CALCE
    # ==================================================================

    print_header(
        "LOADING CALCE DATASET"
    )

    calce = pd.read_csv(CALCE_FILE)

    print()
    print("CALCE")
    print("-" * 70)
    print(f"Rows       : {len(calce)}")
    print(
        f"Columns    : {len(calce.columns)}"
    )
    print(
        f"Batteries  : {calce['Battery_ID'].nunique()}"
    )

    calce["SOH_percent"] = pd.to_numeric(
        calce["SOH_percent"],
        errors="coerce"
    )

    print(
        f"SOH range  : "
        f"{calce['SOH_percent'].min():.6f}% - "
        f"{calce['SOH_percent'].max():.6f}%"
    )

    print()
    print("CALCE columns:")

    for column in calce.columns:
        print(f"  {column}")

    # ==================================================================
    # STANDARDIZE DATASET IDENTIFIERS
    # ==================================================================

    print_header(
        "STANDARDIZING DATASET IDENTIFIERS"
    )

    print("Source_Dataset assigned:")
    print("  NASA   -> NASA")
    print("  Oxford -> Oxford")
    print("  CALCE  -> CALCE")

    # ==================================================================
    # CHECK REQUIRED COLUMNS
    # ==================================================================

    print_header(
        "CHECKING REQUIRED COLUMNS"
    )

    for dataset_name, df in [
        ("NASA", nasa),
        ("Oxford", oxford),
        ("CALCE", calce),
    ]:

        print()
        print(f"{dataset_name}:")

        try:
            validate_required_columns(
                df,
                dataset_name
            )

            print("  [OK] Battery_ID")
            print("  [OK] Cycle")
            print("  [OK] SOH_percent")

            if "Capacity_Ah" in df.columns:
                print("  [OK] Capacity_Ah")
            elif "Capacity_mAh" in df.columns:
                print("  [OK] Capacity_mAh")

        except ValueError as exc:
            print(f"  [FAIL] {exc}")
            raise

    # ==================================================================
    # CONVERT NUMERIC COLUMNS
    # ==================================================================

    print_header(
        "CONVERTING NUMERIC COLUMNS"
    )

    nasa = convert_numeric_columns(nasa)
    oxford = convert_numeric_columns(oxford)
    calce = convert_numeric_columns(calce)

    print("Numeric conversion complete.")

    # ==================================================================
    # CREATE COMMON FEATURE SCHEMA
    # ==================================================================

    print_header(
        "CREATING COMMON FEATURE SCHEMA"
    )

    nasa = prepare_dataset(
        nasa,
        "NASA"
    )

    oxford = prepare_dataset(
        oxford,
        "Oxford"
    )

    calce = prepare_dataset(
        calce,
        "CALCE"
    )

    # ==================================================================
    # CAPACITY STANDARDIZATION
    # ==================================================================

    print_header(
        "STANDARDIZING CAPACITY"
    )

    print(
        "NASA capacity is already in Ah."
    )

    print(
        "Oxford Capacity_mAh is converted to Capacity_Ah."
    )

    print(
        "CALCE capacity is already in Ah."
    )

    print()
    print("Capacity standardization complete.")

    # ==================================================================
    # ALIGN COMMON FEATURE COLUMNS
    # ==================================================================

    print_header(
        "ALIGNING COMMON FEATURE COLUMNS"
    )

    # Already handled by prepare_dataset.
    # Print confirmation for every feature.

    print()
    print(
        "All datasets now contain the same "
        "common feature schema."
    )

    # ==================================================================
    # SELECT COMMON COLUMNS
    # ==================================================================

    print_header(
        "SELECTING COMMON COLUMNS"
    )

    nasa = nasa[COMMON_COLUMNS].copy()
    oxford = oxford[COMMON_COLUMNS].copy()
    calce = calce[COMMON_COLUMNS].copy()

    print(
        f"NASA columns after alignment   : "
        f"{len(nasa.columns)}"
    )

    print(
        f"Oxford columns after alignment : "
        f"{len(oxford.columns)}"
    )

    print(
        f"CALCE columns after alignment  : "
        f"{len(calce.columns)}"
    )

    # ==================================================================
    # COMBINE
    # ==================================================================

    print_header(
        "COMBINING DATASETS"
    )

    nasa_rows = len(nasa)
    oxford_rows = len(oxford)
    calce_rows = len(calce)

    combined = pd.concat(
        [
            nasa,
            oxford,
            calce,
        ],
        ignore_index=True
    )

    print(
        "Datasets combined successfully."
    )

    print()
    print("Rows contributed:")
    print(f"  NASA   : {nasa_rows}")
    print(f"  Oxford : {oxford_rows}")
    print(f"  CALCE  : {calce_rows}")

    print()
    print(
        f"Combined rows: {len(combined)}"
    )

    # ==================================================================
    # SORT
    # ==================================================================

    print_header(
        "SORTING COMBINED DATASET"
    )

    combined = combined.sort_values(
        by=[
            "Source_Dataset",
            "Battery_ID",
            "Cycle",
        ],
        kind="stable"
    ).reset_index(drop=True)

    print("Dataset sorted by:")
    print("  Source_Dataset")
    print("  Battery_ID")
    print("  Cycle")

    # ==================================================================
    # DUPLICATE CHECK
    # ==================================================================

    print_header(
        "CHECKING DUPLICATES"
    )

    exact_duplicates = int(
        combined.duplicated().sum()
    )

    dataset_battery_cycle_duplicates = int(
        combined.duplicated(
            subset=[
                "Source_Dataset",
                "Battery_ID",
                "Cycle",
            ]
        ).sum()
    )

    print(
        "Exact duplicate rows:"
    )
    print(
        f"  {exact_duplicates}"
    )

    print(
        "Duplicate Source_Dataset + "
        "Battery_ID + Cycle rows:"
    )
    print(
        f"  {dataset_battery_cycle_duplicates}"
    )

    # ==================================================================
    # MISSING VALUES
    # ==================================================================

    print_header(
        "MISSING VALUE CHECK"
    )

    missing = combined.isna().sum()

    for column in COMMON_COLUMNS:

        count = int(missing[column])

        percentage = (
            count / len(combined) * 100
            if len(combined) > 0
            else 0
        )

        print(
            f"{column:<30}"
            f"{count:>5} "
            f"({percentage:>6.2f}%)"
        )

    print()
    print("IMPORTANT:")
    print(
        "Some missing feature values are expected "
        "because Oxford and CALCE do not provide "
        "all NASA electrical/thermal features."
    )

    print(
        "These values are retained as NaN and are "
        "NOT replaced with artificial measurements."
    )

    # ==================================================================
    # SOH VALIDATION
    # ==================================================================

    print_header(
        "SOH VALIDATION"
    )

    soh = pd.to_numeric(
        combined["SOH_percent"],
        errors="coerce"
    )

    print(
        f"SOH minimum: {soh.min():.6f}%"
    )

    print(
        f"SOH maximum: {soh.max():.6f}%"
    )

    print(
        f"SOH mean   : {soh.mean():.6f}%"
    )

    invalid_soh_mask = (
        soh.isna()
        | (soh <= 0)
        | (soh > 100)
    )

    invalid_soh_count = int(
        invalid_soh_mask.sum()
    )

    print(
        f"SOH outside expected 0-100% range: "
        f"{invalid_soh_count}"
    )

    # ==================================================================
    # CAPACITY VALIDATION
    # ==================================================================

    print_header(
        "CAPACITY VALIDATION"
    )

    capacity = pd.to_numeric(
        combined["Capacity_Ah"],
        errors="coerce"
    )

    missing_capacity = int(
        capacity.isna().sum()
    )

    nonpositive_capacity = int(
        (capacity <= 0).sum()
    )

    print(
        f"Missing Capacity_Ah: "
        f"{missing_capacity}"
    )

    print(
        f"Capacity_Ah <= 0: "
        f"{nonpositive_capacity}"
    )

    # ==================================================================
    # COMBINED DATASET SUMMARY
    # ==================================================================

    print_header(
        "COMBINED DATASET SUMMARY"
    )

    print(
        f"Total rows: {len(combined)}"
    )

    print(
        f"Total batteries: "
        f"{combined['Battery_ID'].nunique()}"
    )

    print()
    print("Rows by dataset:")

    dataset_counts = (
        combined["Source_Dataset"]
        .value_counts()
        .sort_index()
    )

    for dataset_name, count in dataset_counts.items():
        print(
            f"  {dataset_name:<12}"
            f"{count:>5} rows"
        )

    print()
    print("Batteries by dataset:")

    battery_counts = (
        combined
        .groupby("Source_Dataset")["Battery_ID"]
        .nunique()
        .sort_index()
    )

    for dataset_name, count in battery_counts.items():
        print(
            f"  {dataset_name:<12}"
            f"{count:>5} batteries"
        )

    # ==================================================================
    # BATTERY-WISE SUMMARY
    # ==================================================================

    print_header(
        "BATTERY-WISE SUMMARY"
    )

    battery_summary = (
        combined
        .groupby(
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        )["SOH_percent"]
        .agg(
            count="count",
            first_soh="first",
            last_soh="last",
            minimum_soh="min",
            maximum_soh="max",
            mean_soh="mean",
        )
    )

    print(
        battery_summary.to_string(
            float_format=lambda x: f"{x:.4f}"
        )
    )

    # ==================================================================
    # FIRST SOH VALUES
    # ==================================================================

    print_header(
        "CHECKING FIRST SOH VALUES"
    )

    first_soh = (
        combined
        .sort_values(
            [
                "Source_Dataset",
                "Battery_ID",
                "Cycle",
            ]
        )
        .groupby(
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        )["SOH_percent"]
        .first()
    )

    print(first_soh.to_string())

    first_soh_valid = bool(
        np.allclose(
            first_soh.values,
            100.0,
            atol=1e-6
        )
    )

    if first_soh_valid:
        print()
        print(
            "[PASS] All batteries/cells start "
            "at 100% SOH."
        )
    else:
        print()
        print(
            "[FAIL] One or more batteries/cells "
            "do not start at 100% SOH."
        )

    # ==================================================================
    # FEATURE AVAILABILITY
    # ==================================================================

    print_header(
        "FEATURE AVAILABILITY BY DATASET"
    )

    feature_columns = [
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

    for dataset_name in [
        "CALCE",
        "NASA",
        "Oxford",
    ]:

        dataset_df = combined[
            combined["Source_Dataset"]
            == dataset_name
        ]

        print()
        print(dataset_name)

        for feature in feature_columns:

            available = int(
                dataset_df[feature]
                .notna()
                .sum()
            )

            total = len(dataset_df)

            percentage = (
                available / total * 100
                if total > 0
                else 0
            )

            print(
                f"  {feature:<25}"
                f"{available:>4}/{total:<4} "
                f"({percentage:>6.2f}%)"
            )

    # ==================================================================
    # FINAL COLUMN ORDER
    # ==================================================================

    print_header(
        "FINAL COLUMN ORDER"
    )

    combined = combined[COMMON_COLUMNS].copy()

    for index, column in enumerate(
        combined.columns,
        start=1
    ):
        print(
            f"{index:>4}. {column}"
        )

    # ==================================================================
    # SAVE
    # ==================================================================

    print_header(
        "SAVING COMBINED DATASET"
    )

    SOH_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    combined.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "Combined SOH dataset saved successfully:"
    )

    print(
        f"  {OUTPUT_FILE}"
    )

    # ==================================================================
    # VERIFY SAVED FILE
    # ==================================================================

    print_header(
        "VERIFYING SAVED FILE"
    )

    if not OUTPUT_FILE.exists():
        raise RuntimeError(
            "Output file was not created."
        )

    saved = pd.read_csv(
        OUTPUT_FILE
    )

    saved_soh = pd.to_numeric(
        saved["SOH_percent"],
        errors="coerce"
    )

    print(
        f"Saved rows: {len(saved)}"
    )

    print(
        f"Saved columns: {len(saved.columns)}"
    )

    print(
        f"Saved batteries: "
        f"{saved['Battery_ID'].nunique()}"
    )

    print(
        f"Saved datasets: "
        f"{saved['Source_Dataset'].nunique()}"
    )

    print(
        f"Saved minimum SOH: "
        f"{saved_soh.min():.6f}%"
    )

    print(
        f"Saved maximum SOH: "
        f"{saved_soh.max():.6f}%"
    )

    print(
        f"Saved mean SOH: "
        f"{saved_soh.mean():.6f}%"
    )

    # ==================================================================
    # FINAL VALIDATION
    # ==================================================================

    print_header(
        "FINAL VALIDATION"
    )

    validation_passed = True

    # --------------------------------------------------------------
    # Row count
    # --------------------------------------------------------------

    if len(saved) == (
        nasa_rows
        + oxford_rows
        + calce_rows
    ):
        print(
            "  [PASS] Row count preserved"
        )
    else:
        print(
            "  [FAIL] Row count preserved"
        )
        validation_passed = False

    # --------------------------------------------------------------
    # Column count
    # --------------------------------------------------------------

    if list(saved.columns) == COMMON_COLUMNS:
        print(
            "  [PASS] Column count/order preserved"
        )
    else:
        print(
            "  [FAIL] Column count/order preserved"
        )
        validation_passed = False

    # --------------------------------------------------------------
    # IMPORTANT:
    # Recalculate SOH validation from SAVED DATA.
    # This fixes the previous false failure.
    # --------------------------------------------------------------

    final_soh = pd.to_numeric(
        saved["SOH_percent"],
        errors="coerce"
    )

    final_invalid_soh_mask = (
        final_soh.isna()
        | (final_soh <= 0)
        | (final_soh > 100)
    )

    final_invalid_soh_count = int(
        final_invalid_soh_mask.sum()
    )

    if final_invalid_soh_count == 0:
        print(
            "  [PASS] No invalid SOH"
        )
    else:
        print(
            f"  [FAIL] No invalid SOH "
            f"({final_invalid_soh_count} invalid rows)"
        )
        validation_passed = False

    # --------------------------------------------------------------
    # Capacity
    # --------------------------------------------------------------

    final_capacity = pd.to_numeric(
        saved["Capacity_Ah"],
        errors="coerce"
    )

    final_invalid_capacity_count = int(
        (
            final_capacity.isna()
            | (final_capacity <= 0)
        ).sum()
    )

    if final_invalid_capacity_count == 0:
        print(
            "  [PASS] No non-positive capacity"
        )
    else:
        print(
            f"  [FAIL] No non-positive capacity "
            f"({final_invalid_capacity_count} invalid rows)"
        )
        validation_passed = False

    # --------------------------------------------------------------
    # Exact duplicates
    # --------------------------------------------------------------

    final_exact_duplicates = int(
        saved.duplicated().sum()
    )

    if final_exact_duplicates == 0:
        print(
            "  [PASS] No exact duplicates"
        )
    else:
        print(
            f"  [FAIL] No exact duplicates "
            f"({final_exact_duplicates})"
        )
        validation_passed = False

    # --------------------------------------------------------------
    # Dataset/Battery/Cycle duplicates
    # --------------------------------------------------------------

    final_key_duplicates = int(
        saved.duplicated(
            subset=[
                "Source_Dataset",
                "Battery_ID",
                "Cycle",
            ]
        ).sum()
    )

    if final_key_duplicates == 0:
        print(
            "  [PASS] No dataset/battery/cycle duplicates"
        )
    else:
        print(
            f"  [FAIL] No dataset/battery/cycle duplicates "
            f"({final_key_duplicates})"
        )
        validation_passed = False

    # --------------------------------------------------------------
    # First SOH
    # --------------------------------------------------------------

    final_first_soh = (
        saved
        .sort_values(
            [
                "Source_Dataset",
                "Battery_ID",
                "Cycle",
            ]
        )
        .groupby(
            [
                "Source_Dataset",
                "Battery_ID",
            ]
        )["SOH_percent"]
        .first()
    )

    final_first_soh_valid = bool(
        np.allclose(
            final_first_soh.values,
            100.0,
            atol=1e-6
        )
    )

    if final_first_soh_valid:
        print(
            "  [PASS] All batteries/cells start at 100% SOH"
        )
    else:
        print(
            "  [FAIL] All batteries/cells start at 100% SOH"
        )
        validation_passed = False

    # --------------------------------------------------------------
    # Required columns
    # --------------------------------------------------------------

    required_final_columns = [
        "Source_Dataset",
        "Battery_ID",
        "Cycle",
        "Capacity_Ah",
        "SOH_percent",
    ]

    required_columns_present = all(
        column in saved.columns
        for column in required_final_columns
    )

    if required_columns_present:
        print(
            "  [PASS] Required columns present"
        )
    else:
        print(
            "  [FAIL] Required columns present"
        )
        validation_passed = False

    # ==================================================================
    # FINAL RESULT
    # ==================================================================

    print()

    if not validation_passed:

        print(
            "=" * 70
        )

        print(
            "FINAL VALIDATION FAILED"
        )

        print(
            "=" * 70
        )

        print()
        print(
            "Do not proceed to ML training."
        )

        raise RuntimeError(
            "Final validation failed. "
            "Do not proceed to ML training."
        )

    print_header(
        "COMBINED SOH DATASET PREPARATION COMPLETE"
    )

    print(
        "Combined dataset:"
    )

    print(
        f"  {OUTPUT_FILE}"
    )

    print()
    print(
        f"Rows       : {len(saved)}"
    )

    print(
        f"Batteries  : "
        f"{saved['Battery_ID'].nunique()}"
    )

    print(
        f"Datasets   : "
        f"{saved['Source_Dataset'].nunique()}"
    )

    print(
        f"SOH range  : "
        f"{final_soh.min():.6f}% - "
        f"{final_soh.max():.6f}%"
    )

    print()
    print(
        "All final validation checks passed."
    )

    print()
    print(
        "The combined dataset is ready for "
        "the next preprocessing/feature stage."
    )


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    main()