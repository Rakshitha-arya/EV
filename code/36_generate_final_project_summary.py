import pandas as pd
from pathlib import Path

# ================================================================
# EV DIGITAL TWIN - FINAL PROJECT RESULTS SUMMARY
# ================================================================

print("=" * 70)
print("EV DIGITAL TWIN - FINAL PROJECT RESULTS SUMMARY")
print("=" * 70)

# ----------------------------------------------------------------
# File paths
# ----------------------------------------------------------------
model_comparison_file = Path(
    "processed/NASA_model_comparison.csv"
)

final_evaluation_file = Path(
    "processed/NASA_final_SOH_evaluation.csv"
)

final_predictions_file = Path(
    "processed/NASA_final_SOH_predictions.csv"
)

digital_twin_file = Path(
    "processed/NASA_digital_twin_SOH.csv"
)

prototype_file = Path(
    "processed/EV_prototype_digital_twin.csv"
)

fault_detection_file = Path(
    "processed/EV_fault_detection_results.csv"
)

fault_injection_file = Path(
    "processed/EV_fault_injection_results.csv"
)

output_file = Path(
    "processed/EV_DIGITAL_TWIN_FINAL_SUMMARY.txt"
)

# ----------------------------------------------------------------
# Helper function
# ----------------------------------------------------------------
def load_csv(path):
    if path.exists():
        return pd.read_csv(path)
    return None


# ----------------------------------------------------------------
# Load results
# ----------------------------------------------------------------
model_comparison = load_csv(model_comparison_file)
final_evaluation = load_csv(final_evaluation_file)
final_predictions = load_csv(final_predictions_file)
digital_twin = load_csv(digital_twin_file)
prototype = load_csv(prototype_file)
fault_detection = load_csv(fault_detection_file)
fault_injection = load_csv(fault_injection_file)

# ----------------------------------------------------------------
# Start summary
# ----------------------------------------------------------------
summary = []

summary.append("=" * 70)
summary.append("EV DIGITAL TWIN - FINAL PROJECT RESULTS SUMMARY")
summary.append("=" * 70)

summary.append("")
summary.append("1. PROJECT PIPELINE")
summary.append("-" * 70)
summary.append(
    "NASA battery data -> SOH estimation -> Prototype sensor data -> "
    "Digital Twin -> Fault Detection -> Fault Injection -> Dashboard"
)

# ----------------------------------------------------------------
# SOH MODEL
# ----------------------------------------------------------------
summary.append("")
summary.append("2. FINAL SOH MODEL")
summary.append("-" * 70)

if final_evaluation is not None and len(final_evaluation) > 0:

    row = final_evaluation.iloc[0]

    for column in final_evaluation.columns:
        summary.append(
            f"{column}: {row[column]}"
        )

elif model_comparison is not None:

    best = model_comparison.iloc[0]

    summary.append(
        f"Best model: {best['model']}"
    )

    summary.append(
        f"MAE: {best['MAE_percent']:.4f}%"
    )

    summary.append(
        f"RMSE: {best['RMSE_percent']:.4f}%"
    )

    summary.append(
        f"R²: {best['R2']:.4f}"
    )

else:
    summary.append("Final SOH evaluation file not found.")

# ----------------------------------------------------------------
# MODEL COMPARISON
# ----------------------------------------------------------------
summary.append("")
summary.append("3. MODEL COMPARISON")
summary.append("-" * 70)

if model_comparison is not None:

    summary.append(
        model_comparison.to_string(index=False)
    )

else:
    summary.append(
        "Model comparison file not found."
    )

# ----------------------------------------------------------------
# BATTERY-WISE PERFORMANCE
# ----------------------------------------------------------------
summary.append("")
summary.append("4. BATTERY-WISE SOH PERFORMANCE")
summary.append("-" * 70)

if final_predictions is not None:

    if "battery_id" in final_predictions.columns:

        grouped = final_predictions.groupby(
            "battery_id"
        )

        for battery_id, group in grouped:

            actual = group["SOH_percent"]

            predicted = group[
                "predicted_SOH_percent"
            ]

            mae = (
                (actual - predicted)
                .abs()
                .mean()
            )

            summary.append(
                f"{battery_id}: "
                f"Cycles={len(group)}, "
                f"MAE={mae:.4f}%"
            )

else:
    summary.append(
        "Final prediction file not found."
    )

# ----------------------------------------------------------------
# DIGITAL TWIN SOH
# ----------------------------------------------------------------
summary.append("")
summary.append("5. DIGITAL TWIN SOH STATUS")
summary.append("-" * 70)

if digital_twin is not None:

    if len(digital_twin) > 0:

        latest = digital_twin.iloc[-1]

        summary.append(
            f"Battery: "
            f"{latest.get('battery_id', 'N/A')}"
        )

        summary.append(
            f"Latest cycle: "
            f"{latest.get('cycle_number', 'N/A')}"
        )

        if "predicted_SOH_percent" in digital_twin.columns:

            summary.append(
                f"Predicted SOH: "
                f"{latest['predicted_SOH_percent']:.2f}%"
            )

        if "battery_health" in digital_twin.columns:

            summary.append(
                f"Battery health: "
                f"{latest['battery_health']}"
            )

else:
    summary.append(
        "Digital twin SOH file not found."
    )

# ----------------------------------------------------------------
# PROTOTYPE
# ----------------------------------------------------------------
summary.append("")
summary.append("6. PROTOTYPE DIGITAL TWIN")
summary.append("-" * 70)

if prototype is not None and len(prototype) > 0:

    latest = prototype.iloc[-1]

    fields = [
        ("battery_voltage_V", "Battery voltage", " V"),
        ("battery_current_A", "Battery current", " A"),
        ("battery_power_W", "Battery power", " W"),
        ("load_power_W", "Load power", " W"),
        ("battery_temperature_C", "Battery temperature", " °C"),
        ("gps_speed_kmph", "GPS speed", " km/h"),
        ("tyre_pressure_psi", "Tyre pressure", " PSI"),
        ("vehicle_status", "Vehicle status", "")
    ]

    for column, label, unit in fields:

        if column in prototype.columns:

            summary.append(
                f"{label}: "
                f"{latest[column]}{unit}"
            )

else:
    summary.append(
        "Prototype digital twin file not found."
    )

# ----------------------------------------------------------------
# FAULT DETECTION
# ----------------------------------------------------------------
summary.append("")
summary.append("7. FAULT DETECTION")
summary.append("-" * 70)

if fault_detection is not None and len(fault_detection) > 0:

    latest = fault_detection.iloc[-1]

    for column in [
        "battery_voltage_status",
        "temperature_status",
        "tyre_pressure_status",
        "battery_current_status",
        "SOH_status",
        "vehicle_status"
    ]:

        if column in fault_detection.columns:

            summary.append(
                f"{column}: {latest[column]}"
            )

else:
    summary.append(
        "Fault detection results file not found."
    )

# ----------------------------------------------------------------
# FAULT INJECTION
# ----------------------------------------------------------------
summary.append("")
summary.append("8. FAULT INJECTION VALIDATION")
summary.append("-" * 70)

if fault_injection is not None:

    summary.append(
        f"Scenarios tested: {len(fault_injection)}"
    )

    if "vehicle_status" in fault_injection.columns:

        counts = (
            fault_injection["vehicle_status"]
            .value_counts()
        )

        summary.append(
            f"Healthy scenarios: "
            f"{counts.get('HEALTHY', 0)}"
        )

        summary.append(
            f"Warning scenarios: "
            f"{counts.get('WARNING', 0)}"
        )

        summary.append(
            f"Critical scenarios: "
            f"{counts.get('CRITICAL', 0)}"
        )

    summary.append("")
    summary.append(
        fault_injection.to_string(index=False)
    )

else:
    summary.append(
        "Fault injection results file not found."
    )

# ----------------------------------------------------------------
# OUTPUT FILES
# ----------------------------------------------------------------
summary.append("")
summary.append("9. IMPORTANT OUTPUT FILES")
summary.append("-" * 70)

output_files = [
    "processed/NASA_clean_training_SOH.csv",
    "processed/NASA_train_SOH.csv",
    "processed/NASA_test_SOH.csv",
    "processed/NASA_feature_importance.csv",
    "processed/NASA_model_comparison.csv",
    "processed/NASA_GB_tuning_results.csv",
    "processed/NASA_final_SOH_predictions.csv",
    "processed/NASA_final_SOH_evaluation.csv",
    "processed/NASA_digital_twin_SOH.csv",
    "processed/EV_prototype_sensor_data.csv",
    "processed/EV_prototype_digital_twin.csv",
    "processed/EV_integrated_digital_twin.csv",
    "processed/EV_fault_detection_results.csv",
    "processed/EV_fault_injection_results.csv",
    "processed/EV_live_digital_twin.csv",
    "results/NASA_final_actual_vs_predicted_SOH.png",
    "results/NASA_final_SOH_prediction_error.png",
    "results/EV_digital_twin_dashboard.png",
    "results/EV_integrated_digital_twin_dashboard.png",
    "results/EV_fault_detection_dashboard.png",
    "results/EV_live_digital_twin_dashboard.png",
    "results/EV_fault_injection_dashboard.png"
]

for file in output_files:

    status = "FOUND" if Path(file).exists() else "NOT FOUND"

    summary.append(
        f"{status:10s} {file}"
    )

# ----------------------------------------------------------------
# Final conclusion
# ----------------------------------------------------------------
summary.append("")
summary.append("10. PROJECT CONCLUSION")
summary.append("-" * 70)

summary.append(
    "The EV digital twin combines battery SOH estimation with "
    "prototype vehicle sensor monitoring."
)

summary.append(
    "The final tuned Gradient Boosting model provides the selected "
    "SOH prediction capability."
)

summary.append(
    "The prototype layer monitors battery voltage, battery current, "
    "temperature, GPS speed and tyre pressure."
)

summary.append(
    "The fault-detection layer converts abnormal conditions into "
    "NORMAL, WARNING or CRITICAL states."
)

summary.append(
    "Fault injection scenarios demonstrate that the digital twin "
    "responds appropriately to simulated abnormal conditions."
)

summary.append("")
summary.append("=" * 70)
summary.append("FINAL PROJECT SUMMARY COMPLETE")
summary.append("=" * 70)

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
output_file.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    f.write("\n".join(summary))

# ----------------------------------------------------------------
# Print to terminal
# ----------------------------------------------------------------
print("\n".join(summary))

print("\n")
print("=" * 70)
print("SUMMARY SAVED")
print("=" * 70)
print()
print(output_file)
print()
print("=" * 70)
print("STEP 36 COMPLETE")
print("=" * 70)