from pathlib import Path
import pandas as pd
import scipy.io
import re


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = (
    PROJECT_ROOT.parent
    / "datasets"
)


# ============================================================
# DATASETS
# ============================================================

DATASETS = [
    "CALCE",
    "NASA",
    "OXFORD"
]


# ============================================================
# FILE EXTENSIONS
# ============================================================

EXTENSIONS = {
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".mat"
}


# ============================================================
# HELPER
# ============================================================

def count_rows_csv_or_txt(file_path):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            return sum(1 for _ in f)

    except Exception:

        return None


# ============================================================
# CALCE
# ============================================================

def inspect_calce():

    print("\n" + "=" * 70)
    print("CALCE DATASET DETAILS")
    print("=" * 70)

    root = DATASET_ROOT / "CALCE"

    if not root.exists():

        print("CALCE folder not found:")
        print(root)

        return

    total_files = 0
    total_rows = 0

    batteries = {}

    files = list(root.rglob("*.xlsx"))

    print(f"\nExcel files found: {len(files)}")

    for file in files:

        total_files += 1

        try:

            # Battery name from parent folder
            battery = file.parent.name

            batteries.setdefault(
                battery,
                {
                    "files": 0,
                    "rows": 0
                }
            )

            excel = pd.ExcelFile(file)

            channel_sheets = [
                sheet
                for sheet in excel.sheet_names
                if sheet.lower().startswith("channel_")
            ]

            if not channel_sheets:

                print(
                    f"WARNING: No Channel sheet: "
                    f"{file.name}"
                )

                continue

            sheet = channel_sheets[0]

            df = pd.read_excel(
                file,
                sheet_name=sheet
            )

            rows = len(df)

            batteries[battery]["files"] += 1
            batteries[battery]["rows"] += rows

            total_rows += rows

        except Exception as e:

            print(
                f"ERROR: {file.name}"
            )

            print(e)

    print("\nBattery summary:")

    for battery, data in sorted(
        batteries.items()
    ):

        print(
            f"{battery:15}"
            f" Files: {data['files']:4}"
            f" Rows: {data['rows']:10}"
        )

    print("\nCALCE totals:")

    print("Raw Excel files:", total_files)
    print("Measurement rows:", total_rows)


# ============================================================
# NASA
# ============================================================

def inspect_nasa():

    print("\n" + "=" * 70)
    print("NASA DATASET DETAILS")
    print("=" * 70)

    root = DATASET_ROOT / "NASA"

    if not root.exists():

        print("NASA folder not found:")
        print(root)

        return

    files = []

    for extension in [
        "*.txt",
        "*.mat"
    ]:

        files.extend(
            root.rglob(extension)
        )

    print(
        f"\nFiles found: {len(files)}"
    )

    txt_files = list(
        root.rglob("*.txt")
    )

    mat_files = list(
        root.rglob("*.mat")
    )

    print(
        f"TXT files: {len(txt_files)}"
    )

    print(
        f"MAT files: {len(mat_files)}"
    )

    print("\nFile details:")

    for file in sorted(files):

        size_kb = (
            file.stat().st_size
            / 1024
        )

        print(
            f"{file.name:45}"
            f"{size_kb:12.2f} KB"
        )

    print(
        "\nNote:"
    )

    print(
        "NASA .mat files are MATLAB data containers."
    )

    print(
        "Their internal battery/cycle structure "
        "will be inspected separately."
    )


# ============================================================
# OXFORD
# ============================================================

def inspect_oxford():

    print("\n" + "=" * 70)
    print("OXFORD DATASET DETAILS")
    print("=" * 70)

    root = DATASET_ROOT / "OXFORD"

    if not root.exists():

        print("OXFORD folder not found:")
        print(root)

        return

    txt_files = list(
        root.rglob("*.txt")
    )

    mat_files = list(
        root.rglob("*.mat")
    )

    csv_files = list(
        root.rglob("*.csv")
    )

    print(
        f"\nTXT files: {len(txt_files)}"
    )

    print(
        f"MAT files: {len(mat_files)}"
    )

    print(
        f"CSV files: {len(csv_files)}"
    )

    files = (
        txt_files
        + mat_files
        + csv_files
    )

    print("\nFile details:")

    for file in sorted(files):

        size_kb = (
            file.stat().st_size
            / 1024
        )

        print(
            f"{file.name:45}"
            f"{size_kb:12.2f} KB"
        )


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("BATTERY DATASET DETAILS")
print("=" * 70)

print(
    "\nDataset root:"
)

print(DATASET_ROOT)


inspect_calce()

inspect_nasa()

inspect_oxford()


print("\n" + "=" * 70)
print("DATASET INSPECTION COMPLETE")
print("=" * 70)