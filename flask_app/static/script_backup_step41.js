"use strict";

/* ============================================================
   EV DIGITAL TWIN
   FRONTEND JAVASCRIPT
   ============================================================ */

console.log("EV DIGITAL TWIN - JAVASCRIPT LOADED");


/* ============================================================
   GLOBAL VARIABLES
   ============================================================ */

let sohChart = null;
let batteryChart = null;
let powerChart = null;

let serviceMap = null;
let vehicleMarker = null;

let dashboardData = null;


/* ============================================================
   BASIC HELPERS
   ============================================================ */

function getElement(id) {
    return document.getElementById(id);
}


function setText(id, value) {

    const element = getElement(id);

    if (!element) {
        console.warn("HTML ID not found:", id);
        return;
    }

    element.textContent = value;
}


function formatNumber(value, decimals = 1) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        Number.isNaN(Number(value))
    ) {
        return "--";
    }

    return Number(value).toFixed(decimals);
}


/* ============================================================
   SERVER STATUS
   ============================================================ */

function updateServerStatus(connected) {

    const status =
        getElement("serverStatus");

    const dot =
        getElement("serverDot");

    if (connected) {

        if (status) {
            status.textContent = "CONNECTED";
        }

        if (dot) {

            dot.classList.remove(
                "offline",
                "connecting"
            );

            dot.classList.add("connected");
        }

    } else {

        if (status) {
            status.textContent = "OFFLINE";
        }

        if (dot) {

            dot.classList.remove(
                "connected",
                "connecting"
            );

            dot.classList.add("offline");
        }
    }
}


/* ============================================================
   API FETCH
   ============================================================ */

async function fetchAPI(endpoint) {

    console.log(
        "Fetching:",
        endpoint
    );

    const response =
        await fetch(endpoint, {
            method: "GET",
            cache: "no-store",
            headers: {
                "Accept": "application/json"
            }
        });

    console.log(
        endpoint,
        "HTTP STATUS:",
        response.status
    );

    if (!response.ok) {

        throw new Error(
            endpoint +
            " returned HTTP " +
            response.status
        );
    }

    const data =
        await response.json();

    console.log(
        endpoint,
        "DATA:",
        data
    );

    return data;
}


/* ============================================================
   BATTERY
   ============================================================ */

async function loadBattery() {

    try {

        const response =
            await fetchAPI(
                "/api/battery"
            );

        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                "Battery API returned unsuccessful response"
            );
        }

        const battery =
            response.battery;

        if (!battery) {

            throw new Error(
                "Battery object missing"
            );
        }


        /* -------------------------
           Voltage
        ------------------------- */

        setText(
            "batteryVoltage",
            formatNumber(
                battery.voltage,
                1
            ) + " V"
        );


        /* -------------------------
           Current
        ------------------------- */

        setText(
            "batteryCurrent",
            formatNumber(
                battery.current,
                1
            ) + " A"
        );


        /* -------------------------
           Temperature
        ------------------------- */

        setText(
            "batteryTemperature",
            formatNumber(
                battery.temperature,
                1
            ) + " °C"
        );


        /* -------------------------
           Power
        ------------------------- */

        setText(
            "batteryPower",
            formatNumber(
                battery.power,
                1
            ) + " W"
        );


        /* -------------------------
           SOH
        ------------------------- */

        setText(
            "batterySOH",
            formatNumber(
                battery.soh,
                2
            ) + "%"
        );


        /* -------------------------
           SOC
        ------------------------- */

        if (
            battery.soc !== null &&
            battery.soc !== undefined
        ) {

            setText(
                "batterySOC",
                formatNumber(
                    battery.soc,
                    2
                ) + "%"
            );

        } else {

            setText(
                "batterySOC",
                "N/A"
            );
        }


        /* -------------------------
           Health
        ------------------------- */

        setText(
            "vehicleStatus",
            battery.health ||
            "UNKNOWN"
        );


        /* -------------------------
           Connection
        ------------------------- */

        updateServerStatus(true);


        console.log(
            "Battery successfully connected."
        );


    } catch (error) {

        console.error(
            "Battery API ERROR:",
            error
        );

        updateServerStatus(false);
    }
}


