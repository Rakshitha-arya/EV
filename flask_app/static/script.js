// ============================================================
// EV DIGITAL TWIN
// COMPLETE FRONTEND JAVASCRIPT
// Flask API -> JavaScript -> Dashboard
// ============================================================


// ============================================================
// GLOBAL VARIABLES
// ============================================================

let sohChart = null;
let voltageChart = null;
let currentChart = null;
let temperatureChart = null;


// ============================================================
// HELPER: SET TEXT SAFELY
// ============================================================

function setText(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }

}


// ============================================================
// HELPER: STATUS CSS CLASS
// ============================================================

function getStatusClass(status) {

    if (!status) {
        return "normal";
    }

    const value = String(status).toUpperCase();

    if (value === "CRITICAL") {
        return "critical";
    }

    if (value === "WARNING") {
        return "warning";
    }

    if (value === "HEALTHY") {
        return "normal";
    }

    return "normal";
}


// ============================================================
// UPDATE FAULT STATUS
// ============================================================

function updateFaultStatus(elementId, status) {

    const element = document.getElementById(elementId);

    if (!element) {
        return;
    }

    element.textContent = status;

    element.classList.remove(
        "normal",
        "warning",
        "critical"
    );

    element.classList.add(
        getStatusClass(status)
    );

}


// ============================================================
// UPDATE DASHBOARD CARDS
// ============================================================

function updateDashboard(data) {

    console.log("Updating dashboard:", data);


    // --------------------------------------------------------
    // BATTERY
    // --------------------------------------------------------

    if (data.battery) {

        setText(
            "soh",
            Number(data.battery.soh).toFixed(2) + "%"
        );

        setText(
            "soc",
            Number(data.battery.soc).toFixed(1) + "%"
        );

        setText(
            "voltage",
            Number(data.battery.voltage).toFixed(2) + " V"
        );

        setText(
            "current",
            Number(data.battery.current).toFixed(2) + " A"
        );

        setText(
            "power",
            Number(data.battery.power).toFixed(2) + " W"
        );

        setText(
            "temperature",
            Number(data.battery.temperature).toFixed(1) + " °C"
        );

    }


    // --------------------------------------------------------
    // VEHICLE
    // --------------------------------------------------------

    if (data.vehicle) {

        setText(
            "speed",
            Number(data.vehicle.speed).toFixed(1) + " km/h"
        );

        setText(
            "pressure",
            Number(data.vehicle.tyrePressure).toFixed(1) + " PSI"
        );

        setText(
            "gpsSpeed",
            Number(data.vehicle.speed).toFixed(1) + " km/h"
        );

    }


    // --------------------------------------------------------
    // GPS
    // --------------------------------------------------------

    if (data.gps) {

        setText(
            "latitude",
            Number(data.gps.latitude).toFixed(6)
        );

        setText(
            "longitude",
            Number(data.gps.longitude).toFixed(6)
        );

    }


    // --------------------------------------------------------
    // FAULT DETECTION
    // --------------------------------------------------------

    if (data.status) {

        updateFaultStatus(
            "voltageStatus",
            data.status.voltage
        );

        updateFaultStatus(
            "currentStatus",
            data.status.current
        );

        updateFaultStatus(
            "temperatureStatus",
            data.status.temperature
        );

        updateFaultStatus(
            "pressureStatus",
            data.status.tyrePressure
        );

        updateFaultStatus(
            "sohStatus",
            data.status.soh
        );


        // Overall vehicle status

        const vehicleStatus =
            document.getElementById("vehicleStatus");

        if (vehicleStatus) {

            vehicleStatus.textContent =
                data.status.vehicle;

            vehicleStatus.classList.remove(
                "normal",
                "warning",
                "critical",
                "healthy"
            );

            vehicleStatus.classList.add(
                getStatusClass(
                    data.status.vehicle
                )
            );

        }

    }

}


// ============================================================
// COMMON CHART OPTIONS
// ============================================================

function getCommonChartOptions(
    yTitle,
    yMin,
    yMax,
    yStep
) {

    return {

        responsive: true,

        maintainAspectRatio: false,

        interaction: {

            mode: "index",

            intersect: false

        },

        layout: {

            padding: {

                top: 10,

                right: 20,

                bottom: 10,

                left: 10

            }

        },

        plugins: {

            legend: {

                display: true,

                position: "top",

                labels: {

                    font: {

                        size: 14

                    },

                    padding: 15

                }

            },

            tooltip: {

                enabled: true

            }

        },

        scales: {

            x: {

                display: true,

                title: {

                    display: true,

                    text: "Measurement",

                    font: {

                        size: 14,

                        weight: "bold"

                    }

                },

                ticks: {

                    font: {

                        size: 12

                    }

                }

            },

            y: {

                display: true,

                min: yMin,

                max: yMax,

                title: {

                    display: true,

                    text: yTitle,

                    font: {

                        size: 14,

                        weight: "bold"

                    }

                },

                ticks: {

                    stepSize: yStep,

                    font: {

                        size: 12

                    }

                }

            }

        }

    };

}


// ============================================================
// SOH CHART
// ============================================================

