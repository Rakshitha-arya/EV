import pandas as pd
import matplotlib.pyplot as plt
import os

print("=" * 70)
print("EV DIGITAL TWIN - LIVE DASHBOARD")
print("=" * 70)

# ============================================================
# LOAD LIVE DIGITAL TWIN DATA
# ============================================================

input_file = "processed/EV_live_digital_twin.csv"

if not os.path.exists(input_file):
    print("\nERROR: Live Digital Twin data not found:")
    print(input_file)
    raise SystemExit

df = pd.read_csv(input_file)

print("\nRows loaded:", len(df))

if len(df) == 0:
    print("ERROR: Dataset is empty.")
    raise SystemExit

# ============================================================
# LATEST STATE
# ============================================================

latest = df.iloc[-1]

voltage = float(latest["battery_voltage_V"])
current = float(latest["battery_current_A"])
battery_power = float(latest["battery_power_W"])
load_power = float(latest["load_power_W"])
temperature = float(latest["battery_temperature_C"])
speed = float(latest["gps_speed_kmph"])
tyre_pressure = float(latest["tyre_pressure_psi"])
soh = float(latest["predicted_SOH_percent"])

vehicle_status = str(latest["vehicle_status"])

print("\n" + "=" * 70)
print("LATEST DIGITAL TWIN STATE")
print("=" * 70)

print(f"\nBattery voltage : {voltage:.2f} V")
print(f"Battery current : {current:.2f} A")
print(f"Battery power   : {battery_power:.2f} W")
print(f"Load power      : {load_power:.2f} W")
print(f"Temperature     : {temperature:.2f} °C")
print(f"GPS speed       : {speed:.2f} km/h")
print(f"Tyre pressure   : {tyre_pressure:.2f} PSI")
print(f"Predicted SOH   : {soh:.2f}%")
print(f"Vehicle status  : {vehicle_status}")

# ============================================================
# CREATE DASHBOARD
# ============================================================

fig = plt.figure(figsize=(15, 10))

fig.suptitle(
    "EV DIGITAL TWIN - LIVE MONITORING DASHBOARD",
    fontsize=20,
    fontweight="bold"
)

# ============================================================
# 1. BATTERY VOLTAGE
# ============================================================

ax1 = plt.subplot(3, 3, 1)

ax1.plot(
    df["cycle"],
    df["battery_voltage_V"],
    marker="o"
)

ax1.set_title("Battery Voltage")
ax1.set_xlabel("Live Update")
ax1.set_ylabel("Voltage (V)")
ax1.grid(True)

# ============================================================
# 2. BATTERY CURRENT
# ============================================================

ax2 = plt.subplot(3, 3, 2)

ax2.plot(
    df["cycle"],
    df["battery_current_A"],
    marker="o"
)

ax2.set_title("Battery Current")
ax2.set_xlabel("Live Update")
ax2.set_ylabel("Current (A)")
ax2.grid(True)

# ============================================================
# 3. BATTERY TEMPERATURE
# ============================================================

ax3 = plt.subplot(3, 3, 3)

ax3.plot(
    df["cycle"],
    df["battery_temperature_C"],
    marker="o"
)

ax3.set_title("Battery Temperature")
ax3.set_xlabel("Live Update")
ax3.set_ylabel("Temperature (°C)")
ax3.grid(True)

# ============================================================
# 4. GPS SPEED
# ============================================================

ax4 = plt.subplot(3, 3, 4)

ax4.plot(
    df["cycle"],
    df["gps_speed_kmph"],
    marker="o"
)

ax4.set_title("Vehicle Speed")
ax4.set_xlabel("Live Update")
ax4.set_ylabel("Speed (km/h)")
ax4.grid(True)

# ============================================================
# 5. TYRE PRESSURE
# ============================================================

ax5 = plt.subplot(3, 3, 5)

ax5.plot(
    df["cycle"],
    df["tyre_pressure_psi"],
    marker="o"
)

ax5.set_title("Tyre Pressure")
ax5.set_xlabel("Live Update")
ax5.set_ylabel("Pressure (PSI)")
ax5.grid(True)

# ============================================================
# 6. SOH
# ============================================================

ax6 = plt.subplot(3, 3, 6)

ax6.plot(
    df["cycle"],
    df["predicted_SOH_percent"],
    marker="o"
)

ax6.set_title("Predicted Battery SOH")
ax6.set_xlabel("Live Update")
ax6.set_ylabel("SOH (%)")
ax6.grid(True)

# ============================================================
# 7. BATTERY POWER VS LOAD POWER
# ============================================================

ax7 = plt.subplot(3, 3, 7)

ax7.plot(
    df["cycle"],
    df["battery_power_W"],
    marker="o",
    label="Battery Power"
)

ax7.plot(
    df["cycle"],
    df["load_power_W"],
    marker="o",
    label="Load Power"
)

ax7.set_title("Battery Power vs Load Power")
ax7.set_xlabel("Live Update")
ax7.set_ylabel("Power (W)")
ax7.legend()
ax7.grid(True)

# ============================================================
# 8. POWER DIFFERENCE
# ============================================================

ax8 = plt.subplot(3, 3, 8)

ax8.plot(
    df["cycle"],
    df["power_difference_W"],
    marker="o"
)

ax8.set_title("Power Difference")
ax8.set_xlabel("Live Update")
ax8.set_ylabel("Power Difference (W)")
ax8.grid(True)

# ============================================================
# 9. VEHICLE STATUS
# ============================================================

ax9 = plt.subplot(3, 3, 9)

ax9.axis("off")

ax9.text(
    0.5,
    0.75,
    "VEHICLE STATUS",
    ha="center",
    fontsize=17,
    fontweight="bold"
)

ax9.text(
    0.5,
    0.52,
    vehicle_status,
    ha="center",
    va="center",
    fontsize=25,
    fontweight="bold"
)

ax9.text(
    0.5,
    0.30,
    f"SOH: {soh:.2f}%",
    ha="center",
    fontsize=14
)

ax9.text(
    0.5,
    0.18,
    f"Speed: {speed:.2f} km/h",
    ha="center",
    fontsize=13
)

# ============================================================
# SAVE DASHBOARD
# ============================================================

plt.tight_layout(rect=[0, 0, 1, 0.95])

os.makedirs("results", exist_ok=True)

output_file = "results/EV_live_digital_twin_dashboard.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("LIVE DASHBOARD CREATED")
print("=" * 70)

print("\nSaved to:")
print(output_file)

print("\n" + "=" * 70)
print("LIVE DIGITAL TWIN DASHBOARD COMPLETE")
print("=" * 70)