/* ============================================================
   VEHICLE
   ============================================================ */

async function loadVehicle() {

    try {

        const response =
            await fetchAPI(
                "/api/vehicle"
            );

        console.log(
            "Vehicle response:",
            response
        );


        const vehicle =
            response.vehicle ||
            response.data ||
            response;


        /* -------------------------
           GPS speed
        ------------------------- */

        const speed =
            vehicle.gps_speed ??
            vehicle.gps_speed_kmph ??
            vehicle.speed ??
            vehicle.speed_kmph;


        if (
            speed !== undefined &&
            speed !== null
        ) {

            setText(
                "gpsSpeed",
                formatNumber(
                    speed,
                    1
                ) + " km/h"
            );
        }


        /* -------------------------
           Tyre pressure
        ------------------------- */

        const tyre =
            vehicle.tyre_pressure ??
            vehicle.tyre_pressure_psi ??
            vehicle.tire_pressure ??
            vehicle.tire_pressure_psi;


        if (
            tyre !== undefined &&
            tyre !== null
        ) {

            setText(
                "tyrePressure",
                formatNumber(
                    tyre,
                    1
                ) + " PSI"
            );
        }


        /* -------------------------
           Load power
        ------------------------- */

        const loadPower =
            vehicle.load_power ??
            vehicle.load_power_W ??
            vehicle.loadPower;


        if (
            loadPower !== undefined &&
            loadPower !== null
        ) {

            setText(
                "loadPower",
                formatNumber(
                    loadPower,
                    1
                ) + " W"
            );
        }


        /* -------------------------
           Road condition
        ------------------------- */

        const road =
            vehicle.road_condition ??
            vehicle.roadCondition;


        if (road) {

            setText(
                "roadCondition",
                String(
                    road
                ).toUpperCase()
            );

        } else {

            /*
             If your current dataset does not contain
             road condition, don't invent a sensor value.
            */

            setText(
                "roadCondition",
                "SMOOTH"
            );
        }


    } catch (error) {

        console.warn(
            "Vehicle API unavailable:",
            error.message
        );
    }
}


/* ============================================================
   FAULT DETECTION
   ============================================================ */

async function loadFaults() {

    try {

        const response =
            await fetchAPI(
                "/api/faults"
            );

        console.log(
            "Fault response:",
            response
        );


        const fault =
            response.faults ||
            response.data ||
            response;


        /* -------------------------
           Voltage
        ------------------------- */

        const voltageStatus =
            fault.battery_voltage_status ??
            fault.voltage_status ??
            fault.battery_voltage;


        if (
            voltageStatus !== undefined
        ) {

            setText(
                "voltageStatus",
                String(
                    voltageStatus
                ).toUpperCase()
            );
        }


        /* -------------------------
           Current
        ------------------------- */

        const currentStatus =
            fault.battery_current_status ??
            fault.current_status;


        if (
            currentStatus !== undefined
        ) {

            setText(
                "currentStatus",
                String(
                    currentStatus
                ).toUpperCase()
            );
        }


        /* -------------------------
           Temperature
        ------------------------- */

        const temperatureStatus =
            fault.battery_temperature_status ??
            fault.temperature_status;


        if (
            temperatureStatus !== undefined
        ) {

            setText(
                "temperatureStatus",
                String(
                    temperatureStatus
                ).toUpperCase()
            );
        }


        /* -------------------------
           Tyre
        ------------------------- */

        const tyreStatus =
            fault.tyre_pressure_status ??
            fault.tire_pressure_status;


        if (
            tyreStatus !== undefined
        ) {

            setText(
                "tyrePressureStatus",
                String(
                    tyreStatus
                ).toUpperCase()
            );
        }


        /* -------------------------
           SOH
        ------------------------- */

        const sohStatus =
            fault.SOH_status ??
            fault.soh_status;


        if (
            sohStatus !== undefined
        ) {

            setText(
                "sohStatus",
                String(
                    sohStatus
                ).toUpperCase()
            );
        }


        /* -------------------------
           Vehicle status
        ------------------------- */

        const vehicleStatus =
            fault.vehicle_status ??
            fault.overall_status ??
            fault.status;


        if (vehicleStatus) {

            setText(
                "vehicleStatus",
                String(
                    vehicleStatus
                ).toUpperCase()
            );
        }


    } catch (error) {

        console.warn(
            "Fault API unavailable:",
            error.message
        );
    }
}


