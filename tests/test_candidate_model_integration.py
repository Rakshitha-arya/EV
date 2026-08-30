"""Isolated integration check for the inactive 18-feature candidate."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib

import app as app_module


CANDIDATE_DIR = (
    Path(__file__).resolve().parents[1]
    / "processed"
    / "soh"
    / "models"
    / "leakage_free"
)
CANDIDATE_MODEL_PATH = CANDIDATE_DIR / "leakage_free_ridge_pipeline.pkl"
CANDIDATE_FEATURES_PATH = CANDIDATE_DIR / "feature_columns.json"

PREDICTION_PAYLOAD = {
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


class CandidateModelIntegrationTest(unittest.TestCase):
    def test_candidate_prediction_uses_18_feature_contract(self):
        candidate_model = joblib.load(CANDIDATE_MODEL_PATH)
        with CANDIDATE_FEATURES_PATH.open(encoding="utf-8") as file:
            candidate_features = json.load(file)["feature_columns"]

        self.assertEqual(len(candidate_features), 18)
        self.assertNotIn("Capacity_Ratio", candidate_features)
        self.assertNotIn("Cycle_Normalized", candidate_features)
        self.assertEqual(
            list(candidate_model.feature_names_in_),
            candidate_features,
        )

        deployed_model = app_module.model
        with (
            patch.object(app_module, "model", candidate_model),
            patch.object(app_module, "feature_columns", candidate_features),
            patch.object(app_module, "MODEL_LOADED", True),
        ):
            feature_frame = app_module.build_feature_dataframe(
                PREDICTION_PAYLOAD
            )
            self.assertEqual(list(feature_frame.columns), candidate_features)

            response = app_module.app.test_client().post(
                "/api/predict-soh",
                json=PREDICTION_PAYLOAD,
            )

        self.assertIs(app_module.model, deployed_model)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])
        self.assertIn("soh_percent", response.get_json()["prediction"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
