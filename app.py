import json
import math
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, render_template


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "processed" / "soh" / "models"

MODEL_PATH = MODEL_DIR / "best_soh_model.pkl"
FEATURE_PATH = MODEL_DIR / "feature_columns.json"
METADATA_PATH = MODEL_DIR / "model_metadata.json"


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# GLOBAL MODEL OBJECTS
# ============================================================

MODEL = None
FEATURE_COLUMNS = None
MODEL_METADATA = None


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    global MODEL
    global FEATURE_COLUMNS
    global MODEL_METADATA

    print("=" * 70)
    print("EV DIGITAL TWIN - SOH FLASK API")
    print("=" * 70)

    print("\nLoading SOH model...")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"SOH model not found:\n{MODEL_PATH}"
        )

    with open(MODEL_PATH, "rb") as f:
        MODEL = pickle.load(f)

    print(f"Model loaded: {type(MODEL).__name__}")

    print("\nLoading feature metadata...")

    if not FEATURE_PATH.exists():
        raise FileNotFoundError(
            f"Feature metadata not found:\n{FEATURE_PATH}"
        )

    with open(FEATURE_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Support either a direct list or a dictionary containing feature columns.
    if isinstance(metadata, list):
        FEATURE_COLUMNS = metadata

    elif isinstance(metadata, dict):

        if "feature_columns" in metadata:
            FEATURE_COLUMNS = metadata["feature_columns"]

        elif "features" in metadata:
            FEATURE_COLUMNS = metadata["features"]

        elif "columns" in metadata:
            FEATURE_COLUMNS = metadata["columns"]

        else:
            raise ValueError(
                "Could not find feature columns in feature_columns.json"
            )

    else:
        raise ValueError(
            "Invalid feature_columns.json format"
        )

    print(f"Feature columns loaded: {len(FEATURE_COLUMNS)}")

    print("\nLoading model metadata...")

    if METADATA_PATH.exists():

        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            MODEL_METADATA = json.load(f)

        print("Model metadata loaded.")

    else:

        MODEL_METADATA = {}

        print("[WARNING] Model metadata not found.")


# ============================================================
# NUMERIC CONVERSION
# ============================================================

def to_float(value, field_name, required=True):

    if value is None:

        if required:
            raise ValueError(
                f"Missing required field: {field_name}"
            )

        return np.nan

    try:

        number = float(value)

    except (TypeError, ValueError):

        raise ValueError(
            f"Invalid numeric value for {field_name}: {value}"
        )

    if not math.isfinite(number):

        raise ValueError(
            f"Non-finite numeric value for {field_name}"
        )

    return number


# ============================================================
# CREATE MODEL FEATURES
# ============================================================

def create_features(data):

    df = pd.DataFrame([data])

    # --------------------------------------------------------
    # Required basic fields
    # --------------------------------------------------------

    df["Cycle"] = pd.to_numeric(
        df["Cycle"],
        errors="coerce"
    )

    df["Capacity_Ah"] = pd.to_numeric(
        df["Capacity_Ah"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if df["Cycle"].isna().any():
        raise ValueError("Cycle must be numeric.")

    if df["Capacity_Ah"].isna().any():
        raise ValueError("Capacity_Ah must be numeric.")

    if (df["Cycle"] < 0).any():
        raise ValueError("Cycle cannot be negative.")

    if (df["Capacity_Ah"] <= 0).any():
        raise ValueError("Capacity_Ah must be greater than zero.")

    # --------------------------------------------------------
    # Cycle normalized
    #
    # Since this is a single inference record, use the
    # supplied cycle directly. The trained model already
    # contains the preprocessing pipeline.
    # --------------------------------------------------------

    df["Cycle_Normalized"] = df["Cycle"]

    # --------------------------------------------------------
    # Capacity ratio
    #
    # Capacity ratio needs a reference capacity.
    #
    # For API inference we use the initial nominal capacity
    # supplied by the caller when available.
    # --------------------------------------------------------

    initial_capacity = data.get("Initial_Capacity_Ah")

    if initial_capacity is not None:

        initial_capacity = to_float(
            initial_capacity,
            "Initial_Capacity_Ah"
        )

        if initial_capacity <= 0:
            raise ValueError(
                "Initial_Capacity_Ah must be greater than zero."
            )

        df["Capacity_Ratio"] = (
            df["Capacity_Ah"] / initial_capacity
        )

    else:

        # If no reference capacity is supplied, use 1.0.
        #
        # This keeps the API usable, but for production
        # inference the initial/nominal capacity should be
        # supplied whenever possible.
        df["Capacity_Ratio"] = 1.0

    # --------------------------------------------------------
    # Voltage range
    # --------------------------------------------------------

    if (
        "Voltage_Min_V" in df.columns
        and "Voltage_Max_V" in df.columns
    ):

        df["Voltage_Range_V"] = (
            df["Voltage_Max_V"] -
            df["Voltage_Min_V"]
        )

    else:

        df["Voltage_Range_V"] = np.nan

    # --------------------------------------------------------
    # Current range
    # --------------------------------------------------------

    if (
        "Current_Min_A" in df.columns
        and "Current_Max_A" in df.columns
    ):

        df["Current_Range_A"] = (
            df["Current_Max_A"] -
            df["Current_Min_A"]
        )

    else:

        df["Current_Range_A"] = np.nan

    # --------------------------------------------------------
    # Temperature range
    # --------------------------------------------------------

    if (
        "Temperature_Min_C" in df.columns
        and "Temperature_Max_C" in df.columns
    ):

        df["Temperature_Range_C"] = (
            df["Temperature_Max_C"] -
            df["Temperature_Min_C"]
        )

    else:

        df["Temperature_Range_C"] = np.nan

    # --------------------------------------------------------
    # Ensure Source_Dataset exists
    # --------------------------------------------------------

    if "Source_Dataset" not in df.columns:

        df["Source_Dataset"] = "NASA"

    df["Source_Dataset"] = (
        df["Source_Dataset"]
        .astype(str)
        .str.strip()
    )

    allowed_datasets = {
        "NASA",
        "Oxford",
        "CALCE"
    }

    if df["Source_Dataset"].iloc[0] not in allowed_datasets:

        raise ValueError(
            "Source_Dataset must be one of: "
            "NASA, Oxford, CALCE"
        )

    # --------------------------------------------------------
    # Ensure every trained feature exists
    # --------------------------------------------------------

    for feature in FEATURE_COLUMNS:

        if feature not in df.columns:

            if feature == "Source_Dataset":

                df[feature] = "NASA"

            else:

                df[feature] = np.nan

    # --------------------------------------------------------
    # Correct feature order
    # --------------------------------------------------------

    X = df[FEATURE_COLUMNS].copy()

    return X


# ============================================================
# STATUS CLASSIFICATION
# ============================================================

def classify_soh(soh):

    if soh >= 90:

        return {
            "status": "Excellent",
            "condition": "Healthy",
            "severity": "normal"
        }

    elif soh >= 80:

        return {
            "status": "Good",
            "condition": "Healthy",
            "severity": "normal"
        }

    elif soh >= 70:

        return {
            "status": "Moderate",
            "condition": "Aging",
            "severity": "warning"
        }

    elif soh >= 60:

        return {
            "status": "Poor",
            "condition": "Degraded",
            "severity": "warning"
        }

    else:

        return {
            "status": "Critical",
            "condition": "Replace / Service",
            "severity": "critical"
        }


# ============================================================
# API HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "service": "SOH Prediction API",
        "model_loaded": MODEL is not None,
        "model_type": (
            type(MODEL).__name__
            if MODEL is not None
            else None
        ),
        "features": len(FEATURE_COLUMNS)
        if FEATURE_COLUMNS is not None
        else 0
    })


# ============================================================
# MODEL INFORMATION
# ============================================================

@app.route("/api/model-info", methods=["GET"])
def model_info():

    return jsonify({
        "success": True,
        "model": MODEL_METADATA,
        "feature_count": len(FEATURE_COLUMNS),
        "feature_columns": FEATURE_COLUMNS
    })


# ============================================================
# SOH PREDICTION API
# ============================================================

@app.route("/api/predict-soh", methods=["POST"])
def predict_soh():

    try:

        # ----------------------------------------------------
        # Read JSON
        # ----------------------------------------------------

        data = request.get_json(silent=True)

        if data is None:

            return jsonify({
                "success": False,
                "error": "Request body must contain JSON data."
            }), 400

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        required_fields = [
            "Source_Dataset",
            "Cycle",
            "Capacity_Ah"
        ]

        for field in required_fields:

            if field not in data:

                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400

        # ----------------------------------------------------
        # Convert numeric fields
        # ----------------------------------------------------

        numeric_fields = [

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

            "Initial_Capacity_Ah"
        ]

        clean_data = dict(data)

        for field in numeric_fields:

            if field in clean_data:

                clean_data[field] = to_float(
                    clean_data[field],
                    field,
                    required=False
                )

        # ----------------------------------------------------
        # Create features
        # ----------------------------------------------------

        X = create_features(clean_data)

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        raw_prediction = MODEL.predict(X)

        predicted_soh = float(
            np.asarray(raw_prediction).reshape(-1)[0]
        )

        # ----------------------------------------------------
        # Physical SOH range
        # ----------------------------------------------------

        raw_prediction_value = predicted_soh

        predicted_soh = max(
            0.0,
            min(100.0, predicted_soh)
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        health = classify_soh(predicted_soh)

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        response = {

            "success": True,

            "prediction": {

                "soh_percent": round(
                    predicted_soh,
                    4
                ),

                "raw_soh_percent": round(
                    raw_prediction_value,
                    4
                ),

                "status": health["status"],

                "condition": health["condition"],

                "severity": health["severity"]
            },

            "battery": {

                "source_dataset":
                    clean_data.get(
                        "Source_Dataset"
                    ),

                "battery_id":
                    clean_data.get(
                        "Battery_ID"
                    ),

                "cycle":
                    clean_data.get(
                        "Cycle"
                    ),

                "capacity_ah":
                    clean_data.get(
                        "Capacity_Ah"
                    )
            }

        }

        return jsonify(response)

    except ValueError as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:

        print("\nSOH API ERROR:")
        print(str(e))

        return jsonify({
            "success": False,
            "error": "SOH prediction failed.",
            "details": str(e)
        }), 500


# ============================================================
# SIMPLE WEB PAGE
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return """
<!DOCTYPE html>

<html>

<head>

    <title>EV Digital Twin - SOH</title>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <style>

        body {
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            margin: 0;
            padding: 40px;
        }

        .container {
            max-width: 900px;
            margin: auto;
        }

        h1 {
            color: #1f2937;
        }

        .card {
            background: white;
            padding: 25px;
            margin-top: 20px;
            border-radius: 12px;
            box-shadow:
                0 2px 10px rgba(0,0,0,0.08);
        }

        .grid {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
        }

        label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
        }

        input,
        select {
            width: 100%;
            box-sizing: border-box;
            padding: 10px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
        }

        button {
            margin-top: 20px;
            padding: 12px 25px;
            border: none;
            border-radius: 6px;
            background: #2563eb;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }

        button:hover {
            background: #1d4ed8;
        }

        #result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            background: #eef2ff;
            display: none;
        }

        .soh {
            font-size: 42px;
            font-weight: bold;
            color: #2563eb;
        }

        .error {
            background: #fee2e2 !important;
            color: #991b1b;
        }

    </style>

</head>

<body>

<div class="container">

    <h1>EV Digital Twin</h1>

    <p>Battery State of Health Prediction</p>

    <div class="card">

        <div class="grid">

            <div>
                <label>Dataset</label>

                <select id="Source_Dataset">

                    <option value="NASA">
                        NASA
                    </option>

                    <option value="Oxford">
                        Oxford
                    </option>

                    <option value="CALCE">
                        CALCE
                    </option>

                </select>

            </div>

            <div>
                <label>Battery ID</label>

                <input
                    id="Battery_ID"
                    value="B0005">
            </div>

            <div>
                <label>Cycle</label>

                <input
                    id="Cycle"
                    type="number"
                    value="100">
            </div>

            <div>
                <label>Capacity (Ah)</label>

                <input
                    id="Capacity_Ah"
                    type="number"
                    step="0.0001"
                    value="1.85">
            </div>

            <div>
                <label>Initial Capacity (Ah)</label>

                <input
                    id="Initial_Capacity_Ah"
                    type="number"
                    step="0.0001"
                    value="2.0">
            </div>

            <div>
                <label>Voltage Min (V)</label>

                <input
                    id="Voltage_Min_V"
                    type="number"
                    step="0.0001"
                    value="2.4">
            </div>

            <div>
                <label>Voltage Max (V)</label>

                <input
                    id="Voltage_Max_V"
                    type="number"
                    step="0.0001"
                    value="4.2">
            </div>

            <div>
                <label>Voltage Mean (V)</label>

                <input
                    id="Voltage_Mean_V"
                    type="number"
                    step="0.0001"
                    value="3.5">
            </div>

            <div>
                <label>Voltage Final (V)</label>

                <input
                    id="Voltage_Final_V"
                    type="number"
                    step="0.0001"
                    value="3.4">
            </div>

            <div>
                <label>Current Min (A)</label>

                <input
                    id="Current_Min_A"
                    type="number"
                    step="0.0001"
                    value="-2.0">
            </div>

            <div>
                <label>Current Max (A)</label>

                <input
                    id="Current_Max_A"
                    type="number"
                    step="0.0001"
                    value="0.0">
            </div>

            <div>
                <label>Current Mean (A)</label>

                <input
                    id="Current_Mean_A"
                    type="number"
                    step="0.0001"
                    value="-1.8">
            </div>

            <div>
                <label>Temperature Min (°C)</label>

                <input
                    id="Temperature_Min_C"
                    type="number"
                    step="0.01"
                    value="24">
            </div>

            <div>
                <label>Temperature Max (°C)</label>

                <input
                    id="Temperature_Max_C"
                    type="number"
                    step="0.01"
                    value="40">
            </div>

            <div>
                <label>Temperature Mean (°C)</label>

                <input
                    id="Temperature_Mean_C"
                    type="number"
                    step="0.01"
                    value="32">
            </div>

            <div>
                <label>Temperature Final (°C)</label>

                <input
                    id="Temperature_Final_C"
                    type="number"
                    step="0.01"
                    value="36">
            </div>

            <div>
                <label>Discharge Time (s)</label>

                <input
                    id="Discharge_Time_s"
                    type="number"
                    step="0.01"
                    value="3000">
            </div>

        </div>

        <button onclick="predictSOH()">
            Predict SOH
        </button>

    </div>


    <div id="result">

        <h2>SOH Prediction</h2>

        <div
            id="soh"
            class="soh">
            --
        </div>

        <p>
            <strong>Status:</strong>
            <span id="status">--</span>
        </p>

        <p>
            <strong>Condition:</strong>
            <span id="condition">--</span>
        </p>

    </div>

</div>


<script>

async function predictSOH() {

    const fields = [

        "Source_Dataset",
        "Battery_ID",
        "Cycle",
        "Capacity_Ah",
        "Initial_Capacity_Ah",

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

        "Discharge_Time_s"

    ];


    const data = {};


    fields.forEach(function(field) {

        const element =
            document.getElementById(field);

        if (
            field === "Source_Dataset" ||
            field === "Battery_ID"
        ) {

            data[field] = element.value;

        } else {

            data[field] =
                Number(element.value);

        }

    });


    const result =
        document.getElementById("result");


    try {

        result.style.display = "block";

        result.classList.remove("error");

        result.innerHTML =
            "<h2>Predicting...</h2>";


        const response =
            await fetch(
                "/api/predict-soh",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(data)
                }
            );


        const output =
            await response.json();


        if (!response.ok ||
            !output.success) {

            throw new Error(
                output.error ||
                "Prediction failed."
            );

        }


        result.innerHTML = `

            <h2>SOH Prediction</h2>

            <div class="soh">
                ${output.prediction.soh_percent.toFixed(2)}%
            </div>

            <p>
                <strong>Status:</strong>
                ${output.prediction.status}
            </p>

            <p>
                <strong>Condition:</strong>
                ${output.prediction.condition}
            </p>

            <p>
                <strong>Battery:</strong>
                ${output.battery.battery_id || "N/A"}
            </p>

            <p>
                <strong>Cycle:</strong>
                ${output.battery.cycle}
            </p>

        `;

    }

    catch(error) {

        result.style.display = "block";

        result.classList.add("error");

        result.innerHTML = `

            <h2>Prediction Error</h2>

            <p>
                ${error.message}
            </p>

        `;

    }

}

</script>

</body>

</html>
"""


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    try:

        load_model()

        print("\n" + "=" * 70)
        print("FLASK SOH API READY")
        print("=" * 70)

        print("\nDashboard:")
        print("  http://127.0.0.1:5000")

        print("\nHealth:")
        print("  http://127.0.0.1:5000/api/health")

        print("\nModel information:")
        print("  http://127.0.0.1:5000/api/model-info")

        print("\nSOH prediction:")
        print("  POST http://127.0.0.1:5000/api/predict-soh")

        print("\nPress CTRL+C to stop.")

        app.run(
            host="127.0.0.1",
            port=5000,
            debug=False
        )

    except Exception as e:

        print("\n" + "=" * 70)
        print("APPLICATION STARTUP FAILED")
        print("=" * 70)

        print(str(e))

        raise