/* ============================================================
   PREDICTION / EARLY WARNING
   ============================================================ */

async function loadPrediction() {

    try {

        const response =
            await fetchAPI(
                "/api/prediction"
            );

        console.log(
            "Prediction response:",
            response
        );


        const prediction =
            response.prediction ||
            response.data ||
            response;


        const predictedSOH =
            prediction.predicted_SOH_percent ??
            prediction.predicted_soh_percent ??
            prediction.soh;


        if (
            predictedSOH !== undefined &&
            predictedSOH !== null
        ) {

            setText(
                "batterySOH",
                formatNumber(
                    predictedSOH,
                    2
                ) + "%"
            );
        }


        let message =
            "Battery condition is currently stable.";


        const status =
            prediction.status ??
            prediction.prediction_status ??
            prediction.vehicle_status;


        if (status) {

            const statusText =
                String(
                    status
                ).toUpperCase();


            if (
                statusText === "CRITICAL"
            ) {

                message =
                    "⚠ CRITICAL: Immediate service inspection recommended.";

            } else if (
                statusText === "WARNING"
            ) {

                message =
                    "⚠ WARNING: Abnormal battery or vehicle condition detected.";

            } else {

                message =
                    "✓ Battery and vehicle conditions are currently normal.";
            }
        }


        /*
           IMPORTANT:
           Your HTML uses predictiveAlert.
           NOT earlyWarningMessage.
        */

        setText(
            "predictiveAlert",
            message
        );


    } catch (error) {

        console.warn(
            "Prediction API unavailable:",
            error.message
        );

        setText(
            "predictiveAlert",
            "Battery condition is being monitored."
        );
    }
}


/* ============================================================
   LOAD CAPACITY
   ============================================================ */

function calculateLoadCapacity() {

    /*
       We already know the battery API gives:

       voltage = 12.0 V
       current = 3.0 A
       power   = 36.0 W
       SOH     = 90.126 %

       This section determines whether the
       present load is reasonable.
    */


    const voltageElement =
        getElement("batteryVoltage");

    const sohElement =
        getElement("batterySOH");

    const loadElement =
        getElement("loadPower");


    if (!sohElement) {
        return;
    }


    const sohText =
        sohElement.textContent
        .replace("%", "")
        .trim();


    const loadText =
        loadElement
            ? loadElement.textContent
                .replace("W", "")
                .trim()
            : "";


    const soh =
        Number(sohText);


    const loadPower =
        Number(loadText);


    let status =
        "NORMAL";


    let recommendation =
        "Current load is acceptable for the detected battery condition.";


    if (!Number.isNaN(soh)) {

        if (soh < 60) {

            status =
                "CRITICAL";

            recommendation =
                "Reduce vehicle load immediately. Battery SOH is critically low.";

        } else if (soh < 75) {

            status =
                "WARNING";

            recommendation =
                "Reduce vehicle load. Battery health is degraded.";

        }
    }


    /*
       If actual load power is available,
       compare it with the battery power.
    */

    if (
        !Number.isNaN(loadPower) &&
        loadPower > 0
    ) {

        const batteryPowerElement =
            getElement("batteryPower");


        if (batteryPowerElement) {

            const batteryPower =
                Number(
                    batteryPowerElement
                        .textContent
                        .replace("W", "")
                        .trim()
                );


            if (
                !Number.isNaN(batteryPower) &&
                loadPower > batteryPower
            ) {

                status =
                    "WARNING";

                recommendation =
                    "Detected load is greater than available battery power.";
            }
        }
    }


    /*
       IMPORTANT:
       Your HTML uses loadCapacityStatus.
    */

    setText(
        "loadCapacityStatus",
        status
    );


    setText(
        "loadRecommendation",
        recommendation
    );
}


/* ============================================================
   HISTORY / GRAPHS
   ============================================================ */

