import pandas as pd
import os

print("=" * 70)
print("EV DIGITAL TWIN - FAULT DETECTION & VEHICLE HEALTH ANALYSIS")
print("=" * 70)

# ============================================================
# FILES
# ============================================================

prototype_file = "processed/EV_prototype_digital_twin.csv"
soh_file = "processed/NASA_digital_twin_SOH.csv"

print("\nLoading prototype digital twin data...")

if not os.path.exists(prototype_file):
    print("ERROR: Prototype file not found:")
    print(prototype_file)
    raise SystemExit

if not os.path.exists(soh_file):
    print("ERROR: SOH digital twin file not found:")
    print(soh_file)
    raise SystemExit

prototype = pd.read_csv(prototype_file)
soh = pd.read_csv(soh_file)

print("Prototype rows:", len(prototype))
print("SOH rows:", len(soh))

# ============================================================
# FIND SOH COLUMN
# ============================================================

print("\nSOH dataset columns:")
print(soh.columns.tolist())

possible_soh_columns = [
    "predicted_SOH",
    "predicted_SOH_percent",
    "Predicted_SOH",
    "SOH_percent"
]

soh_column = None

for col in possible_soh_columns:
    if col in soh.columns:
        soh_column = col
        break

if soh_column is None:
    print("\nERROR: Could not find SOH prediction column.")
    raise SystemExit

print("\nUsing SOH column:", soh_column)

# ============================================================
# GET LATEST SOH
# ============================================================

latest_soh_row = soh.iloc[-1]

predicted_soh = float(latest_soh_row[soh_column])

# ============================================================
# FAULT DETECTION
# ============================================================

latest = prototype.iloc[-1]

battery_voltage = float(latest["battery_voltage_V"])
battery_current = float(latest["battery_current_A"])
battery_temperature = float(latest["battery_temperature_C"])
tyre_pressure = float(latest["tyre_pressure_psi"])
gps_speed = float(latest["gps_speed_kmph"])

# ------------------------------------------------------------
# Battery voltage
# ------------------------------------------------------------

if battery_voltage < 10.5:
    voltage_status = "CRITICAL"
elif battery_voltage < 11.5:
    voltage_status = "WARNING"
else:
    voltage_status = "NORMAL"

# ------------------------------------------------------------
# Temperature
# ------------------------------------------------------------

if battery_temperature >= 45:
    temperature_status = "CRITICAL"
elif battery_temperature >= 40:
    temperature_status = "WARNING"
else:
    temperature_status = "NORMAL"

# ------------------------------------------------------------
# Tyre pressure
# ------------------------------------------------------------

if tyre_pressure < 26 or tyre_pressure > 38:
    tyre_status = "CRITICAL"
elif tyre_pressure < 28 or tyre_pressure > 36:
    tyre_status = "WARNING"
else:
    tyre_status = "NORMAL"

# ------------------------------------------------------------
# Battery current
# ------------------------------------------------------------

if battery_current > 10:
    current_status = "CRITICAL"
elif battery_current > 7:
    current_status = "WARNING"
else:
    current_status = "NORMAL"

# ------------------------------------------------------------
# SOH
# ------------------------------------------------------------

if predicted_soh < 60:
    soh_status = "CRITICAL"
elif predicted_soh < 80:
    soh_status = "WARNING"
else:
    soh_status = "NORMAL"

# ============================================================
# OVERALL STATUS
# ============================================================

statuses = [
    voltage_status,
    temperature_status,
    tyre_status,
    current_status,
    soh_status
]

if "CRITICAL" in statuses:
    overall_status = "CRITICAL"
elif "WARNING" in statuses:
    overall_status = "WARNING"
else:
    overall_status = "HEALTHY"

# ============================================================
# DISPLAY
# ============================================================

print("\n" + "=" * 70)
print("LATEST VEHICLE HEALTH")
print("=" * 70)

print(f"\nBattery voltage : {battery_voltage:.2f} V")
print(f"Battery current : {battery_current:.2f} A")
print(f"Temperature     : {battery_temperature:.2f} °C")
print(f"Tyre pressure   : {tyre_pressure:.2f} PSI")
print(f"Vehicle speed   : {gps_speed:.2f} km/h")
print(f"Predicted SOH   : {predicted_soh:.2f} %")

print("\nBattery voltage status :", voltage_status)
print("Temperature status     :", temperature_status)
print("Tyre pressure status   :", tyre_status)
print("Battery current status :", current_status)
print("SOH status              :", soh_status)

print("\n" + "=" * 70)
print("OVERALL VEHICLE STATUS")
print("=" * 70)

print("\n", overall_status)

# ============================================================
# CREATE RESULT DATASET
# ============================================================

result = latest.to_dict()

result["predicted_SOH"] = predicted_soh
result["battery_voltage_status"] = voltage_status
result["temperature_status"] = temperature_status
result["tyre_pressure_status"] = tyre_status
result["battery_current_status"] = current_status
result["SOH_status"] = soh_status
result["overall_fault_status"] = overall_status

result_df = pd.DataFrame([result])

# ============================================================
# SAVE
# ============================================================

output_file = "processed/EV_fault_detection_results.csv"

result_df.to_csv(output_file, index=False)

print("\nResults saved to:")
print(output_file)

print("\n" + "=" * 70)
print("FAULT DETECTION COMPLETE")
print("=" * 70)