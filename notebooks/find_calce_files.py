import os

ROOT = r"C:\Major project"

print("=" * 70)
print("CALCE FILE SEARCH")
print("=" * 70)

extensions = {
    ".csv",
    ".xlsx",
    ".xls",
    ".mat",
    ".txt"
}

count = 0

for root, dirs, files in os.walk(ROOT):

    # Skip unnecessary folders
    dirs[:] = [
        d for d in dirs
        if d not in {
            "__pycache__",
            ".git",
            "node_modules"
        }
    ]

    for file in files:

        ext = os.path.splitext(file)[1].lower()

        if ext in extensions:

            full_path = os.path.join(root, file)

            if "calce" in full_path.lower() or "cs2" in file.lower():

                count += 1

                print(
                    f"{count:>4}. {full_path}"
                )

print()
print("=" * 70)
print("TOTAL CALCE-RELATED FILES FOUND:", count)
print("=" * 70)