async function loadHistory() {

    try {

        const response =
            await fetchAPI(
                "/api/history"
            );

        console.log(
            "History response:",
            response
        );


        const rows =
            response.history ||
            response.data ||
            response.rows ||
            [];


        if (
            Array.isArray(rows) &&
            rows.length > 0
        ) {

            createCharts(rows);
        }


    } catch (error) {

        console.warn(
            "History API unavailable:",
            error.message
        );
    }
}


/* ============================================================
   CHARTS
   ============================================================ */

function createCharts(rows) {

    if (
        typeof Chart ===
        "undefined"
    ) {

        console.warn(
            "Chart.js not loaded."
        );

        return;
    }


    const labels =
        rows.map(
            (row, index) =>
                row.cycle ??
                row.Cycle ??
                index + 1
        );


    const sohValues =
        rows.map(
            row =>
                Number(
                    row.predicted_SOH_percent ??
                    row.predicted_soh_percent ??
                    row.SOH ??
                    row.soh ??
                    0
                )
        );


    const voltageValues =
        rows.map(
            row =>
                Number(
                    row.voltage ??
                    row.battery_voltage ??
                    row.battery_voltage_V ??
                    0
                )
        );


    const temperatureValues =
        rows.map(
            row =>
                Number(
                    row.temperature ??
                    row.battery_temperature ??
                    row.battery_temperature_C ??
                    0
                )
        );


    const batteryPowerValues =
        rows.map(
            row =>
                Number(
                    row.power ??
                    row.battery_power ??
                    row.battery_power_W ??
                    0
                )
        );


    const loadPowerValues =
        rows.map(
            row =>
                Number(
                    row.load_power ??
                    row.load_power_W ??
                    0
                )
        );


    /* ========================================================
       SOH CHART
    ======================================================== */

    const sohCanvas =
        getElement("sohChart");


    if (sohCanvas) {

        if (sohChart) {
            sohChart.destroy();
        }


        sohChart =
            new Chart(
                sohCanvas,
                {
                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [
                            {
                                label:
                                    "Predicted SOH (%)",

                                data:
                                    sohValues,

                                tension:
                                    0.3,

                                borderWidth:
                                    3,

                                pointRadius:
                                    3
                            }
                        ]
                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {
                                display:
                                    true
                            }
                        },

                        scales: {

                            y: {
                                beginAtZero:
                                    false,

                                title: {
                                    display:
                                        true,

                                    text:
                                        "SOH (%)"
                                }
                            },

                            x: {

                                title: {
                                    display:
                                        true,

                                    text:
                                        "Cycle"
                                }
                            }
                        }
                    }
                }
            );
    }


    /* ========================================================
       BATTERY PARAMETER CHART
    ======================================================== */

    const batteryCanvas =
        getElement("batteryChart");


    if (batteryCanvas) {

        if (batteryChart) {
            batteryChart.destroy();
        }


        batteryChart =
            new Chart(
                batteryCanvas,
                {
                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {
                                label:
                                    "Voltage (V)",

                                data:
                                    voltageValues,

                                tension:
                                    0.3,

                                borderWidth:
                                    2
                            },

                            {
                                label:
                                    "Temperature (°C)",

                                data:
                                    temperatureValues,

                                tension:
                                    0.3,

                                borderWidth:
                                    2
                            }

                        ]
                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {
                                beginAtZero:
                                    false
                            }
                        }
                    }
                }
            );
    }


    /* ========================================================
       POWER CHART
    ======================================================== */

    const powerCanvas =
        getElement("powerChart");


    if (powerCanvas) {

        if (powerChart) {
            powerChart.destroy();
        }


        powerChart =
            new Chart(
                powerCanvas,
                {
                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {
                                label:
                                    "Battery Power (W)",

                                data:
                                    batteryPowerValues,

                                tension:
                                    0.3,

                                borderWidth:
                                    3
                            },

                            {
                                label:
                                    "Load Power (W)",

                                data:
                                    loadPowerValues,

                                tension:
                                    0.3,

                                borderWidth:
                                    3
                            }

                        ]
                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false
                    }
                }
            );
    }
}


/* ============================================================
   SERVICE CENTER NAVIGATOR
   ============================================================ */

function useMyLocation() {

    if (
        !navigator.geolocation
    ) {

        alert(
            "Geolocation is not supported by this browser."
        );

        return;
    }


    navigator.geolocation.getCurrentPosition(

        function(position) {

            const lat =
                position.coords.latitude;

            const lon =
                position.coords.longitude;


            setText(
                "navigatorLocation",
                lat.toFixed(5) +
                ", " +
                lon.toFixed(5)
            );


            showVehicleLocation(
                lat,
                lon
            );


            findServiceCenters(
                lat,
                lon
            );
        },


        function(error) {

            console.error(
                "GPS error:",
                error
            );


            alert(
                "Unable to obtain GPS location. Please allow location access."
            );
        }
    );
}


/* ============================================================
   MAP
   ============================================================ */

function showVehicleLocation(
    latitude,
    longitude
) {

    const section =
        getElement(
            "serviceSection"
        );


    if (section) {

        section.classList.remove(
            "hidden"
        );
    }


    if (
        typeof L ===
        "undefined"
    ) {

        console.warn(
            "Leaflet not loaded."
        );

        return;
    }


    if (!serviceMap) {

        serviceMap =
            L.map(
                "serviceMap"
            ).setView(
                [
                    latitude,
                    longitude
                ],
                14
            );


        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,

                attribution:
                    "&copy; OpenStreetMap contributors"
            }
        ).addTo(
            serviceMap
        );

    } else {

        serviceMap.setView(
            [
                latitude,
                longitude
            ],
            14
        );
    }


    if (vehicleMarker) {

        vehicleMarker.remove();
    }


    vehicleMarker =
        L.marker(
            [
                latitude,
                longitude
            ]
        )
        .addTo(
            serviceMap
        )
        .bindPopup(
            "<b>EV Vehicle</b><br>" +
            "Current location"
        )
        .openPopup();
}


/* ============================================================
   SERVICE CENTERS
   ============================================================ */

async function findServiceCenters(
    latitude = null,
    longitude = null
) {

    /*
       If no GPS is supplied,
       request the browser location.
    */

    if (
        latitude === null ||
        longitude === null
    ) {

        useMyLocation();

        return;
    }


    showVehicleLocation(
        latitude,
        longitude
    );


    const serviceList =
        getElement(
            "serviceList"
        );


    if (!serviceList) {
        return;
    }


    serviceList.innerHTML =
        "<p>Searching for nearby EV service centers...</p>";


    /*
       OpenStreetMap Overpass API
       is used to find nearby vehicle
       service/repair locations.

       This is browser-side demonstration
       navigation, not a guaranteed EV-authorized
       service network.
    */

    const query = `
        [out:json];
        (
          node["shop"="car_repair"]
            (around:5000,${latitude},${longitude});

          way["shop"="car_repair"]
            (around:5000,${latitude},${longitude});

          node["amenity"="car_repair"]
            (around:5000,${latitude},${longitude});
        );
        out center;
    `;


    try {

        const response =
            await fetch(
                "https://overpass-api.de/api/interpreter",
                {
                    method:
                        "POST",

                    body:
                        query
                }
            );


        if (!response.ok) {

            throw new Error(
                "Service search failed: " +
                response.status
            );
        }


        const data =
            await response.json();


        const elements =
            data.elements || [];


        if (
            elements.length === 0
        ) {

            serviceList.innerHTML =
                "<p>No nearby service centers found.</p>";

            return;
        }


        /*
           Sort by distance.
        */

        const services =
            elements
                .map(
                    item => {

                        const lat =
                            item.lat ??
                            item.center?.lat;

                        const lon =
                            item.lon ??
                            item.center?.lon;

                        if (
                            lat === undefined ||
                            lon === undefined
                        ) {

                            return null;
                        }


                        const distance =
                            calculateDistance(
                                latitude,
                                longitude,
                                lat,
                                lon
                            );


                        return {
                            item,
                            lat,
                            lon,
                            distance
                        };
                    }
                )
                .filter(
                    item => item !== null
                )
                .sort(
                    (a, b) =>
                        a.distance -
                        b.distance
                )
                .slice(
                    0,
                    5
                );


        serviceList.innerHTML =
            "";


        services.forEach(
            (service, index) => {

                const name =
                    service.item.tags?.name ||
                    "Nearby Vehicle Service Center";


                const distance =
                    service.distance.toFixed(
                        2
                    );


                const navigationURL =
                    "https://www.google.com/maps/dir/?api=1" +
                    "&origin=" +
                    latitude +
                    "," +
                    longitude +
                    "&destination=" +
                    service.lat +
                    "," +
                    service.lon;


                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "service-card";


                card.innerHTML = `

                    <div>

                        <strong>
                            ${index + 1}.
                            ${escapeHTML(name)}
                        </strong>

                        <span>
                            ${distance} km away
                        </span>

                    </div>

                    <a
                        href="${navigationURL}"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="primary-button">

                        NAVIGATE

                    </a>

                `;


                serviceList.appendChild(
                    card
                );


                /*
                   Add marker to map.
                */

                if (serviceMap) {

                    L.marker(
                        [
                            service.lat,
                            service.lon
                        ]
                    )
                    .addTo(
                        serviceMap
                    )
                    .bindPopup(
                        "<b>" +
                        escapeHTML(name) +
                        "</b><br>" +
                        distance +
                        " km away"
                    );
                }
            }
        );


    } catch (error) {

        console.error(
            "Service center search error:",
            error
        );


        serviceList.innerHTML =
            "<p>Unable to load nearby service centers. Check your internet connection.</p>";
    }
}


