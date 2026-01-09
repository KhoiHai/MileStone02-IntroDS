import os
import re
import json
from typing import Dict, List
import bibtexparser

def normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\\url\{.*?\}", "", s)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_arxiv_id(arxiv_id: str) -> str:
    if re.match(r"\d{6}-\d+", arxiv_id):
        return arxiv_id[2:].replace("-", ".")
    return arxiv_id

def extract_year(s: str):
    if not s:
        return None
    m = re.search(r"\b(19|20)\d{2}\b", s)
    return int(m.group()) if m else None

def normalize_author(author: str) -> str:
    author = author.replace("~", " ").strip()

    if "," in author:
        last, first = author.split(",", 1)
        return f"{first.strip()} {last.strip()}".lower()

    return author.lower()

def clean_bibtex(path: str) -> Dict:
    with open(path, encoding="utf-8", errors="ignore") as f:
        bib_db = bibtexparser.load(f)

    cleaned = {}
    seen_keys = set()

    for entry in bib_db.entries:
        key = entry.get("ID")
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)

        title = entry.get("title", "")
        author = entry.get("author", "")

        title = normalize_text(title)
        if not title or not author:
            continue

        authors = [
            normalize_author(a)
            for a in author.split(" and ")
            if a.strip()
        ]

        year = extract_year(entry.get("year", ""))

        cleaned[key] = {
            "title": title,
            "authors": authors,
            "year": year
        }

    return cleaned

def clean_references_json(path: str) -> Dict:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    cleaned = {}

    for arxiv_id, info in raw.items():
        norm_id = normalize_arxiv_id(arxiv_id)

        title = normalize_text(info.get("paper_title", ""))
        authors = [
            normalize_author(a)
            for a in info.get("authors", [])
            if a.strip()
        ]

        year = extract_year(info.get("submission_date", ""))

        if not title or not authors:
            continue

        cleaned[norm_id] = {
            "title": title,
            "authors": authors,
            "year": year
        }

    return cleaned

# Process all papers
def process_all_papers(
    input_root="../../selected",
    output_root="../../clean"
):
    os.makedirs(output_root, exist_ok=True)

    for paper_id in sorted(os.listdir(input_root)):
        paper_dir = os.path.join(input_root, paper_id)
        if not os.path.isdir(paper_dir):
            continue

        bib_path = os.path.join(paper_dir, "refs.bib")
        ref_json_path = os.path.join(paper_dir, "references.json")

        if not os.path.exists(bib_path) or not os.path.exists(ref_json_path):
            continue

        print(f"Processing {paper_id}")

        try:
            bib_clean = clean_bibtex(bib_path)
            ref_clean = clean_references_json(ref_json_path)
        except Exception as e:
            print(f"Failed {paper_id}: {e}")
            continue

        if not bib_clean or not ref_clean:
            continue

        out_dir = os.path.join(output_root, paper_id)
        os.makedirs(out_dir, exist_ok=True)

        with open(os.path.join(out_dir, "parsed_reference.json"), "w", encoding="utf-8") as f:
            json.dump(bib_clean, f, indent=2, ensure_ascii=False)

        with open(os.path.join(out_dir, "crawled_reference.json"), "w", encoding="utf-8") as f:
            json.dump(ref_clean, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    process_all_papers()