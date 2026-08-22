from pathlib import Path
import scipy.io
import h5py


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = (
    PROJECT_ROOT.parent
    / "datasets"
)


# ============================================================
# INSPECT MAT FILE
# ============================================================

def inspect_mat_file(mat_file):

    print("\n" + "=" * 70)
    print(f"FILE: {mat_file.name}")
    print("=" * 70)

    try:

        # Try normal MATLAB MAT-file reader
        data = scipy.io.loadmat(
            mat_file,
            squeeze_me=True,
            struct_as_record=False
        )

        print("\nMATLAB variables:")

        for key, value in data.items():

            if key.startswith("__"):
                continue

            print(
                f"  {key:<30} "
                f"type={type(value).__name__} "
                f"shape={getattr(value, 'shape', 'N/A')}"
            )

    except Exception as e:

        print("\nStandard MATLAB reader failed:")
        print(e)

        print("\nTrying HDF5 inspection...")

        try:

            with h5py.File(mat_file, "r") as f:

                print("\nHDF5 variables:")

                def show_item(name, obj):

                    if isinstance(obj, h5py.Dataset):

                        print(
                            f"  {name:<40} "
                            f"shape={obj.shape} "
                            f"dtype={obj.dtype}"
                        )

                    else:

                        print(
                            f"  {name:<40} "
                            f"[GROUP]"
                        )

                f.visititems(show_item)

        except Exception as h5_error:

            print("\nHDF5 inspection failed:")
            print(h5_error)


# ============================================================
# FIND NASA MAT FILES
# ============================================================

def inspect_nasa():

    nasa_root = DATASET_ROOT / "NASA"

    print("\n" + "=" * 70)
    print("NASA MAT DATASETS")
    print("=" * 70)

    if not nasa_root.exists():

        print("NASA folder not found:")
        print(nasa_root)

        return

    mat_files = sorted(
        nasa_root.rglob("*.mat")
    )

    print(
        f"\nMAT files found: "
        f"{len(mat_files)}"
    )

    for mat_file in mat_files:

        inspect_mat_file(
            mat_file
        )


# ============================================================
# FIND OXFORD MAT FILES
# ============================================================

def inspect_oxford():

    oxford_root = DATASET_ROOT / "OXFORD"

    print("\n" + "=" * 70)
    print("OXFORD MAT DATASET")
    print("=" * 70)

    if not oxford_root.exists():

        print("Oxford folder not found:")
        print(oxford_root)

        return

    mat_files = sorted(
        oxford_root.rglob("*.mat")
    )

    print(
        f"\nMAT files found: "
        f"{len(mat_files)}"
    )

    for mat_file in mat_files:

        inspect_mat_file(
            mat_file
        )


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("MATLAB DATASET STRUCTURE INSPECTION")
print("=" * 70)

print("\nDataset root:")
print(DATASET_ROOT)

inspect_nasa()

inspect_oxford()

print("\n" + "=" * 70)
print("MATLAB INSPECTION COMPLETE")
print("=" * 70)