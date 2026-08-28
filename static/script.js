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
let vehicleAccuracyCircle = null;
let serviceMarkers = [];
let currentVehicleLatitude = null;
let currentVehicleLongitude = null;

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

async function useMyLocation() {
    console.log("STEP 44 - GET VEHICLE GPS");

    try {
        const response = await fetch("/api/vehicle");

        if (!response.ok) {
            throw new Error("Vehicle API HTTP " + response.status);
        }

        const data = await response.json();

        if (!data.success || !data.vehicle) {
            throw new Error("Vehicle GPS data unavailable");
        }

        const latitude = Number(data.vehicle.latitude);
        const longitude = Number(data.vehicle.longitude);

        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
            throw new Error("Invalid vehicle GPS coordinates");
        }

        window.vehicleLatitude = latitude;
        window.vehicleLongitude = longitude;
        setText("navigatorLocation", `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`);
        getElement("serviceSection")?.classList.remove("hidden");
        initializeServiceMap(latitude, longitude);
        await findServiceCenters(latitude, longitude);

        console.log("Vehicle GPS successfully connected.");
    } catch (error) {
        console.error("Vehicle GPS ERROR:", error);
        setText("navigatorLocation", "Vehicle GPS unavailable");
        getElement("serviceSection")?.classList.add("hidden");
    }
}


/* ============================================================
   MAP
   ============================================================ */

function initializeServiceMap(
    latitude,
    longitude
) {
    console.log("STEP 45 - INITIALIZING SERVICE MAP");

    if (typeof L === "undefined") {
        console.error("Leaflet library is not loaded.");
        return;
    }

    latitude = Number(latitude);
    longitude = Number(longitude);

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        console.error("Invalid GPS coordinates.");
        return;
    }

    currentVehicleLatitude = latitude;
    currentVehicleLongitude = longitude;
    window.vehicleLatitude = latitude;
    window.vehicleLongitude = longitude;

    const mapElement = document.getElementById("serviceMap");

    if (!mapElement) {
        console.error("serviceMap element not found.");
        return;
    }

    if (!serviceMap) {
        serviceMap = L.map("serviceMap").setView([latitude, longitude], 14);

        L.tileLayer(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
            }
        ).addTo(serviceMap);
    } else {
        serviceMap.setView([latitude, longitude], 14);
    }

    if (vehicleMarker) {
        serviceMap.removeLayer(vehicleMarker);
    }

    if (vehicleAccuracyCircle) {
        serviceMap.removeLayer(vehicleAccuracyCircle);
    }

    const vehicleIcon = L.divIcon({
        className: "ev-vehicle-marker",
        html: '<div style="width:42px;height:42px;border-radius:50%;background:#2563eb;border:4px solid white;box-shadow:0 3px 12px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;font-size:22px;">🚗</div>',
        iconSize: [42, 42],
        iconAnchor: [21, 21]
    });

    vehicleMarker = L.marker([latitude, longitude], { icon: vehicleIcon })
        .addTo(serviceMap)
        .bindPopup(
            `<div style="text-align:center"><strong>🚗 EV DIGITAL TWIN</strong><br><br><b>Vehicle Location</b><br>Latitude: ${latitude.toFixed(6)}<br>Longitude: ${longitude.toFixed(6)}</div>`
        );

    vehicleAccuracyCircle = L.circle([latitude, longitude], {
        radius: 100,
        color: "#2563eb",
        fillColor: "#2563eb",
        fillOpacity: 0.08,
        weight: 1
    }).addTo(serviceMap);

    setTimeout(() => serviceMap?.invalidateSize(), 300);
}


/* ============================================================
   SERVICE CENTERS
   ============================================================ */

async function findServiceCenters(
    latitude = currentVehicleLatitude,
    longitude = currentVehicleLongitude
) {
    console.log("STEP 45 - FINDING SERVICE CENTERS");

    latitude = Number(latitude ?? window.vehicleLatitude);
    longitude = Number(longitude ?? window.vehicleLongitude);

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        console.error("Cannot find service centers: GPS unavailable.");
        setText("navigatorLocation", "Vehicle GPS location is unavailable.");
        return;
    }

    currentVehicleLatitude = latitude;
    currentVehicleLongitude = longitude;
    initializeServiceMap(latitude, longitude);

    serviceMarkers.forEach(marker => serviceMap?.removeLayer(marker));
    serviceMarkers = [];

    const serviceList = getElement("serviceList");
    if (serviceList) {
        serviceList.innerHTML = '<div class="service-loading">🔍 Searching for nearby EV service centers...</div>';
    }

    const radius = 5000;
    const query = `
        [out:json][timeout:20];
        (
          node[amenity=car_repair](around:${radius},${latitude},${longitude});
          way[amenity=car_repair](around:${radius},${latitude},${longitude});
          node[shop=car](around:${radius},${latitude},${longitude});
          way[shop=car](around:${radius},${latitude},${longitude});
        );
        out center tags;
    `;

    try {
        const response = await fetch(
            "https://overpass-api.de/api/interpreter",
            {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: "data=" + encodeURIComponent(query)
            }
        );

        if (!response.ok) {
            throw new Error("Service center API HTTP " + response.status);
        }

        const data = await response.json();
        const centers = (Array.isArray(data.elements) ? data.elements : [])
            .map(element => {
                const centerLatitude = Number(element.lat ?? element.center?.lat);
                const centerLongitude = Number(element.lon ?? element.center?.lon);

                if (!Number.isFinite(centerLatitude) || !Number.isFinite(centerLongitude)) {
                    return null;
                }

                const tags = element.tags || {};
                return {
                    id: element.id,
                    name: tags.name || tags.brand || "EV / Vehicle Service Center",
                    latitude: centerLatitude,
                    longitude: centerLongitude,
                    address: [tags["addr:housenumber"], tags["addr:street"], tags["addr:city"]].filter(Boolean).join(", ") || "Address unavailable",
                    distance: calculateDistance(latitude, longitude, centerLatitude, centerLongitude),
                    phone: tags.phone || tags["contact:phone"] || "Not available"
                };
            })
            .filter(Boolean)
            .sort((a, b) => a.distance - b.distance);

        const seen = new Set();
        const nearestCenters = centers.filter(center => {
            const key = `${center.name}|${center.latitude.toFixed(5)}|${center.longitude.toFixed(5)}`.toLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        }).slice(0, 8);

        if (!nearestCenters.length) {
            if (serviceList) {
                serviceList.innerHTML = `<div class="service-empty"><strong>No service centers found</strong><p>No vehicle repair centers were found within ${radius / 1000} km.</p></div>`;
            }
            setText("navigatorLocation", "No nearby service centers found.");
            return;
        }

        if (serviceList) serviceList.innerHTML = "";

        nearestCenters.forEach((center, index) => {
            const isNearest = index === 0;
            const icon = L.divIcon({
                className: "service-center-marker",
                html: `<div style="width:34px;height:34px;border-radius:50%;background:${isNearest ? "#dc2626" : "#16a34a"};border:3px solid white;box-shadow:0 3px 10px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;font-size:17px;">🔧</div>`,
                iconSize: [34, 34], iconAnchor: [17, 17]
            });
            const navigationURL = createNavigationURL(latitude, longitude, center.latitude, center.longitude);
            const marker = L.marker([center.latitude, center.longitude], { icon })
                .addTo(serviceMap)
                .bindPopup(`<div style="min-width:220px"><strong>${escapeHTML(center.name)}</strong>${isNearest ? '<div style="margin-top:6px;color:#dc2626;font-weight:700;">⭐ NEAREST SERVICE CENTER</div>' : ""}<br><br>📍 ${formatDistance(center.distance)}<br>${escapeHTML(center.address)}<br><br><a href="${navigationURL}" target="_blank" rel="noopener noreferrer">🧭 NAVIGATE</a></div>`);
            serviceMarkers.push(marker);

            if (serviceList) {
                const card = document.createElement("div");
                card.className = "service-center-card" + (isNearest ? " nearest-service" : "");
                card.innerHTML = `<strong>${index + 1}. ${escapeHTML(center.name)}${isNearest ? " — NEAREST" : ""}</strong><p>📍 ${formatDistance(center.distance)}<br>${escapeHTML(center.address)}<br>📞 ${escapeHTML(center.phone)}</p><a href="${navigationURL}" target="_blank" rel="noopener noreferrer" class="primary-button">🧭 NAVIGATE</a>`;
                card.addEventListener("click", () => {
                    serviceMap.setView([center.latitude, center.longitude], 16);
                    marker.openPopup();
                });
                serviceList.appendChild(card);
            }
        });

        serviceMap.fitBounds(L.latLngBounds([[latitude, longitude], ...nearestCenters.map(center => [center.latitude, center.longitude])]), { padding: [40, 40] });
        setText("navigatorLocation", `Nearest service center: ${nearestCenters[0].name} — ${formatDistance(nearestCenters[0].distance)} away.`);

    } catch (error) {
        console.error("SERVICE CENTER ERROR:", error);
        if (serviceList) {
            serviceList.innerHTML = "<div class=\"service-error\"><strong>Unable to load service centers.</strong><p>Please check your internet connection and try again.</p></div>";
        }
        setText("navigatorLocation", "Service center search is temporarily unavailable.");
    }
}


