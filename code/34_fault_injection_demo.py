import pandas as pd
import os

print("=" * 70)
print("EV DIGITAL TWIN - FAULT INJECTION & WARNING DEMONSTRATION")
print("=" * 70)

# ============================================================
# SIMULATED VEHICLE CONDITIONS
# ============================================================

scenarios = [
    {
        "scenario": "NORMAL",
        "battery_voltage_V": 12.0,
        "battery_current_A": 3.0,
        "battery_temperature_C": 29.2,
        "tyre_pressure_psi": 31.8,
        "gps_speed_kmph": 15.3,
        "predicted_SOH_percent": 90.13
    },
    {
        "scenario": "LOW_BATTERY_VOLTAGE",
        "battery_voltage_V": 10.9,
        "battery_current_A": 4.0,
        "battery_temperature_C": 30.0,
        "tyre_pressure_psi": 31.5,
        "gps_speed_kmph": 20.0,
        "predicted_SOH_percent": 89.5
    },
    {
        "scenario": "HIGH_TEMPERATURE",
        "battery_voltage_V": 12.0,
        "battery_current_A": 4.0,
        "battery_temperature_C": 43.5,
        "tyre_pressure_psi": 31.5,
        "gps_speed_kmph": 20.0,
        "predicted_SOH_percent": 88.0
    },
    {
        "scenario": "LOW_TYRE_PRESSURE",
        "battery_voltage_V": 12.0,
        "battery_current_A": 3.5,
        "battery_temperature_C": 30.0,
        "tyre_pressure_psi": 25.5,
        "gps_speed_kmph": 20.0,
        "predicted_SOH_percent": 87.5
    },
    {
        "scenario": "HIGH_CURRENT",
        "battery_voltage_V": 11.8,
        "battery_current_A": 8.5,
        "battery_temperature_C": 34.0,
        "tyre_pressure_psi": 31.5,
        "gps_speed_kmph": 25.0,
        "predicted_SOH_percent": 85.0
    },
    {
        "scenario": "LOW_SOH",
        "battery_voltage_V": 11.7,
        "battery_current_A": 4.5,
        "battery_temperature_C": 32.0,
        "tyre_pressure_psi": 31.0,
        "gps_speed_kmph": 25.0,
        "predicted_SOH_percent": 72.0
    },
    {
        "scenario": "CRITICAL_COMBINATION",
        "battery_voltage_V": 10.2,
        "battery_current_A": 11.0,
        "battery_temperature_C": 48.0,
        "tyre_pressure_psi": 24.0,
        "gps_speed_kmph": 30.0,
        "predicted_SOH_percent": 55.0
    }
]

# ============================================================
# FAULT DETECTION FUNCTIONS
# ============================================================

def check_voltage(voltage):
    if voltage < 10.5:
        return "CRITICAL"
    elif voltage < 11.5:
        return "WARNING"
    else:
        return "NORMAL"


def check_temperature(temperature):
    if temperature >= 45:
        return "CRITICAL"
    elif temperature >= 40:
        return "WARNING"
    else:
        return "NORMAL"


def check_tyre_pressure(pressure):
    if pressure < 26 or pressure > 38:
        return "CRITICAL"
    elif pressure < 28 or pressure > 36:
        return "WARNING"
    else:
        return "NORMAL"


def check_current(current):
    if current > 10:
        return "CRITICAL"
    elif current > 7:
        return "WARNING"
    else:
        return "NORMAL"


def check_soh(soh):
    if soh < 60:
        return "CRITICAL"
    elif soh < 80:
        return "WARNING"
    else:
        return "NORMAL"


# ============================================================
# RUN FAULT DETECTION
# ============================================================

results = []

for data in scenarios:

    voltage_status = check_voltage(
        data["battery_voltage_V"]
    )

    temperature_status = check_temperature(
        data["battery_temperature_C"]
    )

    tyre_status = check_tyre_pressure(
        data["tyre_pressure_psi"]
    )

    current_status = check_current(
        data["battery_current_A"]
    )

    soh_status = check_soh(
        data["predicted_SOH_percent"]
    )

    statuses = [
        voltage_status,
        temperature_status,
        tyre_status,
        current_status,
        soh_status
    ]

    if "CRITICAL" in statuses:
        vehicle_status = "CRITICAL"
    elif "WARNING" in statuses:
        vehicle_status = "WARNING"
    else:
        vehicle_status = "HEALTHY"

    battery_power = (
        data["battery_voltage_V"]
        * data["battery_current_A"]
    )

    print("\n" + "-" * 70)
    print(f"SCENARIO: {data['scenario']}")
    print("-" * 70)

    print(
        f"Battery voltage : "
        f"{data['battery_voltage_V']:.2f} V "
        f"[{voltage_status}]"
    )

    print(
        f"Battery current : "
        f"{data['battery_current_A']:.2f} A "
        f"[{current_status}]"
    )

    print(
        f"Temperature     : "
        f"{data['battery_temperature_C']:.2f} °C "
        f"[{temperature_status}]"
    )

    print(
        f"Tyre pressure   : "
        f"{data['tyre_pressure_psi']:.2f} PSI "
        f"[{tyre_status}]"
    )

    print(
        f"Predicted SOH   : "
        f"{data['predicted_SOH_percent']:.2f}% "
        f"[{soh_status}]"
    )

    print(
        f"Battery power   : "
        f"{battery_power:.2f} W"
    )

    print(
        f"VEHICLE STATUS  : "
        f"{vehicle_status}"
    )

    results.append({
        **data,
        "battery_power_W": battery_power,
        "voltage_status": voltage_status,
        "current_status": current_status,
        "temperature_status": temperature_status,
        "tyre_pressure_status": tyre_status,
        "SOH_status": soh_status,
        "vehicle_status": vehicle_status
    })


# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

os.makedirs("processed", exist_ok=True)

output_file = "processed/EV_fault_injection_results.csv"

results_df.to_csv(
    output_file,
    index=False
)

# ============================================================
# SUMMARY
# ============================================================

healthy_count = (
    results_df["vehicle_status"] == "HEALTHY"
).sum()

warning_count = (
    results_df["vehicle_status"] == "WARNING"
).sum()

critical_count = (
    results_df["vehicle_status"] == "CRITICAL"
).sum()

print("\n" + "=" * 70)
print("FAULT INJECTION SUMMARY")
print("=" * 70)

print(f"\nHealthy scenarios  : {healthy_count}")
print(f"Warning scenarios  : {warning_count}")
print(f"Critical scenarios : {critical_count}")

print("\n" + "=" * 70)
print("SCENARIO RESULTS")
print("=" * 70)

print(
    results_df[
        [
            "scenario",
            "predicted_SOH_percent",
            "voltage_status",
            "current_status",
            "temperature_status",
            "tyre_pressure_status",
            "SOH_status",
            "vehicle_status"
        ]
    ].to_string(index=False)
)

print("\nResults saved to:")
print(output_file)

print("\n" + "=" * 70)
print("FAULT INJECTION DEMONSTRATION COMPLETE")
print("=" * 70)