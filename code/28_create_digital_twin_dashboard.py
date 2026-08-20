"""
EV DIGITAL TWIN - STEP 28
Prototype Dashboard

Creates a visual dashboard from:
processed/EV_prototype_digital_twin.csv
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


INPUT_PATH = "processed/EV_prototype_digital_twin.csv"
OUTPUT_PATH = "results/EV_digital_twin_dashboard.png"


print("=" * 65)
print("EV DIGITAL TWIN - PROTOTYPE DASHBOARD")
print("=" * 65)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading digital twin data...")

df = pd.read_csv(INPUT_PATH)

print("Rows loaded:", len(df))


# ============================================================
# CHECK COLUMNS
# ============================================================

required_columns = [
    "timestamp",
    "battery_voltage_V",
    "battery_current_A",
    "battery_temperature_C",
    "load_current_A",
    "gps_latitude",
    "gps_longitude",
    "gps_speed_kmph",
    "tyre_pressure_psi",
    "battery_power_W",
    "load_power_W",
    "power_difference_W",
    "temperature_status",
    "tyre_pressure_status",
    "overall_vehicle_status"
]

missing = [
    column for column in required_columns
    if column not in df.columns
]

if missing:
    print("\nERROR: Missing columns:")

    for column in missing:
        print(" -", column)

    raise SystemExit(1)


# ============================================================
# PREPARE DATA
# ============================================================

df["timestamp"] = pd.to_datetime(df["timestamp"])

x = df["timestamp"]


# ============================================================
# CREATE DASHBOARD
# ============================================================

fig = plt.figure(figsize=(15, 10))

fig.suptitle(
    "EV DIGITAL TWIN - PROTOTYPE MONITORING DASHBOARD",
    fontsize=18,
    fontweight="bold"
)


# ============================================================
# 1. BATTERY VOLTAGE
# ============================================================

ax1 = plt.subplot(3, 2, 1)

ax1.plot(
    x,
    df["battery_voltage_V"],
    marker="o"
)

ax1.set_title("Battery Voltage")
ax1.set_ylabel("Voltage (V)")
ax1.grid(True)


# ============================================================
# 2. BATTERY POWER VS LOAD POWER
# ============================================================

ax2 = plt.subplot(3, 2, 2)

ax2.plot(
    x,
    df["battery_power_W"],
    marker="o",
    label="Battery Power"
)

ax2.plot(
    x,
    df["load_power_W"],
    marker="s",
    label="Load Power"
)

ax2.set_title("Power Monitoring")
ax2.set_ylabel("Power (W)")
ax2.legend()
ax2.grid(True)


# ============================================================
# 3. BATTERY TEMPERATURE
# ============================================================

ax3 = plt.subplot(3, 2, 3)

ax3.plot(
    x,
    df["battery_temperature_C"],
    marker="o"
)

ax3.set_title("Battery Temperature")
ax3.set_ylabel("Temperature (°C)")
ax3.grid(True)


# ============================================================
# 4. VEHICLE SPEED
# ============================================================

ax4 = plt.subplot(3, 2, 4)

ax4.plot(
    x,
    df["gps_speed_kmph"],
    marker="o"
)

ax4.set_title("Vehicle Speed")
ax4.set_ylabel("Speed (km/h)")
ax4.grid(True)


# ============================================================
# 5. TYRE PRESSURE
# ============================================================

ax5 = plt.subplot(3, 2, 5)

ax5.plot(
    x,
    df["tyre_pressure_psi"],
    marker="o"
)

ax5.set_title("Tyre Pressure")
ax5.set_ylabel("Pressure (PSI)")
ax5.grid(True)


# ============================================================
# 6. CURRENT
# ============================================================

ax6 = plt.subplot(3, 2, 6)

ax6.plot(
    x,
    df["battery_current_A"],
    marker="o",
    label="Battery Current"
)

ax6.plot(
    x,
    df["load_current_A"],
    marker="s",
    label="Load Current"
)

ax6.set_title("Current Monitoring")
ax6.set_ylabel("Current (A)")
ax6.legend()
ax6.grid(True)


# ============================================================
# FORMAT X AXIS
# ============================================================

for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:

    ax.tick_params(axis="x", rotation=30)


# ============================================================
# LATEST STATE
# ============================================================

latest = df.iloc[-1]

status = latest["overall_vehicle_status"]

summary = (
    f"Latest State\n"
    f"Battery: {latest['battery_voltage_V']:.1f} V | "
    f"{latest['battery_current_A']:.1f} A | "
    f"{latest['battery_power_W']:.1f} W\n"
    f"Temperature: {latest['battery_temperature_C']:.1f} °C\n"
    f"Speed: {latest['gps_speed_kmph']:.1f} km/h\n"
    f"Tyre Pressure: {latest['tyre_pressure_psi']:.1f} PSI\n"
    f"Vehicle Status: {status}"
)

fig.text(
    0.5,
    0.015,
    summary,
    ha="center",
    fontsize=11
)


# ============================================================
# SAVE
# ============================================================

os.makedirs("results", exist_ok=True)

plt.tight_layout(
    rect=[0, 0.08, 1, 0.94]
)

plt.savefig(
    OUTPUT_PATH,
    dpi=200,
    bbox_inches="tight"
)

plt.close()


print("\n" + "=" * 65)
print("DASHBOARD SUMMARY")
print("=" * 65)

print("\nLatest timestamp:", latest["timestamp"])
print(
    "Battery power:",
    round(latest["battery_power_W"], 2),
    "W"
)
print(
    "Load power:",
    round(latest["load_power_W"], 2),
    "W"
)
print(
    "Temperature:",
    round(latest["battery_temperature_C"], 2),
    "°C"
)
print(
    "Speed:",
    round(latest["gps_speed_kmph"], 2),
    "km/h"
)
print(
    "Tyre pressure:",
    round(latest["tyre_pressure_psi"], 2),
    "PSI"
)
print(
    "Overall status:",
    latest["overall_vehicle_status"]
)

print("\nDashboard saved to:")
print(OUTPUT_PATH)

print("\n" + "=" * 65)
print("DIGITAL TWIN DASHBOARD COMPLETE")
print("=" * 65)