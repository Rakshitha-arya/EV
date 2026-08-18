import os
import glob
import scipy.io
import pandas as pd

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

NASA_DIR = os.path.join(
    BASE_DIR,
    "datasets",
    "NASA",
    "extracted"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "processed"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "NASA_all_batteries_SOH.csv"
)

# ---------------------------------------------------------
# Find all MATLAB files
# ---------------------------------------------------------

mat_files = glob.glob(
    os.path.join(NASA_DIR, "**", "*.mat"),
    recursive=True
)

print("=" * 70)
print("NASA - PROCESSING ALL BATTERIES")
print("=" * 70)

print(f"\nMAT files found: {len(mat_files)}")

all_records = []

# ---------------------------------------------------------
# Process every battery
# ---------------------------------------------------------

for file_number, mat_file in enumerate(mat_files, start=1):

    battery_id = os.path.splitext(
        os.path.basename(mat_file)
    )[0]

    print(
        f"\n[{file_number}/{len(mat_files)}] "
        f"Processing {battery_id}"
    )

    try:

        mat = scipy.io.loadmat(
            mat_file,
            squeeze_me=True,
            struct_as_record=False
        )

        if battery_id not in mat:
            print(f"  WARNING: {battery_id} not found")
            continue

        battery = mat[battery_id]
        cycles = battery.cycle

        discharge_number = 0

        for cycle_index, cycle in enumerate(cycles):

            if cycle.type != "discharge":
                continue

            discharge_number += 1

            data = cycle.data

            # -------------------------------------------------
            # Required measurements
            # -------------------------------------------------

            voltage = data.Voltage_measured.flatten()
            current = data.Current_measured.flatten()
            temperature = data.Temperature_measured.flatten()
            time = data.Time.flatten()

            capacity = getattr(
                data,
                "Capacity",
                None
            )

            if capacity is None:
                continue

            try:
                capacity_value = float(capacity)
            except:
                continue

            if len(time) == 0:
                continue

            # -------------------------------------------------
            # Cycle-level features
            # -------------------------------------------------

            duration = (
                time.max() - time.min()
            )

            all_records.append({

                "battery_id": battery_id,

                "cycle_number":
                    discharge_number,

                "cycle_index":
                    cycle_index,

                "ambient_temperature":
                    float(cycle.ambient_temperature),

                "voltage_mean":
                    voltage.mean(),

                "voltage_min":
                    voltage.min(),

                "voltage_max":
                    voltage.max(),

                "voltage_std":
                    voltage.std(),

                "current_mean":
                    current.mean(),

                "current_min":
                    current.min(),

                "current_max":
                    current.max(),

                "current_std":
                    current.std(),

                "temperature_mean":
                    temperature.mean(),

                "temperature_min":
                    temperature.min(),

                "temperature_max":
                    temperature.max(),

                "discharge_time_seconds":
                    duration,

                "capacity_Ah":
                    capacity_value
            })

        print(
            f"  Discharge cycles: "
            f"{discharge_number}"
        )

    except Exception as e:

        print(
            f"  ERROR processing "
            f"{battery_id}: {e}"
        )

# ---------------------------------------------------------
# Create DataFrame
# ---------------------------------------------------------

df = pd.DataFrame(all_records)

# ---------------------------------------------------------
# Calculate SOH separately for each battery
# ---------------------------------------------------------

df["SOH_percent"] = (
    df.groupby("battery_id")["capacity_Ah"]
    .transform(
        lambda x: (x / x.iloc[0]) * 100
    )
)

# ---------------------------------------------------------
# Sort
# ---------------------------------------------------------

df = df.sort_values(
    ["battery_id", "cycle_number"]
).reset_index(drop=True)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("NASA PROCESSING COMPLETE")
print("=" * 70)

print("\nBatteries processed:")
print(df["battery_id"].nunique())

print("\nTotal discharge cycles:")
print(len(df))

print("\nRows per battery:")

print(
    df.groupby("battery_id")
    .size()
    .to_string()
)

print("\nSOH range:")

print(
    df.groupby("battery_id")["SOH_percent"]
    .agg(["min", "max"])
    .to_string()
)

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)