/* ============================================================
   DISTANCE
============================================================ */

function formatDistance(distanceKm) {

    if (!Number.isFinite(distanceKm)) {
        return "--";
    }

    return distanceKm < 1
        ? `${Math.round(distanceKm * 1000)} m`
        : `${distanceKm.toFixed(2)} km`;
}


function createNavigationURL(fromLat, fromLon, toLat, toLon) {

    return (
        "https://www.google.com/maps/dir/?api=1" +
        "&origin=" + encodeURIComponent(`${fromLat},${fromLon}`) +
        "&destination=" + encodeURIComponent(`${toLat},${toLon}`) +
        "&travelmode=driving"
    );
}

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
// ============================================================
// STEP 41 - BATTERY HEALTH & EARLY FAULT PREDICTION
// ============================================================

async function updateBatteryPrediction() {

    console.log("Running battery prediction...");

    try {

        // ----------------------------------------------------
        // Get current battery data
        // ----------------------------------------------------

        const batteryResponse =
            await fetch("/api/battery");

        if (!batteryResponse.ok) {
            throw new Error(
                "Battery API returned HTTP " +
                batteryResponse.status
            );
        }

        const batteryData =
            await batteryResponse.json();


        // ----------------------------------------------------
        // Extract battery object
        // ----------------------------------------------------

        const battery =
            batteryData.battery || {};


        const voltage =
            Number(battery.voltage);

        const current =
            Number(battery.current);

        const temperature =
            Number(battery.temperature);

        const power =
            Number(battery.power);

        const soh =
            Number(battery.soh);


        console.log("Prediction input:", {
            voltage,
            current,
            temperature,
            power,
            soh
        });


        // ----------------------------------------------------
        // Validate data
        // ----------------------------------------------------

        if (
            !Number.isFinite(voltage) ||
            !Number.isFinite(current) ||
            !Number.isFinite(temperature) ||
            !Number.isFinite(power) ||
            !Number.isFinite(soh)
        ) {

            console.warn(
                "Incomplete battery data for prediction."
            );

            return;
        }


        // ----------------------------------------------------
        // Risk calculation
        // ----------------------------------------------------

        let riskScore = 0;

        const warnings = [];


        // Battery SOH
        // ----------------------------------------------------

        if (soh < 70) {

            riskScore += 40;

            warnings.push(
                "Battery SOH is critically low."
            );

        }
        else if (soh < 80) {

            riskScore += 25;

            warnings.push(
                "Battery SOH is below the recommended level."
            );

        }
        else if (soh < 90) {

            riskScore += 10;

            warnings.push(
                "Battery SOH is showing degradation."
            );
        }


        // Battery voltage
        // ----------------------------------------------------

        if (voltage < 10.5) {

            riskScore += 35;

            warnings.push(
                "Battery voltage is critically low."
            );

        }
        else if (voltage < 11.5) {

            riskScore += 20;

            warnings.push(
                "Battery voltage is low."
            );
        }


        // Battery temperature
        // ----------------------------------------------------

        if (temperature >= 45) {

            riskScore += 35;

            warnings.push(
                "Battery temperature is critically high."
            );

        }
        else if (temperature >= 40) {

            riskScore += 20;

            warnings.push(
                "Battery temperature is elevated."
            );
        }


        // Battery current
        // ----------------------------------------------------

        if (current > 10) {

            riskScore += 30;

            warnings.push(
                "Battery current is critically high."
            );

        }
        else if (current > 7) {

            riskScore += 15;

            warnings.push(
                "Battery current is elevated."
            );
        }


        // ----------------------------------------------------
        // Determine overall prediction
        // ----------------------------------------------------

        let predictionStatus;
        let predictionMessage;


        if (riskScore >= 60) {

            predictionStatus = "CRITICAL";

            predictionMessage =
                "Critical battery/vehicle condition detected. " +
                "Immediate service inspection is recommended.";

        }
        else if (riskScore >= 30) {

            predictionStatus = "WARNING";

            predictionMessage =
                "Early warning detected. " +
                "The vehicle should be monitored and service " +
                "may be required soon.";

        }
        else {

            predictionStatus = "NORMAL";

            predictionMessage =
                "Battery condition is stable. " +
                "No immediate fault is predicted.";
        }


        // ----------------------------------------------------
        // Update prediction panel
        // ----------------------------------------------------

        const alertElement =
            document.getElementById("predictiveAlert");


        if (alertElement) {

            alertElement.textContent =
                predictionMessage;

            alertElement.className =
                "prediction-message " +
                predictionStatus.toLowerCase();
        }


        // ----------------------------------------------------
        // Update vehicle status
        // ----------------------------------------------------

        const vehicleStatus =
            document.getElementById("vehicleStatus");


        if (vehicleStatus) {

            vehicleStatus.textContent =
                predictionStatus === "NORMAL"
                    ? "HEALTHY"
                    : predictionStatus;
        }


        // ----------------------------------------------------
        // Display console information
        // ----------------------------------------------------

        console.log(
            "----------------------------------------"
        );

        console.log(
            "BATTERY PREDICTION"
        );

        console.log(
            "SOH:",
            soh
        );

        console.log(
            "Voltage:",
            voltage
        );

        console.log(
            "Temperature:",
            temperature
        );

        console.log(
            "Current:",
            current
        );

        console.log(
            "Risk score:",
            riskScore
        );

        console.log(
            "Prediction:",
            predictionStatus
        );

        console.log(
            "Warnings:",
            warnings
        );

        console.log(
            "----------------------------------------"
        );


        // ----------------------------------------------------
        // Save prediction for other dashboard functions
        // ----------------------------------------------------

        window.evPrediction = {

            status: predictionStatus,

            riskScore: riskScore,

            warnings: warnings,

            soh: soh,

            voltage: voltage,

            current: current,

            temperature: temperature,

            power: power
        };


    }
    catch (error) {

        console.error(
            "Battery prediction error:",
            error
        );
    }
}
// ============================================================
// START STEP 41 PREDICTION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateBatteryPrediction();

        setInterval(
            updateBatteryPrediction,
            10000
        );

    }
);
// ============================================================
// STEP 42
// HISTORICAL TREND ANALYSIS + EARLY FAULT PREDICTION
// ============================================================

