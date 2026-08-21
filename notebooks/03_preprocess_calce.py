from pathlib import Path
import pandas as pd
import numpy as np

# --------------------------------------------------
# PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_FOLDER = (
    PROJECT_ROOT.parent
    / "datasets"
    / "CALCE"
    / "CS2"
    / "CS2_35"
)

OUTPUT_FOLDER = PROJECT_ROOT / "processed"
OUTPUT_FOLDER.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_FOLDER / "calce_cs2_35_processed.csv"


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

RATED_CAPACITY_AH = 1.10


# --------------------------------------------------
# READ ALL EXCEL FILES
# --------------------------------------------------

files = sorted(DATASET_FOLDER.glob("*.xlsx"))

print("=" * 70)
print("CALCE CS2-35 PREPROCESSING")
print("=" * 70)

print(f"\nExcel files found: {len(files)}")

all_data = []

for file in files:

    print(f"\nReading: {file.name}")

    try:
        df = pd.read_excel(
            file,
            sheet_name="Channel_1-008"
        )

        # Add source filename
        df["Source_File"] = file.name

        all_data.append(df)

        print(f"Rows: {len(df)}")

    except Exception as e:
        print(f"ERROR reading {file.name}: {e}")


# --------------------------------------------------
# COMBINE DATA
# --------------------------------------------------

if not all_data:
    raise RuntimeError("No CALCE files could be read.")

data = pd.concat(
    all_data,
    ignore_index=True
)

print("\n" + "=" * 70)
print("COMBINED DATA")
print("=" * 70)

print("Rows:", len(data))
print("Columns:", len(data.columns))


# --------------------------------------------------
# CONVERT IMPORTANT COLUMNS TO NUMERIC
# --------------------------------------------------

numeric_columns = [
    "Test_Time(s)",
    "Step_Time(s)",
    "Step_Index",
    "Cycle_Index",
    "Current(A)",
    "Voltage(V)",
    "Charge_Capacity(Ah)",
    "Discharge_Capacity(Ah)",
    "Charge_Energy(Wh)",
    "Discharge_Energy(Wh)",
    "dV/dt(V/s)",
    "Internal_Resistance(Ohm)",
    "AC_Impedance(Ohm)",
    "ACI_Phase_Angle(Deg)"
]

for column in numeric_columns:

    if column in data.columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )


# --------------------------------------------------
# REMOVE INVALID CYCLES
# --------------------------------------------------

data = data.dropna(
    subset=["Cycle_Index"]
)

data["Cycle_Index"] = data["Cycle_Index"].astype(int)


# --------------------------------------------------
# CREATE CYCLE-LEVEL FEATURES
# --------------------------------------------------

cycle_data = []

for cycle, group in data.groupby("Cycle_Index"):

    # Maximum measured discharge capacity
    discharge_capacity = group[
        "Discharge_Capacity(Ah)"
    ].max()

    charge_capacity = group[
        "Charge_Capacity(Ah)"
    ].max()

    # Average values
    avg_voltage = group[
        "Voltage(V)"
    ].mean()

    avg_current = group[
        "Current(A)"
    ].mean()

    # Voltage statistics
    max_voltage = group[
        "Voltage(V)"
    ].max()

    min_voltage = group[
        "Voltage(V)"
    ].min()

    # Current statistics
    max_current = group[
        "Current(A)"
    ].max()

    min_current = group[
        "Current(A)"
    ].min()

    # Energy
    discharge_energy = group[
        "Discharge_Energy(Wh)"
    ].max()

    charge_energy = group[
        "Charge_Energy(Wh)"
    ].max()

    # Internal resistance
    resistance = group[
        "Internal_Resistance(Ohm)"
    ]

    resistance = resistance[
        resistance > 0
    ]

    if len(resistance) > 0:
        avg_resistance = resistance.mean()
    else:
        avg_resistance = np.nan

    # SOH
    soh = (
        discharge_capacity
        / RATED_CAPACITY_AH
    ) * 100

    cycle_data.append({
        "Cycle": cycle,
        "Discharge_Capacity_Ah": discharge_capacity,
        "Charge_Capacity_Ah": charge_capacity,
        "SOH_percent": soh,

        "Avg_Voltage_V": avg_voltage,
        "Min_Voltage_V": min_voltage,
        "Max_Voltage_V": max_voltage,

        "Avg_Current_A": avg_current,
        "Min_Current_A": min_current,
        "Max_Current_A": max_current,

        "Discharge_Energy_Wh": discharge_energy,
        "Charge_Energy_Wh": charge_energy,

        "Avg_Internal_Resistance_Ohm":
            avg_resistance
    })


# --------------------------------------------------
# CREATE PROCESSED DATAFRAME
# --------------------------------------------------

processed = pd.DataFrame(cycle_data)

processed = processed.sort_values(
    "Cycle"
)

processed = processed.reset_index(
    drop=True
)


# --------------------------------------------------
# REMOVE INVALID SOH VALUES
# --------------------------------------------------

processed = processed[
    processed["Discharge_Capacity_Ah"] > 0
]

processed = processed[
    processed["SOH_percent"] > 0
]


# --------------------------------------------------
# SAVE
# --------------------------------------------------

processed.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

print("\n" + "=" * 70)
print("PREPROCESSING COMPLETE")
print("=" * 70)

print("\nProcessed cycles:", len(processed))

print("\nColumns:")
print(processed.columns.tolist())

print("\nFirst 10 cycles:")
print(
    processed.head(10).to_string(
        index=False
    )
)

print("\nLast 10 cycles:")
print(
    processed.tail(10).to_string(
        index=False
    )
)

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)