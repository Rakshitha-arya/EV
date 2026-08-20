import os
import scipy.io

# ---------------------------------------------------------
# Project paths
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

print("=" * 70)
print("NASA B0005 DATA INSPECTION")
print("=" * 70)

print("\nFile:")
print(FILE_PATH)

# ---------------------------------------------------------
# Load MATLAB file
# ---------------------------------------------------------

mat = scipy.io.loadmat(
    FILE_PATH,
    squeeze_me=True,
    struct_as_record=False
)

print("\nTop-level variables:")
for key in mat.keys():
    if not key.startswith("__"):
        print("  ", key)

# ---------------------------------------------------------
# Get battery structure
# ---------------------------------------------------------

battery = mat["B0005"]

print("\nBattery object:")
print(type(battery))

# ---------------------------------------------------------
# Inspect available fields
# ---------------------------------------------------------

print("\nBattery fields:")

for field in battery._fieldnames:
    print("  ", field)

# ---------------------------------------------------------
# Inspect cycle structure
# ---------------------------------------------------------

cycles = battery.cycle

print("\nNumber of cycles:")
print(len(cycles))

# ---------------------------------------------------------
# Show first few cycles
# ---------------------------------------------------------

print("\nFirst 10 cycles:")

for i, cycle in enumerate(cycles[:10]):

    print(
        f"Cycle index {i}: "
        f"type={cycle.type}, "
        f"ambient_temperature={cycle.ambient_temperature}"
    )

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)