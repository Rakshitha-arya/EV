from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SOH_DIR = BASE_DIR / "processed" / "soh"

NASA_FILE = SOH_DIR / "nasa_soh_features.csv"
OXFORD_FILE = SOH_DIR / "oxford_soh_features.csv"
CALCE_FILE = SOH_DIR / "calce_soh_features.csv"


# ============================================================
# CONFIGURATION
# ============================================================

REQUIRED_COLUMNS = [
    "Battery_ID",
    "Cycle",
    "Capacity_Ah",
    "Initial_Capacity_Ah",
    "SOH_percent",
]

SOH_MIN = 0
SOH_MAX_WARNING = 105

# A small amount of measurement variation above 100% is possible.
# Values substantially above this threshold are suspicious.
CAPACITY_MIN = 0


# ============================================================
# HELPERS
# ============================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def validate_file(dataset_name, file_path):
    print_header(dataset_name)

    print(f"File:")
    print(file_path)

    if not file_path.exists():
        print()
        print("[ERROR] File does not exist.")
        return None

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print()
        print(f"[ERROR] Could not read CSV: {e}")
        return None

    print()
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # --------------------------------------------------------
    # COLUMN CHECK
    # --------------------------------------------------------

    print()
    print("COLUMN CHECK")

    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            print(f"  [OK]      {col}")
        else:
            print(f"  [MISSING] {col}")

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        print()
        print("[ERROR] Required columns are missing.")
        return df

    # --------------------------------------------------------
    # BATTERY COUNT
    # --------------------------------------------------------

    print()
    print("BATTERY/CELL CHECK")

    battery_count = df["Battery_ID"].nunique()

    print(f"Unique batteries/cells: {battery_count}")

    print()
    print("BATTERIES/CELLS")

    battery_counts = (
        df.groupby("Battery_ID")
        .agg(
            Rows=("Battery_ID", "size"),
            Cycles=("Cycle", "nunique"),
        )
        .reset_index()
    )

    print(battery_counts.to_string(index=False))

    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    print()
    print("MISSING VALUES")

    for col in REQUIRED_COLUMNS:
        count = df[col].isna().sum()
        percent = count / len(df) * 100 if len(df) else 0

        print(
            f"  {col:<22}"
            f"{count:>8} "
            f"({percent:>7.2f}%)"
        )

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    print()
    print("DUPLICATE CHECK")

    duplicates = df.duplicated(
        subset=["Battery_ID", "Cycle"],
        keep=False
    )

    duplicate_count = duplicates.sum()

    print(
        f"Duplicate Battery_ID + Cycle rows: "
        f"{duplicate_count}"
    )

    if duplicate_count > 0:
        print()
        print("Duplicate records:")

        duplicate_df = (
            df.loc[duplicates]
            .sort_values(["Battery_ID", "Cycle"])
        )

        print(
            duplicate_df[
                [
                    "Battery_ID",
                    "Cycle",
                    "Capacity_Ah",
                    "Initial_Capacity_Ah",
                    "SOH_percent",
                ]
            ].head(30).to_string(index=False)
        )

        if duplicate_count > 30:
            print(
                f"... showing first 30 of "
                f"{duplicate_count} duplicate rows"
            )
    else:
        print("[OK] No duplicate battery-cycle records.")

    # --------------------------------------------------------
    # NUMERIC CONVERSION
    # --------------------------------------------------------

    numeric_columns = [
        "Cycle",
        "Capacity_Ah",
        "Initial_Capacity_Ah",
        "SOH_percent",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # --------------------------------------------------------
    # CAPACITY CHECK
    # --------------------------------------------------------

    print()
    print("CAPACITY CHECK")

    valid_capacity = df["Capacity_Ah"].notna()

    print(
        f"Valid Capacity_Ah rows: "
        f"{valid_capacity.sum()}"
    )

    if valid_capacity.sum() > 0:
        capacity = df.loc[valid_capacity, "Capacity_Ah"]

        print(
            f"Minimum capacity: "
            f"{capacity.min():.6f}"
        )

        print(
            f"Maximum capacity: "
            f"{capacity.max():.6f}"
        )

        print(
            f"Mean capacity: "
            f"{capacity.mean():.6f}"
        )

        negative_capacity = (
            capacity < CAPACITY_MIN
        ).sum()

        print(
            f"Negative capacity rows: "
            f"{negative_capacity}"
        )

    # --------------------------------------------------------
    # INITIAL CAPACITY CHECK
    # --------------------------------------------------------

    print()
    print("INITIAL CAPACITY CHECK")

    valid_initial = df["Initial_Capacity_Ah"].notna()

    print(
        f"Valid Initial_Capacity_Ah rows: "
        f"{valid_initial.sum()}"
    )

    if valid_initial.sum() > 0:
        initial = df.loc[
            valid_initial,
            "Initial_Capacity_Ah"
        ]

        print(
            f"Minimum initial capacity: "
            f"{initial.min():.6f}"
        )

        print(
            f"Maximum initial capacity: "
            f"{initial.max():.6f}"
        )

        print(
            f"Mean initial capacity: "
            f"{initial.mean():.6f}"
        )

    # --------------------------------------------------------
    # SOH CHECK
    # --------------------------------------------------------

    print()
    print("SOH CHECK")

    valid_soh = df["SOH_percent"].notna()

    print(
        f"Valid SOH rows: "
        f"{valid_soh.sum()}"
    )

    if valid_soh.sum() == 0:
        print("[ERROR] No valid SOH values.")
        return df

    soh = df.loc[valid_soh, "SOH_percent"]

    print(
        f"Minimum SOH: "
        f"{soh.min():.6f}%"
    )

    print(
        f"Maximum SOH: "
        f"{soh.max():.6f}%"
    )

    print(
        f"Mean SOH: "
        f"{soh.mean():.6f}%"
    )

    # --------------------------------------------------------
    # SOH BELOW ZERO
    # --------------------------------------------------------

    below_zero = (
        df["SOH_percent"] < SOH_MIN
    ).sum()

    print()
    print(
        f"SOH < 0% rows: "
        f"{below_zero}"
    )

    # --------------------------------------------------------
    # SOH ABOVE 105
    # --------------------------------------------------------

    above_warning = (
        df["SOH_percent"] > SOH_MAX_WARNING
    ).sum()

    print(
        f"SOH > {SOH_MAX_WARNING}% rows: "
        f"{above_warning}"
    )

    if above_warning > 0:

        print()
        print(
            f"WARNING: "
            f"{above_warning} SOH values exceed "
            f"{SOH_MAX_WARNING}%."
        )

        suspicious = (
            df[df["SOH_percent"] > SOH_MAX_WARNING]
            .sort_values(
                "SOH_percent",
                ascending=False
            )
        )

        print()
        print("Highest suspicious SOH values:")

        print(
            suspicious[
                [
                    "Battery_ID",
                    "Cycle",
                    "Capacity_Ah",
                    "Initial_Capacity_Ah",
                    "SOH_percent",
                ]
            ]
            .head(20)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # SOH CONSISTENCY CHECK
    # --------------------------------------------------------

    print()
    print("SOH FORMULA CONSISTENCY CHECK")

    calculated_soh = (
        df["Capacity_Ah"]
        / df["Initial_Capacity_Ah"]
        * 100
    )

    valid_formula = (
        df["Capacity_Ah"].notna()
        & df["Initial_Capacity_Ah"].notna()
        & df["SOH_percent"].notna()
        & (df["Initial_Capacity_Ah"] != 0)
    )

    if valid_formula.sum() > 0:

        difference = (
            calculated_soh[valid_formula]
            - df.loc[valid_formula, "SOH_percent"]
        ).abs()

        print(
            f"Rows checked: "
            f"{valid_formula.sum()}"
        )

        print(
            f"Maximum SOH formula difference: "
            f"{difference.max():.10f}%"
        )

        print(
            f"Mean SOH formula difference: "
            f"{difference.mean():.10f}%"
        )

        inconsistent = (
            difference > 0.01
        ).sum()

        print(
            f"Rows with difference > 0.01%: "
            f"{inconsistent}"
        )

        if inconsistent == 0:
            print(
                "[OK] SOH matches "
                "Capacity / Initial Capacity."
            )
        else:
            print(
                "[WARNING] Some SOH values do not "
                "match the expected formula."
            )

    # --------------------------------------------------------
    # FIRST CYCLE SOH CHECK
    # --------------------------------------------------------

    print()
    print("FIRST-CYCLE SOH CHECK")

    first_cycles = (
        df.sort_values(
            ["Battery_ID", "Cycle"]
        )
        .groupby("Battery_ID")
        .first()
        .reset_index()
    )

    print(
        first_cycles[
            [
                "Battery_ID",
                "Cycle",
                "Capacity_Ah",
                "Initial_Capacity_Ah",
                "SOH_percent",
            ]
        ].to_string(index=False)
    )

    first_not_100 = (
        first_cycles["SOH_percent"]
        .sub(100)
        .abs()
        > 0.01
    ).sum()

    print()

    if first_not_100 == 0:
        print(
            "[OK] First SOH value is approximately "
            "100% for every battery/cell."
        )
    else:
        print(
            f"[WARNING] {first_not_100} batteries/cells "
            f"do not start at approximately 100% SOH."
        )

    # --------------------------------------------------------
    # MONOTONICITY CHECK
    # --------------------------------------------------------

    print()
    print("CAPACITY TREND CHECK")

    non_monotonic_batteries = []

    for battery_id, group in df.groupby("Battery_ID"):

        group = group.sort_values("Cycle")

        capacities = (
            group["Capacity_Ah"]
            .dropna()
            .to_numpy()
        )

        if len(capacities) < 2:
            continue

        increases = np.diff(capacities) > 0

        if increases.any():
            non_monotonic_batteries.append(
                battery_id
            )

    print(
        f"Batteries/cells with capacity increases: "
        f"{len(non_monotonic_batteries)}"
    )

    if non_monotonic_batteries:
        print(
            "Note: capacity recovery/non-monotonic "
            "behavior can occur in real battery data."
        )

        print(
            "Affected batteries/cells:"
        )

        print(
            ", ".join(
                map(
                    str,
                    non_monotonic_batteries
                )
            )
        )

    # --------------------------------------------------------
    # SOH BY BATTERY SUMMARY
    # --------------------------------------------------------

    print()
    print("SOH SUMMARY BY BATTERY/CELL")

    summary = (
        df.groupby("Battery_ID")
        .agg(
            Records=("SOH_percent", "count"),
            First_SOH=("SOH_percent", "first"),
            Last_SOH=("SOH_percent", "last"),
            Minimum_SOH=("SOH_percent", "min"),
            Maximum_SOH=("SOH_percent", "max"),
            Mean_SOH=("SOH_percent", "mean"),
        )
        .reset_index()
    )

    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}"
        )
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print()
    print("-" * 70)

    problems = []

    if missing_columns:
        problems.append("missing columns")

    if duplicate_count > 0:
        problems.append("duplicate battery-cycle records")

    if below_zero > 0:
        problems.append("SOH below zero")

    if above_warning > 0:
        problems.append("SOH above warning threshold")

    if valid_soh.sum() == 0:
        problems.append("no valid SOH")

    if problems:
        print("VALIDATION RESULT: WARNING")
        print()
        print("Issues detected:")

        for problem in problems:
            print(f"  - {problem}")
    else:
        print("VALIDATION RESULT: PASS")

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SOH FEATURE DATASET VALIDATION")
    print("=" * 70)

    print()
    print("SOH directory:")
    print(SOH_DIR)

    if not SOH_DIR.exists():
        raise RuntimeError(
            f"SOH directory does not exist:\n{SOH_DIR}"
        )

    datasets = [
        ("NASA", NASA_FILE),
        ("OXFORD", OXFORD_FILE),
        ("CALCE", CALCE_FILE),
    ]

    results = {}

    for name, file_path in datasets:

        results[name] = validate_file(
            name,
            file_path
        )

    # ========================================================
    # CROSS DATASET SUMMARY
    # ========================================================

    print_header("CROSS-DATASET SOH SUMMARY")

    summary_rows = []

    for name, df in results.items():

        if df is None:
            continue

        if "Battery_ID" not in df.columns:
            continue

        summary_rows.append(
            {
                "Dataset": name,
                "Rows": len(df),
                "Batteries": df["Battery_ID"].nunique(),
                "Cycles": df[
                    ["Battery_ID", "Cycle"]
                ].drop_duplicates().shape[0],
                "Valid_SOH": (
                    df["SOH_percent"].notna().sum()
                    if "SOH_percent" in df.columns
                    else 0
                ),
            }
        )

    if summary_rows:

        summary_df = pd.DataFrame(
            summary_rows
        )

        print(
            summary_df.to_string(
                index=False
            )
        )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 70)
    print("SOH VALIDATION COMPLETE")
    print("=" * 70)

    print()
    print("IMPORTANT:")
    print(
        "Do not automatically remove SOH values above 100%."
    )
    print(
        "First determine whether they are caused by duplicate files, "
        "incorrect capacity extraction, or real measurement variation."
    )
    print(
        "The NASA extraction currently contains duplicate "
        "Battery_ID + Cycle records in some source folders."
    )


if __name__ == "__main__":
    main()