async function runHistoricalTrendAnalysis() {

    console.log("==========================================");
    console.log("STEP 42 - HISTORICAL TREND ANALYSIS");
    console.log("==========================================");

    try {

        // ----------------------------------------------------
        // 1. Get history from Flask
        // ----------------------------------------------------

        console.log("Fetching /api/history");

        const response =
            await fetch("/api/history");

        if (!response.ok) {

            throw new Error(
                "History API returned HTTP " +
                response.status
            );
        }


        const data =
            await response.json();


        console.log(
            "History data received:",
            data
        );


        // ----------------------------------------------------
        // 2. Extract history array
        // ----------------------------------------------------

        const history =
            Array.isArray(data.data)
                ? data.history
                : [];


        if (history.length === 0) {

            console.warn(
                "No historical records available."
            );

            return;
        }


        console.log(
            "Historical records:",
            history.length
        );


        // ----------------------------------------------------
        // 3. Convert values to numbers
        // ----------------------------------------------------

        const records =
            history.map(function (item) {

                return {

                    voltage:
                        Number(item.battery_voltage_V),

                    current:
                        Number(item.battery_current_A),

                    temperature:
                        Number(item.battery_temperature_C),

                    batteryPower:
                        Number(item.battery_power_W),

                    loadPower:
                        Number(item.load_power_W),

                    soh:
                        Number(item.soh_percent),

                    tyrePressure:
                        Number(item.tyre_pressure_psi),

                    speed:
                        Number(item.gps_speed_kmph),

                    timestamp:
                        item.timestamp
                };

            });


        console.log(
            "Processed history:",
            records
        );


        // ----------------------------------------------------
        // 4. Helper function
        // ----------------------------------------------------

        function validNumbers(values) {

            return values.filter(function (value) {

                return Number.isFinite(value);

            });

        }


        // ----------------------------------------------------
        // 5. Extract individual series
        // ----------------------------------------------------

        const voltageValues =
            validNumbers(
                records.map(
                    r => r.voltage
                )
            );


        const currentValues =
            validNumbers(
                records.map(
                    r => r.current
                )
            );


        const temperatureValues =
            validNumbers(
                records.map(
                    r => r.temperature
                )
            );


        const sohValues =
            validNumbers(
                records.map(
                    r => r.soh
                )
            );


        const tyreValues =
            validNumbers(
                records.map(
                    r => r.tyrePressure
                )
            );


        const loadValues =
            validNumbers(
                records.map(
                    r => r.loadPower
                )
            );


        // ----------------------------------------------------
        // 6. Trend calculation
        // ----------------------------------------------------

        function calculateTrend(values) {

            if (values.length < 2) {

                return {
                    first: values[0] ?? null,
                    last: values[0] ?? null,
                    change: 0,
                    percentage: 0,
                    direction: "STABLE"
                };

            }


            const first =
                values[0];

            const last =
                values[values.length - 1];

            const change =
                last - first;


            const percentage =
                first !== 0
                    ? (change / Math.abs(first)) * 100
                    : 0;


            let direction =
                "STABLE";


            // Small changes are treated as stable.

            if (percentage > 1) {

                direction =
                    "INCREASING";

            }
            else if (percentage < -1) {

                direction =
                    "DECREASING";
            }


            return {

                first:
                    first,

                last:
                    last,

                change:
                    change,

                percentage:
                    percentage,

                direction:
                    direction
            };

        }


        // ----------------------------------------------------
        // 7. Calculate trends
        // ----------------------------------------------------

        const voltageTrend =
            calculateTrend(
                voltageValues
            );


        const currentTrend =
            calculateTrend(
                currentValues
            );


        const temperatureTrend =
            calculateTrend(
                temperatureValues
            );


        const sohTrend =
            calculateTrend(
                sohValues
            );


        const tyreTrend =
            calculateTrend(
                tyreValues
            );


        const loadTrend =
            calculateTrend(
                loadValues
            );


        console.log(
            "Voltage trend:",
            voltageTrend
        );

        console.log(
            "Current trend:",
            currentTrend
        );

        console.log(
            "Temperature trend:",
            temperatureTrend
        );

        console.log(
            "SOH trend:",
            sohTrend
        );

        console.log(
            "Tyre pressure trend:",
            tyreTrend
        );

        console.log(
            "Load trend:",
            loadTrend
        );


        // ----------------------------------------------------
        // 8. Calculate predictive risk score
        // ----------------------------------------------------

        let riskScore =
            0;


        const warnings =
            [];


        // ----------------------------------------------------
        // VOLTAGE TREND
        // ----------------------------------------------------

        if (
            voltageTrend.percentage <= -3
        ) {

            riskScore += 20;

            warnings.push(
                "Battery voltage is decreasing."
            );

        }
        else if (
            voltageTrend.percentage <= -1
        ) {

            riskScore += 10;

            warnings.push(
                "Battery voltage shows a downward trend."
            );

        }


        // ----------------------------------------------------
        // CURRENT TREND
        // ----------------------------------------------------

        if (
            currentTrend.percentage >= 30
        ) {

            riskScore += 20;

            warnings.push(
                "Battery current demand is increasing."
            );

        }
        else if (
            currentTrend.percentage >= 15
        ) {

            riskScore += 10;

            warnings.push(
                "Battery current demand is rising."
            );

        }


        // ----------------------------------------------------
        // TEMPERATURE TREND
        // ----------------------------------------------------

        if (
            temperatureTrend.percentage >= 8
        ) {

            riskScore += 20;

            warnings.push(
                "Battery temperature is increasing."
            );

        }
        else if (
            temperatureTrend.percentage >= 4
        ) {

            riskScore += 10;

            warnings.push(
                "Battery temperature shows an upward trend."
            );

        }


        // ----------------------------------------------------
        // SOH TREND
        // ----------------------------------------------------

        if (
            sohTrend.change <= -5
        ) {

            riskScore += 30;

            warnings.push(
                "Battery SOH is degrading rapidly."
            );

        }
        else if (
            sohTrend.change <= -2
        ) {

            riskScore += 20;

            warnings.push(
                "Battery SOH is showing degradation."
            );

        }


        // ----------------------------------------------------
        // TYRE PRESSURE
        // ----------------------------------------------------

        if (
            tyreValues.length > 0
        ) {

            const latestTyre =
                tyreValues[
                    tyreValues.length - 1
                ];


            if (
                latestTyre < 26
            ) {

                riskScore += 25;

                warnings.push(
                    "Tyre pressure is critically low."
                );

            }
            else if (
                latestTyre < 28
            ) {

                riskScore += 10;

                warnings.push(
                    "Tyre pressure is below the preferred range."
                );

            }

        }


        // ----------------------------------------------------
        // LOAD TREND
        // ----------------------------------------------------

        if (
            loadTrend.percentage >= 30
        ) {

            riskScore += 15;

            warnings.push(
                "Vehicle load demand is increasing."
            );

        }


        // ----------------------------------------------------
        // 9. Limit risk score
        // ----------------------------------------------------

        riskScore =
            Math.min(
                riskScore,
                100
            );


        // ----------------------------------------------------
        // 10. Determine prediction
        // ----------------------------------------------------

        let status =
            "NORMAL";


        let message =
            "Vehicle operating conditions are stable.";


        if (
            riskScore >= 60
        ) {

            status =
                "CRITICAL";


            message =
                "Critical operating trend detected. " +
                "Immediate inspection is recommended.";

        }
        else if (
            riskScore >= 30
        ) {

            status =
                "WARNING";


            message =
                "Early warning detected. " +
                "Vehicle and battery conditions should " +
                "be monitored closely.";

        }
        else {

            status =
                "NORMAL";


            message =
                "Battery and vehicle operating trends " +
                "are currently stable.";

        }


        // ----------------------------------------------------
        // 11. Create detailed trend message
        // ----------------------------------------------------

        let detailedMessage =
            message;


        if (
            warnings.length > 0
        ) {

            detailedMessage +=
                " " +
                warnings.join(" ");

        }


        // ----------------------------------------------------
        // 12. Update Early Warning System
        // ----------------------------------------------------

        const alert =
            document.getElementById(
                "predictiveAlert"
            );


        if (alert) {

            alert.textContent =
                detailedMessage;


            alert.className =
                "prediction-message " +
                status.toLowerCase();

        }


        // ----------------------------------------------------
        // 13. Update vehicle status
        // ----------------------------------------------------

        const vehicleStatus =
            document.getElementById(
                "vehicleStatus"
            );


        if (vehicleStatus) {

            vehicleStatus.textContent =
                status === "NORMAL"
                    ? "HEALTHY"
                    : status;

        }


        // ----------------------------------------------------
        // 14. Store result globally
        // ----------------------------------------------------

        window.evTrendPrediction = {

            status:
                status,

            riskScore:
                riskScore,

            message:
                detailedMessage,

            warnings:
                warnings,

            voltageTrend:
                voltageTrend,

            currentTrend:
                currentTrend,

            temperatureTrend:
                temperatureTrend,

            sohTrend:
                sohTrend,

            tyreTrend:
                tyreTrend,

            loadTrend:
                loadTrend
        };


        // ----------------------------------------------------
        // 15. Console output
        // ----------------------------------------------------

        console.log(
            "=========================================="
        );

        console.log(
            "STEP 42 RESULT"
        );

        console.log(
            "=========================================="
        );

        console.log(
            "Records:",
            records.length
        );

        console.log(
            "Voltage:",
            voltageTrend.direction,
            voltageTrend.percentage.toFixed(2) + "%"
        );

        console.log(
            "Current:",
            currentTrend.direction,
            currentTrend.percentage.toFixed(2) + "%"
        );

        console.log(
            "Temperature:",
            temperatureTrend.direction,
            temperatureTrend.percentage.toFixed(2) + "%"
        );

        console.log(
            "SOH:",
            sohTrend.direction,
            sohTrend.percentage.toFixed(2) + "%"
        );

        console.log(
            "Tyre pressure:",
            tyreTrend.direction,
            tyreTrend.percentage.toFixed(2) + "%"
        );

        console.log(
            "Load:",
            loadTrend.direction,
            loadTrend.percentage.toFixed(2) + "%"
        );

        console.log(
            "------------------------------------------"
        );

        console.log(
            "RISK SCORE:",
            riskScore
        );

        console.log(
            "STATUS:",
            status
        );

        console.log(
            "WARNINGS:",
            warnings
        );

        console.log(
            "=========================================="
        );


    }
    catch (error) {

        console.error(
            "STEP 42 ERROR:",
            error
        );

    }

}
// ============================================================
// START STEP 42
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        runHistoricalTrendAnalysis();

        // Recalculate every 10 seconds
        setInterval(
            runHistoricalTrendAnalysis,
            10000
        );

    }
);
/* =========================================================
   STEP 43
   PREDICTIVE VEHICLE INTELLIGENCE
   ========================================================= */

