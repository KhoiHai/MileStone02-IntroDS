from typing import Dict, List, Tuple
from difflib import SequenceMatcher
from .reference_extraction import Reference_Entry

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def deduplicate_references(
    ref_dict: Dict[str, Reference_Entry],
    sim_threshold: float = 0.9
) -> Tuple[Dict[str, Reference_Entry], Dict[str, str], List[Tuple[str, str, float]]]:

    canonical_map: Dict[str, Reference_Entry] = {}  # key -> ref
    key_map: Dict[str, str] = {}                   # original key -> canonical key
    similarity_list: List[Tuple[str, str, float]] = []

    for key, ref in ref_dict.items():
        best_match_key = None
        best_sim = 0.0

        # Compare with all existing canonical references
        for ck, cref in canonical_map.items():
            a1 = (ref.fields.get("author", "") + " " + ref.fields.get("title", "")).strip()
            a2 = (cref.fields.get("author", "") + " " + cref.fields.get("title", "")).strip()
            sim = similarity(a1, a2)
            if sim > best_sim:
                best_sim = sim
                best_match_key = ck

        if best_match_key and best_sim >= sim_threshold:
            # Merge into canonical
            canonical_map[best_match_key].fields.update(ref.fields)
            if not hasattr(canonical_map[best_match_key], "merged_from"):
                canonical_map[best_match_key].merged_from = []
            canonical_map[best_match_key].merged_from.append(ref.key)
            key_map[key] = canonical_map[best_match_key].key
            similarity_list.append((key, canonical_map[best_match_key].key, best_sim))
            print(f"[MATCH] {key} -> {canonical_map[best_match_key].key}, similarity={best_sim:.3f}")
        else:
            # New canonical reference
            canonical_map[ref.key] = ref
            key_map[key] = ref.key
            print(f"[NEW] {key} -> {ref.key}")

    print(f"\nTotal canonical references: {len(canonical_map)}")
    return canonical_map, key_map, similarity_list
