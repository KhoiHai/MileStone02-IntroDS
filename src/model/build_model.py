from typing import Dict, List, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

from model.feature_engineering import FEATURE_COLS, pair_feature_row
from model.load_data import BibEntry, RefEntry



def train_classifier(train_df: pd.DataFrame) -> LogisticRegression:
    X = train_df[FEATURE_COLS].values
    y = train_df["y"].values
    clf = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        solver="lbfgs",
    )
    clf.fit(X, y)
    return clf

def predict_topk_for_publication_with_scores(
    clf: LogisticRegression,
    bib_entries: List[BibEntry],
    ref_entries: List[RefEntry],
    label: Dict[str, str],
    vectorizer: TfidfVectorizer,
    k: int = 5,
    predict_only_labeled: bool = True,
) -> Tuple[Dict[str, List[str]], Dict[str, List[Tuple[str, float]]]]:
    
    if predict_only_labeled:
        keys = set(label.keys())
        bib_entries = [b for b in bib_entries if b.bibkey in keys]

    if not bib_entries or not ref_entries:
        return {}, {}

    
    X_bib = vectorizer.transform([b.title_norm for b in bib_entries])
    X_ref = vectorizer.transform([r.title_norm for r in ref_entries])
    sim = cosine_similarity(X_bib, X_ref)

    topk_ids = {}
    topk_scored = {}

    
    ref_list = ref_entries
    for i, b in enumerate(bib_entries):
        rows = []
        for j, r in enumerate(ref_list):
           
            rows.append(pair_feature_row(b, r, float(sim[i, j]), y=0))
        df_pairs = pd.DataFrame(rows)

        X = df_pairs[FEATURE_COLS].values
        proba = clf.predict_proba(X)[:, 1]
        df_pairs["score"] = proba

        g2 = df_pairs.sort_values("score", ascending=False).head(k)
        topk_ids[b.bibkey] = g2["arxiv_id"].tolist()
        topk_scored[b.bibkey] = list(zip(g2["arxiv_id"].tolist(), g2["score"].astype(float).tolist()))

    return topk_ids, topk_scored


def debug_one_bibkey(label: Dict[str, str], pred_ids: Dict[str, List[str]], pred_scored: Dict[str, List[Tuple[str,float]]], bibkey: str):
    gt = label.get(bibkey)
    print("\n[CHECK ONE]")
    print(" bibkey =", bibkey)
    print(" gt =", gt)
    print(" top5 =", pred_ids.get(bibkey))
    print(" top5_scored =", pred_scored.get(bibkey))
    if gt and pred_ids.get(bibkey):
        if gt in pred_ids[bibkey]:
            print(" gt_rank =", pred_ids[bibkey].index(gt) + 1)
        else:
            print(" gt_rank = > 5 (miss)")