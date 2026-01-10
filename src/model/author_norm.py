import re
from typing import Dict, List, Tuple, Optional
from model.text_norm import normalize_text

def normalize_author_list(authors) -> List[str]:
    if authors is None:
        return []
    if isinstance(authors, str):
        parts = re.split(r"\band\b|;|,|\|", authors)
        parts = [p.strip() for p in parts if p.strip()]
    elif isinstance(authors, list):
        parts = []
        for a in authors:
            if isinstance(a, str):
                parts.append(a)
            elif isinstance(a, dict):
                if a.get("family"):
                    parts.append(str(a["family"]))
                elif a.get("name"):
                    parts.append(str(a["name"]))
                else:
                    parts.append(" ".join([str(v) for v in a.values() if v]))
            else:
                parts.append(str(a))
    else:
        parts = [str(authors)]

    last_names = []
    for p in parts:
        p = normalize_text(p)
        if not p:
            continue
        toks = p.split()
        last_names.append(toks[-1])

    seen, out = set(), []
    for ln in last_names:
        if ln not in seen:
            out.append(ln)
            seen.add(ln)
    return out
