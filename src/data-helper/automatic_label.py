import os
import json
import re
from typing import Dict, List
from rapidfuzz import fuzz

ROOT_DIR = "../../clean"
AUTO_THRESHOLD = 0.80

LATEX_ACCENT_RE = re.compile(
    r"""
    \\['"`^~=\.uvHckbd]\s*   
    """,
    re.VERBOSE
)

def post_clean_author(name: str) -> str:
    if not name:
        return name

    # Remove LaTeX 
    name = LATEX_ACCENT_RE.sub("", name)

    # Remove all braces
    name = name.replace("{", "").replace("}", "")

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()

    return name.lower()

# This is for post clean the author string since it is still some uncleaned stuffs
def post_clean_authors(authors: List[str]) -> List[str]:
    return [post_clean_author(a) for a in authors]

# This is for similarity
def title_score(t1: str, t2: str) -> float:
    # assume title already cleaned
    return fuzz.token_set_ratio(t1, t2) / 100.0

def author_overlap(a1: List[str], a2: List[str]) -> float:
    s1 = set(post_clean_authors(a1))
    s2 = set(post_clean_authors(a2))
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / min(len(s1), len(s2))

def year_score(y1, y2) -> float:
    try:
        y1 = int(y1)
        y2 = int(y2)
    except (TypeError, ValueError):
        return 0.0

    if y1 == y2:
        return 1.0
    if abs(y1 - y2) == 1:
        return 0.5
    return 0.0

def final_score(p: Dict, c: Dict) -> float:
    return (
        0.5 * title_score(p["title"], c["title"]) +
        0.4 * author_overlap(p.get("authors", []), c.get("authors", [])) +
        0.1 * year_score(p.get("year", 0), c.get("year", 0))
    )

def main():
    for folder in os.listdir(ROOT_DIR):
        folder_path = os.path.join(ROOT_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        parsed_path = os.path.join(folder_path, "parsed_reference.json")
        crawled_path = os.path.join(folder_path, "crawled_reference.json")

        if not os.path.exists(parsed_path) or not os.path.exists(crawled_path):
            continue

        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed_refs = json.load(f)

        with open(crawled_path, "r", encoding="utf-8") as f:
            crawled_refs = json.load(f)

        labels: Dict[str, str] = {}

        for bibkey, pref in parsed_refs.items():
            best_score = 0.0
            best_crawled_key = None

            for crawled_key, cref in crawled_refs.items():
                score = final_score(pref, cref)
                if score > best_score:
                    best_score = score
                    best_crawled_key = crawled_key

            if best_score >= AUTO_THRESHOLD and best_crawled_key is not None:
                labels[bibkey] = best_crawled_key

        if not labels:
            continue

        label_path = os.path.join(folder_path, "label.json")
        with open(label_path, "w", encoding="utf-8") as f:
            json.dump(labels, f, indent=4, ensure_ascii=False)

        print(f"[OK] {folder}: labeled {len(labels)} pairs")

    print("[DONE] Auto labeling finished.")

if __name__ == "__main__":
    for folder in os.listdir(ROOT_DIR):
        folder_path = os.path.join(ROOT_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        label_path = os.path.join(folder_path, "label.json")
        if os.path.exists(label_path):
            os.remove(label_path)
            print(f"[CLEAN] Removed old label.json in {folder}")
    main()