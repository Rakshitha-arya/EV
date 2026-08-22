from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "processed"


# ============================================================
# INPUT FILE
# ============================================================

CALCE_FILE = (
    PROCESSED_DIR
    / "calce_cs2_all_cells.csv"
)


# ============================================================
# OUTPUT FILE
# ============================================================

OUTPUT_FILE = (
    PROCESSED_DIR
    / "dashboard_dataset.csv"
)


# ============================================================
# LOAD CALCE DATA
# ============================================================

print("=" * 70)
print("CREATING DASHBOARD DATASET")
print("=" * 70)

print("\nInput:")
print(CALCE_FILE)

if not CALCE_FILE.exists():

    print("\nERROR: CALCE processed dataset not found.")
    print("Run 06_process_all_calce.py first.")
    raise SystemExit


df = pd.read_csv(CALCE_FILE)

print("\nInput rows:", len(df))


# ============================================================
# CREATE DASHBOARD COLUMNS
# ============================================================

dashboard = pd.DataFrame()


dashboard["Dataset"] = "CALCE"

dashboard["Battery_ID"] = df["Battery"]

dashboard["Cycle"] = df["Cycle"]


# ------------------------------------------------------------
# Battery parameters
# ------------------------------------------------------------

dashboard["Voltage_V"] = df["Avg_Voltage_V"]

dashboard["Current_A"] = df["Avg_Current_A"]

dashboard["Temperature_C"] = pd.NA

dashboard["SOC_percent"] = pd.NA

dashboard["SOH_percent"] = df["SOH_percent"]


# ------------------------------------------------------------
# Energy / power
# ------------------------------------------------------------

dashboard["Power_W"] = (
    dashboard["Voltage_V"]
    * dashboard["Current_A"]
)


dashboard["Energy_Wh"] = (
    df["Discharge_Energy_Wh"]
)


# ------------------------------------------------------------
# Vehicle parameters
# ------------------------------------------------------------

dashboard["Speed_kmph"] = pd.NA

dashboard["Distance_km"] = pd.NA


# ------------------------------------------------------------
# GPS
# ------------------------------------------------------------

dashboard["Latitude"] = pd.NA

dashboard["Longitude"] = pd.NA


# ============================================================
# CLEAN NUMERIC VALUES
# ============================================================

numeric_columns = [

    "Cycle",

    "Voltage_V",

    "Current_A",

    "Temperature_C",

    "SOC_percent",

    "SOH_percent",

    "Power_W",

    "Energy_Wh",

    "Speed_kmph",

    "Distance_km",

    "Latitude",

    "Longitude"
]


for column in numeric_columns:

    dashboard[column] = pd.to_numeric(
        dashboard[column],
        errors="coerce"
    )


# ============================================================
# SORT
# ============================================================

dashboard = dashboard.sort_values(
    [
        "Battery_ID",
        "Cycle"
    ]
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

dashboard.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\nDashboard columns:")

for column in dashboard.columns:

    print(f"  {column}")


print("\nBattery counts:")

print(
    dashboard["Battery_ID"]
    .value_counts()
)


print("\nTotal dashboard rows:")

print(len(dashboard))


print("\nSaved dashboard dataset:")

print(OUTPUT_FILE)


print("\n" + "=" * 70)
print("DASHBOARD DATASET CREATED")
print("=" * 70)