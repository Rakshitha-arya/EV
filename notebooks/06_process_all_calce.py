from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = (
    PROJECT_ROOT.parent
    / "datasets"
    / "CALCE"
    / "CS2"
)

OUTPUT_DIR = PROJECT_ROOT / "processed"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# BATTERIES
# ============================================================

BATTERIES = [
    "CS2_35",
    "CS2_36",
    "CS2_37",
    "CS2_38"
]

# CALCE CS2 rated capacity
RATED_CAPACITY_AH = 1.10


# ============================================================
# FIND CHANNEL SHEET
# ============================================================

def find_channel_sheet(excel_file):

    excel = pd.ExcelFile(excel_file)

    channel_sheets = [
        sheet
        for sheet in excel.sheet_names
        if sheet.lower().startswith("channel_")
    ]

    if not channel_sheets:
        return None

    return channel_sheets[0]


# ============================================================
# READ ONE BATTERY
# ============================================================

def process_battery(battery_name):

    print("\n" + "=" * 70)
    print(f"PROCESSING {battery_name}")
    print("=" * 70)

    battery_folder = DATASET_ROOT / battery_name

    if not battery_folder.exists():

        print("ERROR: Folder not found:")
        print(battery_folder)

        return None

    excel_files = sorted(battery_folder.glob("*.xlsx"))

    print(f"Excel files: {len(excel_files)}")

    all_data = []

    for excel_file in excel_files:

        try:

            sheet_name = find_channel_sheet(excel_file)

            if sheet_name is None:

                print(f"  SKIP: {excel_file.name}")
                print("  No Channel sheet found")
                continue

            df = pd.read_excel(
                excel_file,
                sheet_name=sheet_name,
                header=0
            )

            if df.empty:

                print(f"  SKIP: {excel_file.name}")
                print("  Empty sheet")
                continue

            df["Source_File"] = excel_file.name
            df["Battery"] = battery_name

            all_data.append(df)

            print(
                f"  {excel_file.name}: "
                f"{len(df)} rows "
                f"[{sheet_name}]"
            )

        except Exception as e:

            print(f"  ERROR: {excel_file.name}")
            print(f"  {e}")

    if not all_data:

        print(f"\nNo data found for {battery_name}")
        return None

    # ========================================================
    # COMBINE
    # ========================================================

    combined = pd.concat(
        all_data,
        ignore_index=True
    )

    print("\nCombined rows:", len(combined))

    # ========================================================
    # CONVERT NUMERIC COLUMNS
    # ========================================================

    numeric_columns = [
        "Cycle_Index",
        "Current(A)",
        "Voltage(V)",
        "Charge_Capacity(Ah)",
        "Discharge_Capacity(Ah)",
        "Charge_Energy(Wh)",
        "Discharge_Energy(Wh)",
        "Internal_Resistance(Ohm)"
    ]

    for column in numeric_columns:

        if column in combined.columns:

            combined[column] = pd.to_numeric(
                combined[column],
                errors="coerce"
            )

    combined = combined.dropna(
        subset=["Cycle_Index"]
    )

    combined["Cycle_Index"] = (
        combined["Cycle_Index"]
        .astype(int)
    )

    # ========================================================
    # SORT DATA
    # ========================================================

    # Preserve the actual order of measurements
    combined = combined.reset_index(drop=True)

    # ========================================================
    # GET CUMULATIVE CAPACITY AT EACH CYCLE
    # ========================================================

    cycle_data = []

    previous_discharge_capacity = 0.0
    previous_charge_capacity = 0.0

    previous_discharge_energy = 0.0
    previous_charge_energy = 0.0

    cycles = sorted(
        combined["Cycle_Index"].unique()
    )

    for cycle in cycles:

        group = combined[
            combined["Cycle_Index"] == cycle
        ]

        if group.empty:
            continue

        # ----------------------------------------------------
        # Cumulative values at end of this cycle
        # ----------------------------------------------------

        cumulative_discharge = group[
            "Discharge_Capacity(Ah)"
        ].max()

        cumulative_charge = group[
            "Charge_Capacity(Ah)"
        ].max()

        cumulative_discharge_energy = group[
            "Discharge_Energy(Wh)"
        ].max()

        cumulative_charge_energy = group[
            "Charge_Energy(Wh)"
        ].max()

        # ----------------------------------------------------
        # Convert cumulative values to cycle values
        # ----------------------------------------------------

        if pd.notna(cumulative_discharge):

            cycle_discharge_capacity = (
                cumulative_discharge
                - previous_discharge_capacity
            )

        else:

            cycle_discharge_capacity = np.nan

        if pd.notna(cumulative_charge):

            cycle_charge_capacity = (
                cumulative_charge
                - previous_charge_capacity
            )

        else:

            cycle_charge_capacity = np.nan

        if pd.notna(cumulative_discharge_energy):

            cycle_discharge_energy = (
                cumulative_discharge_energy
                - previous_discharge_energy
            )

        else:

            cycle_discharge_energy = np.nan

        if pd.notna(cumulative_charge_energy):

            cycle_charge_energy = (
                cumulative_charge_energy
                - previous_charge_energy
            )

        else:

            cycle_charge_energy = np.nan

        # ----------------------------------------------------
        # Update previous cumulative values
        # ----------------------------------------------------

        if pd.notna(cumulative_discharge):
            previous_discharge_capacity = cumulative_discharge

        if pd.notna(cumulative_charge):
            previous_charge_capacity = cumulative_charge

        if pd.notna(cumulative_discharge_energy):
            previous_discharge_energy = cumulative_discharge_energy

        if pd.notna(cumulative_charge_energy):
            previous_charge_energy = cumulative_charge_energy

        # ----------------------------------------------------
        # Other cycle features
        # ----------------------------------------------------

        avg_voltage = group[
            "Voltage(V)"
        ].mean()

        min_voltage = group[
            "Voltage(V)"
        ].min()

        max_voltage = group[
            "Voltage(V)"
        ].max()

        avg_current = group[
            "Current(A)"
        ].mean()

        min_current = group[
            "Current(A)"
        ].min()

        max_current = group[
            "Current(A)"
        ].max()

        internal_resistance = (
            group[
                "Internal_Resistance(Ohm)"
            ]
            .replace(0, np.nan)
            .mean()
        )

        # ----------------------------------------------------
        # Ignore invalid capacity
        # ----------------------------------------------------

        if (
            pd.isna(cycle_discharge_capacity)
            or cycle_discharge_capacity <= 0
        ):
            continue

        # ----------------------------------------------------
        # SOH
        # ----------------------------------------------------

        soh = (
            cycle_discharge_capacity
            / RATED_CAPACITY_AH
        ) * 100

        cycle_data.append({

            "Battery": battery_name,

            "Cycle": cycle,

            "Discharge_Capacity_Ah":
                cycle_discharge_capacity,

            "Charge_Capacity_Ah":
                cycle_charge_capacity,

            "SOH_percent":
                soh,

            "Avg_Voltage_V":
                avg_voltage,

            "Min_Voltage_V":
                min_voltage,

            "Max_Voltage_V":
                max_voltage,

            "Avg_Current_A":
                avg_current,

            "Min_Current_A":
                min_current,

            "Max_Current_A":
                max_current,

            "Discharge_Energy_Wh":
                cycle_discharge_energy,

            "Charge_Energy_Wh":
                cycle_charge_energy,

            "Avg_Internal_Resistance_Ohm":
                internal_resistance
        })

    # ========================================================
    # RESULT
    # ========================================================

    result = pd.DataFrame(
        cycle_data
    )

    if result.empty:

        print("\nERROR: No valid cycles found.")
        return None

    result = result.sort_values(
        "Cycle"
    ).reset_index(drop=True)

    print(
        f"\nCycles processed: "
        f"{len(result)}"
    )

    # ========================================================
    # CHECK SOH
    # ========================================================

    print("\nFirst 5 SOH values:")

    print(
        result[
            [
                "Cycle",
                "Discharge_Capacity_Ah",
                "SOH_percent"
            ]
        ]
        .head()
        .to_string(index=False)
    )

    print("\nLast 5 SOH values:")

    print(
        result[
            [
                "Cycle",
                "Discharge_Capacity_Ah",
                "SOH_percent"
            ]
        ]
        .tail()
        .to_string(index=False)
    )

    # ========================================================
    # SAVE INDIVIDUAL BATTERY
    # ========================================================

    output_file = (
        OUTPUT_DIR
        / f"{battery_name.lower()}_soh.csv"
    )

    result.to_csv(
        output_file,
        index=False
    )

    print("\nSaved:")
    print(output_file)

    return result


# ============================================================
# PROCESS ALL BATTERIES
# ============================================================

all_results = []

for battery in BATTERIES:

    result = process_battery(
        battery
    )

    if result is not None:

        all_results.append(result)


# ============================================================
# COMBINE ALL BATTERIES
# ============================================================

print("\n" + "=" * 70)
print("ALL CALCE CELLS PROCESSED")
print("=" * 70)


if all_results:

    combined_result = pd.concat(
        all_results,
        ignore_index=True
    )

    combined_result = combined_result.sort_values(
        [
            "Battery",
            "Cycle"
        ]
    ).reset_index(drop=True)

    combined_output = (
        OUTPUT_DIR
        / "calce_cs2_all_cells.csv"
    )

    combined_result.to_csv(
        combined_output,
        index=False
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\nBattery counts:")

    print(
        combined_result[
            "Battery"
        ].value_counts()
    )

    print(
        "\nTotal samples:",
        len(combined_result)
    )

    print("\nSOH statistics:")

    print(
        combined_result[
            "SOH_percent"
        ].describe()
    )

    print("\nSaved combined dataset:")

    print(combined_output)

else:

    print("\nERROR: No batteries were processed.")


print("\n" + "=" * 70)
print("PROCESSING COMPLETE")
print("=" * 70)