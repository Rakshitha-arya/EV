from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CALCE_ROOT = (
    PROJECT_ROOT.parent
    / "datasets"
    / "CALCE"
    / "CS2"
)

CELLS = [
    "CS2_36",
    "CS2_37",
    "CS2_38"
]

for cell in CELLS:

    folder = CALCE_ROOT / cell

    print("\n" + "=" * 70)
    print(cell)
    print("=" * 70)

    files = sorted(folder.glob("*.xlsx"))

    for file in files:

        try:
            excel = pd.ExcelFile(file)

            print("\nFILE:", file.name)

            for sheet in excel.sheet_names:
                print("   ", sheet)

        except Exception as e:
            print("ERROR:", file.name)
            print(e)

print("\n" + "=" * 70)
print("SHEET CHECK COMPLETE")
print("=" * 70)