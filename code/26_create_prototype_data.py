"""
EV DIGITAL TWIN - STEP 26
Prototype sensor data interface

Creates a standardized prototype-data file that can later
be replaced by real ESP32 sensor readings.
"""

import os
import pandas as pd


OUTPUT_PATH = "processed/EV_prototype_sensor_data.csv"


print("=" * 65)
print("EV DIGITAL TWIN - PROTOTYPE SENSOR DATA INTERFACE")
print("=" * 65)


# ============================================================
# SAMPLE PROTOTYPE DATA
# ============================================================

data = {
    "timestamp": [
        "2026-08-16 17:10:00",
        "2026-08-16 17:10:05",
        "2026-08-16 17:10:10",
        "2026-08-16 17:10:15",
        "2026-08-16 17:10:20"
    ],

    "battery_voltage_V": [
        12.4,
        12.3,
        12.2,
        12.1,
        12.0
    ],

    "battery_current_A": [
        1.8,
        2.1,
        2.4,
        2.7,
        3.0
    ],

    "battery_temperature_C": [
        28.1,
        28.3,
        28.6,
        28.9,
        29.2
    ],

    "load_current_A": [
        1.2,
        1.5,
        1.8,
        2.1,
        2.4
    ],

    "gps_latitude": [
        12.9716,
        12.9717,
        12.9718,
        12.9719,
        12.9720
    ],

    "gps_longitude": [
        77.5946,
        77.5947,
        77.5948,
        77.5949,
        77.5950
    ],

    "gps_speed_kmph": [
        0.0,
        5.2,
        8.4,
        12.1,
        15.3
    ],

    "tyre_pressure_psi": [
        32.0,
        31.9,
        31.9,
        31.8,
        31.8
    ]
}


df = pd.DataFrame(data)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    "processed",
    exist_ok=True
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\nPrototype parameters:")

for column in df.columns:
    print(" -", column)


print("\nRows created:", len(df))

print("\nSample prototype data:")
print(df.to_string(index=False))


print("\nSaved to:")
print(OUTPUT_PATH)


print("\n" + "=" * 65)
print("PROTOTYPE DATA INTERFACE COMPLETE")
print("=" * 65)