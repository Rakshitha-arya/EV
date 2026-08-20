import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NASA_EXTRACTED = os.path.join(
    BASE_DIR,
    "datasets",
    "NASA",
    "extracted"
)

print("=" * 70)
print("NASA EXTRACTED DATASET INSPECTION")
print("=" * 70)

for root, dirs, files in os.walk(NASA_EXTRACTED):

    level = root.replace(NASA_EXTRACTED, "").count(os.sep)
    indent = "    " * level

    print(f"{indent}{os.path.basename(root)}/")

    for file in files:
        print(f"{indent}    {file}")

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)