from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT.parent / "datasets"

print("=" * 70)
print("RAW DATASET LOG COUNT")
print("=" * 70)

extensions = {
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".mat"
}

grand_total = 0

for dataset in ["CALCE", "NASA", "OXFORD"]:

    dataset_path = DATASET_ROOT / dataset

    print(f"\n{'=' * 70}")
    print(f"{dataset}")
    print(f"{'=' * 70}")

    if not dataset_path.exists():
        print("Folder not found:", dataset_path)
        continue

    counts = {}

    for ext in extensions:
        files = list(dataset_path.rglob(f"*{ext}"))
        counts[ext] = len(files)

    dataset_total = sum(counts.values())
    grand_total += dataset_total

    for ext, count in counts.items():
        if count > 0:
            print(f"{ext:6} : {count}")

    print(f"TOTAL : {dataset_total}")

print(f"\n{'=' * 70}")
print("GRAND TOTAL RAW LOG FILES")
print(f"{'=' * 70}")
print(f"TOTAL : {grand_total}")
print("=" * 70)