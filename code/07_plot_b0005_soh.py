import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_B0005_SOH.csv"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "B0005_SOH_curve.png"
)

df = pd.read_csv(INPUT_FILE)

plt.figure(figsize=(10, 6))

plt.plot(
    df["cycle_number"],
    df["SOH_percent"],
    marker="o",
    markersize=2
)

plt.xlabel("Discharge Cycle")
plt.ylabel("SOH (%)")
plt.title("NASA B0005 Battery SOH Degradation")

plt.grid(True)

plt.tight_layout()

plt.savefig(OUTPUT_FILE, dpi=300)

plt.show()

print("SOH plot saved to:")
print(OUTPUT_FILE)