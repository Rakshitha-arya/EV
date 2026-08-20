import os
import scipy.io
import numpy as np

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "NASA",
    "extracted",
    "3. BatteryAgingARC_25-44",
    "B0033.mat"
)

mat = scipy.io.loadmat(
    FILE_PATH,
    squeeze_me=True,
    struct_as_record=False
)

battery = mat["B0033"]
cycles = battery.cycle

print("=" * 70)
print("NASA B0033 CAPACITY INSPECTION")
print("=" * 70)

records = []

for cycle_index, cycle in enumerate(cycles):

    if cycle.type != "discharge":
        continue

    capacity = getattr(
        cycle.data,
        "Capacity",
        None
    )

    if capacity is None:
        continue

    try:
        capacity = float(capacity)
    except:
        continue

    records.append(
        (
            cycle_index,
            capacity
        )
    )

print("\nTotal discharge records:", len(records))

print("\nFirst 20 capacities:")

for i, (cycle, capacity) in enumerate(records[:20]):
    print(
        f"Cycle index {cycle:3d} -> "
        f"{capacity:.6f} Ah"
    )

print("\nLast 20 capacities:")

for cycle, capacity in records[-20:]:
    print(
        f"Cycle index {cycle:3d} -> "
        f"{capacity:.6f} Ah"
    )

values = np.array(
    [x[1] for x in records]
)

print("\nCapacity statistics:")

print(
    f"Minimum : {values.min():.6f} Ah"
)

print(
    f"Maximum : {values.max():.6f} Ah"
)

print(
    f"Median  : {np.median(values):.6f} Ah"
)

print(
    f"Mean    : {values.mean():.6f} Ah"
)

print(
    f"Zeros   : {np.sum(values == 0)}"
)

print(
    f"< 0.5Ah : {np.sum(values < 0.5)}"
)

print(
    f"> 2.0Ah : {np.sum(values > 2.0)}"
)

print("\n" + "=" * 70)