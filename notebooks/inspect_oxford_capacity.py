import os
import numpy as np
from scipy.io import loadmat

OXFORD_FILE = r"C:\Major project\datasets\Oxford\Oxford_Battery_Degradation_Dataset_1.mat"


def get_fields(obj):
    """Return MATLAB struct field names."""
    if hasattr(obj, "_fieldnames"):
        return obj._fieldnames
    return []


def to_numeric_array(value):
    """Convert a MATLAB field to a numeric numpy array if possible."""
    try:
        arr = np.asarray(value, dtype=float).squeeze()

        if arr.size == 0:
            return None

        return arr

    except Exception:
        return None


print("=" * 70)
print("OXFORD CAPACITY FIELD INSPECTION")
print("=" * 70)

print("\nFile:")
print(OXFORD_FILE)

if not os.path.exists(OXFORD_FILE):
    print("\nERROR: Oxford MAT file not found.")
    raise SystemExit(1)


# ------------------------------------------------------------
# Load MAT file
# ------------------------------------------------------------

mat = loadmat(
    OXFORD_FILE,
    squeeze_me=True,
    struct_as_record=False
)


# ------------------------------------------------------------
# Show top-level variables
# ------------------------------------------------------------

print("\nTop-level MAT variables:")

for key in mat.keys():

    if not key.startswith("__"):

        value = mat[key]

        print(
            f"  {key:<10} "
            f"type={type(value).__name__}"
        )


# ------------------------------------------------------------
# Inspect Cell1 and Cell2
# ------------------------------------------------------------

for cell_number in [1, 2]:

    cell_name = f"Cell{cell_number}"

    print("\n" + "=" * 70)
    print(cell_name)
    print("=" * 70)

    if cell_name not in mat:

        print(f"{cell_name} NOT FOUND")
        continue

    cell = mat[cell_name]

    cycle_fields = get_fields(cell)

    print(f"Characterization records: {len(cycle_fields)}")

    if not cycle_fields:

        print("No cycle fields found.")
        continue


    # --------------------------------------------------------
    # First characterization record
    # --------------------------------------------------------

    cycle_name = cycle_fields[0]

    print(f"\nFirst record: {cycle_name}")

    cycle = getattr(cell, cycle_name)

    print("\nRecord fields:")

    for field in get_fields(cycle):
        print(f"  {field}")


    # --------------------------------------------------------
    # Inspect C1dc
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("C1dc INSPECTION")
    print("-" * 70)

    if not hasattr(cycle, "C1dc"):

        print("C1dc NOT FOUND")
        continue

    c1dc = cycle.C1dc

    print("\nC1dc fields:")

    for field in get_fields(c1dc):
        print(f"  {field}")


    print("\nC1dc numeric field details:")

    for field in get_fields(c1dc):

        value = getattr(c1dc, field)

        arr = to_numeric_array(value)

        if arr is None:

            print(
                f"  {field:<8} "
                f"non-numeric"
            )

            continue

        print(
            f"  {field:<8} "
            f"shape={str(arr.shape):<15} "
            f"size={arr.size:<8} "
            f"min={np.nanmin(arr):.6f} "
            f"max={np.nanmax(arr):.6f} "
            f"first={arr.flat[0]:.6f} "
            f"last={arr.flat[-1]:.6f}"
        )


    # --------------------------------------------------------
    # Inspect OCVdc
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("OCVdc INSPECTION")
    print("-" * 70)

    if not hasattr(cycle, "OCVdc"):

        print("OCVdc NOT FOUND")
        continue

    ocvdc = cycle.OCVdc

    print("\nOCVdc fields:")

    for field in get_fields(ocvdc):
        print(f"  {field}")


    print("\nOCVdc numeric field details:")

    for field in get_fields(ocvdc):

        value = getattr(ocvdc, field)

        arr = to_numeric_array(value)

        if arr is None:

            print(
                f"  {field:<8} "
                f"non-numeric"
            )

            continue

        print(
            f"  {field:<8} "
            f"shape={str(arr.shape):<15} "
            f"size={arr.size:<8} "
            f"min={np.nanmin(arr):.6f} "
            f"max={np.nanmax(arr):.6f} "
            f"first={arr.flat[0]:.6f} "
            f"last={arr.flat[-1]:.6f}"
        )


print("\n" + "=" * 70)
print("OXFORD CAPACITY INSPECTION COMPLETE")
print("=" * 70)