# ============================================================
# EV DIGITAL TWIN - COMPLETE FLASK BACKEND
# ============================================================
#
# AI-Based EV Digital Twin Monitoring System
#
# Provides:
#   /                       Dashboard
#   /api/health             Server/model health
#   /api/model-info         Model information
#   /api/predict-soh        SOH prediction
#   /api/prediction         Prediction model status
#   /api/battery            Complete battery telemetry
#   /api/vehicle            Vehicle + GPS telemetry
#   /api/live               Live telemetry
#   /api/status             Dashboard status
#   /api/history            Historical SOH data
#   /api/soh-data           SOH dataset
#   /api/faults             Active faults
#   /api/fault-injection    Fault simulation
#   /api/data               Project/data information
#
# ============================================================

from __future__ import annotations

import json
import math
import traceback
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from flask import Flask, jsonify, render_template, request


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

PROCESSED_DIR = BASE_DIR / "processed"
SOH_DIR = PROCESSED_DIR / "soh"
SOH_MODEL_DIR = SOH_DIR / "models"

MODEL_PATH = SOH_MODEL_DIR / "best_soh_model.pkl"
FEATURE_COLUMNS_PATH = SOH_MODEL_DIR / "feature_columns.json"
MODEL_METADATA_PATH = SOH_MODEL_DIR / "model_metadata.json"

# The deployed model remains active.  The leakage-free artefacts are
# registered for inspection only and are not loaded for inference.
DEPLOYED_MODEL_ID = "ridge-20-feature-deployed"
CANDIDATE_MODEL_ID = "ridge-18-feature-leakage-free-candidate"
CANDIDATE_MODEL_DIR = SOH_MODEL_DIR / "leakage_free"
CANDIDATE_MODEL_PATH = (
    CANDIDATE_MODEL_DIR / "leakage_free_ridge_pipeline.pkl"
)
CANDIDATE_FEATURE_COLUMNS_PATH = (
    CANDIDATE_MODEL_DIR / "feature_columns.json"
)
CANDIDATE_MODEL_METADATA_PATH = (
    CANDIDATE_MODEL_DIR / "model_metadata.json"
)
CANDIDATE_DEPLOYMENT_CONFIG_PATH = (
    CANDIDATE_MODEL_DIR / "candidate_deployment.json"
)

SOH_DATASET_PATH = SOH_DIR / "combined_soh_dataset.csv"
SOH_PREDICTIONS_PATH = SOH_DIR / "soh_predictions.csv"


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
)

# Do not rely on deprecated JSON_SORT_KEYS configuration.
app.json.sort_keys = False


# ============================================================
# GLOBAL MODEL STATE
# ============================================================

model = None
feature_columns: list[str] = []
model_metadata: dict[str, Any] = {}

MODEL_LOADED = False
MODEL_LOAD_ERROR: str | None = None


# ============================================================
# EXPECTED MODEL FEATURES
# ============================================================

EXPECTED_FEATURES = [
    "Cycle",
    "Capacity_Ah",
    "Voltage_Min_V",
    "Voltage_Max_V",
    "Voltage_Mean_V",
    "Voltage_Final_V",
    "Current_Min_A",
    "Current_Max_A",
    "Current_Mean_A",
    "Temperature_Min_C",
    "Temperature_Max_C",
    "Temperature_Mean_C",
    "Temperature_Final_C",
    "Discharge_Time_s",
    "Cycle_Normalized",
    "Capacity_Ratio",
    "Voltage_Range_V",
    "Current_Range_A",
    "Temperature_Range_C",
    "Source_Dataset",
]


# ============================================================
# DEFAULT TELEMETRY
# ============================================================

DEFAULT_TELEMETRY = {
    "battery_id": "B0005",
    "source_dataset": "NASA",

    "voltage": 3.5,
    "current": -1.8,
    "temperature": 32.0,

    "power": -6.3,
    "load_power": 6.3,

    "soh": 76.5527351897165,
    "soc": None,

    "speed_kmph": 0.0,
    "motor_rpm": 0.0,

    "tyre_pressure": 32.0,

    "road_condition": "SMOOTH",
    "drive_mode": "Eco",

    "cycle": 100,
    "capacity_ah": 1.85,
}


# ============================================================
# DEFAULT MODEL INPUT
# ============================================================

