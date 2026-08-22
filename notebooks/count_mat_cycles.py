from pathlib import Path
import scipy.io
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = PROJECT_ROOT.parent / "datasets"


# ============================================================
# FIND NUMBER OF CYCLES IN MATLAB STRUCTURE
# ============================================================

def inspect_structure(obj, name="root", level=0):

    if level > 4:
        return

    if hasattr(obj, "_fieldnames"):

        fields = obj._fieldnames

        print(
            "  " * level +
            f"{name}: STRUCT"
        )

        for field in fields:

            value = getattr(obj, field)

            print(
                "  " * (level + 1) +
                f"{field}: "
                f"type={type(value).__name__}, "
                f"shape={getattr(value, 'shape', 'N/A')}"
            )

            if level < 2:
                inspect_structure(
                    value,
                    field,
                    level + 2
                )


# ============================================================
# NASA
# ============================================================

def inspect_nasa():

    nasa_root = DATASET_ROOT / "NASA"

    print("\n" + "=" * 70)
    print("NASA BATTERY STRUCTURE")
    print("=" * 70)

    mat_files = sorted(
        nasa_root.rglob("*.mat")
    )

    print(
        f"\nMAT files: {len(mat_files)}"
    )

    for mat_file in mat_files:

        print("\n" + "-" * 70)
        print(mat_file.name)
        print("-" * 70)

        try:

            data = scipy.io.loadmat(
                mat_file,
                squeeze_me=True,
                struct_as_record=False
            )

            for key, value in data.items():

                if key.startswith("__"):
                    continue

                inspect_structure(
                    value,
                    key
                )

        except Exception as e:

            print("ERROR:", e)


# ============================================================
# OXFORD
# ============================================================

def inspect_oxford():

    oxford_root = DATASET_ROOT / "OXFORD"

    print("\n" + "=" * 70)
    print("OXFORD BATTERY STRUCTURE")
    print("=" * 70)

    mat_files = sorted(
        oxford_root.rglob("*.mat")
    )

    for mat_file in mat_files:

        print("\n" + "-" * 70)
        print(mat_file.name)
        print("-" * 70)

        try:

            data = scipy.io.loadmat(
                mat_file,
                squeeze_me=True,
                struct_as_record=False
            )

            for key, value in data.items():

                if key.startswith("__"):
                    continue

                inspect_structure(
                    value,
                    key
                )

        except Exception as e:

            print("ERROR:", e)


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("MATLAB BATTERY CYCLE STRUCTURE INSPECTION")
print("=" * 70)

print("\nDataset root:")
print(DATASET_ROOT)

inspect_nasa()

inspect_oxford()

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)