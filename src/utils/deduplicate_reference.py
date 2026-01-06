import os
import re
import hashlib
from dataclasses import dataclass
from typing import Dict, List
from .reference_extraction import *

def canonical_ref_id(ref: Reference_Entry) -> str:
    """Create a canonical hash based on author + title + year"""
    s = (
        ref.fields.get("author", "") +
        ref.fields.get("title", "") +
        ref.fields.get("year", "")
    ).lower()
    return hashlib.sha1(s.encode()).hexdigest()

def deduplicate_references(ref_dict: Dict[str, Reference_Entry]) -> Dict[str, Reference_Entry]:
    """Deduplicate by canonical ID, unionize fields, choose a canonical key"""
    canonical_map = {}  # canonical_id -> Reference_Entry
    key_map = {}        # old_key -> canonical_key

    for key, ref in ref_dict.items():
        cid = canonical_ref_id(ref)
        if cid not in canonical_map:
            canonical_map[cid] = ref
        else:
            # merge fields
            canonical_map[cid].fields.update(ref.fields)
        key_map[key] = canonical_map[cid].key

    return canonical_map, key_map