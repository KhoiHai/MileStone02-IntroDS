import os
from typing import Dict, List, Tuple

from model.load_data import BibEntry, RefEntry, load_publication

def has_usable_label(label: Dict[str, str]) -> bool:
    return isinstance(label, dict) and len(label) > 0

def clean_and_filter_labels(
    bib_entries: List[BibEntry],
    ref_entries: List[RefEntry],
    label: Dict[str, str],
    verbose: bool = False,
) -> Tuple[Dict[str, str], Dict[str, int]]:
    bibkey_set = {b.bibkey for b in bib_entries}
    cand_set = {r.arxiv_id for r in ref_entries}

    stats = {
        "label_total": 0,
        "label_kept": 0,
        "drop_empty_value": 0,
        "drop_bibkey_not_in_parsed": 0,
        "drop_gt_not_in_candidates": 0,
    }

    filtered = {}
    if not isinstance(label, dict):
        return filtered, stats

    stats["label_total"] = len(label)

    for k, v in label.items():
        if v is None or str(v).strip() == "":
            stats["drop_empty_value"] += 1
            continue
        if k not in bibkey_set:
            stats["drop_bibkey_not_in_parsed"] += 1
            continue
        v = str(v).strip()
        if v not in cand_set:
            stats["drop_gt_not_in_candidates"] += 1
            continue
        filtered[k] = v

    stats["label_kept"] = len(filtered)

    if verbose:
        print("[LABEL FILTER]", stats)

    return filtered, stats

def filter_pubs_with_nonempty_label(base_dir: str, pubs: List[str], group_name: str) -> List[str]:
    usable = []
    skipped = []
    for pub_id in pubs:
        pub_dir = os.path.join(base_dir, pub_id)
        _, _, raw_label = load_publication(pub_dir)
        if has_usable_label(raw_label):
            usable.append(pub_id)
        else:
            skipped.append(pub_id)

    print(f"[STATS] {group_name}: total={len(pubs)} | has_label(non-empty)={len(usable)} | skipped={len(skipped)}")
    if skipped:
        print(f"[STATS] {group_name} skipped examples (up to 20): {skipped[:20]}")
    return usable