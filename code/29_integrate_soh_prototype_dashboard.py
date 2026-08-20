import os
import pandas as pd
import matplotlib.pyplot as plt


print("=" * 70)
print("EV DIGITAL TWIN - SOH + PROTOTYPE INTEGRATION")
print("=" * 70)


# ============================================================
# FILES
# ============================================================

PROTOTYPE_FILE = "processed/EV_prototype_digital_twin.csv"
SOH_FILE = "processed/NASA_digital_twin_SOH.csv"

OUTPUT_CSV = "processed/EV_integrated_digital_twin.csv"
OUTPUT_PLOT = "results/EV_integrated_digital_twin_dashboard.png"


# ============================================================
# LOAD PROTOTYPE DATA
# ============================================================

print("\nLoading prototype digital twin data...")

prototype = pd.read_csv(PROTOTYPE_FILE)

print("Prototype rows:", len(prototype))


# ============================================================
# LOAD SOH DATA
# ============================================================

print("\nLoading SOH digital twin data...")

soh = pd.read_csv(SOH_FILE)

print("SOH rows:", len(soh))


# ============================================================
# GET LATEST SOH INFORMATION
# ============================================================

# Use the latest prediction available for the SOH model.
latest_soh = soh.iloc[-1]

predicted_soh = latest_soh["predicted_SOH_percent"]


# ============================================================
# SOH HEALTH CLASSIFICATION
# ============================================================

def classify_soh(soh_value):

    if soh_value >= 80:
        return "HEALTHY"

    elif soh_value >= 60:
        return "MODERATE"

    else:
        return "POOR"


soh_status = classify_soh(predicted_soh)


# ============================================================
# PROTOTYPE HEALTH
# ============================================================

prototype["soh_percent"] = predicted_soh
prototype["soh_status"] = soh_status


# ============================================================
# COMBINED VEHICLE STATUS
# ============================================================

def combined_status(row):

    if row["overall_vehicle_status"] == "HEALTHY" and row["soh_status"] == "HEALTHY":
        return "HEALTHY"

    elif row["soh_status"] == "POOR":
        return "POOR"

    else:
        return "MODERATE"


prototype["integrated_vehicle_status"] = prototype.apply(
    combined_status,
    axis=1
)


# ============================================================
# SAVE INTEGRATED DATA
# ============================================================

os.makedirs("processed", exist_ok=True)

prototype.to_csv(
    OUTPUT_CSV,
    index=False
)


# ============================================================
# LATEST STATE
# ============================================================

latest = prototype.iloc[-1]


print("\n" + "=" * 70)
print("INTEGRATED DIGITAL TWIN STATE")
print("=" * 70)

print("\nLatest timestamp:", latest["timestamp"])

print("\nPrototype parameters:")
print(
    "Battery voltage:",
    latest["battery_voltage_V"],
    "V"
)

print(
    "Battery current:",
    latest["battery_current_A"],
    "A"
)

print(
    "Battery temperature:",
    latest["battery_temperature_C"],
    "°C"
)

print(
    "Battery power:",
    latest["battery_power_W"],
    "W"
)

print(
    "Load power:",
    latest["load_power_W"],
    "W"
)

print(
    "GPS speed:",
    latest["gps_speed_kmph"],
    "km/h"
)

print(
    "Tyre pressure:",
    latest["tyre_pressure_psi"],
    "PSI"
)

print("\nSOH digital twin:")
print(
    "Predicted SOH:",
    round(predicted_soh, 2),
    "%"
)

print(
    "SOH status:",
    soh_status
)

print(
    "Vehicle status:",
    latest["overall_vehicle_status"]
)

print(
    "Integrated status:",
    latest["integrated_vehicle_status"]
)


# ============================================================
# CREATE DASHBOARD
# ============================================================

print("\nCreating integrated dashboard...")

fig = plt.figure(figsize=(16, 11))

fig.suptitle(
    "EV DIGITAL TWIN - INTEGRATED SOH + PROTOTYPE DASHBOARD",
    fontsize=18,
    fontweight="bold"
)


