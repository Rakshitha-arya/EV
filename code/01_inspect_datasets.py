import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "datasets")

print("=" * 60)
print("EV DIGITAL TWIN - DATASET INSPECTION")
print("=" * 60)

for root, dirs, files in os.walk(DATASET_DIR):

    level = root.replace(DATASET_DIR, "").count(os.sep)
    indent = "    " * level

    print(f"\n{indent}{os.path.basename(root)}/")

    for file in files:
        print(f"{indent}    {file}")