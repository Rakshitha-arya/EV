"""
Extract SOH / capacity features from NASA and Oxford battery datasets.

Phase:
    Raw dataset -> SOH feature extraction

NASA:
    Uses the raw discharge-cycle Capacity field directly.
    SOH (%) = Capacity_Ah / Initial_Capacity_Ah * 100

Oxford:
    Uses the extracted Oxford measurement CSV.
    Capacity is estimated from charge accumulation within each
    characterization record because the standardized measurement
    dataset does not contain Capacity_Ah.

CALCE:
    Not calculated here because the current standardized CALCE file
    contains empty measurement columns. CALCE will be handled separately
    after inspecting the original XLSX files.

Outputs:
    processed/features/nasa_soh_features.csv
    processed/features/oxford_soh_features.csv
"""

import os
import glob
import numpy as np
import pandas as pd
from scipy.io import loadmat


# ================================================================
# PATHS
# ================================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_ROOT = os.path.join(
    os.path.dirname(PROJECT_ROOT),
    "datasets"
)

NASA_ROOT = os.path.join(
    DATASET_ROOT,
    "NASA"
)

OXFORD_ROOT = os.path.join(
    DATASET_ROOT,
    "Oxford"
)

PROCESSED_ROOT = os.path.join(
    PROJECT_ROOT,
    "processed"
)

FEATURE_ROOT = os.path.join(
    PROCESSED_ROOT,
    "features"
)

os.makedirs(FEATURE_ROOT, exist_ok=True)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def scalar_value(value):
    """
    Convert MATLAB/scipy scalar-like objects to a Python scalar.
    """
    try:
        if isinstance(value, np.ndarray):
            if value.size == 1:
                return value.item()
        return value
    except Exception:
        return value


def get_struct_field(obj, field_name):
    """
    Safely obtain a field from scipy.io MATLAB structures.
    """
    if hasattr(obj, field_name):
        return getattr(obj, field_name)

    if isinstance(obj, dict):
        return obj.get(field_name)

    return None


def to_float_array(value):
    """
    Convert a MATLAB/scipy value into a 1-D float array.
    """
    if value is None:
        return np.array([], dtype=float)

    try:
        arr = np.asarray(value, dtype=float).reshape(-1)
        return arr
    except Exception:
        return np.array([], dtype=float)


# ================================================================
# NASA
# ================================================================