function evaluateVehiclePrediction(battery, vehicle, history) {

    console.log("======================================");
    console.log("STEP 43 - PREDICTIVE ANALYSIS");
    console.log("======================================");

    if (!battery) {
        console.warn("Battery data unavailable.");
        return;
    }

    if (!vehicle) {
        console.warn("Vehicle data unavailable.");
        return;
    }

    const voltage = Number(battery.voltage || 0);
    const current = Number(battery.current || 0);
    const temperature = Number(battery.temperature || 0);
    const soh = Number(battery.soh || 0);

    const speed = Number(vehicle.speed || 0);
    const tyrePressure = Number(vehicle.tyre_pressure || 0);

    const batteryPower =
        Number(battery.power || (voltage * current));

    const warnings = [];
    const criticals = [];

    /* -----------------------------------------
       BATTERY VOLTAGE
       ----------------------------------------- */

    if (voltage > 0 && voltage < 11.0) {

        criticals.push(
            "Battery voltage is critically low."
        );

    } else if (voltage > 0 && voltage < 11.5) {

        warnings.push(
            "Battery voltage is decreasing."
        );
    }


    /* -----------------------------------------
       BATTERY CURRENT
       ----------------------------------------- */

    if (current > 8.0) {

        criticals.push(
            "Battery current is critically high."
        );

    } else if (current > 6.0) {

        warnings.push(
            "Battery current is higher than normal."
        );
    }


    /* -----------------------------------------
       BATTERY TEMPERATURE
       ----------------------------------------- */

    if (temperature >= 45) {

        criticals.push(
            "Battery temperature is critical."
        );

    } else if (temperature >= 40) {

        warnings.push(
            "Battery temperature is increasing."
        );
    }


    /* -----------------------------------------
       BATTERY SOH
       ----------------------------------------- */

    if (soh > 0 && soh < 60) {

        criticals.push(
            "Battery State of Health is critically low."
        );

    } else if (soh > 0 && soh < 75) {

        warnings.push(
            "Battery State of Health is low."
        );
    }


    /* -----------------------------------------
       TYRE PRESSURE
       ----------------------------------------- */

    if (tyrePressure > 0 && tyrePressure < 26) {

        criticals.push(
            "Tyre pressure is critically low."
        );

    } else if (
        tyrePressure > 0 &&
        (tyrePressure < 29 || tyrePressure > 35)
    ) {

        warnings.push(
            "Tyre pressure is outside the recommended range."
        );
    }


    /* -----------------------------------------
       LOAD CAPACITY
       ----------------------------------------- */

    let loadStatus = "NORMAL";
    let loadRecommendation = "LOAD ACCEPTABLE";

    /*
       Simple software-level capacity estimation.

       This is a project prototype rule.
       It will later be replaced/refined using
       real hardware measurements.
    */

    const estimatedCapacity = Math.max(
        0,
        100 * (soh / 100)
    );

    const loadPercentage =
        batteryPower > 0
            ? Math.min(
                100,
                (batteryPower / 100) * 100
              )
            : 0;


    if (soh > 0 && soh < 60) {

        loadStatus = "CRITICAL";

        loadRecommendation =
            "REDUCE LOAD - BATTERY CAPACITY TOO LOW";

    } else if (
        soh > 0 &&
        soh < 75
    ) {

        loadStatus = "WARNING";

        loadRecommendation =
            "LIMIT VEHICLE LOAD";

    } else if (
        batteryPower > 80
    ) {

        loadStatus = "WARNING";

        loadRecommendation =
            "HIGH LOAD - MONITOR BATTERY";

    }


    /* -----------------------------------------
       ROAD CONDITION
       ----------------------------------------- */

    let roadCondition = "SMOOTH";

    if (speed >= 25) {

        roadCondition = "HIGH SPEED";

    } else if (speed >= 15) {

        roadCondition = "NORMAL";

    } else if (speed > 0) {

        roadCondition = "LOW SPEED";

    } else {

        roadCondition = "STOPPED";
    }


    /* -----------------------------------------
       OVERALL STATUS
       ----------------------------------------- */

    let overallStatus = "HEALTHY";

    if (criticals.length > 0) {

        overallStatus = "CRITICAL";

    } else if (warnings.length > 0) {

        overallStatus = "WARNING";

    }


    /* -----------------------------------------
       PREDICTIVE MESSAGE
       ----------------------------------------- */

    let predictionMessage =
        "Vehicle condition is stable.";

    if (criticals.length > 0) {

        predictionMessage =
            "CRITICAL: Immediate vehicle inspection recommended.";

    } else if (warnings.length > 0) {

        predictionMessage =
            "WARNING: Potential vehicle issue detected before failure.";

    } else {

        predictionMessage =
            "Vehicle condition is stable. No early fault detected.";
    }


    /* -----------------------------------------
       UPDATE EARLY WARNING SYSTEM
       ----------------------------------------- */

    const predictionElement =
        document.getElementById("predictiveAlert");

    if (predictionElement) {

        predictionElement.textContent =
            predictionMessage;

        predictionElement.classList.remove(
            "healthy",
            "warning",
            "critical"
        );

        predictionElement.classList.add(
            overallStatus.toLowerCase()
        );
    }


    /* -----------------------------------------
       UPDATE LOAD CAPACITY
       ----------------------------------------- */

    const loadStatusElement =
        document.getElementById(
            "loadCapacityStatus"
        );

    if (loadStatusElement) {

        loadStatusElement.textContent =
            loadStatus;
    }


    const loadRecommendationElement =
        document.getElementById(
            "loadRecommendation"
        );

    if (loadRecommendationElement) {

        loadRecommendationElement.textContent =
            loadRecommendation;
    }


    /* -----------------------------------------
       UPDATE ROAD CONDITION
       ----------------------------------------- */

    const roadElement =
        document.getElementById(
            "roadCondition"
        );

    if (roadElement) {

        roadElement.textContent =
            roadCondition;
    }


    /* -----------------------------------------
       UPDATE VEHICLE STATUS
       ----------------------------------------- */

    const vehicleStatusElement =
        document.getElementById(
            "vehicleStatus"
        );

    if (vehicleStatusElement) {

        vehicleStatusElement.textContent =
            overallStatus;
    }


    /* -----------------------------------------
       SERVICE CENTER DECISION
       ----------------------------------------- */

    const serviceSection =
        document.getElementById(
            "serviceSection"
        );

    if (serviceSection) {

        if (
            overallStatus === "WARNING" ||
            overallStatus === "CRITICAL"
        ) {

            serviceSection.classList.remove(
                "hidden"
            );

        } else {

            serviceSection.classList.add(
                "hidden"
            );
        }
    }


    /* -----------------------------------------
       CONSOLE OUTPUT
       ----------------------------------------- */

    console.log(
        "Battery voltage:",
        voltage
    );

    console.log(
        "Battery current:",
        current
    );

    console.log(
        "Battery temperature:",
        temperature
    );

    console.log(
        "Battery SOH:",
        soh
    );

    console.log(
        "Battery power:",
        batteryPower
    );

    console.log(
        "Vehicle speed:",
        speed
    );

    console.log(
        "Tyre pressure:",
        tyrePressure
    );

    console.log(
        "Estimated capacity:",
        estimatedCapacity.toFixed(2),
        "%"
    );

    console.log(
        "Load percentage:",
        loadPercentage.toFixed(2),
        "%"
    );

    console.log(
        "Road condition:",
        roadCondition
    );

    console.log(
        "Warnings:",
        warnings
    );

    console.log(
        "Critical faults:",
        criticals
    );

    console.log(
        "Overall vehicle status:",
        overallStatus
    );


    return {

        voltage: voltage,

        current: current,

        temperature: temperature,

        soh: soh,

        power: batteryPower,

        speed: speed,

        tyrePressure: tyrePressure,

        estimatedCapacity: estimatedCapacity,

        loadPercentage: loadPercentage,

        roadCondition: roadCondition,

        loadStatus: loadStatus,

        overallStatus: overallStatus,

        warnings: warnings,

        criticals: criticals
    };
}
/* =========================================================
   STEP 44 - FAULT INJECTION TEST MODE
   ========================================================= */

