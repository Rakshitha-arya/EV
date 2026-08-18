import os
import zipfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NASA_DIR = os.path.join(BASE_DIR, "datasets", "NASA")
EXTRACT_DIR = os.path.join(NASA_DIR, "extracted")

os.makedirs(EXTRACT_DIR, exist_ok=True)

print("=" * 60)
print("NASA DATASET EXTRACTION")
print("=" * 60)

zip_files = [
    file for file in os.listdir(NASA_DIR)
    if file.lower().endswith(".zip")
]

print(f"\nFound {len(zip_files)} ZIP files.\n")

for zip_file in zip_files:

    zip_path = os.path.join(NASA_DIR, zip_file)

    folder_name = os.path.splitext(zip_file)[0]
    output_folder = os.path.join(EXTRACT_DIR, folder_name)

    os.makedirs(output_folder, exist_ok=True)

    print(f"Extracting: {zip_file}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(output_folder)

    print(f"Done → {output_folder}\n")

print("=" * 60)
print("NASA EXTRACTION COMPLETE")
print("=" * 60)