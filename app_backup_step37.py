from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "processed")


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/status")
def status():

    data = {
        "battery": {
            "soh": 90.13,
            "soc": 78.4,
            "voltage": 12.0,
            "current": 3.0,
            "power": 36.0,
            "temperature": 29.2
        },

        "vehicle": {
            "speed": 15.3,
            "tyrePressure": 31.8
        },

        "gps": {
            "latitude": 12.971598,
            "longitude": 77.594566
        },

        "status": {
            "voltage": "NORMAL",
            "current": "NORMAL",
            "temperature": "NORMAL",
            "tyrePressure": "NORMAL",
            "soh": "NORMAL",
            "vehicle": "HEALTHY"
        }
    }

    return jsonify(data)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )