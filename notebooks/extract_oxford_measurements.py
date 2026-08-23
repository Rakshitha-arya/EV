import os
import numpy as np
import pandas as pd
from scipy.io import loadmat

# ============================================================
# OXFORD MEASUREMENT EXTRACTION
# ============================================================

DATASET_ROOT = r"C:\Major project\datasets\Oxford"
OUTPUT_DIR = r"C:\Major project\flask_app\processed\oxford"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "oxford_measurements.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("OXFORD MEASUREMENT EXTRACTION")
print("=" * 70)

mat_files = [
    f for f in os.listdir(DATASET_ROOT)
    if f.lower().endswith(".mat")
]

print()
print("MAT files found:", len(mat_files))

all_rows = []

# ------------------------------------------------------------
# Helper function
# ------------------------------------------------------------

def get_field(obj, field):
    """Safely retrieve a MATLAB struct field."""
    try:
        return getattr(obj, field)
    except Exception:
        return None


# ------------------------------------------------------------
# Process each MAT file
# ------------------------------------------------------------

for filename in mat_files:

    filepath = os.path.join(DATASET_ROOT, filename)

    print()
    print("-" * 70)
    print("FILE:", filename)
    print("-" * 70)

    mat = loadmat(
        filepath,
        squeeze_me=True,
        struct_as_record=False
    )

    cell_names = [
        key for key in mat.keys()
        if key.startswith("Cell")
    ]

    print("Cells found:", len(cell_names))

    for cell_name in sorted(cell_names):

        cell = mat[cell_name]

        # Find characterization cycle fields
        cycle_names = [
            name for name in dir(cell)
            if name.startswith("cyc")
        ]

        cycle_names = sorted(
            cycle_names,
            key=lambda x: int(x[3:])
        )

        print(
            f"{cell_name:<10} "
            f"Cycles: {len(cycle_names):4d}"
        )

        for cycle_name in cycle_names:

            cycle = get_field(cell, cycle_name)

            if cycle is None:
                continue

            # Oxford characterization structures
            discharge = get_field(cycle, "C1dc")

            if discharge is None:
                continue

            time = get_field(discharge, "t")
            voltage = get_field(discharge, "v")
            charge = get_field(discharge, "q")
            temperature = get_field(discharge, "T")

            if time is None or voltage is None:
                continue

            time = np.asarray(time).flatten()
            voltage = np.asarray(voltage).flatten()

            if charge is not None:
                charge = np.asarray(charge).flatten()
            else:
                charge = np.full(len(time), np.nan)

            if temperature is not None:
                temperature = np.asarray(
                    temperature
                ).flatten()
            else:
                temperature = np.full(len(time), np.nan)

            # Make all arrays equal length
            n = min(
                len(time),
                len(voltage),
                len(charge),
                len(temperature)
            )

            time = time[:n]
            voltage = voltage[:n]
            charge = charge[:n]
            temperature = temperature[:n]

            # Extract cycle number
            try:
                cycle_number = int(cycle_name[3:])
            except Exception:
                cycle_number = np.nan

            for i in range(n):

                all_rows.append({
                    "Cell_ID": cell_name,
                    "Cycle": cycle_number,
                    "Cycle_Label": cycle_name,
                    "Time": time[i],
                    "Voltage": voltage[i],
                    "Charge_mAh": charge[i],
                    "Temperature": temperature[i]
                })


# ============================================================
# CREATE DATAFRAME
# ============================================================

print()
print("=" * 70)
print("CREATING OXFORD MEASUREMENT DATASET")
print("=" * 70)

if len(all_rows) == 0:
    print()
    print("ERROR: No measurement records were extracted.")
    print("Check the MATLAB structure and field names.")
    raise SystemExit(1)

df = pd.DataFrame(all_rows)

# Sort data
df = df.sort_values(
    by=["Cell_ID", "Cycle", "Time"]
).reset_index(drop=True)

# ============================================================
# SUMMARY
# ============================================================

print()
print("Total measurement rows:", len(df))
print("Cells:", df["Cell_ID"].nunique())
print("Characterization cycles:", df["Cycle_Label"].nunique())

print()
print("Columns:")

for column in df.columns:
    print(" ", column)

print()
print("Rows by cell:")

cell_counts = df.groupby("Cell_ID").size()

for cell, count in cell_counts.items():
    print(f"  {cell:<10} {count:>10}")

# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved:")
print(OUTPUT_FILE)

print()
print("=" * 70)
print("OXFORD EXTRACTION COMPLETE")
print("=" * 70)