DEFAULT_INPUT = {
    "Source_Dataset": "NASA",
    "Battery_ID": "B0005",

    "Cycle": 100,

    "Capacity_Ah": 1.85,
    "Initial_Capacity_Ah": 2.0,

    "Voltage_Min_V": 2.4,
    "Voltage_Max_V": 4.2,
    "Voltage_Mean_V": 3.5,
    "Voltage_Final_V": 3.4,

    "Current_Min_A": -2.0,
    "Current_Max_A": 0.0,
    "Current_Mean_A": -1.8,

    "Temperature_Min_C": 24.0,
    "Temperature_Max_C": 40.0,
    "Temperature_Mean_C": 32.0,
    "Temperature_Final_C": 36.0,

    "Discharge_Time_s": 3000.0,
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    if value is None:
        return default

    if isinstance(value, bool):
        return float(value)

    try:
        number = float(value)

        if not math.isfinite(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clean_json_value(value: Any) -> Any:

    if isinstance(value, dict):
        return {
            str(key): clean_json_value(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            clean_json_value(item)
            for item in value
        ]

    if isinstance(value, np.ndarray):
        return clean_json_value(value.tolist())

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        number = float(value)

        if math.isfinite(number):
            return number

        return None

    if isinstance(value, float):
        if math.isfinite(value):
            return value

        return None

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def load_json_file(
    path: Path,
) -> dict[str, Any]:

    if not path.exists():
        return {}

    try:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except Exception:

        return {}


# ============================================================
# CSV HELPERS
# ============================================================

def find_first_existing_csv(
    candidates: list[Path],
) -> Path | None:

    for path in candidates:

        if path.exists():
            return path

    return None


def read_csv_safely(
    path: Path,
) -> pd.DataFrame:

    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(
            path,
            encoding="latin1",
        )


def dataframe_to_records(
    dataframe: pd.DataFrame,
    limit: int = 1000,
) -> list[dict[str, Any]]:

    if dataframe is None or dataframe.empty:
        return []

    dataframe = dataframe.head(limit).copy()

    dataframe = dataframe.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    dataframe = dataframe.where(
        pd.notna(dataframe),
        None,
    )

    records = dataframe.to_dict(
        orient="records"
    )

    return clean_json_value(records)


# ============================================================
# MODEL LOADING
# ============================================================

def load_model() -> None:

    global model
    global feature_columns
    global model_metadata
    global MODEL_LOADED
    global MODEL_LOAD_ERROR

    print()
    print("=" * 70)
    print("EV DIGITAL TWIN - SOH MODEL")
    print("=" * 70)

    print(f"Project directory: {BASE_DIR}")
    print(f"Model path       : {MODEL_PATH}")

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    if not MODEL_PATH.exists():

        MODEL_LOADED = False

        MODEL_LOAD_ERROR = (
            f"SOH model not found: {MODEL_PATH}"
        )

        print(MODEL_LOAD_ERROR)

        return

    try:

        model = joblib.load(MODEL_PATH)

        MODEL_LOADED = True
        MODEL_LOAD_ERROR = None

        print(
            "Model loaded successfully:"
            f" {type(model).__name__}"
        )

    except Exception as exc:

        MODEL_LOADED = False

        MODEL_LOAD_ERROR = str(exc)

        print(
            f"Model loading failed: {exc}"
        )

        traceback.print_exc()

        return

    # --------------------------------------------------------
    # FEATURE COLUMNS
    # --------------------------------------------------------

    loaded_features = []

    if FEATURE_COLUMNS_PATH.exists():

        try:

            raw_features = load_json_file(
                FEATURE_COLUMNS_PATH
            )

            if isinstance(raw_features, dict):

                loaded_features = raw_features.get(
                    "feature_columns",
                    [],
                )

        except Exception:
            loaded_features = []

        if not loaded_features:

            try:

                with FEATURE_COLUMNS_PATH.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    raw = json.load(file)

                if isinstance(raw, list):
                    loaded_features = raw

            except Exception:
                loaded_features = []

    if loaded_features:

        feature_columns = [
            str(x)
            for x in loaded_features
        ]

    else:

        feature_columns = EXPECTED_FEATURES.copy()

    print(
        f"Feature count    : {len(feature_columns)}"
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    model_metadata = load_json_file(
        MODEL_METADATA_PATH
    )

    print(
        "Model metadata   : "
        + (
            "loaded"
            if model_metadata
            else "not available"
        )
    )

    print("=" * 70)


# ============================================================
# SOH CLASSIFICATION
# ============================================================

def classify_soh(
    soh: float,
) -> dict[str, str]:

    soh = safe_float(soh)

    if soh >= 90:

        return {
            "status": "Excellent",
            "condition": "Healthy",
            "severity": "normal",
        }

    if soh >= 80:

        return {
            "status": "Good",
            "condition": "Healthy",
            "severity": "normal",
        }

    if soh >= 70:

        return {
            "status": "Fair",
            "condition": "Degraded",
            "severity": "warning",
        }

    if soh >= 60:

        return {
            "status": "Poor",
            "condition": "Degraded",
            "severity": "warning",
        }

    return {
        "status": "Critical",
        "condition": "Unhealthy",
        "severity": "critical",
    }


# ============================================================
# SOH VALUE FROM DATAFRAME
# ============================================================

def extract_soh_from_row(
    row: pd.Series,
) -> float | None:

    possible_columns = [
        "predicted_SOH_percent",
        "Predicted_SOH_percent",
        "predicted_soh_percent",
        "Predicted_SOH",
        "SOH_percent",
        "SOH",
        "soh",
        "soh_percent",
        "SOH_Percent",
    ]

    for column in possible_columns:

        if column not in row.index:
            continue

        value = safe_float(
            row.get(column),
            default=float("nan"),
        )

        if math.isfinite(value):

            # If stored as fraction, convert to %
            if 0 <= value <= 1:
                value *= 100.0

            return max(
                0.0,
                min(
                    100.0,
                    value,
                ),
            )

    return None


# ============================================================
# LOAD LATEST BATTERY DATA
# ============================================================

def get_latest_battery_record() -> dict[str, Any]:

    telemetry = dict(DEFAULT_TELEMETRY)

    path = find_first_existing_csv(
        [
            SOH_PREDICTIONS_PATH,
            SOH_DATASET_PATH,
        ]
    )

    if path is None:
        return telemetry

    try:

        dataframe = read_csv_safely(path)

        if dataframe.empty:
            return telemetry

        latest = dataframe.iloc[-1]

        # ----------------------------------------------------
        # Battery ID
        # ----------------------------------------------------

        for column in [
            "Battery_ID",
            "battery_id",
            "Battery",
            "battery",
        ]:

            if column in latest.index:

                value = latest.get(column)

                if pd.notna(value):
                    telemetry["battery_id"] = str(value)
                    break

        # ----------------------------------------------------
        # Dataset
        # ----------------------------------------------------

        for column in [
            "Source_Dataset",
            "source_dataset",
            "Dataset",
            "dataset",
        ]:

            if column in latest.index:

                value = latest.get(column)

                if pd.notna(value):
                    telemetry["source_dataset"] = str(value)
                    break

        # ----------------------------------------------------
        # Cycle
        # ----------------------------------------------------

        for column in [
            "Cycle",
            "cycle",
        ]:

            if column in latest.index:

                telemetry["cycle"] = safe_int(
                    latest.get(column),
                    telemetry["cycle"],
                )

                break

        # ----------------------------------------------------
        # Capacity
        # ----------------------------------------------------

        for column in [
            "Capacity_Ah",
            "capacity_ah",
            "Capacity",
            "capacity",
        ]:

            if column in latest.index:

                telemetry["capacity_ah"] = safe_float(
                    latest.get(column),
                    telemetry["capacity_ah"],
                )

                break

        # ----------------------------------------------------
        # Voltage
        # ----------------------------------------------------

        voltage = None

        for column in [
            "Voltage_Mean_V",
            "Voltage_Final_V",
            "voltage",
            "Voltage",
            "voltage_mean",
        ]:

            if column in latest.index:

                value = safe_float(
                    latest.get(column),
                    float("nan"),
                )

                if math.isfinite(value):
                    voltage = value
                    break

        if voltage is not None:
            telemetry["voltage"] = voltage

        # ----------------------------------------------------
        # Current
        # ----------------------------------------------------

        current = None

        for column in [
            "Current_Mean_A",
            "Current_Final_A",
            "current",
            "Current",
            "current_mean",
        ]:

            if column in latest.index:

                value = safe_float(
                    latest.get(column),
                    float("nan"),
                )

                if math.isfinite(value):
                    current = value
                    break

        if current is not None:
            telemetry["current"] = current

        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        temperature = None

        for column in [
            "Temperature_Mean_C",
            "Temperature_Final_C",
            "temperature",
            "Temperature",
            "temperature_mean",
        ]:

            if column in latest.index:

                value = safe_float(
                    latest.get(column),
                    float("nan"),
                )

                if math.isfinite(value):
                    temperature = value
                    break

        if temperature is not None:
            telemetry["temperature"] = temperature

        # ----------------------------------------------------
        # SOH
        # ----------------------------------------------------

        soh = extract_soh_from_row(latest)

        if soh is not None:
            telemetry["soh"] = soh

    except Exception as exc:

        print(
            "Warning: unable to read latest battery "
            f"record: {exc}"
        )

    # --------------------------------------------------------
    # Always calculate power consistently
    # --------------------------------------------------------

    voltage = safe_float(
        telemetry["voltage"]
    )

    current = safe_float(
        telemetry["current"]
    )

    telemetry["power"] = voltage * current

    # Absolute electrical load magnitude.
    telemetry["load_power"] = abs(
        telemetry["power"]
    )

    return clean_json_value(
        telemetry
    )


# ============================================================
# CURRENT TELEMETRY FOR DASHBOARD PREDICTION
# ============================================================

def get_current_telemetry() -> dict[str, Any]:
    """Return the latest dataset-backed telemetry without synthetic values."""

    source_path = find_first_existing_csv(
        [SOH_PREDICTIONS_PATH, SOH_DATASET_PATH]
    )
    battery = {
        "battery_id": None, "source_dataset": None, "cycle": None,
        "capacity_ah": None, "voltage": None, "current": None,
        "temperature": None, "power": None, "soh": None,
    }
    vehicle = {
        "speed_kmph": None,
        "motor_rpm": None,
        "tyre_pressure": None,
        "road_condition": None,
        "drive_mode": None,
        "unavailable_fields": [
            "speed_kmph", "motor_rpm", "tyre_pressure",
            "road_condition", "drive_mode",
        ],
    }
    prediction_input: dict[str, Any] = {}
    source_details = {
        "battery_record": (
            str(source_path.relative_to(BASE_DIR))
            if source_path is not None else None
        ),
        "feature_record": None,
    }

    if source_path is not None:
        try:
            source_data = read_csv_safely(source_path)
            if source_data.empty:
                raise ValueError("Current telemetry source is empty.")

            latest = source_data.iloc[-1]
            feature_row = latest

            # Prediction results omit input features, so use the matching row
            # from the source dataset when it is available.
            if source_path != SOH_DATASET_PATH and SOH_DATASET_PATH.exists():
                feature_data = read_csv_safely(SOH_DATASET_PATH)
                match = feature_data
                for column in ["Source_Dataset", "Battery_ID", "Cycle"]:
                    if column in match.columns and column in latest.index:
                        match = match.loc[
                            match[column].astype(str) == str(latest.get(column))
                        ]
                if not match.empty:
                    feature_row = match.iloc[-1]
                    source_details["feature_record"] = str(
                        SOH_DATASET_PATH.relative_to(BASE_DIR)
                    )

            for column, field in {
                "Battery_ID": "battery_id",
                "Source_Dataset": "source_dataset",
            }.items():
                if column in latest.index and pd.notna(latest.get(column)):
                    value = str(latest.get(column))
                    battery[field] = value
                    prediction_input[column] = value

            for column, field in {
                "Cycle": "cycle",
                "Capacity_Ah": "capacity_ah",
                "Voltage_Mean_V": "voltage",
                "Current_Mean_A": "current",
                "Temperature_Mean_C": "temperature",
            }.items():
                row = feature_row if column in feature_row.index else latest
                value = safe_float(row.get(column), default=float("nan"))
                if math.isfinite(value):
                    battery[field] = value
                    prediction_input[column] = value

            # Include only real model inputs; missing values remain absent.
            for column in EXPECTED_FEATURES:
                if column == "Source_Dataset" or column not in feature_row.index:
                    continue
                value = safe_float(feature_row.get(column), default=float("nan"))
                if math.isfinite(value):
                    prediction_input[column] = value

            battery["soh"] = extract_soh_from_row(latest)
            if battery["soh"] is None:
                battery["soh"] = extract_soh_from_row(feature_row)

            if battery["voltage"] is not None and battery["current"] is not None:
                battery["power"] = battery["voltage"] * battery["current"]

        except Exception as exc:
            print(f"Warning: unable to load current telemetry: {exc}")

    battery["unavailable_fields"] = [
        field
        for field in [
            "battery_id", "source_dataset", "cycle", "capacity_ah",
            "voltage", "current", "temperature", "power", "soh",
        ]
        if battery[field] is None
    ]
    battery["prediction_input"] = prediction_input
    return clean_json_value(
        {"battery": battery, "vehicle": vehicle, "source": source_details}
    )


# ============================================================
# BUILD MODEL FEATURES
# ============================================================

def build_feature_dataframe(
    payload: dict[str, Any],
) -> pd.DataFrame:

    data = dict(DEFAULT_INPUT)

    for key, value in payload.items():

        if key in data:
            data[key] = value

    # --------------------------------------------------------
    # Dataset
    # --------------------------------------------------------

    source_dataset = str(
        data.get(
            "Source_Dataset",
            "NASA",
        )
    ).strip()

    if not source_dataset:
        source_dataset = "NASA"

    data["Source_Dataset"] = source_dataset

    # --------------------------------------------------------
    # Numeric base features
    # --------------------------------------------------------

    numeric_base = [
        "Cycle",
        "Capacity_Ah",

        "Voltage_Min_V",
        "Voltage_Max_V",
        "Voltage_Mean_V",
        "Voltage_Final_V",

        "Current_Min_A",
        "Current_Max_A",
        "Current_Mean_A",

        "Temperature_Min_C",
        "Temperature_Max_C",
        "Temperature_Mean_C",
        "Temperature_Final_C",

        "Discharge_Time_s",
    ]

    for column in numeric_base:

        data[column] = safe_float(
            data.get(column)
        )

    # --------------------------------------------------------
    # Derived features
    # --------------------------------------------------------

    cycle = data["Cycle"]

    capacity = data["Capacity_Ah"]

    voltage_min = data["Voltage_Min_V"]
    voltage_max = data["Voltage_Max_V"]

    current_min = data["Current_Min_A"]
    current_max = data["Current_Max_A"]

    temperature_min = data["Temperature_Min_C"]
    temperature_max = data["Temperature_Max_C"]

    # --------------------------------------------------------
    # Cycle normalized
    # --------------------------------------------------------

    data["Cycle_Normalized"] = min(
        max(
            cycle / 1000.0,
            0.0,
        ),
        1.0,
    )

    # --------------------------------------------------------
    # Capacity ratio
    # --------------------------------------------------------

    initial_capacity = safe_float(
        payload.get(
            "Initial_Capacity_Ah",
            data.get(
                "Initial_Capacity_Ah",
                2.0,
            ),
        ),
        default=2.0,
    )

    if initial_capacity <= 0:
        initial_capacity = 2.0

    data["Capacity_Ratio"] = (
        capacity / initial_capacity
    )

    # --------------------------------------------------------
    # Ranges
    # --------------------------------------------------------

    data["Voltage_Range_V"] = (
        voltage_max - voltage_min
    )

    data["Current_Range_A"] = (
        current_max - current_min
    )

    data["Temperature_Range_C"] = (
        temperature_max - temperature_min
    )

    # --------------------------------------------------------
    # Dataframe
    # --------------------------------------------------------

    row = {}

    for column in feature_columns:

        if column in data:

            row[column] = data[column]

        else:

            row[column] = 0.0

    dataframe = pd.DataFrame(
        [row],
        columns=feature_columns,
    )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    for column in dataframe.columns:

        if column != "Source_Dataset":

            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )

            dataframe[column] = dataframe[
                column
            ].fillna(0.0)

    return dataframe


# ============================================================
# ROOT
# ============================================================

@app.route("/")
def dashboard():

    return render_template(
        "index.html"
    )


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"],
)
def health():

    return jsonify(
        clean_json_value(
            {
                "success": True,
                "service": "EV Digital Twin Flask API",

                "model_loaded": MODEL_LOADED,

                "model_type": (
                    type(model).__name__
                    if model is not None
                    else None
                ),

                "feature_count": len(
                    feature_columns
                ),

                "model_error": MODEL_LOAD_ERROR,
            }
        )
    )


# ============================================================
# MODEL INFO
# ============================================================

@app.route(
    "/api/model-info",
    methods=["GET"],
)
def model_info():

    result_metadata = dict(
        model_metadata
    )

    result_metadata["model_file"] = str(
        MODEL_PATH
    )

    result_metadata["feature_columns"] = (
        feature_columns
    )

    result_metadata.setdefault(
        "target_column",
        "SOH_percent",
    )

    result_metadata.setdefault(
        "input_dataset",
        str(SOH_DATASET_PATH),
    )

    candidate_config = load_json_file(
        CANDIDATE_DEPLOYMENT_CONFIG_PATH
    )

    return jsonify(
        clean_json_value(
            {
                "success": True,
                "deployment": {
                    "active_model_id": DEPLOYED_MODEL_ID,
                    "active_model_path": str(MODEL_PATH),
                    "active_feature_count": len(feature_columns),
                    "candidate": {
                        "model_id": CANDIDATE_MODEL_ID,
                        "deployment_status": "candidate_not_active",
                        "model_path": str(CANDIDATE_MODEL_PATH),
                        "feature_columns_path": str(
                            CANDIDATE_FEATURE_COLUMNS_PATH
                        ),
                        "metadata_path": str(
                            CANDIDATE_MODEL_METADATA_PATH
                        ),
                        "config": candidate_config,
                    },
                },
                "feature_count": len(
                    feature_columns
                ),
                "feature_columns": feature_columns,
                "model": result_metadata,
            }
        )
    )


# ============================================================
# SOH PREDICTION
# ============================================================

@app.route(
    "/api/predict-soh",
    methods=["POST"],
)
def predict_soh():

    if not MODEL_LOADED or model is None:

        return jsonify(
            {
                "success": False,
                "error": "SOH model is not loaded.",
                "details": MODEL_LOAD_ERROR,
            }
        ), 503

    payload = request.get_json(
        silent=True
    )

    if not isinstance(payload, dict):

        return jsonify(
            {
                "success": False,
                "error": (
                    "Request body must be a "
                    "JSON object."
                ),
            }
        ), 400

    try:

        dataframe = build_feature_dataframe(
            payload
        )

        prediction = model.predict(
            dataframe
        )

        raw_soh = float(
            np.asarray(
                prediction
            ).reshape(-1)[0]
        )

        if not math.isfinite(raw_soh):

            raise ValueError(
                "Model returned a non-finite SOH."
            )

        predicted_soh = max(
            0.0,
            min(
                100.0,
                raw_soh,
            ),
        )

        health_data = classify_soh(
            predicted_soh
        )

        battery_id = str(
            payload.get(
                "Battery_ID",
                "B0005",
            )
        )

        source_dataset = str(
            payload.get(
                "Source_Dataset",
                "NASA",
            )
        )

        cycle = safe_float(
            payload.get(
                "Cycle",
                0,
            )
        )

        capacity = safe_float(
            payload.get(
                "Capacity_Ah",
                0,
            )
        )

        response = {
            "success": True,

            "battery": {
                "battery_id": battery_id,
                "source_dataset": source_dataset,
                "cycle": cycle,
                "capacity_ah": capacity,
            },

            "prediction": {
                "soh_percent": round(
                    predicted_soh,
                    4,
                ),

                "raw_soh_percent": round(
                    raw_soh,
                    4,
                ),

                "status": health_data[
                    "status"
                ],

                "condition": health_data[
                    "condition"
                ],

                "severity": health_data[
                    "severity"
                ],
            },
        }

        print()
        print("-" * 60)
        print("SOH PREDICTION")
        print("-" * 60)
        print(
            f"Dataset : {source_dataset}"
        )
        print(
            f"Battery : {battery_id}"
        )
        print(
            f"Cycle   : {cycle}"
        )
        print(
            f"SOH     : {predicted_soh:.4f}%"
        )
        print(
            f"Status  : {health_data['status']}"
        )
        print("-" * 60)

        return jsonify(
            clean_json_value(
                response
            )
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("SOH PREDICTION ERROR")
        print("=" * 70)

        traceback.print_exc()

        return jsonify(
            {
                "success": False,
                "error": "SOH prediction failed.",
                "details": str(exc),
            }
        ), 500


# ============================================================
# BATTERY API
# ============================================================

@app.route(
    "/api/battery",
    methods=["GET"],
)
def battery():

    current_telemetry = get_current_telemetry()
    telemetry = current_telemetry["battery"]
    voltage = telemetry["voltage"]
    current = telemetry["current"]
    temperature = telemetry["temperature"]
    power = telemetry["power"]
    soh = telemetry["soh"]
    health_data = (
        classify_soh(soh)
        if soh is not None
        else {"status": "Unavailable", "condition": "Unavailable"}
    )

    response = {
        "success": True,

        "battery": {

            # Main values expected by JS
            "voltage": voltage,
            "current": current,
            "temperature": temperature,
            "power": power,
            "load_power": abs(power) if power is not None else None,

            "soh": soh,
            "soc": None,

            # Naming aliases
            "battery_voltage": voltage,
            "battery_current": current,
            "battery_temperature": temperature,
            "battery_power": power,
            "battery_soh": soh,
            "battery_soc": None,

            # Battery identity
            "battery_id": telemetry["battery_id"],
            "source_dataset": telemetry["source_dataset"],
            "cycle": telemetry["cycle"],
            "capacity_ah": telemetry["capacity_ah"],
            "prediction_input": telemetry["prediction_input"],
            "unavailable_fields": telemetry["unavailable_fields"],
            "telemetry_source": current_telemetry["source"],

            # Additional useful fields
            "status": health_data["status"],
            "condition": health_data["condition"],
        },
    }

    return jsonify(
        clean_json_value(response)
    )


# ============================================================
# VEHICLE API
# ============================================================

@app.route(
    "/api/vehicle",
    methods=["GET"],
)
def vehicle():

    telemetry = get_latest_battery_record()

    response = {
        "success": True,

        "vehicle": {

            "status": "Connected",

            "speed_kmph": safe_float(
                telemetry.get(
                    "speed_kmph",
                    0.0,
                )
            ),

            "speed": safe_float(
                telemetry.get(
                    "speed_kmph",
                    0.0,
                )
            ),

            "motor_rpm": safe_float(
                telemetry.get(
                    "motor_rpm",
                    0.0,
                )
            ),

            "drive_mode": telemetry.get(
                "drive_mode",
                "Eco",
            ),

            "road_condition": telemetry.get(
                "road_condition",
                "SMOOTH",
            ),

            "tyre_pressure": safe_float(
                telemetry.get(
                    "tyre_pressure",
                    32.0,
                )
            ),

            "tyrePressure": safe_float(
                telemetry.get(
                    "tyre_pressure",
                    32.0,
                )
            ),

            "battery_voltage": safe_float(
                telemetry.get(
                    "voltage",
                    3.5,
                )
            ),

            "battery_current": safe_float(
                telemetry.get(
                    "current",
                    -1.8,
                )
            ),

            "battery_temperature": safe_float(
                telemetry.get(
                    "temperature",
                    32.0,
                )
            ),

            "battery_power": (
                safe_float(
                    telemetry.get(
                        "voltage",
                        3.5,
                    )
                )
                *
                safe_float(
                    telemetry.get(
                        "current",
                        -1.8,
                    )
                )
            ),

            "soh": safe_float(
                telemetry.get(
                    "soh",
                    76.55,
                )
            ),
        },

        # GPS is included even when the real GPS
        # device is not connected yet.
        "gps": {
            "available": False,
            "latitude": None,
            "longitude": None,
            "accuracy_m": None,
            "speed_kmph": 0.0,
        },
    }

    return jsonify(
        clean_json_value(
            response
        )
    )


# ============================================================
# LIVE API
# ============================================================

@app.route(
    "/api/live",
    methods=["GET"],
)
def live():

    telemetry = get_latest_battery_record()

    voltage = safe_float(
        telemetry["voltage"]
    )

    current = safe_float(
        telemetry["current"]
    )

    temperature = safe_float(
        telemetry["temperature"]
    )

    power = voltage * current

    return jsonify(
        clean_json_value(
            {
                "success": True,

                "live": {

                    "vehicle_status": "Connected",

                    "battery_voltage": voltage,
                    "battery_current": current,
                    "battery_temperature": temperature,

                    "battery_power": power,

                    "battery_soh": safe_float(
                        telemetry["soh"]
                    ),

                    "speed_kmph": 0.0,

                    "motor_rpm": 0.0,

                    "tyre_pressure": 32.0,

                    "road_condition": "SMOOTH",
                },
            }
        )
    )


# ============================================================
# STATUS API
# ============================================================

@app.route(
    "/api/status",
    methods=["GET"],
)
def status():

    telemetry = get_latest_battery_record()

    soh = safe_float(
        telemetry.get("soh")
    )

    health_data = classify_soh(
        soh
    )

    voltage = safe_float(
        telemetry.get("voltage")
    )

    current = safe_float(
        telemetry.get("current")
    )

    temperature = safe_float(
        telemetry.get("temperature")
    )

    return jsonify(
        clean_json_value(
            {
                "success": True,

                "status": {

                    "vehicle": "Connected",

                    "voltage": (
                        f"{voltage:.2f} V"
                    ),

                    "current": (
                        f"{current:.2f} A"
                    ),

                    "temperature": (
                        f"{temperature:.2f} °C"
                    ),

                    "power": (
                        f"{voltage * current:.2f} W"
                    ),

                    "tyrePressure": (
                        "32.00 PSI"
                    ),

                    "soh": health_data[
                        "status"
                    ],

                    "roadCondition": (
                        "SMOOTH"
                    ),
                },

                "battery": telemetry,

                "model": {

                    "loaded": MODEL_LOADED,

                    "type": (
                        type(model).__name__
                        if model is not None
                        else None
                    ),
                },
            }
        )
    )


# ============================================================
# PREDICTION STATUS
# ============================================================

@app.route(
    "/api/prediction",
    methods=["GET"],
)
def prediction():

    return jsonify(
        {
            "success": True,

            "model_loaded": MODEL_LOADED,

            "model_type": (
                type(model).__name__
                if model is not None
                else None
            ),

            "message": (
                "SOH prediction model ready."
                if MODEL_LOADED
                else "SOH model unavailable."
            ),
        }
    )


# ============================================================
# HISTORY API
# ============================================================

@app.route(
    "/api/history",
    methods=["GET"],
)
def history():

    path = find_first_existing_csv(
        [
            SOH_PREDICTIONS_PATH,
            SOH_DATASET_PATH,
        ]
    )

    if path is None:

        return jsonify(
            {
                "success": True,
                "columns": [],
                "rows": 0,
                "data": [],
            }
        )

    try:

        dataframe = read_csv_safely(
            path
        )

        # ----------------------------------------------------
        # Normalize useful SOH columns so JavaScript can
        # recognize the historical records.
        # ----------------------------------------------------

        normalized = dataframe.copy()

        # Cycle
        if "Cycle" not in normalized.columns:

            for candidate in [
                "cycle",
                "Cycle_Number",
                "cycle_number",
            ]:

                if candidate in normalized.columns:

                    normalized["Cycle"] = (
                        pd.to_numeric(
                            normalized[candidate],
                            errors="coerce",
                        )
                    )

                    break

        # SOH
        if "SOH_percent" not in normalized.columns:

            for candidate in [
                "predicted_SOH_percent",
                "Predicted_SOH_percent",
                "predicted_soh_percent",
                "Predicted_SOH",
                "SOH_percent",
                "SOH",
                "soh",
                "soh_percent",
            ]:

                if candidate in normalized.columns:

                    normalized[
                        "SOH_percent"
                    ] = pd.to_numeric(
                        normalized[candidate],
                        errors="coerce",
                    )

                    break

        # Convert fractional SOH to percentage if required.
        if "SOH_percent" in normalized.columns:

            soh_values = pd.to_numeric(
                normalized["SOH_percent"],
                errors="coerce",
            )

            valid = soh_values.dropna()

            if (
                not valid.empty
                and valid.max() <= 1.0
            ):

                normalized[
                    "SOH_percent"
                ] = soh_values * 100.0

        # Battery ID
        if "Battery_ID" not in normalized.columns:

            for candidate in [
                "battery_id",
                "Battery",
                "battery",
            ]:

                if candidate in normalized.columns:

                    normalized[
                        "Battery_ID"
                    ] = normalized[
                        candidate
                    ]

                    break

        # Dataset
        if "Source_Dataset" not in normalized.columns:

            for candidate in [
                "source_dataset",
                "Dataset",
                "dataset",
            ]:

                if candidate in normalized.columns:

                    normalized[
                        "Source_Dataset"
                    ] = normalized[
                        candidate
                    ]

                    break

        # ----------------------------------------------------
        # Keep all original data plus normalized fields.
        # ----------------------------------------------------

        records = dataframe_to_records(
            normalized,
            limit=1000,
        )

        columns = [
            str(column)
            for column in normalized.columns
        ]

        return jsonify(
            clean_json_value(
                {
                    "success": True,

                    "source": str(path),

                    "rows": len(
                        normalized
                    ),

                    "columns": columns,

                    "data": records,
                }
            )
        )

    except Exception as exc:

        traceback.print_exc()

        return jsonify(
            {
                "success": False,
                "columns": [],
                "rows": 0,
                "data": [],
                "error": str(exc),
            }
        ), 500


# ============================================================
# SOH DATA API
# ============================================================

@app.route(
    "/api/soh-data",
    methods=["GET"],
)
def soh_data():

    path = find_first_existing_csv(
        [
            SOH_PREDICTIONS_PATH,
            SOH_DATASET_PATH,
        ]
    )

    if path is None:

        return jsonify(
            {
                "success": False,
                "data": [],
                "rows": 0,
                "error": (
                    "No SOH CSV data file found."
                ),
            }
        ), 404

    try:

        dataframe = read_csv_safely(
            path
        )

        return jsonify(
            clean_json_value(
                {
                    "success": True,
                    "source": str(path),
                    "rows": len(dataframe),
                    "columns": [
                        str(x)
                        for x in dataframe.columns
                    ],
                    "data": dataframe_to_records(
                        dataframe,
                        limit=1000,
                    ),
                }
            )
        )

    except Exception as exc:

        traceback.print_exc()

        return jsonify(
            {
                "success": False,
                "error": str(exc),
                "data": [],
            }
        ), 500


# ============================================================
# FAULTS API
# ============================================================

@app.route(
    "/api/faults",
    methods=["GET"],
)
def faults():

    telemetry = get_latest_battery_record()

    faults_list = []

    voltage = safe_float(
        telemetry.get("voltage")
    )

    temperature = safe_float(
        telemetry.get("temperature")
    )

    current = safe_float(
        telemetry.get("current")
    )

    soh = safe_float(
        telemetry.get("soh")
    )

    tyre_pressure = safe_float(
        telemetry.get(
            "tyre_pressure",
            32.0,
        )
    )

    # --------------------------------------------------------
    # Voltage
    # --------------------------------------------------------

    if voltage < 3.0:

        faults_list.append(
            {
                "type": "LOW_BATTERY_VOLTAGE",
                "severity": "critical",
                "message": (
                    "Battery voltage is critically low."
                ),
            }
        )

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    if temperature > 45:

        faults_list.append(
            {
                "type": "HIGH_TEMPERATURE",
                "severity": "warning",
                "message": (
                    "Battery temperature is high."
                ),
            }
        )

    # --------------------------------------------------------
    # SOH
    # --------------------------------------------------------

    if soh < 70:

        faults_list.append(
            {
                "type": "LOW_SOH",
                "severity": "warning",
                "message": (
                    "Battery SOH is below "
                    "the recommended level."
                ),
            }
        )

    # --------------------------------------------------------
    # Current
    # --------------------------------------------------------

    if abs(current) > 10:

        faults_list.append(
            {
                "type": "HIGH_CURRENT",
                "severity": "warning",
                "message": (
                    "Battery current is abnormally high."
                ),
            }
        )

    # --------------------------------------------------------
    # Tyre
    # --------------------------------------------------------

    if tyre_pressure < 28:

        faults_list.append(
            {
                "type": "LOW_TYRE_PRESSURE",
                "severity": "warning",
                "message": (
                    "Tyre pressure is low."
                ),
            }
        )

    return jsonify(
        clean_json_value(
            {
                "success": True,

                "count": len(
                    faults_list
                ),

                "faults": faults_list,
            }
        )
    )


# ============================================================
# FAULT INJECTION
# ============================================================

@app.route(
    "/api/fault-injection",
    methods=["GET", "POST"],
)
def fault_injection():

    if request.method == "POST":

        payload = request.get_json(
            silent=True
        )

        if not isinstance(
            payload,
            dict,
        ):

            payload = {}

        scenario = payload.get(
            "scenario",
            "NORMAL",
        )

    else:

        scenario = request.args.get(
            "scenario",
            "NORMAL",
        )

    scenario = str(
        scenario
    ).upper().strip()

    scenarios = {

        "NORMAL": {
            "status": "NORMAL",
            "severity": "normal",
            "message": (
                "Vehicle operating normally."
            ),
        },

        "LOW_BATTERY_VOLTAGE": {
            "status": "LOW BATTERY VOLTAGE",
            "severity": "warning",
            "message": (
                "Battery voltage is below "
                "the recommended operating level."
            ),
        },

        "HIGH_TEMPERATURE": {
            "status": "HIGH TEMPERATURE",
            "severity": "warning",
            "message": (
                "Battery temperature is high."
            ),
        },

        "LOW_TYRE_PRESSURE": {
            "status": "LOW TYRE PRESSURE",
            "severity": "warning",
            "message": (
                "Tyre pressure is below "
                "the recommended level."
            ),
        },

        "HIGH_CURRENT": {
            "status": "HIGH CURRENT",
            "severity": "warning",
            "message": (
                "Battery current is abnormally high."
            ),
        },

        "LOW_SOH": {
            "status": "LOW SOH",
            "severity": "warning",
            "message": (
                "Battery State of Health is low."
            ),
        },

        "CRITICAL_COMBINATION": {
            "status": "CRITICAL COMBINATION",
            "severity": "critical",
            "message": (
                "Multiple abnormal vehicle "
                "conditions detected."
            ),
        },
    }

    result = scenarios.get(
        scenario,
        scenarios["NORMAL"],
    )

    telemetry = get_latest_battery_record()

    # --------------------------------------------------------
    # Simulated values
    # --------------------------------------------------------

    simulated = {
        "voltage": safe_float(
            telemetry["voltage"]
        ),

        "current": safe_float(
            telemetry["current"]
        ),

        "temperature": safe_float(
            telemetry["temperature"]
        ),

        "soh": safe_float(
            telemetry["soh"]
        ),

        "tyre_pressure": safe_float(
            telemetry.get(
                "tyre_pressure",
                32.0,
            )
        ),

        "speed": 0.0,
    }

    if scenario == "LOW_BATTERY_VOLTAGE":
        simulated["voltage"] = 2.7

    elif scenario == "HIGH_TEMPERATURE":
        simulated["temperature"] = 55.0

    elif scenario == "LOW_TYRE_PRESSURE":
        simulated["tyre_pressure"] = 22.0

    elif scenario == "HIGH_CURRENT":
        simulated["current"] = -15.0

    elif scenario == "LOW_SOH":
        simulated["soh"] = 55.0

    elif scenario == "CRITICAL_COMBINATION":

        simulated["voltage"] = 2.6
        simulated["temperature"] = 60.0
        simulated["current"] = -15.0
        simulated["soh"] = 50.0
        simulated["tyre_pressure"] = 20.0

        result = scenarios[
            "CRITICAL_COMBINATION"
        ]

    simulated["power"] = (
        simulated["voltage"]
        *
        simulated["current"]
    )

    return jsonify(
        clean_json_value(
            {
                "success": True,

                "scenario": scenario,

                "prediction": result,

                "simulation": {

                    "voltage": simulated[
                        "voltage"
                    ],

                    "current": simulated[
                        "current"
                    ],

                    "temperature": simulated[
                        "temperature"
                    ],

                    "soh": simulated[
                        "soh"
                    ],

                    "tyre_pressure": simulated[
                        "tyre_pressure"
                    ],

                    "speed": simulated[
                        "speed"
                    ],

                    "power": simulated[
                        "power"
                    ],
                },
            }
        )
    )


# ============================================================
# DATA API
# ============================================================

@app.route(
    "/api/data",
    methods=["GET"],
)
def data():

    return jsonify(
        clean_json_value(
            {
                "success": True,

                "project_directory": str(
                    BASE_DIR
                ),

                "processed_directory": str(
                    PROCESSED_DIR
                ),

                "soh_model": {

                    "model_id": DEPLOYED_MODEL_ID,

                    "exists": MODEL_PATH.exists(),

                    "loaded": MODEL_LOADED,

                    "path": str(
                        MODEL_PATH
                    ),
                },

                "soh_model_candidate": {

                    "model_id": CANDIDATE_MODEL_ID,

                    "deployment_status": "candidate_not_active",

                    "exists": CANDIDATE_MODEL_PATH.exists(),

                    "path": str(
                        CANDIDATE_MODEL_PATH
                    ),
                },

                "soh_dataset": {

                    "exists": (
                        SOH_DATASET_PATH.exists()
                    ),

                    "path": str(
                        SOH_DATASET_PATH
                    ),
                },

                "soh_predictions": {

                    "exists": (
                        SOH_PREDICTIONS_PATH.exists()
                    ),

                    "path": str(
                        SOH_PREDICTIONS_PATH
                    ),
                },
            }
        )
    )


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    if request.path.startswith("/api/"):

        return jsonify(
            {
                "success": False,
                "error": "API endpoint not found.",
                "path": request.path,
            }
        ), 404

    return (
        "<h1>404 - Page Not Found</h1>",
        404,
    )


# ============================================================
# 405
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):

    if request.path.startswith("/api/"):

        return jsonify(
            {
                "success": False,
                "error": "HTTP method not allowed.",
                "path": request.path,
            }
        ), 405

    return (
        "<h1>405 - Method Not Allowed</h1>",
        405,
    )


# ============================================================
# 500
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    if request.path.startswith("/api/"):

        return jsonify(
            {
                "success": False,
                "error": "Internal server error.",
            }
        ), 500

    return (
        "<h1>500 - Internal Server Error</h1>",
        500,
    )


# ============================================================
# LOAD MODEL
# ============================================================

load_model()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("STARTING EV DIGITAL TWIN")
    print("=" * 70)

    print()
    print(
        f"Project directory : {BASE_DIR}"
    )

    print(
        f"Model path        : {MODEL_PATH}"
    )

    print(
        f"Model exists      : "
        f"{MODEL_PATH.exists()}"
    )

    print(
        f"Model loaded      : "
        f"{MODEL_LOADED}"
    )

    print()
    print("Endpoints:")
    print(
        "  Dashboard       : "
        "http://127.0.0.1:5000/"
    )

    print(
        "  Health          : "
        "http://127.0.0.1:5000/api/health"
    )

    print(
        "  Battery         : "
        "http://127.0.0.1:5000/api/battery"
    )

    print(
        "  Vehicle         : "
        "http://127.0.0.1:5000/api/vehicle"
    )

    print(
        "  History         : "
        "http://127.0.0.1:5000/api/history"
    )

    print(
        "  Prediction      : "
        "http://127.0.0.1:5000/api/prediction"
    )

    print(
        "  Faults          : "
        "http://127.0.0.1:5000/api/faults"
    )

    print()
    print(
        "Server: "
        "http://127.0.0.1:5000"
    )

    print("=" * 70)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )
