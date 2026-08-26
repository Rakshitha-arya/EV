import os
import numpy as np
from scipy.io import loadmat

NASA_ROOT = r"C:\Major project\datasets\NASA\extracted"

print("=" * 70)
print("NASA CAPACITY FIELD INSPECTION")
print("=" * 70)

mat_files = []

for root, dirs, files in os.walk(NASA_ROOT):
    for file in files:
        if file.lower().endswith(".mat"):
            mat_files.append(os.path.join(root, file))

print(f"\nMAT files found: {len(mat_files)}")

for mat_path in mat_files:

    battery_id = os.path.splitext(os.path.basename(mat_path))[0]

    print("\n" + "-" * 70)
    print(f"BATTERY: {battery_id}")
    print(f"FILE: {mat_path}")
    print("-" * 70)

    try:
        mat = loadmat(
            mat_path,
            squeeze_me=True,
            struct_as_record=False
        )
    except Exception as e:
        print(f"ERROR loading file: {e}")
        continue

    variables = [
        key for key in mat.keys()
        if not key.startswith("__")
    ]

    print("\nTop-level variables:")
    for key in variables:
        obj = mat[key]
        print(f"  {key:20s} type={type(obj).__name__}")

    # Usually the battery variable has the same name as the file
    if battery_id not in mat:
        print(f"\nWARNING: {battery_id} not found as top-level variable.")
        continue

    battery = mat[battery_id]

    if not hasattr(battery, "cycle"):
        print("\nWARNING: No 'cycle' field found.")
        continue

    cycles = battery.cycle

    if not isinstance(cycles, np.ndarray):
        cycles = np.atleast_1d(cycles)

    print(f"\nNumber of cycles: {len(cycles)}")

    # Inspect first few cycles
    inspect_count = min(5, len(cycles))

    for i in range(inspect_count):

        cycle = cycles[i]

        print("\n" + "-" * 50)
        print(f"CYCLE INDEX: {i}")
        print("-" * 50)

        if not hasattr(cycle, "_fieldnames"):
            print(f"Cycle type: {type(cycle).__name__}")
            continue

        print("Cycle fields:")

        for field in cycle._fieldnames:

            value = getattr(cycle, field)

            if isinstance(value, np.ndarray):
                print(
                    f"  {field:25s} "
                    f"type=ndarray "
                    f"shape={value.shape}"
                )
            else:
                print(
                    f"  {field:25s} "
                    f"type={type(value).__name__}"
                )

            # Print operation type
            if field == "type":
                print(f"       VALUE: {value}")

        # If data exists, inspect its fields
        if hasattr(cycle, "data"):

            data = cycle.data

            print("\nDATA FIELDS:")

            if hasattr(data, "_fieldnames"):

                for field in data._fieldnames:

                    value = getattr(data, field)

                    if isinstance(value, np.ndarray):

                        print(
                            f"  {field:25s} "
                            f"type=ndarray "
                            f"shape={value.shape}"
                        )

                        if value.size > 0:
                            try:
                                numeric = np.asarray(
                                    value,
                                    dtype=float
                                ).flatten()

                                print(
                                    f"       min={np.nanmin(numeric):.6f} "
                                    f"max={np.nanmax(numeric):.6f} "
                                    f"first={numeric[0]:.6f} "
                                    f"last={numeric[-1]:.6f}"
                                )
                            except Exception:
                                pass

                    else:

                        print(
                            f"  {field:25s} "
                            f"type={type(value).__name__}"
                        )

            else:
                print(
                    f"  data type: {type(data).__name__}"
                )

    # Count operation types for this battery
    print("\n" + "=" * 50)
    print("OPERATION TYPE SUMMARY")
    print("=" * 50)

    type_counts = {}

    for cycle in cycles:

        if hasattr(cycle, "type"):

            cycle_type = str(cycle.type).strip()

            type_counts[cycle_type] = (
                type_counts.get(cycle_type, 0) + 1
            )

    for cycle_type, count in type_counts.items():
        print(f"  {cycle_type:20s} {count}")

print("\n" + "=" * 70)
print("NASA CAPACITY INSPECTION COMPLETE")
print("=" * 70)