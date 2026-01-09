import os
import json
import shutil
import re

SRC_DIR = "../../few-data"
DST_DIR = "../../selected"

TARGET_COUNT = 2500
MIN_RICH_REF = 20
MAX_RICH_REF = 500

os.makedirs(DST_DIR, exist_ok=True)

selected = []
rich_candidates = []

summary = {
    "total_scanned": 0,
    "valid_publications": 0,
    "selected": 0,
    "rich_candidates": 0
}

bib_entry_pattern = re.compile(r'^@\w+\{', re.MULTILINE)

for pub_id in sorted(os.listdir(SRC_DIR)):
    if len(selected) >= TARGET_COUNT:
        break

    pub_path = os.path.join(SRC_DIR, pub_id)
    if not os.path.isdir(pub_path):
        continue

    summary["total_scanned"] += 1

    ref_json_path = os.path.join(pub_path, "references.json")
    bib_path = os.path.join(pub_path, "refs.bib")

    if not os.path.exists(ref_json_path) or not os.path.exists(bib_path):
        continue

    # Load references
    try:
        with open(ref_json_path, encoding="utf-8") as f:
            ref_json = json.load(f)
    except Exception:
        continue

    if not isinstance(ref_json, dict) or len(ref_json) == 0:
        continue

    # Count Bibitex entries
    try:
        with open(bib_path, encoding="utf-8", errors="ignore") as f:
            bib_content = f.read()
    except Exception:
        continue

    bib_count = len(bib_entry_pattern.findall(bib_content))
    ref_count = len(ref_json)

    if bib_count == 0:
        continue

    # Valiadation publication
    summary["valid_publications"] += 1

    # Copy folder
    shutil.copytree(
        pub_path,
        os.path.join(DST_DIR, pub_id),
        dirs_exist_ok=True
    )

    selected.append(pub_id)
    summary["selected"] += 1

    # Rich candidate
    if bib_count >= MIN_RICH_REF and ref_count >= MIN_RICH_REF and ref_count <= MAX_RICH_REF:
        rich_candidates.append({
            "pub_id": pub_id,
            "bib_entries": bib_count,
            "references": ref_count
        })
        summary["rich_candidates"] += 1

print("Selection finished")

# ---- Save artifacts ----
with open("selection_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

with open("rich_candidates.txt", "w", encoding="utf-8") as f:
    for item in rich_candidates:
        f.write(
            f"{item['pub_id']}\t"
            f"bib={item['bib_entries']}\t"
            f"refs={item['references']}\n"
        )

print("Saved selection_summary.json")
print("Saved rich_candidates.txt")
print(f"Selected publications: {len(selected)}")
print(f"Rich candidates (>=25 refs): {len(rich_candidates)}")
