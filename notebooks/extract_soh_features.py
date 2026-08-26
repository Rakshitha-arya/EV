import os
import glob
import numpy as np
import pandas as pd
from scipy.io import loadmat

# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"C:\Major project"

NASA_DIR = os.path.join(
    BASE_DIR,
    "datasets",
    "NASA",
    "extracted"
)

OXFORD_FILE = os.path.join(
    BASE_DIR,
    "datasets",
    "Oxford",
    "Oxford_Battery_Degradation_Dataset_1.mat"
)

CALCE_DIR = os.path.join(
    BASE_DIR,
    "datasets",
    "CALCE"
)

OUTPUT_DIR = r"C:\Major project\flask_app\processed\soh"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_fields(obj):
    if hasattr(obj, "_fieldnames"):
        return obj._fieldnames
    return []


def safe_array(value):
    try:
        arr = np.asarray(value, dtype=float).squeeze()

        if arr.size == 0:
            return None

        return arr

    except Exception:
        return None


# ============================================================
# NASA SOH
# ============================================================

def extract_nasa_soh():

    print("=" * 70)
    print("NASA SOH FEATURE EXTRACTION")
    print("=" * 70)

    rows = []

    mat_files = glob.glob(
        os.path.join(NASA_DIR, "**", "*.mat"),
        recursive=True
    )

    # Remove duplicate filenames
    unique_files = {}

    for path in mat_files:
        battery_id = os.path.splitext(
            os.path.basename(path)
        )[0]

        if battery_id not in unique_files:
            unique_files[battery_id] = path

    for battery_id, path in sorted(unique_files.items()):

        mat = loadmat(
            path,
            squeeze_me=True,
            struct_as_record=False
        )

        if battery_id not in mat:
            continue

        cycles = mat[battery_id]
        cycles = np.atleast_1d(cycles)

        discharge_number = 0

        print("\n" + "-" * 70)
        print(f"Battery: {battery_id}")

        for cycle_index, cycle in enumerate(cycles, start=1):

            if not hasattr(cycle, "type"):
                continue

            cycle_type = str(cycle.type).lower()

            if cycle_type != "discharge":
                continue

            if not hasattr(cycle, "data"):
                continue

            data = cycle.data

            capacity = None

            # NASA discharge capacity field
            for field in get_fields(data):

                if field.lower() in [
                    "capacity",
                    "capacity_ah",
                    "capacitya_h",
                    "capacityah"
                ]:

                    value = safe_array(
                        getattr(data, field)
                    )

                    if value is not None:
                        capacity = float(
                            np.nanmax(np.abs(value))
                        )
                        break

            if capacity is None:
                continue

            discharge_number += 1

            rows.append({
                "Dataset": "NASA",
                "Battery_ID": battery_id,
                "Cycle": discharge_number,
                "Capacity_Ah": capacity
            })

        print(
            f"Discharge cycles: {discharge_number}"
        )

    df = pd.DataFrame(rows)

    if df.empty:
        print("\nERROR: NASA SOH dataset is empty.")
        return df

    # --------------------------------------------------------
    # SOH relative to first measured capacity
    # --------------------------------------------------------

    df["SOH_percent"] = (
        df.groupby("Battery_ID")["Capacity_Ah"]
        .transform(
            lambda x: x / x.iloc[0] * 100
        )
    )

    output = os.path.join(
        OUTPUT_DIR,
        "nasa_soh_features.csv"
    )

    df.to_csv(output, index=False)

    print("\n" + "=" * 70)
    print("NASA SOH SUMMARY")
    print("=" * 70)

    print(f"Rows: {len(df)}")
    print(
        f"Batteries: "
        f"{df['Battery_ID'].nunique()}"
    )

    print(
        df.groupby("Battery_ID")["SOH_percent"]
        .agg(["count", "first", "last", "min"])
    )

    print("\nSaved:")
    print(output)

    return df


