from pathlib import Path
import scipy.io


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = PROJECT_ROOT.parent / "datasets"

NASA_ROOT = DATASET_ROOT / "NASA"
OXFORD_ROOT = DATASET_ROOT / "Oxford"


print("=" * 70)
print("CYCLE FIELD INSPECTION")
print("=" * 70)


# ============================================================
# NASA
# ============================================================

print()
print("=" * 70)
print("NASA CYCLE FIELDS")
print("=" * 70)


nasa_files = sorted(NASA_ROOT.rglob("*.mat"))

# Use first unique-looking battery file
seen_batteries = set()
nasa_count = 0

for mat_file in nasa_files:

    try:

        data = scipy.io.loadmat(
            mat_file,
            struct_as_record=False,
            squeeze_me=True
        )

        battery_names = [
            key for key in data.keys()
            if key.startswith("B")
        ]

        for battery_name in battery_names:

            if battery_name in seen_batteries:
                continue

            seen_batteries.add(battery_name)

            battery = data[battery_name]

            fields = getattr(
                battery,
                "_fieldnames",
                []
            )

            if "cycle" not in fields:
                continue

            cycles = getattr(
                battery,
                "cycle"
            )

            print()
            print("-" * 70)
            print("Battery:", battery_name)
            print("Number of cycles:", len(cycles))

            # Inspect first cycle
            first_cycle = cycles[0]

            cycle_fields = getattr(
                first_cycle,
                "_fieldnames",
                []
            )

            print()
            print("First cycle fields:")

            for field in cycle_fields:
                print(" ", field)

            # Inspect first cycle values/types
            print()
            print("First cycle field details:")

            for field in cycle_fields:

                try:
                    value = getattr(
                        first_cycle,
                        field
                    )

                    print(
                        f"  {field:<20} "
                        f"type={type(value).__name__} "
                        f"shape={getattr(value, 'shape', 'N/A')}"
                    )

                except Exception as e:

                    print(
                        f"  {field:<20} "
                        f"ERROR: {e}"
                    )

            nasa_count += 1

            # Only inspect 3 unique batteries
            if nasa_count >= 3:
                break

        if nasa_count >= 3:
            break

    except Exception as e:

        print(
            "ERROR:",
            mat_file.name,
            e
        )


# ============================================================
# OXFORD
# ============================================================

print()
print()
print("=" * 70)
print("OXFORD CYCLE FIELDS")
print("=" * 70)


oxford_files = sorted(
    OXFORD_ROOT.glob("*.mat")
)

if not oxford_files:

    print("ERROR: Oxford MAT file not found.")

else:

    mat_file = oxford_files[0]

    data = scipy.io.loadmat(
        mat_file,
        struct_as_record=False,
        squeeze_me=True
    )

    cell_names = [
        key for key in data.keys()
        if key.startswith("Cell")
    ]

    print()
    print("Cells:", len(cell_names))

    # Inspect first two cells
    for cell_name in sorted(cell_names)[:2]:

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

        print()
        print("-" * 70)
        print("Cell:", cell_name)
        print(
            "Cycle/characterization fields:",
            len(cycle_fields)
        )

        if not cycle_fields:
            continue

        # First characterization record
        cycle_name = cycle_fields[0]

        cycle = getattr(
            cell,
            cycle_name
        )

        print()
        print("First record:", cycle_name)

        record_fields = getattr(
            cycle,
            "_fieldnames",
            []
        )

        print()
        print("Record fields:")

        for field in record_fields:
            print(" ", field)

        print()
        print("Record field details:")

        for field in record_fields:

            try:

                value = getattr(
                    cycle,
                    field
                )

                print(
                    f"  {field:<20} "
                    f"type={type(value).__name__} "
                    f"shape={getattr(value, 'shape', 'N/A')}"
                )

            except Exception as e:

                print(
                    f"  {field:<20} "
                    f"ERROR: {e}"
                )


print()
print("=" * 70)
print("CYCLE FIELD INSPECTION COMPLETE")
print("=" * 70)