const faultScenarios = {

    NORMAL: {
        voltage: 12.0,
        current: 3.0,
        temperature: 29.2,
        soh: 90.126,
        tyrePressure: 31.8,
        speed: 15.3
    },

    LOW_BATTERY_VOLTAGE: {
        voltage: 10.9,
        current: 4.0,
        temperature: 30.0,
        soh: 89.5,
        tyrePressure: 31.5,
        speed: 20.0
    },

    HIGH_TEMPERATURE: {
        voltage: 12.0,
        current: 4.0,
        temperature: 43.5,
        soh: 88.0,
        tyrePressure: 31.5,
        speed: 20.0
    },

    LOW_TYRE_PRESSURE: {
        voltage: 12.0,
        current: 3.5,
        temperature: 30.0,
        soh: 87.5,
        tyrePressure: 25.5,
        speed: 20.0
    },

    HIGH_CURRENT: {
        voltage: 11.8,
        current: 8.5,
        temperature: 34.0,
        soh: 85.0,
        tyrePressure: 31.5,
        speed: 25.0
    },

    LOW_SOH: {
        voltage: 11.7,
        current: 4.5,
        temperature: 32.0,
        soh: 72.0,
        tyrePressure: 31.0,
        speed: 25.0
    },

    CRITICAL_COMBINATION: {
        voltage: 10.2,
        current: 11.0,
        temperature: 48.0,
        soh: 55.0,
        tyrePressure: 24.0,
        speed: 30.0
    }
};


/* =========================================================
   RUN FAULT SCENARIO
   ========================================================= */