# ============================================================
# OXFORD SOH
# ============================================================

def extract_oxford_soh():

    print("\n" + "=" * 70)
    print("OXFORD SOH FEATURE EXTRACTION")
    print("=" * 70)

    print(f"File: {OXFORD_FILE}")

    if not os.path.exists(OXFORD_FILE):

        print("\nERROR: Oxford MAT file not found.")

        return pd.DataFrame()

    mat = loadmat(
        OXFORD_FILE,
        squeeze_me=True,
        struct_as_record=False
    )

    rows = []

    # --------------------------------------------------------
    # Cell1 ... Cell8
    # --------------------------------------------------------

    for cell_number in range(1, 9):

        battery_id = f"Cell{cell_number}"

        if battery_id not in mat:

            print(
                f"\nWARNING: {battery_id} not found."
            )

            continue

        cell = mat[battery_id]

        cycle_fields = get_fields(cell)

        print("\n" + "-" * 70)
        print(
            f"Cell: {battery_id}"
        )
        print(
            f"Characterization records: "
            f"{len(cycle_fields)}"
        )

        characterization_number = 0

        for record_name in cycle_fields:

            record = getattr(
                cell,
                record_name
            )

            # ------------------------------------------------
            # C1dc = 1C constant-current discharge
            # ------------------------------------------------

            if not hasattr(record, "C1dc"):
                continue

            c1dc = record.C1dc

            if not hasattr(c1dc, "q"):
                continue

            q = safe_array(c1dc.q)

            if q is None:
                continue

            if q.size == 0:
                continue

            # ------------------------------------------------
            # Discharge capacity
            #
            # q starts near 0 and becomes negative during
            # discharge.
            #
            # Therefore:
            #
            # Capacity = absolute final q
            # ------------------------------------------------

            finite_q = q[np.isfinite(q)]

            if finite_q.size == 0:
                continue

            capacity_mAh = abs(
                float(finite_q[-1])
            )

            if capacity_mAh <= 0:
                continue

            characterization_number += 1

            # Extract cycle label
            try:
                cycle_label = int(
                    record_name.replace(
                        "cyc",
                        ""
                    )
                )
            except Exception:
                cycle_label = characterization_number

            rows.append({
                "Dataset": "Oxford",
                "Battery_ID": battery_id,
                "Cycle": characterization_number,
                "Cycle_Label": cycle_label,
                "Capacity_mAh": capacity_mAh
            })

        print(
            f"Valid discharge capacity records: "
            f"{characterization_number}"
        )

    df = pd.DataFrame(rows)

    if df.empty:

        print(
            "\nERROR: Oxford SOH dataset is empty."
        )

        return df

    # --------------------------------------------------------
    # SOH
    #
    # SOH = current capacity / initial capacity * 100
    # --------------------------------------------------------

    df["SOH_percent"] = (
        df.groupby("Battery_ID")["Capacity_mAh"]
        .transform(
            lambda x: x / x.iloc[0] * 100
        )
    )

    # --------------------------------------------------------
    # Convert capacity to Ah as well
    # --------------------------------------------------------

    df["Capacity_Ah"] = (
        df["Capacity_mAh"] / 1000.0
    )

    output = os.path.join(
        OUTPUT_DIR,
        "oxford_soh_features.csv"
    )

    df.to_csv(
        output,
        index=False
    )

    print("\n" + "=" * 70)
    print("OXFORD SOH SUMMARY")
    print("=" * 70)

    print(f"Rows: {len(df)}")

    print(
        f"Cells: "
        f"{df['Battery_ID'].nunique()}"
    )

    print(
        df.groupby("Battery_ID")["SOH_percent"]
        .agg(["count", "first", "last", "min"])
    )

    print("\nCapacity summary:")

    print(
        df.groupby("Battery_ID")["Capacity_mAh"]
        .agg(["first", "last", "min", "max"])
    )

    print("\nSaved:")
    print(output)

    return df