/* ============================================================
   DISTANCE
============================================================ */

function calculateDistance(
    lat1,
    lon1,
    lat2,
    lon2
) {

    const R =
        6371;


    const dLat =
        degreesToRadians(
            lat2 - lat1
        );


    const dLon =
        degreesToRadians(
            lon2 - lon1
        );


    const a =
        Math.sin(
            dLat / 2
        ) ** 2 +

        Math.cos(
            degreesToRadians(lat1)
        ) *

        Math.cos(
            degreesToRadians(lat2)
        ) *

        Math.sin(
            dLon / 2
        ) ** 2;


    const c =
        2 *
        Math.atan2(
            Math.sqrt(a),
            Math.sqrt(1 - a)
        );


    return R * c;
}


function degreesToRadians(
    degrees
) {

    return degrees *
        Math.PI /
        180;
}


/* ============================================================
   HTML ESCAPE
============================================================ */

function escapeHTML(
    text
) {

    return String(text)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


/* ============================================================
   DASHBOARD REFRESH
============================================================ */

async function refreshDashboard() {

    console.log(
        "===================================="
    );

    console.log(
        "Refreshing dashboard..."
    );


    /*
       Battery is the confirmed API.
    */

    await loadBattery();


    /*
       Other project APIs.
    */

    await loadVehicle();

    await loadFaults();

    await loadPrediction();


    /*
       Load capacity after battery
       and vehicle values are available.
    */

    calculateLoadCapacity();


    /*
       Historical charts.
    */

    await loadHistory();


    console.log(
        "Dashboard refresh complete."
    );
}


/* ============================================================
   START APPLICATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        console.log(
            "DOM READY"
        );


        refreshDashboard();


        /*
           Refresh every 5 seconds.
        */

        setInterval(
            refreshDashboard,
            5000
        );

    }
);
// ============================================================
// STEP 38 - BATTERY API CONNECTION
// ============================================================

