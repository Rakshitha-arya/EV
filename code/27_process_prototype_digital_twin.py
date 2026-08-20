"""
EV DIGITAL TWIN - STEP 27
Prototype Digital Twin Processing

Reads prototype sensor data and calculates:
- Battery power
- Load power
- Power difference
- Battery temperature status
- Tyre pressure status
- Vehicle speed status
- Overall vehicle status
"""

import os
import pandas as pd


INPUT_PATH = "processed/EV_prototype_sensor_data.csv"
OUTPUT_PATH = "processed/EV_prototype_digital_twin.csv"


print("=" * 65)
print("EV DIGITAL TWIN - PROTOTYPE DIGITAL TWIN PROCESSOR")
print("=" * 65)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading prototype sensor data...")

df = pd.read_csv(INPUT_PATH)

print("Rows loaded:", len(df))


# ============================================================
# CHECK REQUIRED COLUMNS
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
    "tyre_pressure_psi"
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


print("All required prototype fields found.")


# ============================================================
# BATTERY POWER
# ============================================================

df["battery_power_W"] = (
    df["battery_voltage_V"]
    * df["battery_current_A"]
)


# ============================================================
# LOAD POWER
# ============================================================

df["load_power_W"] = (
    df["battery_voltage_V"]
    * df["load_current_A"]
)


# ============================================================
# POWER DIFFERENCE
# ============================================================

df["power_difference_W"] = (
    df["battery_power_W"]
    - df["load_power_W"]
)


# ============================================================
# BATTERY TEMPERATURE STATUS
# ============================================================

def temperature_status(temp):

    if temp < 20:
        return "LOW"

    elif temp <= 40:
        return "NORMAL"

    elif temp <= 50:
        return "HIGH"

    else:
        return "CRITICAL"


df["temperature_status"] = (
    df["battery_temperature_C"]
    .apply(temperature_status)
)


# ============================================================
# TYRE PRESSURE STATUS
# ============================================================

def tyre_status(pressure):

    if pressure < 28:
        return "LOW"

    elif pressure <= 35:
        return "NORMAL"

    else:
        return "HIGH"


df["tyre_pressure_status"] = (
    df["tyre_pressure_psi"]
    .apply(tyre_status)
)


# ============================================================
# SPEED STATUS
# ============================================================

def speed_status(speed):

    if speed == 0:
        return "STOPPED"

    elif speed <= 20:
        return "LOW_SPEED"

    elif speed <= 40:
        return "NORMAL_SPEED"

    else:
        return "HIGH_SPEED"


df["speed_status"] = (
    df["gps_speed_kmph"]
    .apply(speed_status)
)


# ============================================================
# BATTERY VOLTAGE STATUS
# ============================================================

def voltage_status(voltage):

    if voltage < 11.0:
        return "LOW"

    elif voltage <= 12.6:
        return "NORMAL"

    else:
        return "HIGH"


df["voltage_status"] = (
    df["battery_voltage_V"]
    .apply(voltage_status)
)


# ============================================================
# OVERALL VEHICLE HEALTH
# ============================================================

def overall_status(row):

    critical_conditions = [
        row["temperature_status"] == "CRITICAL",
        row["voltage_status"] == "LOW",
        row["tyre_pressure_status"] == "LOW"
    ]

    warning_conditions = [
        row["temperature_status"] == "HIGH",
        row["voltage_status"] == "HIGH",
        row["tyre_pressure_status"] == "HIGH"
    ]

    if any(critical_conditions):
        return "CRITICAL"

    elif any(warning_conditions):
        return "WARNING"

    else:
        return "HEALTHY"


df["overall_vehicle_status"] = (
    df.apply(overall_status, axis=1)
)


# ============================================================
# SAVE RESULT
# ============================================================

os.makedirs("processed", exist_ok=True)

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 65)
print("DIGITAL TWIN RESULTS")
print("=" * 65)

print("\nBattery power:")
print(
    df["battery_power_W"]
    .round(2)
    .tolist()
)

print("\nLoad power:")
print(
    df["load_power_W"]
    .round(2)
    .tolist()
)

print("\nPower difference:")
print(
    df["power_difference_W"]
    .round(2)
    .tolist()
)

print("\nTemperature status:")
print(
    df["temperature_status"]
    .tolist()
)

print("\nTyre pressure status:")
print(
    df["tyre_pressure_status"]
    .tolist()
)

print("\nVehicle status:")
print(
    df["overall_vehicle_status"]
    .tolist()
)


print("\n" + "=" * 65)
print("LATEST DIGITAL TWIN STATE")
print("=" * 65)

latest = df.iloc[-1]

print("\nTimestamp:", latest["timestamp"])
print(
    "Battery voltage:",
    round(latest["battery_voltage_V"], 2),
    "V"
)
print(
    "Battery current:",
    round(latest["battery_current_A"], 2),
    "A"
)
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
    "Battery temperature:",
    round(latest["battery_temperature_C"], 2),
    "°C"
)
print(
    "GPS speed:",
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


print("\nSaved to:")
print(OUTPUT_PATH)

print("\n" + "=" * 65)
print("PROTOTYPE DIGITAL TWIN PROCESSING COMPLETE")
print("=" * 65)