# ============================================================
# CALCE SOH
# ============================================================

def extract_calce_soh():

    print("\n" + "=" * 70)
    print("CALCE SOH FEATURE EXTRACTION")
    print("=" * 70)

    # --------------------------------------------------------
    # Use existing CALCE SOH files if already available
    # --------------------------------------------------------

    existing_files = [
        r"C:\Major project\flask_app\processed\cs2_35_soh.csv",
        r"C:\Major project\flask_app\processed\cs2_36_soh.csv",
        r"C:\Major project\flask_app\processed\cs2_37_soh.csv",
        r"C:\Major project\flask_app\processed\cs2_38_soh.csv"
    ]

    rows = []

    for path in existing_files:

        if not os.path.exists(path):
            continue

        try:

            df = pd.read_csv(path)

        except Exception:
            continue

        if df.empty:
            continue

        # Identify battery
        battery_id = None

        for column in [
            "Battery_ID",
            "Battery",
            "battery",
            "Cell"
        ]:

            if column in df.columns:

                battery_id = str(
                    df[column].iloc[0]
                )

                break

        if battery_id is None:

            battery_id = os.path.basename(
                path
            ).replace(
                "_soh.csv",
                ""
            ).upper()

        # Identify capacity
        capacity_column = None

        for column in [
            "Discharge_Capacity_Ah",
            "Capacity_Ah",
            "Capacity",
            "capacity"
        ]:

            if column in df.columns:

                capacity_column = column

                break

        if capacity_column is None:
            continue

        capacity = pd.to_numeric(
            df[capacity_column],
            errors="coerce"
        )

        temp = pd.DataFrame({
            "Dataset": "CALCE",
            "Battery_ID": battery_id,
            "Cycle": np.arange(
                1,
                len(df) + 1
            ),
            "Capacity_Ah": capacity
        })

        temp = temp.dropna(
            subset=["Capacity_Ah"]
        )

        if temp.empty:
            continue

        temp["SOH_percent"] = (
            temp["Capacity_Ah"]
            / temp["Capacity_Ah"].iloc[0]
            * 100
        )

        rows.append(temp)

    if not rows:

        print(
            "\nWARNING: No existing CALCE SOH "
            "files could be used."
        )

        return pd.DataFrame()

    df = pd.concat(
        rows,
        ignore_index=True
    )

    output = os.path.join(
        OUTPUT_DIR,
        "calce_soh_features.csv"
    )

    df.to_csv(
        output,
        index=False
    )

    print("\n" + "=" * 70)
    print("CALCE SOH SUMMARY")
    print("=" * 70)

    print(f"Rows: {len(df)}")

    print(
        f"Batteries: "
        f"{df['Battery_ID'].nunique()}"
    )

    print(
        df.groupby("Battery_ID")["SOH_percent"]
        .agg(["count", "first", "last", "min"])
    )

    print("\nSaved:")
    print(output)

    return df


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    nasa_df = extract_nasa_soh()

    oxford_df = extract_oxford_soh()

    calce_df = extract_calce_soh()

    print("\n" + "=" * 70)
    print("SOH FEATURE EXTRACTION COMPLETE")
    print("=" * 70)

    print("\nOutput directory:")
    print(OUTPUT_DIR)

    print("\nFiles:")

    print(
        os.path.join(
            OUTPUT_DIR,
            "nasa_soh_features.csv"
        )
    )

    print(
        os.path.join(
            OUTPUT_DIR,
            "oxford_soh_features.csv"
        )
    )

    print(
        os.path.join(
            OUTPUT_DIR,
            "calce_soh_features.csv"
        )
    )

    print("\nIMPORTANT:")
    print(
        "Oxford SOH is calculated from the "
        "final absolute C1dc.q value."
    )

    print(
        "SOH is normalized independently for "
        "each battery/cell using its first "
        "characterization capacity."
    )