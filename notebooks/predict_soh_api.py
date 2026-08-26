"""
SOH PREDICTION API / INFERENCE MODULE
=====================================

Loads the trained SOH model and provides reusable prediction functions
for the Flask EV Digital Twin application.

Project:
    C:\Major project\flask_app

Model:
    processed\soh\models\best_soh_model.pkl

Feature metadata:
    processed\soh\models\feature_columns.json

Model metadata:
    processed\soh\models\model_metadata.json
"""

from pathlib import Path
import json
import pickle
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

SOH_DIR = PROJECT_DIR / "processed" / "soh"
MODEL_DIR = SOH_DIR / "models"

MODEL_PATH = MODEL_DIR / "best_soh_model.pkl"
FEATURE_METADATA_PATH = MODEL_DIR / "feature_columns.json"
MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"


# ============================================================================
# REQUIRED FEATURES
# ============================================================================

BASE_NUMERIC_FEATURES = [
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

DERIVED_FEATURES = [
    "Cycle_Normalized",
    "Capacity_Ratio",
    "Voltage_Range_V",
    "Current_Range_A",
    "Temperature_Range_C",
]

IDENTIFIER_FEATURE = "Source_Dataset"


# ============================================================================
# SOH PREDICTOR CLASS
# ============================================================================

class SOHPredictor:
    """
    Reusable SOH prediction class.

    Loads the trained pipeline and metadata once, then provides
    prediction methods for individual battery records or DataFrames.
    """

    def __init__(
        self,
        model_path=MODEL_PATH,
        feature_metadata_path=FEATURE_METADATA_PATH,
        model_metadata_path=MODEL_METADATA_PATH,
    ):

        self.model_path = Path(model_path)
        self.feature_metadata_path = Path(feature_metadata_path)
        self.model_metadata_path = Path(model_metadata_path)

        self.model = None
        self.feature_columns = None
        self.model_metadata = None

        self._load_all()

    # ------------------------------------------------------------------------
    # LOAD MODEL + METADATA
    # ------------------------------------------------------------------------

    def _load_all(self):

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"SOH model not found:\n{self.model_path}"
            )

        if not self.feature_metadata_path.exists():
            raise FileNotFoundError(
                f"Feature metadata not found:\n"
                f"{self.feature_metadata_path}"
            )

        print("Loading SOH model...")

        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)

        print(f"Model loaded: {type(self.model).__name__}")

        print("Loading feature metadata...")

        with open(self.feature_metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Support either:
        # {"feature_columns": [...]}
        # or directly [...]
        if isinstance(metadata, dict):
            self.feature_columns = metadata.get(
                "feature_columns",
                metadata.get("features", [])
            )
        else:
            self.feature_columns = metadata

        if not self.feature_columns:
            raise ValueError(
                "No feature columns found in feature metadata."
            )

        print(
            f"Feature columns loaded: "
            f"{len(self.feature_columns)}"
        )

        if self.model_metadata_path.exists():

            with open(
                self.model_metadata_path,
                "r",
                encoding="utf-8"
            ) as f:
                self.model_metadata = json.load(f)

        else:

            self.model_metadata = {}

    # ------------------------------------------------------------------------
    # FEATURE ENGINEERING
    # ------------------------------------------------------------------------

    @staticmethod
    def create_features(df):
        """
        Recreates exactly the derived features used during training.
        """

        df = df.copy()

        # --------------------------------------------------------------
        # Numeric conversion
        # --------------------------------------------------------------

        numeric_columns = [
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

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # --------------------------------------------------------------
        # Cycle normalized
        # --------------------------------------------------------------

        if "Cycle" in df.columns:

            max_cycle = df["Cycle"].max()

            if pd.isna(max_cycle) or max_cycle <= 0:
                max_cycle = 1.0

            df["Cycle_Normalized"] = (
                df["Cycle"] / max_cycle
            )

        # --------------------------------------------------------------
        # Capacity ratio
        #
        # Capacity ratio is calculated relative to the first capacity
        # of each battery/cell when Battery_ID is available.
        # --------------------------------------------------------------

        if "Capacity_Ah" in df.columns:

            if "Battery_ID" in df.columns:

                first_capacity = (
                    df.groupby(
                        ["Source_Dataset", "Battery_ID"]
                    )["Capacity_Ah"]
                    .transform("first")
                )

                first_capacity = first_capacity.replace(
                    0,
                    np.nan
                )

                df["Capacity_Ratio"] = (
                    df["Capacity_Ah"] /
                    first_capacity
                )

            else:

                first_capacity = df["Capacity_Ah"].iloc[0]

                if (
                    pd.isna(first_capacity)
                    or first_capacity == 0
                ):
                    first_capacity = 1.0

                df["Capacity_Ratio"] = (
                    df["Capacity_Ah"] /
                    first_capacity
                )

        # --------------------------------------------------------------
        # Voltage range
        # --------------------------------------------------------------

        if (
            "Voltage_Max_V" in df.columns
            and "Voltage_Min_V" in df.columns
        ):

            df["Voltage_Range_V"] = (
                df["Voltage_Max_V"]
                - df["Voltage_Min_V"]
            )

        # --------------------------------------------------------------
        # Current range
        # --------------------------------------------------------------

        if (
            "Current_Max_A" in df.columns
            and "Current_Min_A" in df.columns
        ):

            df["Current_Range_A"] = (
                df["Current_Max_A"]
                - df["Current_Min_A"]
            )

        # --------------------------------------------------------------
        # Temperature range
        # --------------------------------------------------------------

        if (
            "Temperature_Max_C" in df.columns
            and "Temperature_Min_C" in df.columns
        ):

            df["Temperature_Range_C"] = (
                df["Temperature_Max_C"]
                - df["Temperature_Min_C"]
            )

        return df

    # ------------------------------------------------------------------------
    # PREPARE INPUT
    # ------------------------------------------------------------------------

    def prepare_input(self, data):
        """
        Prepare a DataFrame for model prediction.
        """

        if isinstance(data, dict):

            df = pd.DataFrame([data])

        elif isinstance(data, pd.DataFrame):

            df = data.copy()

        else:

            raise TypeError(
                "Input must be a dictionary or pandas DataFrame."
            )

        # --------------------------------------------------------------
        # Source dataset
        # --------------------------------------------------------------

        if "Source_Dataset" not in df.columns:

            df["Source_Dataset"] = "NASA"

        df["Source_Dataset"] = (
            df["Source_Dataset"]
            .astype(str)
            .str.strip()
        )

        # --------------------------------------------------------------
        # Create derived features
        # --------------------------------------------------------------

        df = self.create_features(df)

        # --------------------------------------------------------------
        # Make sure every required feature exists
        # --------------------------------------------------------------

        for feature in self.feature_columns:

            if feature not in df.columns:

                df[feature] = np.nan

        # --------------------------------------------------------------
        # Select feature order exactly as training
        # --------------------------------------------------------------

        X = df[self.feature_columns].copy()

        # --------------------------------------------------------------
        # Numeric columns
        # --------------------------------------------------------------

        categorical_columns = {
            "Source_Dataset"
        }

        for column in X.columns:

            if column not in categorical_columns:

                X[column] = pd.to_numeric(
                    X[column],
                    errors="coerce"
                )

        # --------------------------------------------------------------
        # Missing values
        #
        # The trained Pipeline contains preprocessing, so numeric NaN
        # values can be handled by the pipeline if configured that way.
        #
        # For safety, fill missing values here using column medians
        # calculated from the current input.
        # --------------------------------------------------------------

        numeric_columns = [
            column
            for column in X.columns
            if column not in categorical_columns
        ]

        for column in numeric_columns:

            if X[column].isna().any():

                median_value = X[column].median()

                if pd.isna(median_value):
                    median_value = 0.0

                X[column] = X[column].fillna(
                    median_value
                )

        # --------------------------------------------------------------
        # Replace non-finite values
        # --------------------------------------------------------------

        for column in numeric_columns:

            X[column] = X[column].replace(
                [np.inf, -np.inf],
                np.nan
            )

            X[column] = X[column].fillna(0.0)

        return X

    # ------------------------------------------------------------------------
    # PREDICT
    # ------------------------------------------------------------------------

    def predict(self, data):
        """
        Predict SOH for one record or multiple records.

        Returns:
            numpy array
        """

        X = self.prepare_input(data)

        predictions = self.model.predict(X)

        predictions = np.asarray(
            predictions,
            dtype=float
        )

        # Physical SOH range
        predictions = np.clip(
            predictions,
            0.0,
            100.0
        )

        return predictions

    # ------------------------------------------------------------------------
    # PREDICT SINGLE RECORD
    # ------------------------------------------------------------------------

    def predict_single(self, data):
        """
        Predict SOH for one battery record.

        Returns:
            float
        """

        predictions = self.predict(data)

        if len(predictions) != 1:

            raise ValueError(
                "predict_single() expects exactly one record."
            )

        return float(predictions[0])

    # ------------------------------------------------------------------------
    # PREDICT WITH STATUS
    # ------------------------------------------------------------------------

    def predict_with_status(self, data):
        """
        Predict SOH and provide a simple battery health status.
        """

        soh = self.predict_single(data)

        if soh >= 90:

            status = "Excellent"
            condition = "Healthy"

        elif soh >= 80:

            status = "Good"
            condition = "Healthy"

        elif soh >= 70:

            status = "Moderate"
            condition = "Aging"

        elif soh >= 60:

            status = "Poor"
            condition = "Aging"

        else:

            status = "Critical"
            condition = "Replace / Inspect"

        return {
            "predicted_soh_percent": round(soh, 4),
            "status": status,
            "condition": condition,
        }


# ============================================================================
# TEST PREDICTION
# ============================================================================

def test_predictor():

    print("=" * 70)
    print("SOH API / INFERENCE TEST")
    print("=" * 70)

    print()
    print("Project directory:")
    print(f"  {PROJECT_DIR}")

    print()
    print("Loading predictor...")

    predictor = SOHPredictor()

    print()
    print("Predictor loaded successfully.")

    # ------------------------------------------------------------------------
    # Example input
    # ------------------------------------------------------------------------

    sample_input = {

        "Source_Dataset": "NASA",

        "Battery_ID": "B0005",

        "Cycle": 100,

        "Capacity_Ah": 1.85,

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

        "Discharge_Time_s": 3000,
    }

    print()
    print("=" * 70)
    print("TEST INPUT")
    print("=" * 70)

    for key, value in sample_input.items():

        print(
            f"{key:<25}: {value}"
        )

    print()
    print("=" * 70)
    print("PREDICTION")
    print("=" * 70)

    result = predictor.predict_with_status(
        sample_input
    )

    print(
        f"Predicted SOH : "
        f"{result['predicted_soh_percent']:.4f}%"
    )

    print(
        f"Status        : "
        f"{result['status']}"
    )

    print(
        f"Condition     : "
        f"{result['condition']}"
    )

    print()
    print("=" * 70)
    print("API / INFERENCE TEST COMPLETE")
    print("=" * 70)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    test_predictor()