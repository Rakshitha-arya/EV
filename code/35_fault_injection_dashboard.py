import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ================================================================
# EV DIGITAL TWIN - FAULT INJECTION DASHBOARD
# ================================================================

print("=" * 70)
print("EV DIGITAL TWIN - FAULT INJECTION DASHBOARD")
print("=" * 70)

INPUT_FILE = Path("processed/EV_fault_injection_results.csv")
OUTPUT_FILE = Path("results/EV_fault_injection_dashboard.png")

# ----------------------------------------------------------------
# Load data
# ----------------------------------------------------------------
if not INPUT_FILE.exists():
    print(f"\nERROR: File not found:")
    print(INPUT_FILE)
    raise SystemExit(1)

df = pd.read_csv(INPUT_FILE)

print(f"\nRows loaded: {len(df)}")

# ----------------------------------------------------------------
# Check required columns
# ----------------------------------------------------------------
required_columns = [
    "scenario",
    "predicted_SOH_percent",
    "voltage_status",
    "current_status",
    "temperature_status",
    "tyre_pressure_status",
    "SOH_status",
    "vehicle_status"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    print("\nERROR: Missing required columns:")
    for c in missing:
        print(f" - {c}")
    raise SystemExit(1)

# ----------------------------------------------------------------
# Display summary
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("FAULT INJECTION SUMMARY")
print("=" * 70)

status_counts = df["vehicle_status"].value_counts()

for status in ["HEALTHY", "WARNING", "CRITICAL"]:
    print(f"{status:10s}: {status_counts.get(status, 0)}")

# ----------------------------------------------------------------
# Create status numeric value for plotting
# ----------------------------------------------------------------
status_map = {
    "HEALTHY": 0,
    "WARNING": 1,
    "CRITICAL": 2
}

df["status_level"] = df["vehicle_status"].map(status_map)

# ----------------------------------------------------------------
# Create dashboard
# ----------------------------------------------------------------
fig = plt.figure(figsize=(16, 10))

# ================================================================
# 1. Scenario health status
# ================================================================
ax1 = plt.subplot(2, 2, 1)

ax1.bar(
    range(len(df)),
    df["status_level"],
    tick_label=df["scenario"]
)

ax1.set_title("Fault Injection - Vehicle Health Status")
ax1.set_ylabel("Health Level")
ax1.set_ylim(-0.2, 2.5)

ax1.set_yticks([0, 1, 2])
ax1.set_yticklabels([
    "HEALTHY",
    "WARNING",
    "CRITICAL"
])

plt.setp(
    ax1.get_xticklabels(),
    rotation=45,
    ha="right"
)

# ================================================================
# 2. Predicted SOH
# ================================================================
ax2 = plt.subplot(2, 2, 2)

ax2.bar(
    range(len(df)),
    df["predicted_SOH_percent"]
)

ax2.axhline(
    80,
    linestyle="--",
    label="80% SOH"
)

ax2.axhline(
    70,
    linestyle="--",
    label="70% SOH"
)

ax2.set_title("Predicted Battery SOH")
ax2.set_ylabel("SOH (%)")

ax2.set_xticks(range(len(df)))
ax2.set_xticklabels(
    df["scenario"],
    rotation=45,
    ha="right"
)

ax2.legend()

# ================================================================
# 3. Fault status matrix
# ================================================================
ax3 = plt.subplot(2, 2, 3)

status_columns = [
    "voltage_status",
    "current_status",
    "temperature_status",
    "tyre_pressure_status",
    "SOH_status"
]

status_matrix = []

for _, row in df.iterrows():
    values = []

    for column in status_columns:
        status = str(row[column])

        if status == "NORMAL":
            values.append(0)
        elif status == "WARNING":
            values.append(1)
        elif status == "CRITICAL":
            values.append(2)
        else:
            values.append(-1)

    status_matrix.append(values)

im = ax3.imshow(
    status_matrix,
    aspect="auto"
)

ax3.set_title("Fault Status Matrix")

ax3.set_xticks(range(len(status_columns)))
ax3.set_xticklabels([
    "Voltage",
    "Current",
    "Temperature",
    "Tyre Pressure",
    "SOH"
])

ax3.set_yticks(range(len(df)))
ax3.set_yticklabels(df["scenario"])

plt.setp(
    ax3.get_xticklabels(),
    rotation=30,
    ha="right"
)

# ================================================================
# 4. Overall scenario table
# ================================================================
ax4 = plt.subplot(2, 2, 4)
ax4.axis("off")

table_data = []

for _, row in df.iterrows():

    table_data.append([
        row["scenario"],
        f'{row["predicted_SOH_percent"]:.1f}%',
        row["voltage_status"],
        row["current_status"],
        row["temperature_status"],
        row["tyre_pressure_status"],
        row["SOH_status"],
        row["vehicle_status"]
    ])

columns = [
    "Scenario",
    "SOH",
    "Voltage",
    "Current",
    "Temp",
    "Tyre",
    "SOH Status",
    "Vehicle"
]

table = ax4.table(
    cellText=table_data,
    colLabels=columns,
    loc="center",
    cellLoc="center"
)

table.auto_set_font_size(False)
table.set_fontsize(7)
table.scale(1, 1.5)

ax4.set_title(
    "Fault Injection Scenario Results",
    pad=15
)

# ================================================================
# Dashboard title
# ================================================================
fig.suptitle(
    "EV DIGITAL TWIN - FAULT INJECTION & VEHICLE HEALTH DASHBOARD",
    fontsize=18,
    fontweight="bold"
)

plt.tight_layout(rect=[0, 0, 1, 0.95])

# ----------------------------------------------------------------
# Save dashboard
# ----------------------------------------------------------------
OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

plt.savefig(
    OUTPUT_FILE,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("\n" + "=" * 70)
print("DASHBOARD SAVED")
print("=" * 70)

print("\nSaved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)
print("FAULT INJECTION DASHBOARD COMPLETE")
print("=" * 70)