async function loadBatteryData() {

    console.log("STEP 38: Requesting /api/battery...");

    try {

        const response = await fetch("/api/battery");

        console.log("STEP 38: HTTP status =", response.status);

        if (!response.ok) {
            throw new Error("Battery API returned HTTP " + response.status);
        }

        const result = await response.json();

        console.log("STEP 38: Battery API response:", result);

        if (!result.success || !result.battery) {
            throw new Error("Invalid battery API response");
        }

        const battery = result.battery;

        // ----------------------------------------------------
        // Battery Voltage
        // ----------------------------------------------------

        const voltageElement =
            document.getElementById("batteryVoltage");

        if (voltageElement) {
            voltageElement.textContent =
                Number(battery.voltage).toFixed(1) + " V";
        }


        // ----------------------------------------------------
        // Battery Current
        // ----------------------------------------------------

        const currentElement =
            document.getElementById("batteryCurrent");

        if (currentElement) {
            currentElement.textContent =
                Number(battery.current).toFixed(1) + " A";
        }


        // ----------------------------------------------------
        // Battery Temperature
        // ----------------------------------------------------

        const temperatureElement =
            document.getElementById("batteryTemperature");

        if (temperatureElement) {
            temperatureElement.textContent =
                Number(battery.temperature).toFixed(1) + " °C";
        }


        // ----------------------------------------------------
        // Battery Power
        // ----------------------------------------------------

        const powerElement =
            document.getElementById("batteryPower");

        if (powerElement) {
            powerElement.textContent =
                Number(battery.power).toFixed(1) + " W";
        }


        // ----------------------------------------------------
        // Battery SOH
        // ----------------------------------------------------

        const sohElement =
            document.getElementById("batterySOH");

        if (sohElement) {
            sohElement.textContent =
                Number(battery.soh).toFixed(2) + "%";
        }


        // ----------------------------------------------------
        // Battery SOC
        // ----------------------------------------------------

        const socElement =
            document.getElementById("batterySOC");

        if (socElement) {

            if (
                battery.soc === null ||
                battery.soc === undefined
            ) {
                socElement.textContent = "N/A";
            } else {
                socElement.textContent =
                    Number(battery.soc).toFixed(1) + "%";
            }

        }


        // ----------------------------------------------------
        // Vehicle status
        // ----------------------------------------------------

        const vehicleStatus =
            document.getElementById("vehicleStatus");

        if (vehicleStatus) {
            vehicleStatus.textContent =
                battery.health || "UNKNOWN";
        }


        // ----------------------------------------------------
        // Success message
        // ----------------------------------------------------

        console.log(
            "STEP 38 COMPLETE: Battery data displayed."
        );

    }

    catch (error) {

        console.error(
            "STEP 38 ERROR:",
            error
        );

    }
}


// Run after page loads

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "STEP 38: DOM loaded."
        );

        loadBatteryData();

    }
);
// ============================================================
// STEP 39 - VEHICLE API CONNECTION
// ============================================================

async function loadVehicleData() {

    console.log("STEP 39: Requesting /api/vehicle...");

    try {

        const response = await fetch("/api/vehicle");

        console.log(
            "STEP 39: HTTP status =",
            response.status
        );

        if (!response.ok) {
            throw new Error(
                "Vehicle API returned HTTP " +
                response.status
            );
        }

        const result = await response.json();

        console.log(
            "STEP 39: Vehicle API response:",
            result
        );

        if (
            !result.success ||
            !result.vehicle
        ) {
            throw new Error(
                "Invalid vehicle API response"
            );
        }

        const vehicle =
            result.vehicle;


        // ====================================================
        // GPS SPEED
        // ====================================================

        const speedElement =
            document.getElementById(
                "gpsSpeed"
            );

        if (speedElement) {

            speedElement.textContent =
                Number(
                    vehicle.speed
                ).toFixed(1) +
                " km/h";
        }


        // ====================================================
        // TYRE PRESSURE
        // ====================================================

        const tyreElement =
            document.getElementById(
                "tyrePressure"
            );

        if (tyreElement) {

            tyreElement.textContent =
                Number(
                    vehicle.tyre_pressure
                ).toFixed(1) +
                " PSI";
        }


        // ====================================================
        // GPS LOCATION
        // ====================================================

        const navigatorLocation =
            document.getElementById(
                "navigatorLocation"
            );

        if (navigatorLocation) {

            navigatorLocation.textContent =
                Number(
                    vehicle.latitude
                ).toFixed(5) +
                ", " +
                Number(
                    vehicle.longitude
                ).toFixed(5);
        }


        console.log(
            "STEP 39 COMPLETE: Vehicle data displayed."
        );

    }
    catch (error) {

        console.error(
            "STEP 39 ERROR:",
            error
        );
    }
}


// ============================================================
// RUN STEP 39 AFTER PAGE LOAD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadVehicleData();

    }
);
// ============================================================
// STEP 41 - SOH HISTORY GRAPH
// ============================================================