function runFaultScenario(scenarioName) {

    console.log("");
    console.log("======================================");
    console.log("FAULT INJECTION TEST");
    console.log("======================================");

    console.log(
        "Scenario:",
        scenarioName
    );


    const data =
        faultScenarios[scenarioName];


    if (!data) {

        console.error(
            "Unknown fault scenario:",
            scenarioName
        );

        return;
    }


    console.log(
        "Simulation input:",
        data
    );


    /* -----------------------------------------
       UPDATE SIMULATED VALUES
       ----------------------------------------- */

    document.getElementById(
        "faultScenarioName"
    ).textContent = scenarioName;


    document.getElementById(
        "simVoltage"
    ).textContent =
        data.voltage.toFixed(1) + " V";


    document.getElementById(
        "simCurrent"
    ).textContent =
        data.current.toFixed(1) + " A";


    document.getElementById(
        "simTemperature"
    ).textContent =
        data.temperature.toFixed(1) + " °C";


    document.getElementById(
        "simSOH"
    ).textContent =
        data.soh.toFixed(1) + "%";


    document.getElementById(
        "simTyrePressure"
    ).textContent =
        data.tyrePressure.toFixed(1) + " PSI";


    document.getElementById(
        "simSpeed"
    ).textContent =
        data.speed.toFixed(1) + " km/h";


    /* -----------------------------------------
       CALCULATE RISK
       ----------------------------------------- */

    let riskScore = 0;

    const warnings = [];


    if (data.voltage < 11.0) {

        riskScore += 3;

        warnings.push(
            "LOW BATTERY VOLTAGE"
        );

    } else if (data.voltage < 11.5) {

        riskScore += 1;

        warnings.push(
            "Battery voltage decreasing"
        );
    }


    if (data.current > 8.0) {

        riskScore += 3;

        warnings.push(
            "HIGH BATTERY CURRENT"
        );

    } else if (data.current > 6.0) {

        riskScore += 1;

        warnings.push(
            "Battery current elevated"
        );
    }


    if (data.temperature >= 45) {

        riskScore += 3;

        warnings.push(
            "CRITICAL BATTERY TEMPERATURE"
        );

    } else if (data.temperature >= 40) {

        riskScore += 2;

        warnings.push(
            "Battery temperature high"
        );
    }


    if (data.tyrePressure < 26) {

        riskScore += 3;

        warnings.push(
            "CRITICAL TYRE PRESSURE"
        );

    } else if (data.tyrePressure < 29) {

        riskScore += 1;

        warnings.push(
            "Tyre pressure low"
        );
    }


    if (data.soh < 60) {

        riskScore += 3;

        warnings.push(
            "CRITICAL BATTERY SOH"
        );

    } else if (data.soh < 75) {

        riskScore += 2;

        warnings.push(
            "Battery SOH low"
        );
    }


    /* -----------------------------------------
       DETERMINE PREDICTION
       ----------------------------------------- */

    let prediction = "NORMAL";
    let recommendation = "Vehicle condition is healthy.";


    if (riskScore >= 6) {

        prediction = "CRITICAL";

        recommendation =
            "STOP VEHICLE AND VISIT SERVICE CENTER.";

    } else if (riskScore >= 2) {

        prediction = "WARNING";

        recommendation =
            "REDUCE LOAD AND CHECK VEHICLE CONDITION.";

    }


    /* -----------------------------------------
       DISPLAY RESULT
       ----------------------------------------- */

    const predictionElement =
        document.getElementById(
            "simulationPrediction"
        );


    predictionElement.textContent =
        "Prediction: " +
        prediction +
        " | Risk Score: " +
        riskScore;


    const recommendationElement =
        document.getElementById(
            "simulationRecommendation"
        );


    recommendationElement.textContent =
        recommendation;


    /* -----------------------------------------
       SERVICE CENTER
       ----------------------------------------- */

    const serviceSection =
        document.getElementById(
            "serviceSection"
        );


    if (serviceSection) {

        if (
            prediction === "WARNING" ||
            prediction === "CRITICAL"
        ) {

            serviceSection.classList.remove(
                "hidden"
            );

        } else {

            serviceSection.classList.add(
                "hidden"
            );
        }
    }


    /* -----------------------------------------
       UPDATE VEHICLE STATUS
       ----------------------------------------- */

    const vehicleStatus =
        document.getElementById(
            "vehicleStatus"
        );


    if (vehicleStatus) {

        vehicleStatus.textContent =
            prediction;
    }


    /* -----------------------------------------
       UPDATE LOAD RECOMMENDATION
       ----------------------------------------- */

    const loadStatus =
        document.getElementById(
            "loadCapacityStatus"
        );


    const loadRecommendation =
        document.getElementById(
            "loadRecommendation"
        );


    if (prediction === "CRITICAL") {

        if (loadStatus) {

            loadStatus.textContent =
                "CRITICAL";
        }


        if (loadRecommendation) {

            loadRecommendation.textContent =
                "DO NOT OPERATE VEHICLE";
        }

    } else if (prediction === "WARNING") {

        if (loadStatus) {

            loadStatus.textContent =
                "WARNING";
        }


        if (loadRecommendation) {

            loadRecommendation.textContent =
                "LIMIT VEHICLE LOAD";
        }

    } else {

        if (loadStatus) {

            loadStatus.textContent =
                "NORMAL";
        }


        if (loadRecommendation) {

            loadRecommendation.textContent =
                "LOAD ACCEPTABLE";
        }
    }


    /* -----------------------------------------
       LOG DETAILS
       ----------------------------------------- */

    console.log(
        "Risk score:",
        riskScore
    );

    console.log(
        "Prediction:",
        prediction
    );

    console.log(
        "Warnings:",
        warnings
    );

    console.log(
        "Recommendation:",
        recommendation
    );

    console.log(
        "======================================"
    );
}
/* ============================================================
   STEP 43
   DYNAMIC LOAD CAPACITY + ROAD CONDITION ANALYSIS
   ============================================================ */

console.log("==============================================");
console.log("STEP 43 - LOAD + ROAD CONDITION ANALYSIS");
console.log("==============================================");


/* ------------------------------------------------------------
   LOAD CAPACITY ANALYSIS
   ------------------------------------------------------------ */

