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
print("NASA SOH REFERENCE METHOD TEST")
print("=" * 70)

results = []

for battery_id, group in df.groupby("battery_id"):

    group = group.sort_values("cycle_number")

    capacities = group["capacity_Ah"].values

    # Keep only realistic positive capacities
    valid = capacities[
        capacities > 1.0
    ]

    if len(valid) < 10:

        print(
            f"{battery_id}: "
            f"NOT ENOUGH VALID CAPACITY VALUES"
        )

        continue

    # First 10 valid capacity measurements
    first_10 = valid[:10]

    reference_capacity = np.median(
        first_10
    )

    # Calculate SOH
    soh = (
        capacities /
        reference_capacity *
        100
    )

    results.append({

        "battery_id": battery_id,

        "cycles": len(group),

        "reference_capacity_Ah":
            reference_capacity,

        "first_capacity_Ah":
            capacities[0],

        "final_capacity_Ah":
            capacities[-1],

        "final_SOH_percent":
            soh[-1],

        "minimum_SOH_percent":
            soh.min(),

        "maximum_SOH_percent":
            soh.max()
    })

result_df = pd.DataFrame(results)

print("\nReference capacity results:")
print(
    result_df.to_string(
        index=False
    )
)

print("\n" + "=" * 70)
print("B0005 REFERENCE")
print("=" * 70)

print(
    result_df[
        result_df["battery_id"] == "B0005"
    ].to_string(index=False)
)

print("\n" + "=" * 70)
print("B0033 REFERENCE")
print("=" * 70)

print(
    result_df[
        result_df["battery_id"] == "B0033"
    ].to_string(index=False)
)

print("\n" + "=" * 70)