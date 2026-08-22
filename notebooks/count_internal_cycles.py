from pathlib import Path
import scipy.io
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = PROJECT_ROOT.parent / "datasets"

NASA_ROOT = DATASET_ROOT / "NASA"
OXFORD_ROOT = DATASET_ROOT / "OXFORD"


# ============================================================
# HELPER: COUNT MATLAB STRUCTURE CONTENT
# ============================================================

def inspect_structure(obj, indent=0):

    prefix = " " * indent

    if hasattr(obj, "_fieldnames"):

        print(prefix + "Fields:")

        for field in obj._fieldnames:

            try:
                value = getattr(obj, field)

                if isinstance(value, np.ndarray):

                    print(
                        prefix
                        + f"  {field}: "
                        + f"array shape={value.shape}"
                    )

                else:

                    print(
                        prefix
                        + f"  {field}: "
                        + f"type={type(value).__name__}"
                    )

            except Exception:

                print(
                    prefix
                    + f"  {field}: <unable to inspect>"
                )


# ============================================================
# NASA
# ============================================================

print("=" * 70)
print("NASA INTERNAL DATASET COUNT")
print("=" * 70)

nasa_files = sorted(
    NASA_ROOT.rglob("*.mat")
)

print(f"\nNASA MAT files found: {len(nasa_files)}")

nasa_batteries = []

for mat_file in nasa_files:

    print("\n" + "=" * 70)
    print(f"FILE: {mat_file.name}")
    print("=" * 70)

    try:

        data = scipy.io.loadmat(
            mat_file,
            squeeze_me=True,
            struct_as_record=False
        )

        variables = [
            key
            for key in data.keys()
            if not key.startswith("__")
        ]

        for variable in variables:

            obj = data[variable]

            print(
                f"\nVariable: {variable}"
            )

            print(
                f"Type: {type(obj).__name__}"
            )

            if hasattr(obj, "_fieldnames"):

                print("Fields:")

                for field in obj._fieldnames:

                    try:

                        value = getattr(
                            obj,
                            field
                        )

                        if isinstance(
                            value,
                            np.ndarray
                        ):

                            print(
                                f"  {field}: "
                                f"shape={value.shape}"
                            )

                        else:

                            print(
                                f"  {field}: "
                                f"type={type(value).__name__}"
                            )

                    except Exception:

                        print(
                            f"  {field}: "
                            "<error>"
                        )

                nasa_batteries.append(
                    variable
                )

    except Exception as e:

        print("ERROR:")
        print(e)


print("\n" + "=" * 70)
print("NASA SUMMARY")
print("=" * 70)

print(
    f"MAT files : {len(nasa_files)}"
)

print(
    f"Battery variables inspected : "
    f"{len(nasa_batteries)}"
)


# ============================================================
# OXFORD
# ============================================================

print("\n" + "=" * 70)
print("OXFORD INTERNAL DATASET COUNT")
print("=" * 70)

oxford_files = sorted(
    OXFORD_ROOT.rglob("*.mat")
)

print(
    f"\nOxford MAT files found: "
    f"{len(oxford_files)}"
)

oxford_cells = []

for mat_file in oxford_files:

    print("\n" + "=" * 70)
    print(f"FILE: {mat_file.name}")
    print("=" * 70)

    try:

        data = scipy.io.loadmat(
            mat_file,
            squeeze_me=True,
            struct_as_record=False
        )

        variables = [
            key
            for key in data.keys()
            if not key.startswith("__")
        ]

        print("\nMATLAB variables:")

        for variable in variables:

            obj = data[variable]

            print(
                f"  {variable}: "
                f"type={type(obj).__name__}"
            )

            if hasattr(
                obj,
                "_fieldnames"
            ):

                oxford_cells.append(
                    variable
                )

    except Exception as e:

        print("ERROR:")
        print(e)


print("\n" + "=" * 70)
print("OXFORD SUMMARY")
print("=" * 70)

print(
    f"MAT files : {len(oxford_files)}"
)

print(
    f"Cells found : "
    f"{len(oxford_cells)}"
)

print(
    "\nCells:"
)

for cell in oxford_cells:

    print(
        f"  {cell}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("INTERNAL DATASET INSPECTION COMPLETE")
print("=" * 70)

print("\nNOTE:")
print(
    "This script identifies the internal MATLAB "
    "battery/cell structures."
)

print(
    "The next step will count the actual "
    "cycle records inside each structure."
)

print("=" * 70)