function createSOHChart() {

    const canvas =
        document.getElementById("sohChart");

    if (!canvas) {

        console.warn(
            "sohChart canvas not found"
        );

        return;

    }


    if (sohChart) {

        sohChart.destroy();

    }


    sohChart = new Chart(

        canvas,

        {

            type: "line",

            data: {

                labels: [

                    "Cycle 1",

                    "Cycle 5",

                    "Cycle 10",

                    "Cycle 15",

                    "Cycle 20",

                    "Cycle 25",

                    "Cycle 30",

                    "Cycle 35",

                    "Cycle 40"

                ],

                datasets: [

                    {

                        label:
                            "Battery SOH (%)",

                        data: [

                            100.00,

                            99.20,

                            98.10,

                            97.00,

                            95.80,

                            94.50,

                            93.00,

                            91.50,

                            90.13

                        ],

                        borderWidth: 4,

                        pointRadius: 5,

                        pointHoverRadius: 8,

                        tension: 0.25,

                        fill: false

                    }

                ]

            },

            options:
                getCommonChartOptions(

                    "State of Health (%)",

                    80,

                    100,

                    2

                )

        }

    );

}


// ============================================================
// VOLTAGE CHART
// ============================================================

function createVoltageChart() {

    const canvas =
        document.getElementById("voltageChart");

    if (!canvas) {

        console.warn(
            "voltageChart canvas not found"
        );

        return;

    }


    if (voltageChart) {

        voltageChart.destroy();

    }


    voltageChart = new Chart(

        canvas,

        {

            type: "line",

            data: {

                labels: [

                    "1",

                    "2",

                    "3",

                    "4",

                    "5",

                    "6",

                    "7",

                    "8"

                ],

                datasets: [

                    {

                        label:
                            "Battery Voltage (V)",

                        data: [

                            12.10,

                            12.00,

                            12.05,

                            11.98,

                            12.02,

                            11.95,

                            12.00,

                            12.00

                        ],

                        borderWidth: 4,

                        pointRadius: 5,

                        pointHoverRadius: 8,

                        tension: 0.25,

                        fill: false

                    }

                ]

            },

            options:
                getCommonChartOptions(

                    "Voltage (V)",

                    11.5,

                    12.5,

                    0.1

                )

        }

    );

}


// ============================================================
// CURRENT CHART
// ============================================================

function createCurrentChart() {

    const canvas =
        document.getElementById("currentChart");

    if (!canvas) {

        console.warn(
            "currentChart canvas not found"
        );

        return;

    }


    if (currentChart) {

        currentChart.destroy();

    }


    currentChart = new Chart(

        canvas,

        {

            type: "line",

            data: {

                labels: [

                    "1",

                    "2",

                    "3",

                    "4",

                    "5",

                    "6",

                    "7",

                    "8"

                ],

                datasets: [

                    {

                        label:
                            "Battery Current (A)",

                        data: [

                            2.8,

                            3.0,

                            3.1,

                            2.9,

                            3.2,

                            3.0,

                            3.1,

                            3.0

                        ],

                        borderWidth: 4,

                        pointRadius: 5,

                        pointHoverRadius: 8,

                        tension: 0.25,

                        fill: false

                    }

                ]

            },

            options:
                getCommonChartOptions(

                    "Current (A)",

                    0,

                    5,

                    0.5

                )

        }

    );

}


// ============================================================
// TEMPERATURE CHART
// ============================================================

function createTemperatureChart() {

    const canvas =
        document.getElementById(
            "temperatureChart"
        );

    if (!canvas) {

        console.warn(
            "temperatureChart canvas not found"
        );

        return;

    }


    if (temperatureChart) {

        temperatureChart.destroy();

    }


    temperatureChart = new Chart(

        canvas,

        {

            type: "line",

            data: {

                labels: [

                    "1",

                    "2",

                    "3",

                    "4",

                    "5",

                    "6",

                    "7",

                    "8"

                ],

                datasets: [

                    {

                        label:
                            "Battery Temperature (°C)",

                        data: [

                            28.1,

                            28.4,

                            28.7,

                            29.0,

                            29.2,

                            29.4,

                            29.3,

                            29.2

                        ],

                        borderWidth: 4,

                        pointRadius: 5,

                        pointHoverRadius: 8,

                        tension: 0.25,

                        fill: false

                    }

                ]

            },

            options:
                getCommonChartOptions(

                    "Temperature (°C)",

                    20,

                    50,

                    5

                )

        }

    );

}


// ============================================================
// LOAD DATA FROM FLASK
// ============================================================

async function loadDashboard() {

    try {

        console.log(
            "Requesting data from Flask..."
        );


        const response =
            await fetch(
                "/api/status"
            );


        if (!response.ok) {

            throw new Error(
                "Flask API returned HTTP " +
                response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "Data received from Flask:"
        );

        console.log(data);


        updateDashboard(data);


    }

    catch (error) {

        console.error(
            "Could not get data from Flask:",
            error
        );

    }

}


// ============================================================
// INITIALIZE EVERYTHING
// ============================================================

function initializeDashboard() {

    console.log(
        "Initializing EV Digital Twin..."
    );


    // Create graphs

    createSOHChart();

    createVoltageChart();

    createCurrentChart();

    createTemperatureChart();


    // Load Flask data

    loadDashboard();

}


// ============================================================
// START WHEN PAGE IS READY
// ============================================================

document.addEventListener(

    "DOMContentLoaded",

    function () {

        console.log(
            "EV Digital Twin frontend started"
        );

        initializeDashboard();

    }

);


// ============================================================
// AUTOMATIC REFRESH
// ============================================================
//
// Every 5 seconds the frontend asks Flask
// for the latest sensor/status data.
//
// ============================================================

setInterval(

    function () {

        loadDashboard();

    },

    5000

);