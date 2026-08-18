import pandas as pd
import numpy as np
import time
import os

print("=" * 70)
print("EV DIGITAL TWIN - LIVE SENSOR SIMULATION")
print("=" * 70)

# ============================================================
# LOAD TRAINED SOH MODEL
# ============================================================

model_file = "models/NASA_tuned_GradientBoosting_SOH.pkl"

print("\nLoading trained SOH model...")

if not os.path.exists(model_file):
    print("ERROR: SOH model not found:")
    print(model_file)
    raise SystemExit

import joblib

model = joblib.load(model_file)

print("Model loaded successfully.")

# ============================================================
# MODEL FEATURES
# ============================================================

model_features = [
    "cycle_number",
    "ambient_temperature",
    "voltage_mean",
    "voltage_min",
    "voltage_max",
    "voltage_std",
    "current_mean",
    "current_min",
    "current_max",
    "current_std",
    "temperature_mean",
    "temperature_min",
    "temperature_max",
    "discharge_time_seconds",
    "voltage_change",
    "voltage_range",
    "current_range",
    "temperature_range",
    "temperature_change",
    "discharge_time_change_percent"
]

# ============================================================
# SIMULATED LIVE SENSOR DATA
# ============================================================

sensor_data = [
    [12.4, 1.8, 28.1, 1.2, 12.9716, 77.5946, 0.0, 32.0],
    [12.3, 2.1, 28.3, 1.5, 12.9717, 77.5947, 5.2, 31.9],
    [12.2, 2.4, 28.6, 1.8, 12.9718, 77.5948, 8.4, 31.9],
    [12.1, 2.7, 28.9, 2.1, 12.9719, 77.5949, 12.1, 31.8],
    [12.0, 3.0, 29.2, 2.4, 12.9720, 77.5950, 15.3, 31.8],
    [11.9, 3.2, 29.5, 2.7, 12.9721, 77.5951, 18.0, 31.7],
    [11.8, 3.4, 29.8, 3.0, 12.9722, 77.5952, 20.4, 31.6],
    [11.7, 3.6, 30.1, 3.2, 12.9723, 77.5953, 22.5, 31.5],
    [11.6, 3.8, 30.5, 3.4, 12.9724, 77.5954, 24.1, 31.4],
    [11.5, 4.0, 30.8, 3.6, 12.9725, 77.5955, 25.7, 31.3]
]

# ============================================================
# PREVIOUS VALUES
# ============================================================

previous_voltage = None
previous_temperature = None
previous_discharge_time = 100.0

results = []

# ============================================================
# LIVE SIMULATION
# ============================================================