function analyzeLoadCapacity(batteryData, vehicleData) {

    console.log("----------------------------------------------");
    console.log("LOAD CAPACITY ANALYSIS");
    console.log("----------------------------------------------");

    try {

        if (!batteryData) {
            console.warn("Battery data unavailable.");
            return;
        }

        const voltage = Number(batteryData.voltage) || 0;
        const current = Number(batteryData.current) || 0;
        const batteryPower = Number(batteryData.power) || 0;

        /*
         * Load power comes from the vehicle dataset.
         * We first try load_power.
         * If unavailable, calculate using load current.
         */

        let loadPower = 0;

        if (
            vehicleData &&
            vehicleData.load_power !== undefined &&
            vehicleData.load_power !== null
        ) {

            loadPower = Number(vehicleData.load_power) || 0;

        }

        /*
         * If load_power is not available from vehicle API,
         * estimate it using battery power and a default
         * load ratio.
         */

        if (loadPower <= 0) {

            loadPower = batteryPower * 0.80;

        }


        console.log("Battery voltage:", voltage);
        console.log("Battery current:", current);
        console.log("Battery power:", batteryPower);
        console.log("Detected load power:", loadPower);


        /* ----------------------------------------------------
           LOAD PERCENTAGE
           ---------------------------------------------------- */

        let loadPercentage = 0;

        if (batteryPower > 0) {

            loadPercentage =
                (loadPower / batteryPower) * 100;

        }


        loadPercentage =
            Math.max(0, Math.min(100, loadPercentage));


        console.log(
            "Load percentage:",
            loadPercentage.toFixed(2) + "%"
        );


        /* ----------------------------------------------------
           DETERMINE LOAD STATUS
           ---------------------------------------------------- */

        let loadStatus = "NORMAL";
        let recommendation = "LOAD ACCEPTABLE";


        if (loadPercentage < 60) {

            loadStatus = "NORMAL";

            recommendation =
                "LOAD ACCEPTABLE";

        }

        else if (loadPercentage < 80) {

            loadStatus = "MODERATE";

            recommendation =
                "LOAD ACCEPTABLE - MONITOR BATTERY";

        }

        else if (loadPercentage < 95) {

            loadStatus = "HIGH";

            recommendation =
                "REDUCE LOAD IF POSSIBLE";

        }

        else {

            loadStatus = "CRITICAL";

            recommendation =
                "REDUCE LOAD IMMEDIATELY";

        }


        /* ----------------------------------------------------
           BATTERY HEALTH CHECK
           ---------------------------------------------------- */

        const soh =
            Number(batteryData.soh) || 0;

        const temperature =
            Number(batteryData.temperature) || 0;


        if (soh > 0 && soh < 70) {

            loadStatus = "HIGH";

            recommendation =
                "BATTERY HEALTH LOW - REDUCE LOAD";

        }


        if (temperature >= 45) {

            loadStatus = "HIGH";

            recommendation =
                "BATTERY TEMPERATURE HIGH - REDUCE LOAD";

        }


        if (temperature >= 55) {

            loadStatus = "CRITICAL";

            recommendation =
                "CRITICAL TEMPERATURE - STOP HIGH LOAD";

        }


        /* ----------------------------------------------------
           UPDATE DASHBOARD
           ---------------------------------------------------- */

        const statusElement =
            document.getElementById(
                "loadCapacityStatus"
            );

        const recommendationElement =
            document.getElementById(
                "loadRecommendation"
            );


        if (statusElement) {

            statusElement.textContent =
                loadStatus;

            statusElement.className =
                "load-status-" +
                loadStatus.toLowerCase();

        }


        if (recommendationElement) {

            recommendationElement.textContent =
                recommendation;

        }


        /* ----------------------------------------------------
           UPDATE LOAD POWER CARD
           ---------------------------------------------------- */

        const loadPowerElement =
            document.getElementById("loadPower");


        if (loadPowerElement) {

            loadPowerElement.textContent =
                loadPower.toFixed(2) + " W";

        }


        /* ----------------------------------------------------
           CONSOLE OUTPUT
           ---------------------------------------------------- */

        console.log(
            "Load status:",
            loadStatus
        );

        console.log(
            "Recommendation:",
            recommendation
        );

        console.log(
            "SOH:",
            soh
        );

        console.log(
            "Temperature:",
            temperature
        );


        return {

            loadPower: loadPower,

            loadPercentage: loadPercentage,

            loadStatus: loadStatus,

            recommendation: recommendation

        };

    }

    catch (error) {

        console.error(
            "Load capacity analysis error:",
            error
        );

    }

}



/* ============================================================
   ROAD CONDITION ANALYSIS
   ============================================================ */

function analyzeRoadCondition(vehicleData) {

    console.log("----------------------------------------------");
    console.log("ROAD CONDITION ANALYSIS");
    console.log("----------------------------------------------");

    try {

        if (!vehicleData) {

            console.warn(
                "Vehicle data unavailable."
            );

            return;

        }


        const speed =
            Number(vehicleData.speed) || 0;

        const tyrePressure =
            Number(vehicleData.tyre_pressure) || 0;


        console.log(
            "Vehicle speed:",
            speed
        );

        console.log(
            "Tyre pressure:",
            tyrePressure
        );


        let roadCondition = "SMOOTH";
        let roadMessage =
            "Road condition is suitable for driving.";


        /* ----------------------------------------------------
           SPEED-BASED ROAD ESTIMATION
           ---------------------------------------------------- */

        if (speed <= 20) {

            roadCondition = "SMOOTH";

            roadMessage =
                "Road condition appears smooth.";

        }

        else if (speed <= 40) {

            roadCondition = "NORMAL";

            roadMessage =
                "Normal driving condition.";

        }

        else if (speed <= 60) {

            roadCondition = "ROUGH";

            roadMessage =
                "Moderate road stress detected.";

        }

        else {

            roadCondition = "HIGH STRESS";

            roadMessage =
                "High-speed driving detected.";

        }


        /* ----------------------------------------------------
           TYRE PRESSURE CHECK
           ---------------------------------------------------- */

        if (
            tyrePressure > 0 &&
            tyrePressure < 28
        ) {

            roadCondition =
                "UNSAFE";

            roadMessage =
                "Low tyre pressure detected.";

        }


        if (
            tyrePressure > 0 &&
            tyrePressure > 36
        ) {

            roadCondition =
                "UNSAFE";

            roadMessage =
                "High tyre pressure detected.";

        }


        /* ----------------------------------------------------
           UPDATE ROAD CONDITION
           ---------------------------------------------------- */

        const roadElement =
            document.getElementById(
                "roadCondition"
            );


        if (roadElement) {

            roadElement.textContent =
                roadCondition;

        }


        /* ----------------------------------------------------
           GLOBAL MESSAGE
           ---------------------------------------------------- */

        const globalMessage =
            document.getElementById(
                "globalMessage"
            );


        if (globalMessage) {

            globalMessage.textContent =
                roadMessage;

        }


        console.log(
            "Road condition:",
            roadCondition
        );

        console.log(
            "Road message:",
            roadMessage
        );


        return {

            roadCondition:
                roadCondition,

            roadMessage:
                roadMessage

        };

    }

    catch (error) {

        console.error(
            "Road condition analysis error:",
            error
        );

    }

}



/* ============================================================
   STEP 43 INTEGRATION
   ============================================================ */

