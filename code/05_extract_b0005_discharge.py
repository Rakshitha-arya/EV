import os
import scipy.io
import pandas as pd

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "NASA",
    "extracted",
    "1. BatteryAgingARC-FY08Q4",
    "B0005.mat"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "processed"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "NASA_B0005_discharge.csv"
)

# ---------------------------------------------------------
# Load MATLAB file
# ---------------------------------------------------------

mat = scipy.io.loadmat(
    FILE_PATH,
    squeeze_me=True,
    struct_as_record=False
)

battery = mat["B0005"]
cycles = battery.cycle

# ---------------------------------------------------------
# Extract discharge cycles
# ---------------------------------------------------------

records = []

discharge_number = 0

for cycle_index, cycle in enumerate(cycles):

    if cycle.type != "discharge":
        continue

    discharge_number += 1

    data = cycle.data

    # NASA discharge data fields
    voltage = data.Voltage_measured
    current = data.Current_measured
    temperature = data.Temperature_measured
    time = data.Time

    # Capacity is normally available for discharge cycles
    capacity = getattr(data, "Capacity", None)

    # Convert arrays safely
    voltage = voltage.flatten()
    current = current.flatten()
    temperature = temperature.flatten()
    time = time.flatten()

    # Capacity is a cycle-level value
    if capacity is not None:
        try:
            capacity_value = float(capacity)
        except:
            capacity_value = None
    else:
        capacity_value = None

    # One row per measurement
    for i in range(len(time)):

        records.append({
            "battery_id": "B0005",
            "cycle_index": cycle_index,
            "discharge_number": discharge_number,
            "ambient_temperature": cycle.ambient_temperature,
            "time_seconds": time[i],
            "voltage": voltage[i],
            "current": current[i],
            "temperature": temperature[i],
            "capacity_Ah": capacity_value
        })

# ---------------------------------------------------------
# Create DataFrame
# ---------------------------------------------------------

df = pd.DataFrame(records)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print("=" * 70)
print("B0005 DISCHARGE EXTRACTION")
print("=" * 70)

print("\nDischarge cycles found:")
print(discharge_number)

print("\nTotal measurements:")
print(len(df))

print("\nColumns:")
print(list(df.columns))

print("\nFirst 10 rows:")
print(df.head(10))

print("\nMissing values:")
print(df.isnull().sum())

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)
print("EXTRACTION COMPLETE")
print("=" * 70)