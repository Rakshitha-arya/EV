from pathlib import Path

# Project structure:
# Major project/
# ├── datasets/
# └── flask_app/
#     └── notebooks/

# Go from notebooks -> flask_app -> Major project -> datasets
DATASET_FOLDER = Path(__file__).resolve().parents[2] / "datasets"

print("=" * 60)
print("BATTERY DATASET INSPECTION")
print("=" * 60)

print(f"\nDataset location:")
print(DATASET_FOLDER)

if not DATASET_FOLDER.exists():
    print("\nERROR: Dataset folder was not found!")
    print("Expected location:")
    print(DATASET_FOLDER)
    exit()

print("\nDatasets found:\n")

for path in sorted(DATASET_FOLDER.rglob("*")):
    if path.is_file():
        relative_path = path.relative_to(DATASET_FOLDER)
        print(f"FILE: {relative_path}")

print("\n" + "=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)