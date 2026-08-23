import os
import numpy as np
import pandas as pd
from scipy.io import loadmat

DATASET_ROOT = r"C:\Major project\datasets\NASA"

OUTPUT_DIR = r"C:\Major project\flask_app\processed\nasa"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_field(obj, name):
    """Safely get a MATLAB struct field."""
    try:
        return getattr(obj, name)
    except Exception:
        return None


def flatten(value):
    """Convert MATLAB arrays into 1-D NumPy arrays."""
    if value is None:
        return np.array([])

    return np.asarray(value).flatten()


print("=" * 70)
print("NASA MEASUREMENT EXTRACTION")
print("=" * 70)

# Find all MAT files recursively
mat_files = []

for root, dirs, files in os.walk(DATASET_ROOT):
    for file in files:
        if file.lower().endswith(".mat"):
            mat_files.append(os.path.join(root, file))

# Remove duplicate file paths based on battery name
unique_files = {}

for path in mat_files:
    name = os.path.splitext(os.path.basename(path))[0]

    if name not in unique_files:
        unique_files[name] = path

print()
print("MAT files found :", len(mat_files))
print("Unique batteries:", len(unique_files))
print()

all_records = []

for battery_id, mat_path in sorted(unique_files.items()):

    print("-" * 70)
    print(f"Battery: {battery_id}")
    print(f"File   : {mat_path}")

    try:
        mat = loadmat(
            mat_path,
            squeeze_me=True,
            struct_as_record=False
        )

        battery = mat.get(battery_id)

        if battery is None:
            print("WARNING: Battery variable not found")
            continue

        cycles = get_field(battery, "cycle")

        if cycles is None:
            print("WARNING: cycle field not found")
            continue

        cycles = np.asarray(cycles).flatten()

        print("Cycles:", len(cycles))

        extracted = 0

        for cycle_number, cycle in enumerate(cycles, start=1):

            cycle_type = get_field(cycle, "type")

            # We primarily need discharge measurements for SOH.
            if cycle_type != "discharge":
                continue

            data = get_field(cycle, "data")

            if data is None:
                continue

            voltage = flatten(get_field(data, "Voltage_measured"))
            current = flatten(get_field(data, "Current_measured"))
            temperature = flatten(get_field(data, "Temperature_measured"))
            time = flatten(get_field(data, "Time"))

            capacity = get_field(data, "Capacity")

            if capacity is not None:
                try:
                    capacity = float(np.asarray(capacity).flatten()[0])
                except Exception:
                    capacity = np.nan
            else:
                capacity = np.nan

            n = max(
                len(voltage),
                len(current),
                len(temperature),
                len(time)
            )

            if n == 0:
                continue

            def resize_array(arr):
                if len(arr) == n:
                    return arr

                result = np.full(n, np.nan)

                if len(arr) > 0:
                    result[:min(len(arr), n)] = arr[:n]

                return result

            voltage = resize_array(voltage)
            current = resize_array(current)
            temperature = resize_array(temperature)
            time = resize_array(time)

            for i in range(n):

                all_records.append({
                    "Battery_ID": battery_id,
                    "Cycle": cycle_number,
                    "Time": time[i],
                    "Voltage": voltage[i],
                    "Current": current[i],
                    "Temperature": temperature[i],
                    "Capacity_Ah": capacity
                })

            extracted += 1

        print("Discharge cycles extracted:", extracted)

    except Exception as e:
        print("ERROR:", e)


print()
print("=" * 70)
print("CREATING NASA MEASUREMENT DATASET")
print("=" * 70)

if not all_records:
    print("ERROR: No measurements extracted.")
    print("Check the MATLAB field names.")
    raise SystemExit

df = pd.DataFrame(all_records)

output_file = os.path.join(
    OUTPUT_DIR,
    "nasa_measurements.csv"
)

df.to_csv(output_file, index=False)

print()
print("Total measurement rows:", len(df))
print("Batteries:", df["Battery_ID"].nunique())
print("Cycles:", df[["Battery_ID", "Cycle"]].drop_duplicates().shape[0])

print()
print("Columns:")
for column in df.columns:
    print(" ", column)

print()
print("Saved:")
print(output_file)

print()
print("=" * 70)
print("NASA EXTRACTION COMPLETE")
print("=" * 70)