for cycle, data in enumerate(sensor_data, start=1):

    (
        voltage,
        battery_current,
        temperature,
        load_current,
        latitude,
        longitude,
        speed,
        tyre_pressure
    ) = data

    # --------------------------------------------------------
    # Derived values
    # --------------------------------------------------------

    battery_power = voltage * battery_current
    load_power = voltage * load_current
    power_difference = battery_power - load_power

    voltage_min = voltage - 0.05
    voltage_max = voltage + 0.05
    voltage_std = 0.02

    current_min = battery_current - 0.1
    current_max = battery_current + 0.1
    current_std = 0.05

    temperature_min = temperature - 0.2
    temperature_max = temperature + 0.2

    # --------------------------------------------------------
    # Changes
    # --------------------------------------------------------

    if previous_voltage is None:
        voltage_change = 0.0
        temperature_change = 0.0
        discharge_time_change_percent = 0.0
    else:
        voltage_change = voltage - previous_voltage
        temperature_change = temperature - previous_temperature
        discharge_time_change_percent = (
            (105.0 - previous_discharge_time)
            / previous_discharge_time
        ) * 100

    voltage_range = voltage_max - voltage_min
    current_range = current_max - current_min
    temperature_range = temperature_max - temperature_min

    # --------------------------------------------------------
    # SOH prediction
    # --------------------------------------------------------
    #
    # The live prototype does not contain a real NASA cycle
    # measurement, so cycle number is used as the simulation
    # input while the remaining model features are derived
    # from the simulated sensor state.
    #

    model_row = {
        "cycle_number": cycle,
        "ambient_temperature": temperature,
        "voltage_mean": voltage,
        "voltage_min": voltage_min,
        "voltage_max": voltage_max,
        "voltage_std": voltage_std,
        "current_mean": battery_current,
        "current_min": current_min,
        "current_max": current_max,
        "current_std": current_std,
        "temperature_mean": temperature,
        "temperature_min": temperature_min,
        "temperature_max": temperature_max,
        "discharge_time_seconds": 105.0,
        "voltage_change": voltage_change,
        "voltage_range": voltage_range,
        "current_range": current_range,
        "temperature_range": temperature_range,
        "temperature_change": temperature_change,
        "discharge_time_change_percent":
            discharge_time_change_percent
    }

    X = pd.DataFrame([model_row])[model_features]

    predicted_soh = float(model.predict(X)[0])

    # --------------------------------------------------------
    # Health detection
    # --------------------------------------------------------

    if predicted_soh < 60:
        soh_status = "CRITICAL"
    elif predicted_soh < 80:
        soh_status = "WARNING"
    else:
        soh_status = "NORMAL"

    if voltage < 10.5:
        voltage_status = "CRITICAL"
    elif voltage < 11.5:
        voltage_status = "WARNING"
    else:
        voltage_status = "NORMAL"

    if temperature >= 45:
        temperature_status = "CRITICAL"
    elif temperature >= 40:
        temperature_status = "WARNING"
    else:
        temperature_status = "NORMAL"

    if tyre_pressure < 26 or tyre_pressure > 38:
        tyre_status = "CRITICAL"
    elif tyre_pressure < 28 or tyre_pressure > 36:
        tyre_status = "WARNING"
    else:
        tyre_status = "NORMAL"

    if battery_current > 10:
        current_status = "CRITICAL"
    elif battery_current > 7:
        current_status = "WARNING"
    else:
        current_status = "NORMAL"

    statuses = [
        soh_status,
        voltage_status,
        temperature_status,
        tyre_status,
        current_status
    ]

    if "CRITICAL" in statuses:
        vehicle_status = "CRITICAL"
    elif "WARNING" in statuses:
        vehicle_status = "WARNING"
    else:
        vehicle_status = "HEALTHY"

    # --------------------------------------------------------
    # Display live state
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print(f"LIVE UPDATE {cycle}/10")
    print("-" * 70)

    print(f"Battery voltage : {voltage:.2f} V")
    print(f"Battery current : {battery_current:.2f} A")
    print(f"Battery power   : {battery_power:.2f} W")
    print(f"Load power      : {load_power:.2f} W")
    print(f"Temperature     : {temperature:.2f} °C")
    print(f"GPS speed       : {speed:.2f} km/h")
    print(f"Tyre pressure   : {tyre_pressure:.2f} PSI")
    print(f"Predicted SOH   : {predicted_soh:.2f}%")
    print(f"Vehicle status  : {vehicle_status}")

    results.append({
        "cycle": cycle,
        "battery_voltage_V": voltage,
        "battery_current_A": battery_current,
        "battery_power_W": battery_power,
        "load_current_A": load_current,
        "load_power_W": load_power,
        "power_difference_W": power_difference,
        "battery_temperature_C": temperature,
        "gps_latitude": latitude,
        "gps_longitude": longitude,
        "gps_speed_kmph": speed,
        "tyre_pressure_psi": tyre_pressure,
        "predicted_SOH_percent": predicted_soh,
        "voltage_status": voltage_status,
        "current_status": current_status,
        "temperature_status": temperature_status,
        "tyre_pressure_status": tyre_status,
        "SOH_status": soh_status,
        "vehicle_status": vehicle_status
    })

    previous_voltage = voltage
    previous_temperature = temperature
    previous_discharge_time = 105.0

    time.sleep(1)

# ============================================================
# SAVE LIVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

output_file = "processed/EV_live_digital_twin.csv"

results_df.to_csv(output_file, index=False)

# ============================================================
# FINAL STATE
# ============================================================

latest = results_df.iloc[-1]

print("\n" + "=" * 70)
print("FINAL LIVE DIGITAL TWIN STATE")
print("=" * 70)

print(f"\nBattery voltage : {latest['battery_voltage_V']:.2f} V")
print(f"Battery current : {latest['battery_current_A']:.2f} A")
print(f"Battery power   : {latest['battery_power_W']:.2f} W")
print(f"Temperature     : {latest['battery_temperature_C']:.2f} °C")
print(f"GPS speed       : {latest['gps_speed_kmph']:.2f} km/h")
print(f"Tyre pressure   : {latest['tyre_pressure_psi']:.2f} PSI")
print(f"Predicted SOH   : {latest['predicted_SOH_percent']:.2f}%")
print(f"Vehicle status  : {latest['vehicle_status']}")

print("\nResults saved to:")
print(output_file)

print("\n" + "=" * 70)
print("LIVE DIGITAL TWIN SIMULATION COMPLETE")
print("=" * 70)