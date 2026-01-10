import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from model.author_norm import normalize_author_list
from model.text_norm import normalize_text, safe_int

@dataclass
class BibEntry:
    bibkey: str
    title: str
    title_norm: str
    authors_last: List[str]
    year: Optional[int]

@dataclass
class RefEntry:
    arxiv_id: str
    title: str
    title_norm: str
    authors_last: List[str]
    year: Optional[int]

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_publication(pub_dir: str) -> Tuple[List[BibEntry], List[RefEntry], Dict[str, str]]:
    parsed_path = os.path.join(pub_dir, "parsed_reference.json")
    crawled_path = os.path.join(pub_dir, "crawled_reference.json")
    label_path = os.path.join(pub_dir, "label.json")

    parsed = load_json(parsed_path)
    crawled = load_json(crawled_path)
    label = load_json(label_path) if os.path.exists(label_path) else {}

    bib_entries: List[BibEntry] = []
    for bibkey, obj in parsed.items():
        title = obj.get("title", "") if isinstance(obj, dict) else ""
        year = safe_int(obj.get("year")) if isinstance(obj, dict) else None
        authors = obj.get("authors") if isinstance(obj, dict) else None
        bib_entries.append(
            BibEntry(
                bibkey=bibkey,
                title=title,
                title_norm=normalize_text(title),
                authors_last=normalize_author_list(authors),
                year=year,
            )
        )

    ref_entries: List[RefEntry] = []
    for arxiv_id, obj in crawled.items():
        title = obj.get("title", "") if isinstance(obj, dict) else ""
        year = safe_int(obj.get("year")) if isinstance(obj, dict) else None
        authors = obj.get("authors") if isinstance(obj, dict) else None
        ref_entries.append(
            RefEntry(
                arxiv_id=arxiv_id,
                title=title,
                title_norm=normalize_text(title),
                authors_last=normalize_author_list(authors),
                year=year,
            )
        )

    return bib_entries, ref_entries, label