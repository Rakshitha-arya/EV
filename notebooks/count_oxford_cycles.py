from pathlib import Path
import scipy.io


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OXFORD_ROOT = (
    PROJECT_ROOT.parent
    / "datasets"
    / "Oxford"
)


# ============================================================
# FIND OXFORD MAT FILE
# ============================================================

mat_files = list(OXFORD_ROOT.glob("*.mat"))

print("=" * 70)
print("OXFORD ACTUAL CYCLE COUNT")
print("=" * 70)

print()
print("Dataset root:")
print(OXFORD_ROOT)

print()
print("MAT files found:", len(mat_files))


if not mat_files:
    print()
    print("ERROR: No Oxford .mat file found.")
    raise SystemExit


# ============================================================
# PROCESS MAT FILE
# ============================================================

for mat_file in mat_files:

    print()
    print("=" * 70)
    print("FILE:", mat_file.name)
    print("=" * 70)

    data = scipy.io.loadmat(
        mat_file,
        struct_as_record=False,
        squeeze_me=True
    )

    cell_names = [
        key
        for key in data.keys()
        if key.startswith("Cell")
    ]

    print()
    print("Cells found:", len(cell_names))

    total_cycles = 0

    print()
    print("-" * 70)
    print("CELL CYCLE COUNTS")
    print("-" * 70)

    for cell_name in sorted(cell_names):

        cell = data[cell_name]

        # Get fields inside Cell structure
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

        cycle_count = len(cycle_fields)

        total_cycles += cycle_count

        print(
            f"{cell_name:<10} "
            f"Cycles: {cycle_count:4d}"
        )

    print()
    print("=" * 70)
    print("OXFORD SUMMARY")
    print("=" * 70)

    print()
    print("Cells:", len(cell_names))

    print(
        "Total characterization records:",
        total_cycles
    )


print()
print("=" * 70)
print("OXFORD CYCLE COUNT COMPLETE")
print("=" * 70)