async function runStep43Analysis() {

    console.log("");
    console.log("==============================================");
    console.log("RUNNING STEP 43 ANALYSIS");
    console.log("==============================================");

    try {

        /*
         * Get latest battery information
         */

        const batteryResponse =
            await fetch("/api/battery");


        if (!batteryResponse.ok) {

            throw new Error(
                "Battery API returned HTTP " +
                batteryResponse.status
            );

        }


        const batteryJSON =
            await batteryResponse.json();


        /*
         * Get latest vehicle information
         */

        const vehicleResponse =
            await fetch("/api/vehicle");


        if (!vehicleResponse.ok) {

            throw new Error(
                "Vehicle API returned HTTP " +
                vehicleResponse.status
            );

        }


        const vehicleJSON =
            await vehicleResponse.json();


        console.log(
            "Step 43 battery response:",
            batteryJSON
        );

        console.log(
            "Step 43 vehicle response:",
            vehicleJSON
        );


        const batteryData =
            batteryJSON.battery || {};


        const vehicleData =
            vehicleJSON.vehicle || {};


        /*
         * Run load analysis
         */

        const loadResult =
            analyzeLoadCapacity(
                batteryData,
                vehicleData
            );


        /*
         * Run road analysis
         */

        const roadResult =
            analyzeRoadCondition(
                vehicleData
            );


        /*
         * Combined recommendation
         */

        if (
            loadResult &&
            roadResult
        ) {

            let combinedMessage =
                loadResult.recommendation;


            if (
                roadResult.roadCondition ===
                "UNSAFE"
            ) {

                combinedMessage +=
                    " | CHECK TYRE/ROAD CONDITION";

            }


            const recommendationElement =
                document.getElementById(
                    "loadRecommendation"
                );


            if (recommendationElement) {

                recommendationElement.textContent =
                    combinedMessage;

            }

        }


        console.log("----------------------------------------------");
        console.log("STEP 43 COMPLETE");
        console.log("----------------------------------------------");

    }

    catch (error) {

        console.error(
            "STEP 43 ERROR:",
            error
        );

    }

}



/* ============================================================
   START STEP 43 AFTER PAGE LOAD
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "Step 43 module loaded."
        );

        /*
         * Small delay so existing dashboard
         * API calls can finish first.
         */

        setTimeout(
            function () {

                runStep43Analysis();

            },
            1500
        );

    }
);
// ============================================================
// STEP 43
// DISPLAY BATTERY PREDICTION IN EARLY WARNING SYSTEM
// ============================================================

function displayPredictionResult(predictionResponse) {

    console.log("========================================");
    console.log("STEP 43 - DISPLAYING PREDICTION");
    console.log("========================================");

    console.log("Prediction response:", predictionResponse);

    const alertBox = document.getElementById("predictiveAlert");

    if (!alertBox) {
        console.error("predictiveAlert element not found.");
        return;
    }

    // --------------------------------------------------------
    // Check API response
    // --------------------------------------------------------

    if (!predictionResponse) {

        alertBox.innerHTML =
            "Prediction data is unavailable.";

        alertBox.className =
            "prediction-message warning";

        return;
    }


    // --------------------------------------------------------
    // Get prediction array
    // --------------------------------------------------------

    let predictions = predictionResponse.predictions || [];

    if (!Array.isArray(predictions)) {

        console.warn(
            "Prediction data is not an array."
        );

        alertBox.innerHTML =
            "Prediction data format is invalid.";

        alertBox.className =
            "prediction-message warning";

        return;
    }


    // --------------------------------------------------------
    // If there are no predictions
    // --------------------------------------------------------

    if (predictions.length === 0) {

        alertBox.innerHTML =
            "No battery prediction available.";

        alertBox.className =
            "prediction-message warning";

        return;
    }


    // --------------------------------------------------------
    // Use the latest prediction
    // --------------------------------------------------------

    const latest =
        predictions[predictions.length - 1];


    console.log(
        "Latest prediction:",
        latest
    );


    // --------------------------------------------------------
    // Read prediction fields safely
    // --------------------------------------------------------

    const prediction =
        String(
            latest.prediction ??
            latest.status ??
            latest.health ??
            "NORMAL"
        ).toUpperCase();


    const soh =
        Number(
            latest.soh ??
            latest.soh_percent ??
            latest.predicted_soh ??
            latest.predicted_soh_percent ??
            0
        );


    const riskScore =
        Number(
            latest.risk_score ??
            latest.risk ??
            0
        );


    const warnings =
        latest.warnings ??
        latest.warning ??
        [];


    // --------------------------------------------------------
    // Convert warnings into an array
    // --------------------------------------------------------

    let warningList = [];

    if (Array.isArray(warnings)) {

        warningList = warnings;

    } else if (warnings) {

        warningList = [warnings];

    }


    // --------------------------------------------------------
    // Determine severity
    // --------------------------------------------------------

    let severity = "normal";


    if (
        prediction.includes("CRITICAL") ||
        prediction.includes("DANGER")
    ) {

        severity = "critical";

    } else if (
        prediction.includes("WARNING") ||
        prediction.includes("FAULT") ||
        prediction.includes("RISK")
    ) {

        severity = "warning";

    } else if (
        prediction.includes("NORMAL") ||
        prediction.includes("HEALTHY")
    ) {

        severity = "normal";

    } else {

        // Use risk score when prediction text is unclear

        if (riskScore >= 70) {

            severity = "critical";

        } else if (riskScore >= 30) {

            severity = "warning";

        } else {

            severity = "normal";

        }

    }


    // --------------------------------------------------------
    // Create message
    // --------------------------------------------------------

    let mainMessage = "";


    if (severity === "critical") {

        mainMessage =
            "⚠️ Critical battery condition detected. Immediate inspection is recommended.";

    } else if (severity === "warning") {

        mainMessage =
            "⚠️ Early warning detected. Battery condition should be monitored.";

    } else {

        mainMessage =
            "✓ Battery condition is stable. No immediate abnormality detected.";

    }


    // --------------------------------------------------------
    // Warning details
    // --------------------------------------------------------

    let warningHTML = "";


    if (warningList.length > 0) {

        warningHTML =
            `
            <div class="prediction-warning-list">
                <strong>Warnings:</strong>
                <ul>
                    ${warningList
                        .map(
                            warning =>
                                `<li>${warning}</li>`
                        )
                        .join("")}
                </ul>
            </div>
            `;

    } else {

        warningHTML =
            `
            <div class="prediction-warning-list">
                <strong>Warnings:</strong>
                None
            </div>
            `;

    }


    // --------------------------------------------------------
    // SOH display
    // --------------------------------------------------------

    let sohHTML = "";


    if (!isNaN(soh) && soh > 0) {

        sohHTML =
            `
            <div class="prediction-soh">
                Battery SOH:
                <strong>
                    ${soh.toFixed(2)}%
                </strong>
            </div>
            `;

    }


    // --------------------------------------------------------
    // Risk display
    // --------------------------------------------------------

    const riskHTML =
        `
        <div class="prediction-risk">
            Risk Score:
            <strong>
                ${isNaN(riskScore)
                    ? "0"
                    : riskScore.toFixed(2)}
            </strong>
        </div>
        `;


    // --------------------------------------------------------
    // Update dashboard
    // --------------------------------------------------------

    alertBox.innerHTML =
        `
        <div class="prediction-main">
            ${mainMessage}
        </div>

        <div class="prediction-details">

            <div>
                Prediction:
                <strong>
                    ${prediction}
                </strong>
            </div>

            ${sohHTML}

            ${riskHTML}

            ${warningHTML}

        </div>
        `;


    // --------------------------------------------------------
    // Update CSS class
    // --------------------------------------------------------

    alertBox.className =
        "prediction-message " + severity;


    // --------------------------------------------------------
    // Console confirmation
    // --------------------------------------------------------

    console.log(
        "Prediction displayed:",
        prediction
    );

    console.log(
        "SOH:",
        soh
    );

    console.log(
        "Risk score:",
        riskScore
    );

    console.log(
        "Warnings:",
        warningList
    );

}
