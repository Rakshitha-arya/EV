from flask import Flask, render_template
from pathlib import Path
import pandas as pd
import math
import traceback


# ============================================================
# EV DIGITAL TWIN
# STEP 38 - COMPLETE FLASK BACKEND + API
# ============================================================

app = Flask(__name__)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DIR = BASE_DIR / "processed"
RESULTS_DIR = BASE_DIR / "results"


# ============================================================
# DATA FILES
# ============================================================

SOH_FILE = PROCESSED_DIR / "NASA_digital_twin_SOH.csv"

PROTOTYPE_FILE = PROCESSED_DIR / "EV_prototype_sensor_data.csv"

PROTOTYPE_TWIN_FILE = (
    PROCESSED_DIR / "EV_prototype_digital_twin.csv"
)

INTEGRATED_FILE = (
    PROCESSED_DIR / "EV_integrated_digital_twin.csv"
)

FAULT_FILE = (
    PROCESSED_DIR / "EV_fault_detection_results.csv"
)

FAULT_INJECTION_FILE = (
    PROCESSED_DIR / "EV_fault_injection_results.csv"
)

LIVE_FILE = (
    PROCESSED_DIR / "EV_live_digital_twin.csv"
)

SOH_PREDICTION_FILE = (
    PROCESSED_DIR / "NASA_final_SOH_predictions.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=None):

    try:

        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


def safe_int(value, default=None):

    try:

        if value is None:
            return default

        if pd.isna(value):
            return default

        return int(value)

    except Exception:

        return default


def clean_value(value):

    if value is None:
        return None

    if isinstance(value, float):

        if math.isnan(value) or math.isinf(value):
            return None

        return round(value, 4)

    if isinstance(value, int):
        return value

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass

    return value


def load_csv(file_path):

    try:

        if not file_path.exists():

            print(
                f"[WARNING] File not found: {file_path}"
            )

            return pd.DataFrame()

        df = pd.read_csv(file_path)

        print(
            f"[OK] Loaded {file_path.name} "
            f"({len(df)} rows, {len(df.columns)} columns)"
        )

        return df

    except Exception as error:

        print(
            f"[ERROR] Could not load "
            f"{file_path.name}: {error}"
        )

        return pd.DataFrame()


def find_column(df, possible_names):

    if df is None or df.empty:
        return None

    # Exact matching
    normalized = {}

    for column in df.columns:

        key = str(column).strip().lower()

        normalized[key] = column

    for name in possible_names:

        key = name.strip().lower()

        if key in normalized:

            return normalized[key]

    # Partial matching
    for column in df.columns:

        column_lower = (
            str(column).strip().lower()
        )

        for name in possible_names:

            name_lower = (
                name.strip().lower()
            )

            if name_lower in column_lower:

                return column

    return None


def latest_record(df):

    if df is None or df.empty:

        return {}

    return df.iloc[-1].to_dict()


def dataframe_to_records(df, limit=100):

    if df is None or df.empty:

        return []

    data = df.tail(limit).copy()

    records = []

    for _, row in data.iterrows():

        record = {}

        for column in data.columns:

            record[str(column)] = clean_value(
                row[column]
            )

        records.append(record)

    return records


# ============================================================
# LOAD ALL PROJECT DATA
# ============================================================

def load_project_data():

    return {

        "soh": load_csv(SOH_FILE),

        "prototype": load_csv(PROTOTYPE_FILE),

        "prototype_twin": load_csv(
            PROTOTYPE_TWIN_FILE
        ),

        "integrated": load_csv(
            INTEGRATED_FILE
        ),

        "fault": load_csv(
            FAULT_FILE
        ),

        "fault_injection": load_csv(
            FAULT_INJECTION_FILE
        ),

        "live": load_csv(
            LIVE_FILE
        ),

        "soh_prediction": load_csv(
            SOH_PREDICTION_FILE
        )

    }


# ============================================================
# BATTERY DATA
# ============================================================

def get_battery_data(data):

    integrated = data["integrated"]

    prototype = data["prototype"]

    twin = data["prototype_twin"]

    soh_df = data["soh"]

    # --------------------------------------------------------
    # Select latest record
    # --------------------------------------------------------

    latest = latest_record(integrated)

    if not latest:

        latest = latest_record(twin)

    if not latest:

        latest = latest_record(prototype)

    # --------------------------------------------------------
    # SOH
    # --------------------------------------------------------

    soh_column = find_column(
        soh_df,
        [
            "predicted_SOH_percent",
            "Predicted_SOH_percent",
            "SOH_percent",
            "SOH",
            "soh"
        ]
    )

    soh = None

    if soh_column and not soh_df.empty:

        soh = safe_float(
            soh_df.iloc[-1][soh_column]
        )

    # Try integrated data if necessary
    if soh is None:

        soh_column_integrated = find_column(
            integrated,
            [
                "predicted_SOH_percent",
                "Predicted_SOH_percent",
                "SOH_percent",
                "SOH",
                "soh"
            ]
        )

        if (
            soh_column_integrated
            and not integrated.empty
        ):

            soh = safe_float(
                integrated.iloc[-1][
                    soh_column_integrated
                ]
            )

    # Try latest record
    if soh is None:

        for key in [
            "predicted_SOH_percent",
            "Predicted_SOH_percent",
            "SOH_percent",
            "SOH",
            "soh"
        ]:

            if key in latest:

                soh = safe_float(
                    latest[key]
                )

                if soh is not None:
                    break

    # --------------------------------------------------------
    # VOLTAGE
    # --------------------------------------------------------

    voltage_column = find_column(
        integrated,
        [
            "battery_voltage_V",
            "battery_voltage",
            "voltage_V",
            "voltage"
        ]
    )

    voltage = None

    if (
        voltage_column
        and not integrated.empty
    ):

        voltage = safe_float(
            integrated.iloc[-1][
                voltage_column
            ]
        )

    # Try latest record
    if voltage is None:

        for key in [
            "battery_voltage_V",
            "battery_voltage",
            "voltage_V",
            "voltage"
        ]:

            if key in latest:

                voltage = safe_float(
                    latest[key]
                )

                if voltage is not None:
                    break

    # --------------------------------------------------------
    # CURRENT
    # --------------------------------------------------------

    current_column = find_column(
        integrated,
        [
            "battery_current_A",
            "battery_current",
            "current_A",
            "current"
        ]
    )

    current = None

    if (
        current_column
        and not integrated.empty
    ):

        current = safe_float(
            integrated.iloc[-1][
                current_column
            ]
        )

    if current is None:

        for key in [
            "battery_current_A",
            "battery_current",
            "current_A",
            "current"
        ]:

            if key in latest:

                current = safe_float(
                    latest[key]
                )

                if current is not None:
                    break

    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    temperature_column = find_column(
        integrated,
        [
            "battery_temperature_C",
            "battery_temperature",
            "temperature_C",
            "temperature"
        ]
    )

    temperature = None

    if (
        temperature_column
        and not integrated.empty
    ):

        temperature = safe_float(
            integrated.iloc[-1][
                temperature_column
            ]
        )

    if temperature is None:

        for key in [
            "battery_temperature_C",
            "battery_temperature",
            "temperature_C",
            "temperature"
        ]:

            if key in latest:

                temperature = safe_float(
                    latest[key]
                )

                if temperature is not None:
                    break

    # --------------------------------------------------------
    # POWER
    # --------------------------------------------------------

    power = None

    if (
        voltage is not None
        and current is not None
    ):

        power = voltage * current

    # --------------------------------------------------------
    # CYCLE
    # --------------------------------------------------------

    cycle_column = find_column(
        soh_df,
        [
            "cycle",
            "Cycle",
            "cycle_index"
        ]
    )

    cycle = None

    if (
        cycle_column
        and not soh_df.empty
    ):

        cycle = safe_int(
            soh_df.iloc[-1][
                cycle_column
            ]
        )

    # --------------------------------------------------------
    # SOC
    # --------------------------------------------------------
    #
    # SOC is intentionally left as None for now because
    # Step 41 will implement the actual SOC calculation.
    #
    # We should NOT invent an SOC value.
    #

    soc = None

    return {

        "soh": clean_value(soh),

        "soc": clean_value(soc),

        "voltage": clean_value(voltage),

        "current": clean_value(current),

        "temperature": clean_value(
            temperature
        ),

        "power": clean_value(power),

        "cycle": cycle

    }


# ============================================================
# VEHICLE DATA
# ============================================================

def get_vehicle_data(data):

    integrated = data["integrated"]

    prototype = data["prototype"]

    latest = latest_record(integrated)

    if not latest:

        latest = latest_record(prototype)

    # --------------------------------------------------------
    # GPS SPEED
    # --------------------------------------------------------

    speed_column = find_column(
        integrated,
        [
            "gps_speed_kmph",
            "gps_speed",
            "speed_kmph",
            "speed"
        ]
    )

    speed = None

    if (
        speed_column
        and not integrated.empty
    ):

        speed = safe_float(
            integrated.iloc[-1][
                speed_column
            ]
        )

    if speed is None:

        for key in [
            "gps_speed_kmph",
            "gps_speed",
            "speed_kmph",
            "speed"
        ]:

            if key in latest:

                speed = safe_float(
                    latest[key]
                )

                if speed is not None:
                    break

    # --------------------------------------------------------
    # TYRE PRESSURE
    # --------------------------------------------------------

    pressure_column = find_column(
        integrated,
        [
            "tyre_pressure_psi",
            "tyre_pressure",
            "tire_pressure_psi",
            "tire_pressure",
            "pressure"
        ]
    )

    pressure = None

    if (
        pressure_column
        and not integrated.empty
    ):

        pressure = safe_float(
            integrated.iloc[-1][
                pressure_column
            ]
        )

    if pressure is None:

        for key in [
            "tyre_pressure_psi",
            "tyre_pressure",
            "tire_pressure_psi",
            "tire_pressure",
            "pressure"
        ]:

            if key in latest:

                pressure = safe_float(
                    latest[key]
                )

                if pressure is not None:
                    break

    # --------------------------------------------------------
    # LATITUDE
    # --------------------------------------------------------

    latitude_column = find_column(
        integrated,
        [
            "latitude",
            "lat",
            "gps_latitude"
        ]
    )

    latitude = None

    if (
        latitude_column
        and not integrated.empty
    ):

        latitude = safe_float(
            integrated.iloc[-1][
                latitude_column
            ]
        )

    # --------------------------------------------------------
    # LONGITUDE
    # --------------------------------------------------------

    longitude_column = find_column(
        integrated,
        [
            "longitude",
            "lon",
            "lng",
            "gps_longitude"
        ]
    )

    longitude = None

    if (
        longitude_column
        and not integrated.empty
    ):

        longitude = safe_float(
            integrated.iloc[-1][
                longitude_column
            ]
        )

    return {

        "speed": clean_value(speed),

        "tyre_pressure": clean_value(
            pressure
        ),

        "latitude": clean_value(
            latitude
        ),

        "longitude": clean_value(
            longitude
        )

    }


# ============================================================
# FAULT DATA
# ============================================================

def get_fault_data(data):

    fault_df = data["fault"]

    latest = latest_record(fault_df)

    # --------------------------------------------------------
    # No fault data
    # --------------------------------------------------------

    if not latest:

        return {

            "voltage": "NORMAL",

            "current": "NORMAL",

            "temperature": "NORMAL",

            "tyre_pressure": "NORMAL",

            "soh": "NORMAL",

            "vehicle": "HEALTHY"

        }

    # --------------------------------------------------------
    # VOLTAGE
    # --------------------------------------------------------

    voltage = latest.get(
        "battery_voltage_status",
        latest.get(
            "voltage_status",
            "NORMAL"
        )
    )

    # --------------------------------------------------------
    # CURRENT
    # --------------------------------------------------------

    current = latest.get(
        "battery_current_status",
        latest.get(
            "current_status",
            "NORMAL"
        )
    )

    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    temperature = latest.get(
        "battery_temperature_status",
        latest.get(
            "temperature_status",
            "NORMAL"
        )
    )

    # --------------------------------------------------------
    # TYRE
    # --------------------------------------------------------

    tyre = latest.get(
        "tyre_pressure_status",
        "NORMAL"
    )

    # --------------------------------------------------------
    # SOH
    # --------------------------------------------------------

    soh = latest.get(
        "SOH_status",
        latest.get(
            "soh_status",
            "NORMAL"
        )
    )

    # --------------------------------------------------------
    # VEHICLE
    # --------------------------------------------------------

    vehicle = latest.get(
        "vehicle_status",
        "HEALTHY"
    )

    return {

        "voltage": str(voltage),

        "current": str(current),

        "temperature": str(
            temperature
        ),

        "tyre_pressure": str(tyre),

        "soh": str(soh),

        "vehicle": str(vehicle)

    }


# ============================================================
# BATTERY HEALTH
# ============================================================

def get_health_status(soh):

    if soh is None:

        return "UNKNOWN"

    if soh >= 80:

        return "HEALTHY"

    if soh >= 60:

        return "WARNING"

    return "CRITICAL"


# ============================================================
# COMPLETE DIGITAL TWIN
# ============================================================

def build_digital_twin_data():

    data = load_project_data()

    battery = get_battery_data(data)

    vehicle = get_vehicle_data(data)

    faults = get_fault_data(data)

    health = get_health_status(
        battery["soh"]
    )

    return {

        "success": True,

        "battery": {

            **battery,

            "health": health

        },

        "vehicle": vehicle,

        "faults": faults,

        "timestamp":
            pd.Timestamp.now().isoformat()

    }


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# API HEALTH
# ============================================================

@app.route("/api/health")
def api_health():

    return {

        "success": True,

        "status": "ONLINE",

        "message":
            "EV Digital Twin Flask API is running"

    }


# ============================================================
# API STATUS
# ============================================================

@app.route("/api/status")
def api_status():

    try:

        data = build_digital_twin_data()

        return {

            "success": True,

            "status": "ONLINE",

            "message":
                "EV Digital Twin is running",

            "battery":
                data["battery"],

            "vehicle":
                data["vehicle"],

            "faults":
                data["faults"],

            "timestamp":
                data["timestamp"]

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "status": "OFFLINE",

            "error": str(error)

        }, 500


# ============================================================
# API - COMPLETE DATA
# ============================================================

@app.route("/api/data")
def api_data():

    try:

        return build_digital_twin_data()

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# API - BATTERY
# ============================================================

@app.route("/api/battery")
def api_battery():

    try:

        data = load_project_data()

        battery = get_battery_data(
            data
        )

        battery["health"] = (
            get_health_status(
                battery["soh"]
            )
        )

        return {

            "success": True,

            "battery": battery

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# API - VEHICLE
# ============================================================

@app.route("/api/vehicle")
def api_vehicle():

    try:

        data = load_project_data()

        vehicle = get_vehicle_data(
            data
        )

        return {

            "success": True,

            "vehicle": vehicle

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# API - FAULTS
# ============================================================

@app.route("/api/faults")
def api_faults():

    try:

        data = load_project_data()

        faults = get_fault_data(
            data
        )

        return {

            "success": True,

            "faults": faults

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# API - HISTORY
# ============================================================

@app.route("/api/history")
def api_history():

    try:

        data = load_project_data()

        integrated = data["integrated"]

        records = dataframe_to_records(
            integrated,
            limit=100
        )

        return {

            "success": True,

            "count": len(records),

            "history": records

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# API - FAULT INJECTION
# ============================================================

@app.route("/api/fault-injection")
def api_fault_injection():

    try:

        data = load_project_data()

        fault_df = data[
            "fault_injection"
        ]

        records = dataframe_to_records(
            fault_df,
            limit=100
        )

        return {

            "success": True,

            "count": len(records),

            "scenarios": records

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# API - SOH PREDICTIONS
# ============================================================

@app.route("/api/prediction")
def api_prediction():

    try:

        data = load_project_data()

        soh_df = data[
            "soh_prediction"
        ]

        records = dataframe_to_records(
            soh_df,
            limit=100
        )

        return {

            "success": True,

            "count": len(records),

            "predictions": records

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# API - LIVE DATA
# ============================================================

@app.route("/api/live")
def api_live():

    try:

        data = load_project_data()

        live_df = data["live"]

        records = dataframe_to_records(
            live_df,
            limit=100
        )

        return {

            "success": True,

            "count": len(records),

            "live": records

        }

    except Exception as error:

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error)

        }, 500


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print()

    print("=" * 70)

    print(
        "EV DIGITAL TWIN - FLASK SERVER"
    )

    print("=" * 70)

    print(
        f"Project directory : {BASE_DIR}"
    )

    print(
        f"Processed data    : {PROCESSED_DIR}"
    )

    print()

    print(
        "Checking important files:"
    )

    print()

    files_to_check = [

        SOH_FILE,

        PROTOTYPE_FILE,

        PROTOTYPE_TWIN_FILE,

        INTEGRATED_FILE,

        FAULT_FILE,

        FAULT_INJECTION_FILE,

        LIVE_FILE,

        SOH_PREDICTION_FILE

    ]

    for file_path in files_to_check:

        if file_path.exists():

            status = "FOUND"

        else:

            status = "MISSING"

        print(
            f"{status:8} "
            f"{file_path.name}"
        )

    print()

    print("=" * 70)

    print("API endpoints:")

    print()

    print(
        "  http://127.0.0.1:5000/api/health"
    )

    print(
        "  http://127.0.0.1:5000/api/status"
    )

    print(
        "  http://127.0.0.1:5000/api/data"
    )

    print(
        "  http://127.0.0.1:5000/api/battery"
    )

    print(
        "  http://127.0.0.1:5000/api/vehicle"
    )

    print(
        "  http://127.0.0.1:5000/api/faults"
    )

    print(
        "  http://127.0.0.1:5000/api/history"
    )

    print(
        "  http://127.0.0.1:5000/api/fault-injection"
    )

    print(
        "  http://127.0.0.1:5000/api/prediction"
    )

    print(
        "  http://127.0.0.1:5000/api/live"
    )

    print()

    print("=" * 70)

    print("Starting Flask...")

    print("=" * 70)

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )