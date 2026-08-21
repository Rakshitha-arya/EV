import os

DATASET_FOLDER = "../datasets"

for root, dirs, files in os.walk(DATASET_FOLDER):
    level = root.replace(DATASET_FOLDER, "").count(os.sep)
    indent = "    " * level

    print(f"{indent}{os.path.basename(root)}/")

    for file in files:
        print(f"{indent}    {file}")