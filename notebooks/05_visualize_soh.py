from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "calce_cs2_35_soh.csv"
)

df = pd.read_csv(INPUT_FILE)

plt.figure(figsize=(10, 5))

plt.plot(
    df["Cycle"],
    df["SOH_percent"],
    marker="o"
)

plt.xlabel("Cycle")
plt.ylabel("SOH (%)")
plt.title("CALCE CS2-35 Battery SOH")

plt.grid(True)

plt.tight_layout()

plt.show()