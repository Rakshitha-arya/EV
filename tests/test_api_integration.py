"""Lightweight integration coverage for the existing Flask API."""

import unittest
from unittest.mock import patch

from app import app


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


class ApiIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def assert_success(self, response, endpoint):
        self.assertEqual(response.status_code, 200, endpoint)
        self.assertTrue(response.get_json()["success"], endpoint)

    def test_get_endpoints(self):
        for endpoint in [
            "/api/health",
            "/api/battery",
            "/api/vehicle",
            "/api/faults",
            "/api/prediction",
            "/api/history",
        ]:
            with self.subTest(endpoint=endpoint):
                self.assert_success(self.client.get(endpoint), endpoint)

    def test_battery_telemetry_drives_soh_prediction(self):
        battery_response = self.client.get("/api/battery")
        self.assert_success(battery_response, "/api/battery")

        battery = battery_response.get_json()["battery"]
        for field in [
            "voltage", "current", "temperature", "power", "soh",
            "soc", "battery_soc", "cycle", "capacity_ah", "battery_id", "source_dataset",
            "prediction_input", "unavailable_fields",
        ]:
            self.assertIn(field, battery)

        self.assertIsNone(battery["soc"])
        self.assertIsNone(battery["battery_soc"])

        response = self.client.post(
            "/api/predict-soh",
            json=battery["prediction_input"],
        )
        self.assert_success(response, "/api/predict-soh from telemetry")
        self.assertIn("soh_percent", response.get_json()["prediction"])

    def test_missing_optional_telemetry_is_explicit_and_predictable(self):
        current_telemetry = {
            "battery": {
                "battery_id": "B0005",
                "source_dataset": "NASA",
                "cycle": 100.0,
                "capacity_ah": 1.85,
                "voltage": None,
                "current": None,
                "temperature": None,
                "power": None,
                "soh": None,
                "prediction_input": {
                    "Battery_ID": "B0005",
                    "Source_Dataset": "NASA",
                    "Cycle": 100.0,
                    "Capacity_Ah": 1.85,
                },
                "unavailable_fields": [
                    "voltage", "current", "temperature", "power", "soh",
                ],
            },
            "source": {"battery_record": "test fixture", "feature_record": None},
        }

        with patch("app.get_current_telemetry", return_value=current_telemetry):
            battery_response = self.client.get("/api/battery")

        battery = battery_response.get_json()["battery"]
        self.assertIsNone(battery["voltage"])
        self.assertIn("temperature", battery["unavailable_fields"])

        response = self.client.post(
            "/api/predict-soh",
            json=battery["prediction_input"],
        )
        self.assert_success(response, "/api/predict-soh with optional gaps")

    def test_predict_soh(self):
        response = self.client.post(
            "/api/predict-soh",
            json=PREDICTION_PAYLOAD,
        )
        self.assert_success(response, "/api/predict-soh")
        self.assertIn("soh_percent", response.get_json()["prediction"])

    def test_fault_injection_scenarios(self):
        for scenario in [
            "HIGH_TEMPERATURE",
            "LOW_SOH",
            "CRITICAL_COMBINATION",
        ]:
            with self.subTest(scenario=scenario):
                response = self.client.post(
                    "/api/fault-injection",
                    json={"scenario": scenario},
                )
                self.assert_success(response, scenario)
                self.assertEqual(response.get_json()["scenario"], scenario)


if __name__ == "__main__":
    unittest.main(verbosity=2)
