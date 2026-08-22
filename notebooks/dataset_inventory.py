from pathlib import Path
import pandas as pd
import scipy.io


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = PROJECT_ROOT.parent / "datasets"

CALCE_ROOT = DATASET_ROOT / "CALCE"
NASA_ROOT = DATASET_ROOT / "NASA"
OXFORD_ROOT = DATASET_ROOT / "Oxford"


print("=" * 70)
print("FINAL BATTERY DATASET INVENTORY")
print("=" * 70)

print()
print("Dataset root:")
print(DATASET_ROOT)


# ============================================================
# CALCE
# ============================================================

print()
print("=" * 70)
print("CALCE")
print("=" * 70)

calce_files = list(CALCE_ROOT.rglob("*.xlsx"))

calce_rows = 0
calce_batteries = {}

for file in calce_files:

    try:
        excel = pd.ExcelFile(file)

        channel_sheets = [
            s for s in excel.sheet_names
            if s.lower().startswith("channel_")
        ]

        if not channel_sheets:
            continue

        df = pd.read_excel(
            file,
            sheet_name=channel_sheets[0]
        )

        calce_rows += len(df)

        battery = file.stem.split("_")[0] + "_" + file.stem.split("_")[1]

        calce_batteries.setdefault(
            battery,
            0
        )

        calce_batteries[battery] += 1

    except Exception as e:

        print(
            "ERROR:",
            file.name,
            e
        )


print()
print("Raw Excel files:", len(calce_files))

print()
print("CALCE batteries:")

for battery, count in sorted(calce_batteries.items()):

    print(
        f"{battery:<12} Files: {count:3d}"
    )

print()
print("Measurement rows:", calce_rows)


# ============================================================
# NASA
# ============================================================

print()
print("=" * 70)
print("NASA")
print("=" * 70)

nasa_files = list(
    NASA_ROOT.rglob("*.mat")
)

nasa_unique = {}

for file in nasa_files:

    try:

        data = scipy.io.loadmat(
            file,
            struct_as_record=False,
            squeeze_me=True
        )

        battery_names = [
            key
            for key in data.keys()
            if key.startswith("B")
        ]

        for battery in battery_names:

            if battery not in nasa_unique:

                nasa_unique[battery] = {
                    "file": file.name,
                    "cycles": 0
                }

            battery_struct = data[battery]

            fields = getattr(
                battery_struct,
                "_fieldnames",
                []
            )

            if "cycle" in fields:

                cycle_data = getattr(
                    battery_struct,
                    "cycle"
                )

                try:
                    nasa_unique[battery]["cycles"] = len(
                        cycle_data
                    )
                except TypeError:
                    nasa_unique[battery]["cycles"] = 1

    except Exception as e:

        print(
            "ERROR:",
            file.name,
            e
        )


print()
print("Raw MAT files:", len(nasa_files))

print(
    "Unique NASA batteries:",
    len(nasa_unique)
)

print()
print("NASA batteries:")

nasa_total_cycles = 0

for battery in sorted(nasa_unique):

    cycles = nasa_unique[battery]["cycles"]

    nasa_total_cycles += cycles

    print(
        f"{battery:<10} "
        f"Cycles: {cycles:4d}"
    )

print()
print(
    "Unique NASA cycle records:",
    nasa_total_cycles
)


# ============================================================
# OXFORD
# ============================================================

print()
print("=" * 70)
print("OXFORD")
print("=" * 70)

oxford_files = list(
    OXFORD_ROOT.glob("*.mat")
)

oxford_cells = {}
oxford_total_records = 0

for file in oxford_files:

    try:

        data = scipy.io.loadmat(
            file,
            struct_as_record=False,
            squeeze_me=True
        )

        cell_names = [
            key
            for key in data.keys()
            if key.startswith("Cell")
        ]

        for cell_name in sorted(cell_names):

            cell = data[cell_name]

            fields = getattr(
                cell,
                "_fieldnames",
                []
            )

            cycle_fields = [
                field
                for field in fields
                if field.lower().startswith("cyc")
            ]

            count = len(cycle_fields)

            oxford_cells[cell_name] = count

            oxford_total_records += count

    except Exception as e:

        print(
            "ERROR:",
            file.name,
            e
        )


print()
print("MAT files:", len(oxford_files))

print(
    "Oxford cells:",
    len(oxford_cells)
)

print()
print("Oxford cells:")

for cell, count in sorted(oxford_cells.items()):

    print(
        f"{cell:<10} "
        f"Records: {count:4d}"
    )

print()
print(
    "Characterization records:",
    oxford_total_records
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

print()
print(
    f"CALCE raw Excel files       : {len(calce_files)}"
)

print(
    f"CALCE measurement rows      : {calce_rows}"
)

print()
print(
    f"NASA raw MAT files          : {len(nasa_files)}"
)

print(
    f"NASA unique batteries       : {len(nasa_unique)}"
)

print(
    f"NASA cycle records          : {nasa_total_cycles}"
)

print()
print(
    f"Oxford MAT files            : {len(oxford_files)}"
)

print(
    f"Oxford cells                : {len(oxford_cells)}"
)

print(
    f"Oxford characterization     : {oxford_total_records}"
)

print()
print("=" * 70)
print("DATASET INVENTORY COMPLETE")
print("=" * 70)