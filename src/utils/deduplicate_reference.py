import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
from .reference_extraction import Reference_Entry

# Return similarity
def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Get the canonical reference hash
def canonical_ref_id(ref: Reference_Entry) -> str:
    """Create canonical hash based on author + title + year"""
    s = (
        ref.fields.get("author", "") +
        ref.fields.get("title", "") +
        ref.fields.get("year", "")
    ).lower()
    return hashlib.sha1(s.encode()).hexdigest()

# Deduplicate references
def deduplicate_references(
    ref_dict: Dict[str, Reference_Entry],
    sim_threshold: float = 0.9
) -> Tuple[Dict[str, Reference_Entry], Dict[str, str], List[Tuple[str, str, float]]]:

    canonical_map: Dict[str, Reference_Entry] = {}
    key_map: Dict[str, str] = {}
    similarity_list: List[Tuple[str, str, float]] = []

    for key, ref in ref_dict.items():
        best_match_cid = None
        best_sim = 0.0

        # Compare with all existing canonical references
        for cid, cref in canonical_map.items():
            a1 = (ref.fields.get("author", "") + " " + ref.fields.get("title", "")).strip()
            a2 = (cref.fields.get("author", "") + " " + cref.fields.get("title", "")).strip()
            sim = similarity(a1, a2)
            if sim > best_sim:
                best_sim = sim
                best_match_cid = cid

        if best_match_cid and best_sim >= sim_threshold:
            # Merge fields into the best canonical reference
            canonical_map[best_match_cid].fields.update(ref.fields)
            key_map[key] = canonical_map[best_match_cid].key
            similarity_list.append((key, canonical_map[best_match_cid].key, best_sim))
            print(f"[MATCH] {key} -> {canonical_map[best_match_cid].key}, similarity={best_sim:.3f}")
        else:
            # Create new canonical reference
            cid = canonical_ref_id(ref)
            canonical_map[cid] = ref
            key_map[key] = ref.key
            print(f"[NEW] {key} -> {ref.key} (canonical_id={cid})")

    print(f"\nTotal canonical references: {len(canonical_map)}")
    return canonical_map, key_map, similarity_list
