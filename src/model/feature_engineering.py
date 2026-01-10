import os
import json
import re
import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from model.load_data import BibEntry, RefEntry, load_publication
from model.label_filter import clean_and_filter_labels, has_usable_label
from model.text_norm import jaccard, tokenize

FEATURE_COLS = [
    "title_tfidf_cosine",
    "year_abs_diff",
    "author_overlap_ratio",
#    "title_jaccard",
#    "year_match",
#   "first_author_match",
#   "title_len_diff",
]

def pair_feature_row(b: BibEntry, r: RefEntry, title_tfidf_cosine: float, y: int) -> Dict:
    b_tokens = tokenize(b.title_norm)
    r_tokens = tokenize(r.title_norm)

    if b.year is None or r.year is None:
        year_abs_diff = 10.0
        year_match = 0
    else:
        year_abs_diff = float(abs(b.year - r.year))
        year_match = 1 if year_abs_diff == 0 else 0

    b_auth = b.authors_last
    r_auth = r.authors_last
    if not b_auth:
        author_overlap_ratio = 0.0
    else:
        author_overlap_ratio = len(set(b_auth) & set(r_auth)) / max(1, len(set(b_auth)))
    first_author_match = 1 if (b_auth and r_auth and b_auth[0] == r_auth[0]) else 0
    title_len_diff = float(abs(len(b_tokens) - len(r_tokens)))

    return {
        "bibkey": b.bibkey,
        "arxiv_id": r.arxiv_id,
        "y": int(y),
        "title_tfidf_cosine": float(title_tfidf_cosine),
        "title_jaccard": float(jaccard(b_tokens, r_tokens)),
        "year_abs_diff": float(year_abs_diff),
        "year_match": int(year_match),
        "author_overlap_ratio": float(author_overlap_ratio),
        "first_author_match": int(first_author_match),
        "title_len_diff": float(title_len_diff),
    }

def fit_vectorizer_from_train(
    train_pubs: List[Tuple[str, str]],
    manual_dir: str,
    nonmanual_dir: str,
) -> TfidfVectorizer:
    # Fit TF-IDF once using TRAIN publications only
    titles = []
    for group, pub_id in tqdm(train_pubs, desc="Fitting TF-IDF on train titles"):
        base_dir = manual_dir if group == "manual" else nonmanual_dir
        pub_dir = os.path.join(base_dir, pub_id)
        bib_entries, ref_entries, raw_label = load_publication(pub_dir)
        if not has_usable_label(raw_label):
            continue
        label, _ = clean_and_filter_labels(bib_entries, ref_entries, raw_label)
        if not label:
            continue

        # only titles from labeled bibkeys + all candidate refs
        labeled_keys = set(label.keys())
        for b in bib_entries:
            if b.bibkey in labeled_keys:
                titles.append(b.title_norm)
        for r in ref_entries:
            titles.append(r.title_norm)

    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    vec.fit(titles if titles else ["dummy"])
    return vec

def build_pairs_hardneg(
    bib_entries: List[BibEntry],
    ref_entries: List[RefEntry],
    label: Dict[str, str],
    vectorizer: TfidfVectorizer,
    topn_neg: int = 50,
    ensure_pos_in_candidates: bool = True,
) -> pd.DataFrame:
    """
    For each labeled bibkey:
      - include (bib, gt) as positive
      - include topN hard negatives by TFIDF cosine (excluding gt)
    """
    # filter bibs to labeled only
    bib_map = {b.bibkey: b for b in bib_entries}
    ref_map = {r.arxiv_id: r for r in ref_entries}
    cand_ids = [r.arxiv_id for r in ref_entries]

    rows = []

    # precompute TF-IDF matrices
    bib_list = [bib_map[k] for k in label.keys() if k in bib_map]
    if not bib_list or not ref_entries:
        return pd.DataFrame(columns=["bibkey", "arxiv_id", "y"] + FEATURE_COLS)

    X_bib = vectorizer.transform([b.title_norm for b in bib_list])
    X_ref = vectorizer.transform([r.title_norm for r in ref_entries])
    sim = cosine_similarity(X_bib, X_ref)  # (#bibs, #refs)

    for i, b in enumerate(bib_list):
        gt = label.get(b.bibkey)

        if ensure_pos_in_candidates and (gt not in ref_map):
            # should not happen if label already filtered
            continue

        # rank candidates by cosine
        order = np.argsort(-sim[i])  # descending

        # positive
        if gt in ref_map:
            # find cosine for gt
            j_gt = cand_ids.index(gt)
            rows.append(pair_feature_row(b, ref_map[gt], float(sim[i, j_gt]), y=1))

        # negatives: topN excluding gt
        neg_added = 0
        for j in order:
            arxiv_id = cand_ids[j]
            if arxiv_id == gt:
                continue
            rows.append(pair_feature_row(b, ref_map[arxiv_id], float(sim[i, j]), y=0))
            neg_added += 1
            if neg_added >= topn_neg:
                break

    return pd.DataFrame(rows)