def extract_nasa():
    print("=" * 70)
    print("NASA SOH FEATURE EXTRACTION")
    print("=" * 70)

    # Search recursively because the dataset has several extracted folders.
    mat_files = glob.glob(
        os.path.join(NASA_ROOT, "**", "*.mat"),
        recursive=True
    )

    print()
    print("MAT files found:", len(mat_files))

    # Remove duplicate files using battery ID.
    battery_files = {}

    for path in mat_files:
        filename = os.path.basename(path)

        if not filename.lower().startswith("b"):
            continue

        battery_id = os.path.splitext(filename)[0].upper()

        if battery_id not in battery_files:
            battery_files[battery_id] = path

    print("Unique batteries:", len(battery_files))

    rows = []

    for battery_id in sorted(battery_files):

        mat_path = battery_files[battery_id]

        print()
        print("-" * 70)
        print("Battery:", battery_id)
        print("File:", mat_path)

        try:
            mat = loadmat(
                mat_path,
                squeeze_me=True,
                struct_as_record=False
            )

            if battery_id not in mat:
                print("WARNING: battery key not found")
                continue

            battery = mat[battery_id]

            cycles = get_struct_field(battery, "cycle")

            if cycles is None:
                print("WARNING: cycle field not found")
                continue

            cycles = np.atleast_1d(cycles)

            discharge_number = 0

            for cycle_index, cycle in enumerate(cycles, start=1):

                cycle_type = get_struct_field(cycle, "type")
                cycle_type = scalar_value(cycle_type)

                if isinstance(cycle_type, bytes):
                    cycle_type = cycle_type.decode(errors="ignore")

                if cycle_type is None:
                    continue

                cycle_type = str(cycle_type).strip().lower()

                if cycle_type != "discharge":
                    continue

                data = get_struct_field(cycle, "data")

                if data is None:
                    continue

                capacity = get_struct_field(data, "Capacity")
                capacity = scalar_value(capacity)

                try:
                    capacity = float(np.asarray(capacity).squeeze())
                except Exception:
                    continue

                if not np.isfinite(capacity):
                    continue

                discharge_number += 1

                ambient_temperature = get_struct_field(
                    cycle,
                    "ambient_temperature"
                )

                try:
                    ambient_temperature = float(
                        np.asarray(ambient_temperature).squeeze()
                    )
                except Exception:
                    ambient_temperature = np.nan

                # Extract useful cycle-level measurements.
                voltage = to_float_array(
                    get_struct_field(data, "Voltage_measured")
                )

                current = to_float_array(
                    get_struct_field(data, "Current_measured")
                )

                temperature = to_float_array(
                    get_struct_field(data, "Temperature_measured")
                )

                time = to_float_array(
                    get_struct_field(data, "Time")
                )

                row = {
                    "Dataset": "NASA",
                    "Battery_ID": battery_id,
                    "Cycle": discharge_number,
                    "Raw_Cycle_Index": cycle_index,
                    "Capacity_Ah": capacity,
                    "Ambient_Temperature_C": ambient_temperature,
                    "Initial_Voltage_V": (
                        voltage[0] if len(voltage) else np.nan
                    ),
                    "Final_Voltage_V": (
                        voltage[-1] if len(voltage) else np.nan
                    ),
                    "Min_Voltage_V": (
                        np.nanmin(voltage) if len(voltage) else np.nan
                    ),
                    "Max_Voltage_V": (
                        np.nanmax(voltage) if len(voltage) else np.nan
                    ),
                    "Mean_Voltage_V": (
                        np.nanmean(voltage) if len(voltage) else np.nan
                    ),
                    "Mean_Current_A": (
                        np.nanmean(current) if len(current) else np.nan
                    ),
                    "Min_Current_A": (
                        np.nanmin(current) if len(current) else np.nan
                    ),
                    "Max_Current_A": (
                        np.nanmax(current) if len(current) else np.nan
                    ),
                    "Mean_Temperature_C": (
                        np.nanmean(temperature)
                        if len(temperature)
                        else np.nan
                    ),
                    "Max_Temperature_C": (
                        np.nanmax(temperature)
                        if len(temperature)
                        else np.nan
                    ),
                    "Discharge_Time_s": (
                        time[-1] - time[0]
                        if len(time) >= 2
                        else np.nan
                    ),
                }

                rows.append(row)

            print("Discharge records:", discharge_number)

        except Exception as exc:
            print("ERROR:", exc)

    if not rows:
        print()
        print("ERROR: No NASA discharge records extracted.")
        return None

    df = pd.DataFrame(rows)

    # ------------------------------------------------------------
    # SOH calculation
    # ------------------------------------------------------------
    #
    # Each battery gets its own initial capacity because the
    # measured initial capacities are not exactly identical.
    #
    # SOH = capacity / initial capacity * 100
    #

    df["Initial_Capacity_Ah"] = (
        df.groupby("Battery_ID")["Capacity_Ah"]
        .transform("first")
    )

    df["SOH_percent"] = (
        df["Capacity_Ah"]
        / df["Initial_Capacity_Ah"]
        * 100.0
    )

    # Capacity fade relative to the first measured capacity.
    df["Capacity_Fade_percent"] = (
        100.0 - df["SOH_percent"]
    )

    # Keep impossible numerical values out.
    df.loc[
        ~np.isfinite(df["SOH_percent"]),
        "SOH_percent"
    ] = np.nan

    output_path = os.path.join(
        FEATURE_ROOT,
        "nasa_soh_features.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print()
    print("=" * 70)
    print("NASA RESULT")
    print("=" * 70)

    print("Rows:", len(df))
    print("Batteries:", df["Battery_ID"].nunique())
    print("Discharge cycles:", df.groupby("Battery_ID").size().sum())

    print()
    print("SOH RANGE")
    print(
        "Minimum SOH:",
        round(df["SOH_percent"].min(), 3)
    )
    print(
        "Maximum SOH:",
        round(df["SOH_percent"].max(), 3)
    )

    print()
    print("BATTERY SUMMARY")

    summary = (
        df.groupby("Battery_ID")
        .agg(
            Cycles=("Cycle", "count"),
            Initial_Capacity_Ah=(
                "Initial_Capacity_Ah",
                "first"
            ),
            Final_Capacity_Ah=(
                "Capacity_Ah",
                "last"
            ),
            Final_SOH_percent=(
                "SOH_percent",
                "last"
            )
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    print()
    print("Saved:")
    print(output_path)

    return df


# ================================================================
# OXFORD
# ================================================================

def extract_oxford():
    print()
    print("=" * 70)
    print("OXFORD SOH FEATURE EXTRACTION")
    print("=" * 70)

    input_path = os.path.join(
        PROCESSED_ROOT,
        "oxford",
        "oxford_measurements.csv"
    )

    if not os.path.exists(input_path):

        print()
        print("ERROR: Oxford measurement file not found:")
        print(input_path)

        return None

    print()
    print("Input:")
    print(input_path)

    df = pd.read_csv(input_path)

    required_columns = [
        "Cell_ID",
        "Cycle",
        "Cycle_Label",
        "Time",
        "Voltage",
        "Charge_mAh",
        "Temperature"
    ]

    missing = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing:

        print()
        print("ERROR: Missing columns:")
        print(missing)

        return None

    # ------------------------------------------------------------
    # Important Oxford note
    # ------------------------------------------------------------
    #
    # Oxford data contains characterization records rather than
    # the NASA-style Capacity field.
    #
    # The extracted CSV contains Charge_mAh, so we use the maximum
    # charge accumulated within each characterization record as
    # the capacity-related measurement.
    #
    # This is deliberately kept separate from NASA capacity.
    #

    print()
    print("Calculating characterization-level capacity...")

    grouped = []

    for (cell_id, cycle, cycle_label), group in df.groupby(
        ["Cell_ID", "Cycle", "Cycle_Label"],
        sort=True
    ):

        charge = pd.to_numeric(
            group["Charge_mAh"],
            errors="coerce"
        )

        voltage = pd.to_numeric(
            group["Voltage"],
            errors="coerce"
        )

        temperature = pd.to_numeric(
            group["Temperature"],
            errors="coerce"
        )

        time = pd.to_numeric(
            group["Time"],
            errors="coerce"
        )

        valid_charge = charge.dropna()

        if len(valid_charge):

            # Charge_mAh is cumulative within the record.
            capacity_mAh = valid_charge.max()

        else:
            capacity_mAh = np.nan

        row = {
            "Dataset": "Oxford",
            "Battery_ID": cell_id,
            "Cycle": cycle,
            "Cycle_Label": cycle_label,

            "Capacity_mAh": capacity_mAh,

            "Initial_Voltage_V": (
                voltage.iloc[0]
                if len(voltage.dropna())
                else np.nan
            ),

            "Final_Voltage_V": (
                voltage.iloc[-1]
                if len(voltage.dropna())
                else np.nan
            ),

            "Min_Voltage_V": (
                voltage.min()
                if len(voltage.dropna())
                else np.nan
            ),

            "Max_Voltage_V": (
                voltage.max()
                if len(voltage.dropna())
                else np.nan
            ),

            "Mean_Voltage_V": (
                voltage.mean()
                if len(voltage.dropna())
                else np.nan
            ),

            "Mean_Temperature_C": (
                temperature.mean()
                if len(temperature.dropna())
                else np.nan
            ),

            "Max_Temperature_C": (
                temperature.max()
                if len(temperature.dropna())
                else np.nan
            ),

            "Time_Start": (
                time.min()
                if len(time.dropna())
                else np.nan
            ),

            "Time_End": (
                time.max()
                if len(time.dropna())
                else np.nan
            ),
        }

        if (
            pd.notna(row["Time_Start"])
            and pd.notna(row["Time_End"])
        ):
            row["Duration"] = (
                row["Time_End"]
                - row["Time_Start"]
            )
        else:
            row["Duration"] = np.nan

        grouped.append(row)

    features = pd.DataFrame(grouped)

    if features.empty:

        print()
        print("ERROR: No Oxford characterization records found.")

        return None

    # ------------------------------------------------------------
    # Initial capacity per cell
    # ------------------------------------------------------------

    features["Initial_Capacity_mAh"] = (
        features.groupby("Battery_ID")["Capacity_mAh"]
        .transform("first")
    )

    # ------------------------------------------------------------
    # SOH
    # ------------------------------------------------------------

    features["SOH_percent"] = (
        features["Capacity_mAh"]
        / features["Initial_Capacity_mAh"]
        * 100.0
    )

    features["Capacity_Fade_percent"] = (
        100.0 - features["SOH_percent"]
    )

    features.loc[
        ~np.isfinite(features["SOH_percent"]),
        "SOH_percent"
    ] = np.nan

    output_path = os.path.join(
        FEATURE_ROOT,
        "oxford_soh_features.csv"
    )

    features.to_csv(
        output_path,
        index=False
    )

    print()
    print("=" * 70)
    print("OXFORD RESULT")
    print("=" * 70)

    print("Rows:", len(features))
    print("Cells:", features["Battery_ID"].nunique())

    print()
    print("CAPACITY RANGE")

    valid_capacity = features[
        "Capacity_mAh"
    ].dropna()

    if len(valid_capacity):

        print(
            "Minimum capacity:",
            round(valid_capacity.min(), 4),
            "mAh"
        )

        print(
            "Maximum capacity:",
            round(valid_capacity.max(), 4),
            "mAh"
        )

    else:

        print("No valid capacity values.")

    print()
    print("SOH RANGE")

    valid_soh = features[
        "SOH_percent"
    ].dropna()

    if len(valid_soh):

        print(
            "Minimum SOH:",
            round(valid_soh.min(), 3)
        )

        print(
            "Maximum SOH:",
            round(valid_soh.max(), 3)
        )

    else:

        print("No valid SOH values.")

    print()
    print("CELL SUMMARY")

    summary = (
        features.groupby("Battery_ID")
        .agg(
            Characterization_Records=(
                "Cycle",
                "count"
            ),
            Initial_Capacity_mAh=(
                "Initial_Capacity_mAh",
                "first"
            ),
            Final_Capacity_mAh=(
                "Capacity_mAh",
                "last"
            ),
            Final_SOH_percent=(
                "SOH_percent",
                "last"
            )
        )
        .reset_index()
    )

    print(summary.to_string(index=False))

    print()
    print("Saved:")
    print(output_path)

    return features


# ================================================================
# CALCE STATUS
# ================================================================

def report_calce_status():

    print()
    print("=" * 70)
    print("CALCE SOH STATUS")
    print("=" * 70)

    print()
    print("CALCE SOH is NOT calculated in this script.")

    print()
    print(
        "Reason:"
    )

    print(
        "The current standardized CALCE dataset contains "
        "cycle-level rows, but its measurement columns are empty."
    )

    print()
    print(
        "The original CALCE XLSX files must be inspected and "
        "capacity extracted directly from the raw sheets."
    )

    print()
    print(
        "Next CALCE phase:"
    )

    print(
        "Raw XLSX -> inspect sheet structure -> extract discharge "
        "capacity -> calculate SOH"
    )


# ================================================================
# MAIN
# ================================================================

def main():

    print("=" * 70)
    print("BATTERY SOH FEATURE EXTRACTION")
    print("=" * 70)

    print()
    print("Project:")
    print(PROJECT_ROOT)

    print()
    print("Feature output directory:")
    print(FEATURE_ROOT)

    nasa_df = extract_nasa()

    oxford_df = extract_oxford()

    report_calce_status()

    print()
    print("=" * 70)
    print("SOH FEATURE EXTRACTION COMPLETE")
    print("=" * 70)

    print()
    print("Outputs:")

    nasa_output = os.path.join(
        FEATURE_ROOT,
        "nasa_soh_features.csv"
    )

    oxford_output = os.path.join(
        FEATURE_ROOT,
        "oxford_soh_features.csv"
    )

    print()
    print("NASA:")
    print(nasa_output)

    print()
    print("Oxford:")
    print(oxford_output)

    print()
    print("CALCE:")
    print("Pending raw XLSX capacity extraction.")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()