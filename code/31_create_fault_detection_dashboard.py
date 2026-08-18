import pandas as pd
import matplotlib.pyplot as plt
import os

print("=" * 70)
print("EV DIGITAL TWIN - FAULT DETECTION DASHBOARD")
print("=" * 70)

# ============================================================
# LOAD DATA
# ============================================================

input_file = "processed/EV_fault_detection_results.csv"

if not os.path.exists(input_file):
    print("ERROR: Fault detection results not found:")
    print(input_file)
    raise SystemExit

df = pd.read_csv(input_file)

print("\nRows loaded:", len(df))

latest = df.iloc[-1]

# ============================================================
# GET VALUES
# ============================================================

voltage = float(latest["battery_voltage_V"])
current = float(latest["battery_current_A"])
temperature = float(latest["battery_temperature_C"])
tyre_pressure = float(latest["tyre_pressure_psi"])
speed = float(latest["gps_speed_kmph"])
soh = float(latest["predicted_SOH"])

overall_status = str(latest["overall_fault_status"])

voltage_status = str(latest["battery_voltage_status"])
temperature_status = str(latest["temperature_status"])
tyre_status = str(latest["tyre_pressure_status"])
current_status = str(latest["battery_current_status"])
soh_status = str(latest["SOH_status"])

battery_power = voltage * current

# ============================================================
# DISPLAY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("LATEST VEHICLE HEALTH")
print("=" * 70)

print(f"\nBattery voltage : {voltage:.2f} V")
print(f"Battery current : {current:.2f} A")
print(f"Battery power   : {battery_power:.2f} W")
print(f"Temperature     : {temperature:.2f} °C")
print(f"Tyre pressure   : {tyre_pressure:.2f} PSI")
print(f"GPS speed       : {speed:.2f} km/h")
print(f"Predicted SOH   : {soh:.2f} %")

print("\nOverall status:", overall_status)

# ============================================================
# CREATE DASHBOARD
# ============================================================

fig = plt.figure(figsize=(14, 9))

fig.suptitle(
    "EV DIGITAL TWIN - FAULT DETECTION DASHBOARD",
    fontsize=20,
    fontweight="bold"
)

# ------------------------------------------------------------
# SOH
# ------------------------------------------------------------

ax1 = plt.subplot(2, 3, 1)

ax1.bar(["SOH"], [soh])
ax1.set_ylim(0, 110)
ax1.set_ylabel("SOH (%)")
ax1.set_title("Battery State of Health")

ax1.text(
    0,
    soh + 3,
    f"{soh:.2f}%",
    ha="center",
    fontsize=14,
    fontweight="bold"
)

# ------------------------------------------------------------
# Battery voltage
# ------------------------------------------------------------

ax2 = plt.subplot(2, 3, 2)

ax2.bar(["Voltage"], [voltage])
ax2.set_ylabel("Voltage (V)")
ax2.set_title("Battery Voltage")

ax2.text(
    0,
    voltage + 0.3,
    f"{voltage:.2f} V",
    ha="center",
    fontsize=13
)

# ------------------------------------------------------------
# Battery current
# ------------------------------------------------------------

ax3 = plt.subplot(2, 3, 3)

ax3.bar(["Current"], [current])
ax3.set_ylabel("Current (A)")
ax3.set_title("Battery Current")

ax3.text(
    0,
    current + 0.15,
    f"{current:.2f} A",
    ha="center",
    fontsize=13
)

# ------------------------------------------------------------
# Temperature
# ------------------------------------------------------------

ax4 = plt.subplot(2, 3, 4)

ax4.bar(["Temperature"], [temperature])
ax4.set_ylabel("Temperature (°C)")
ax4.set_title("Battery Temperature")

ax4.text(
    0,
    temperature + 1,
    f"{temperature:.2f} °C",
    ha="center",
    fontsize=13
)

# ------------------------------------------------------------
# Tyre pressure
# ------------------------------------------------------------

ax5 = plt.subplot(2, 3, 5)

ax5.bar(["Tyre Pressure"], [tyre_pressure])
ax5.set_ylabel("Pressure (PSI)")
ax5.set_title("Tyre Pressure")

ax5.text(
    0,
    tyre_pressure + 0.5,
    f"{tyre_pressure:.2f} PSI",
    ha="center",
    fontsize=13
)

# ------------------------------------------------------------
# Vehicle status
# ------------------------------------------------------------

ax6 = plt.subplot(2, 3, 6)

ax6.axis("off")

ax6.text(
    0.5,
    0.70,
    "VEHICLE STATUS",
    ha="center",
    fontsize=16,
    fontweight="bold"
)

ax6.text(
    0.5,
    0.50,
    overall_status,
    ha="center",
    va="center",
    fontsize=24,
    fontweight="bold"
)

ax6.text(
    0.5,
    0.25,
    f"GPS Speed: {speed:.2f} km/h",
    ha="center",
    fontsize=13
)

# ============================================================
# FAULT STATUS TEXT
# ============================================================

fig.text(
    0.5,
    0.02,
    f"Voltage: {voltage_status}   |   "
    f"Current: {current_status}   |   "
    f"Temperature: {temperature_status}   |   "
    f"Tyre: {tyre_status}   |   "
    f"SOH: {soh_status}",
    ha="center",
    fontsize=11
)

plt.tight_layout(rect=[0, 0.05, 1, 0.94])

# ============================================================
# SAVE
# ============================================================

output_file = "results/EV_fault_detection_dashboard.png"

os.makedirs("results", exist_ok=True)

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("\n" + "=" * 70)
print("DASHBOARD SAVED")
print("=" * 70)

print("\nSaved to:")
print(output_file)

print("\n" + "=" * 70)
print("FAULT DETECTION DASHBOARD COMPLETE")
print("=" * 70)