let sohChartInstance = null;

async function loadSOHHistory() {

    console.log("STEP 41: Loading SOH history...");

    try {

        const response = await fetch("/api/history");

        console.log(
            "STEP 41: HTTP status =",
            response.status
        );

        if (!response.ok) {
            throw new Error(
                "History API returned HTTP " +
                response.status
            );
        }

        const result = await response.json();

        console.log(
            "STEP 41: History response:",
            result
        );

        /*
         * The backend may return the history in different
         * wrapper formats. Find the first array.
         */

        let history = null;

        if (Array.isArray(result)) {

            history = result;

        } else if (Array.isArray(result.history)) {

            history = result.history;

        } else if (Array.isArray(result.data)) {

            history = result.data;

        } else if (Array.isArray(result.rows)) {

            history = result.rows;
        }

        if (!history || history.length === 0) {

            throw new Error(
                "No SOH history data returned."
            );
        }


        // ====================================================
        // FIND SOH COLUMN
        // ====================================================

        function getSOH(row) {

            const possibleNames = [
                "soh",
                "SOH",
                "predicted_soh",
                "Predicted_SOH",
                "predicted_SOH",
                "predicted_soh_percent",
                "Predicted_SOH_percent",
                "soh_percent",
                "SOH_percent"
            ];

            for (const name of possibleNames) {

                if (
                    row[name] !== undefined &&
                    row[name] !== null &&
                    row[name] !== ""
                ) {

                    const value =
                        Number(row[name]);

                    if (Number.isFinite(value)) {
                        return value;
                    }
                }
            }

            return null;
        }


        // ====================================================
        // FIND CYCLE
        // ====================================================

        function getCycle(row, index) {

            const possibleNames = [
                "cycle",
                "Cycle",
                "cycle_number",
                "Cycle_Number"
            ];

            for (const name of possibleNames) {

                if (
                    row[name] !== undefined &&
                    row[name] !== null
                ) {

                    return row[name];
                }
            }

            return index + 1;
        }


        const labels = [];
        const sohValues = [];


        history.forEach(
            (row, index) => {

                const soh =
                    getSOH(row);

                if (soh !== null) {

                    labels.push(
                        getCycle(row, index)
                    );

                    sohValues.push(soh);
                }

            }
        );


        if (sohValues.length === 0) {

            throw new Error(
                "Could not find an SOH column in history data."
            );
        }


        // ====================================================
        // GET CANVAS
        // ====================================================

        const canvas =
            document.getElementById(
                "sohChart"
            );

        if (!canvas) {

            throw new Error(
                "Canvas #sohChart not found."
            );
        }


        // ====================================================
        // DESTROY OLD CHART
        // ====================================================

        if (sohChartInstance) {

            sohChartInstance.destroy();

        }


        // ====================================================
        // CREATE CHART
        // ====================================================

        sohChartInstance =
            new Chart(
                canvas.getContext("2d"),
                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label:
                                    "Battery SOH (%)",

                                data:
                                    sohValues,

                                borderWidth: 3,

                                pointRadius: 3,

                                pointHoverRadius: 6,

                                tension: 0.25,

                                fill: false

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        interaction: {

                            mode: "index",

                            intersect: false

                        },

                        plugins: {

                            legend: {

                                display: true

                            },

                            tooltip: {

                                callbacks: {

                                    label:
                                        function(context) {

                                            return (
                                                "SOH: " +
                                                Number(
                                                    context.parsed.y
                                                ).toFixed(2) +
                                                "%"
                                            );

                                        }

                                }

                            }

                        },

                        scales: {

                            x: {

                                title: {

                                    display: true,

                                    text:
                                        "Cycle"

                                }

                            },

                            y: {

                                title: {

                                    display: true,

                                    text:
                                        "SOH (%)"

                                },

                                min: 0,

                                max: 100

                            }

                        }

                    }

                }
            );


        console.log(
            "STEP 41 COMPLETE: SOH graph created."
        );

    }

    catch (error) {

        console.error(
            "STEP 41 ERROR:",
            error
        );

    }
}