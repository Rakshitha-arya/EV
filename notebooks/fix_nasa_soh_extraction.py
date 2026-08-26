from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import loadmat


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Your actual dataset is outside flask_app
DATASET_ROOT = BASE_DIR.parent / "datasets" / "NASA"

# Search recursively inside all NASA folders
NASA_DIRS = [
    DATASET_ROOT / "extracted",
    DATASET_ROOT,
]

OUTPUT_DIR = BASE_DIR / "processed" / "soh"
OUTPUT_FILE = OUTPUT_DIR / "nasa_soh_features.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

BATTERY_NAMES = {
    "B0005",
    "B0006",
    "B0007",
    "B0018",
    "B0025",
    "B0026",
    "B0027",
    "B0028",
    "B0029",
    "B0030",
    "B0031",
    "B0032",
    "B0033",
    "B0034",
    "B0036",
    "B0038",
    "B0039",
    "B0040",
    "B0041",
    "B0042",
    "B0043",
    "B0044",
    "B0045",
    "B0046",
    "B0047",
    "B0048",
    "B0049",
    "B0050",
    "B0051",
    "B0052",
    "B0053",
    "B0054",
    "B0055",
    "B0056",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_string(value):
    """
    Convert MATLAB string/character/object values into Python string.
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, bytes):
        return value.decode(errors="ignore").strip()

    if isinstance(value, np.ndarray):
        if value.size == 1:
            return clean_string(value.reshape(-1)[0])

        if value.dtype.kind in {"U", "S"}:
            return "".join(str(x) for x in value.flatten()).strip()

    return str(value).strip()


def unwrap(value):
    """
    Recursively unwrap MATLAB object arrays.
    """
    while isinstance(value, np.ndarray) and value.size == 1:
        value = value.reshape(-1)[0]

    return value


def get_field(obj, field_name):
    """
    Read a field from either:
      - scipy mat_struct
      - numpy structured object
      - dictionary
    """
    obj = unwrap(obj)

    if obj is None:
        return None

    if hasattr(obj, field_name):
        return getattr(obj, field_name)

    if isinstance(obj, dict):
        return obj.get(field_name)

    if isinstance(obj, np.void):
        if obj.dtype.names and field_name in obj.dtype.names:
            return obj[field_name]

    return None


def get_array(value):
    """
    Convert MATLAB numeric arrays to flattened float arrays.
    """
    if value is None:
        return np.array([], dtype=float)

    value = unwrap(value)

    try:
        arr = np.asarray(value, dtype=float)
        return arr.reshape(-1)
    except Exception:
        return np.array([], dtype=float)


def get_cycles(mat, battery_id):
    """
    Extract the MATLAB 'cycle' structure from a battery.
    """
    if battery_id not in mat:
        return None

    battery = unwrap(mat[battery_id])

    cycles = get_field(battery, "cycle")

    if cycles is None:
        return None

    cycles = unwrap(cycles)

    # MATLAB structure arrays can appear as ndarray
    if isinstance(cycles, np.ndarray):
        cycles = cycles.reshape(-1)

    else:
        cycles = [cycles]

    return cycles


def find_mat_files():
    """
    Recursively find all NASA MAT files.
    """
    files = []

    seen = set()

    for root in NASA_DIRS:
        if not root.exists():
            continue

        for path in root.rglob("*.mat"):
            resolved = path.resolve()

            if resolved in seen:
                continue

            seen.add(resolved)

            # Only keep files corresponding to known battery IDs
            if path.stem.upper() in BATTERY_NAMES:
                files.append(path)

    return sorted(files)


def extract_capacity(data):
    """
    Extract the official NASA discharge Capacity field.

    NASA battery data provides:
        data.Capacity

    for discharge cycles.

    Capacity is measured in Ah.
    """
    capacity = get_field(data, "Capacity")

    if capacity is None:
        return None

    arr = get_array(capacity)

    if arr.size == 0:
        return None

    finite = arr[np.isfinite(arr)]

    if finite.size == 0:
        return None

    # Capacity should be positive.
    positive = finite[finite > 0]

    if positive.size == 0:
        return None

    return float(positive[-1])


def extract_measurement_features(data):
    """
    Extract useful discharge-cycle features from NASA data.
    """

    voltage = get_array(get_field(data, "Voltage_measured"))
    current = get_array(get_field(data, "Current_measured"))
    temperature = get_array(get_field(data, "Temperature_measured"))
    time = get_array(get_field(data, "Time"))

    features = {}

    if voltage.size:
        finite = voltage[np.isfinite(voltage)]

        if finite.size:
            features["Voltage_Min_V"] = float(np.min(finite))
            features["Voltage_Max_V"] = float(np.max(finite))
            features["Voltage_Mean_V"] = float(np.mean(finite))
            features["Voltage_Final_V"] = float(finite[-1])

    if current.size:
        finite = current[np.isfinite(current)]

        if finite.size:
            features["Current_Min_A"] = float(np.min(finite))
            features["Current_Max_A"] = float(np.max(finite))
            features["Current_Mean_A"] = float(np.mean(finite))

    if temperature.size:
        finite = temperature[np.isfinite(temperature)]

        if finite.size:
            features["Temperature_Min_C"] = float(np.min(finite))
            features["Temperature_Max_C"] = float(np.max(finite))
            features["Temperature_Mean_C"] = float(np.mean(finite))
            features["Temperature_Final_C"] = float(finite[-1])

    if time.size:
        finite = time[np.isfinite(time)]

        if finite.size:
            features["Discharge_Time_s"] = float(
                np.max(finite) - np.min(finite)
            )

    return features


def extract_battery(mat_file):
    """
    Extract discharge-cycle capacity and features from one MAT file.
    """

    battery_id = mat_file.stem.upper()

    print()
    print("-" * 70)
    print(f"Battery: {battery_id}")
    print(f"File: {mat_file}")

    try:
        mat = loadmat(
            mat_file,
            squeeze_me=True,
            struct_as_record=False
        )
    except Exception as exc:
        print(f"ERROR loading MAT file: {exc}")
        return []

    cycles = get_cycles(mat, battery_id)

    if cycles is None:
        print("ERROR: cycle structure not found.")
        return []

    rows = []

    discharge_count = 0

    for index, cycle in enumerate(cycles):

        cycle = unwrap(cycle)

        cycle_type = get_field(cycle, "type")
        cycle_type = clean_string(cycle_type).lower()

        if cycle_type != "discharge":
            continue

        data = get_field(cycle, "data")
        data = unwrap(data)

        if data is None:
            continue

        discharge_count += 1

        capacity = extract_capacity(data)

        if capacity is None:
            continue

        measurement_features = extract_measurement_features(data)

        row = {
            "Dataset": "NASA",
            "Battery_ID": battery_id,
            "Cycle": discharge_count,
            "Original_Cycle_Index": index,
            "Capacity_Ah": capacity,
        }

        row.update(measurement_features)

        rows.append(row)

    print(f"Discharge cycles: {discharge_count}")
    print(f"Valid capacity records: {len(rows)}")

    return rows


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("NASA SOH EXTRACTION - CORRECTED")
print("=" * 70)

print()
print("Project directory:")
print(BASE_DIR)

print()
print("NASA dataset root:")
print(DATASET_ROOT)

print()
print("Search directories:")

for directory in NASA_DIRS:
    print(f"  {directory}")

print()
print("=" * 70)
print("SEARCHING FOR NASA MAT FILES")
print("=" * 70)

mat_files = find_mat_files()

print()
print(f"MAT files found: {len(mat_files)}")

if not mat_files:
    print()
    print("ERROR: No NASA MAT files found.")
    print()
    print("Expected dataset location:")
    print(DATASET_ROOT)
    print()
    print("Please verify that your NASA folders contain .mat files.")
    raise RuntimeError("No NASA MAT files found.")


print()
print("MAT FILES:")

for path in mat_files:
    print(f"  {path}")


# ============================================================
# EXTRACT
# ============================================================

all_rows = []

for mat_file in mat_files:

    battery_id = mat_file.stem.upper()

    if battery_id not in BATTERY_NAMES:
        continue

    rows = extract_battery(mat_file)

    all_rows.extend(rows)


# ============================================================
# CREATE DATAFRAME
# ============================================================

print()
print("=" * 70)
print("CREATING NASA SOH DATASET")
print("=" * 70)

if not all_rows:
    raise RuntimeError(
        "NASA extraction produced zero valid discharge records."
    )

df = pd.DataFrame(all_rows)


# ============================================================
# CALCULATE SOH
# ============================================================

print()
print("Calculating battery-wise SOH...")

df["SOH_percent"] = np.nan

for battery_id, group in df.groupby("Battery_ID"):

    group = group.sort_values("Cycle")

    valid_capacity = group["Capacity_Ah"].notna()

    if valid_capacity.sum() == 0:
        continue

    first_capacity = group.loc[
        valid_capacity,
        "Capacity_Ah"
    ].iloc[0]

    if not np.isfinite(first_capacity) or first_capacity <= 0:
        continue

    mask = df["Battery_ID"] == battery_id

    df.loc[mask, "SOH_percent"] = (
        df.loc[mask, "Capacity_Ah"] /
        first_capacity *
        100.0
    )


# ============================================================
# REMOVE INVALID SOH
# ============================================================

df = df[
    df["SOH_percent"].notna()
].copy()


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    ["Battery_ID", "Cycle"]
).reset_index(drop=True)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("NASA SOH SUMMARY")
print("=" * 70)

print()

summary = (
    df.groupby("Battery_ID")["SOH_percent"]
    .agg(
        count="count",
        first="first",
        last="last",
        minimum="min",
        maximum="max"
    )
)

print(summary.to_string())


print()
print("Capacity summary:")

capacity_summary = (
    df.groupby("Battery_ID")["Capacity_Ah"]
    .agg(
        first="first",
        last="last",
        minimum="min",
        maximum="max"
    )
)

print(capacity_summary.to_string())


# ============================================================
# DATASET SUMMARY
# ============================================================

print()
print("=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

print(f"Rows: {len(df)}")
print(f"Batteries: {df['Battery_ID'].nunique()}")
print(f"Cycles: {df['Cycle'].nunique()}")


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
print("NASA SOH EXTRACTION COMPLETE")
print("=" * 70)

print()
print("Columns:")

for column in df.columns:
    print(f"  {column}")

print()
print("Important:")
print("SOH is calculated independently for each battery.")
print("The first valid NASA discharge capacity is used as 100% SOH.")
print("NASA Capacity is taken from data.Capacity for discharge cycles.")