# ============================================================
# BATTERY VOLTAGE
# ============================================================

ax1 = plt.subplot(3, 2, 1)

ax1.plot(
    prototype["timestamp"],
    prototype["battery_voltage_V"],
    marker="o"
)

ax1.set_title("Battery Voltage")
ax1.set_ylabel("Voltage (V)")
ax1.grid(True)


# ============================================================
# BATTERY POWER / LOAD POWER
# ============================================================

ax2 = plt.subplot(3, 2, 2)

ax2.plot(
    prototype["timestamp"],
    prototype["battery_power_W"],
    marker="o",
    label="Battery Power"
)

ax2.plot(
    prototype["timestamp"],
    prototype["load_power_W"],
    marker="s",
    label="Load Power"
)

ax2.set_title("Power Monitoring")
ax2.set_ylabel("Power (W)")
ax2.legend()
ax2.grid(True)


# ============================================================
# TEMPERATURE
# ============================================================

ax3 = plt.subplot(3, 2, 3)

ax3.plot(
    prototype["timestamp"],
    prototype["battery_temperature_C"],
    marker="o"
)

ax3.set_title("Battery Temperature")
ax3.set_ylabel("Temperature (°C)")
ax3.grid(True)


# ============================================================
# SPEED
# ============================================================

ax4 = plt.subplot(3, 2, 4)

ax4.plot(
    prototype["timestamp"],
    prototype["gps_speed_kmph"],
    marker="o"
)

ax4.set_title("Vehicle Speed")
ax4.set_ylabel("Speed (km/h)")
ax4.grid(True)


# ============================================================
# TYRE PRESSURE
# ============================================================

ax5 = plt.subplot(3, 2, 5)

ax5.plot(
    prototype["timestamp"],
    prototype["tyre_pressure_psi"],
    marker="o"
)

ax5.set_title("Tyre Pressure")
ax5.set_ylabel("Pressure (PSI)")
ax5.grid(True)


# ============================================================
# SOH
# ============================================================

ax6 = plt.subplot(3, 2, 6)

ax6.axhline(
    80,
    linestyle="--",
    label="Healthy threshold"
)

ax6.axhline(
    60,
    linestyle="--",
    label="Moderate threshold"
)

ax6.plot(
    prototype["timestamp"],
    prototype["soh_percent"],
    marker="o",
    label="Predicted SOH"
)

ax6.set_title("Battery State of Health")
ax6.set_ylabel("SOH (%)")
ax6.set_ylim(0, 110)
ax6.legend()
ax6.grid(True)


# ============================================================
# FORMAT
# ============================================================

for ax in [
    ax1,
    ax2,
    ax3,
    ax4,
    ax5,
    ax6
]:

    ax.tick_params(
        axis="x",
        rotation=30
    )


# ============================================================
# SUMMARY
# ============================================================

summary = (
    f"SOH: {predicted_soh:.2f}% ({soh_status})   |   "
    f"Battery: {latest['battery_voltage_V']:.1f} V, "
    f"{latest['battery_current_A']:.1f} A   |   "
    f"Temperature: {latest['battery_temperature_C']:.1f} °C   |   "
    f"Speed: {latest['gps_speed_kmph']:.1f} km/h   |   "
    f"Tyre: {latest['tyre_pressure_psi']:.1f} PSI   |   "
    f"Status: {latest['integrated_vehicle_status']}"
)

fig.text(
    0.5,
    0.015,
    summary,
    ha="center",
    fontsize=10
)


# ============================================================
# SAVE
# ============================================================

os.makedirs("results", exist_ok=True)

plt.tight_layout(
    rect=[0, 0.07, 1, 0.94]
)

plt.savefig(
    OUTPUT_PLOT,
    dpi=200,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("FILES SAVED")
print("=" * 70)

print("\nIntegrated dataset:")
print(OUTPUT_CSV)

print("\nIntegrated dashboard:")
print(OUTPUT_PLOT)

print("\n" + "=" * 70)
print("INTEGRATED DIGITAL TWIN COMPLETE")
print("=" * 70)