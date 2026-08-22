from pathlib import Path
import scipy.io
import numpy as np
import hashlib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT.parent / "datasets"

NASA_ROOT = DATASET_ROOT / "NASA"
OXFORD_ROOT = DATASET_ROOT / "OXFORD"


# ============================================================
# FILE HASH
# ============================================================

def file_hash(path):

    h = hashlib.md5()

    with open(path, "rb") as f:

        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


# ============================================================
# NASA
# ============================================================

print("=" * 70)
print("NASA ACTUAL CYCLE COUNT")
print("=" * 70)

nasa_files = sorted(NASA_ROOT.rglob("*.mat"))

hashes = {}

unique_nasa_files = []
duplicate_nasa_files = []

for file in nasa_files:

    h = file_hash(file)

    if h in hashes:

        duplicate_nasa_files.append(
            (file, hashes[h])
        )

    else:

        hashes[h] = file
        unique_nasa_files.append(file)


print("\nNASA MAT files found:", len(nasa_files))
print("Unique MAT files:", len(unique_nasa_files))
print("Duplicate MAT files:", len(duplicate_nasa_files))


total_nasa_cycles = 0


print("\n" + "-" * 70)
print("NASA BATTERY CYCLES")
print("-" * 70)


for mat_file in unique_nasa_files:

    try:

        data = scipy.io.loadmat(
            mat_file,
            squeeze_me=True,
            struct_as_record=False
        )

        variables = [
            key for key in data
            if not key.startswith("__")
        ]

        for variable in variables:

            battery = data[variable]

            if hasattr(battery, "cycle"):

                cycles = battery.cycle

                try:
                    count = len(cycles)
                except TypeError:
                    count = 1

                total_nasa_cycles += count

                print(
                    f"{variable:<10} "
                    f"Cycles: {count:>5} "
                    f"File: {mat_file.name}"
                )

    except Exception as e:

        print(
            f"ERROR: {mat_file.name}"
        )

        print(e)


print("\nNASA TOTAL UNIQUE CYCLES:")
print(total_nasa_cycles)


# ============================================================
# DUPLICATES
# ============================================================

if duplicate_nasa_files:

    print("\n" + "-" * 70)
    print("DUPLICATE NASA FILES")
    print("-" * 70)

    for duplicate, original in duplicate_nasa_files:

        print(
            f"{duplicate.name}"
        )

        print(
            f"  duplicate of: "
            f"{original}"
        )


# ============================================================
# OXFORD
# ============================================================

print("\n" + "=" * 70)
print("OXFORD ACTUAL CYCLE COUNT")
print("=" * 70)


oxford_files = sorted(
    OXFORD_ROOT.rglob("*.mat")
)

total_oxford_cycles = 0


for mat_file in oxford_files:

    print(
        f"\nFILE: {mat_file.name}"
    )

    try:

        data = scipy.io.loadmat(
            mat_file,
            squeeze_me=True,
            struct_as_record=False
        )

        cells = [
            key for key in data
            if key.startswith("Cell")
        ]

        print(
            "Cells found:",
            len(cells)
        )

        for cell_name in cells:

            cell = data[cell_name]

            print(
                f"\n{cell_name}"
            )

            if hasattr(
                cell,
                "_fieldnames"
            ):

                print(
                    "Fields:",
                    cell._fieldnames
                )

                for field in cell._fieldnames:

                    try:

                        value = getattr(
                            cell,
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

                    except Exception:
                        pass

    except Exception as e:

        print("ERROR:")
        print(e)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DATASET CYCLE COUNT SUMMARY")
print("=" * 70)

print(
    "\nNASA unique MAT files:",
    len(unique_nasa_files)
)

print(
    "NASA duplicate MAT files:",
    len(duplicate_nasa_files)
)

print(
    "NASA unique cycle records:",
    total_nasa_cycles
)

print(
    "\nOxford MAT files:",
    len(oxford_files)
)

print(
    "Oxford cells:",
    8
)

print("\nNOTE:")
print(
    "Oxford cycle counts will be finalized after "
    "identifying the cycle/time-series field in each Cell."
)

print("=" * 70)