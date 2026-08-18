import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_clean_training_SOH.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "results"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "NASA_all_batteries_SOH.png"
)

df = pd.read_csv(INPUT_FILE)

plt.figure(figsize=(12, 7))

for battery_id, group in df.groupby("battery_id"):

    group = group.sort_values("cycle_number")

    plt.plot(
        group["cycle_number"],
        group["SOH_percent"],
        label=battery_id
    )

plt.xlabel("Discharge Cycle")
plt.ylabel("SOH (%)")

plt.title(
    "NASA Battery SOH Degradation"
)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.grid(True)

plt.tight_layout()

plt.savefig(
    OUTPUT_FILE,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("=" * 60)
print("NASA SOH VISUALIZATION COMPLETE")
print("=" * 60)

print("\nSaved to:")
print(OUTPUT_FILE)