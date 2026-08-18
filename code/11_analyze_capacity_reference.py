import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_all_batteries_SOH.csv"
)

df = pd.read_csv(INPUT_FILE)

print("=" * 70)
print("NASA CAPACITY REFERENCE ANALYSIS")
print("=" * 70)

for battery_id in ["B0005", "B0033"]:

    battery = df[
        df["battery_id"] == battery_id
    ].sort_values("cycle_number")

    capacity = battery["capacity_Ah"].values

    print("\n" + "-" * 70)
    print(f"Battery: {battery_id}")
    print("-" * 70)

    print("\nFirst 20 capacity values:")

    for i, value in enumerate(capacity[:20], start=1):

        print(
            f"Cycle {i:3d}: "
            f"{value:.6f} Ah"
        )

    # Ignore extremely small values
    valid = capacity[
        capacity > 0.5
    ]

    print("\nCapacity > 0.5 Ah:")

    print(
        f"Count : {len(valid)}"
    )

    print(
        f"Median: {np.median(valid):.6f} Ah"
    )

    print(
        f"Mean  : {np.mean(valid):.6f} Ah"
    )

    # First 10 valid measurements
    first_valid = valid[:10]

    print("\nFirst 10 valid capacities:")

    for value in first_valid:

        print(
            f"{value:.6f} Ah"
        )

print("\n" + "=" * 70)