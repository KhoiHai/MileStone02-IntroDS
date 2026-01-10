import json
import os
import time
from typing import Dict, List, Tuple, Optional

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from model.feature_engineering import FEATURE_COLS

def list_publications(root_dir: str) -> List[str]:
    pubs = []
    if not os.path.exists(root_dir):
        return pubs
    for d in os.listdir(root_dir):
        p = os.path.join(root_dir, d)
        if os.path.isdir(p):
            if os.path.exists(os.path.join(p, "parsed_reference.json")) and os.path.exists(os.path.join(p, "crawled_reference.json")):
                pubs.append(d)
    return sorted(pubs)

def pick_splits(manual_usable: List[str], nonmanual_usable: List[str]) -> Tuple[List[Tuple[str,str]], List[Tuple[str,str]], List[Tuple[str,str]]]:
    if len(manual_usable) < 2:
        raise ValueError("Need >= 2 manual pubs with label.json non-empty.")
    if len(nonmanual_usable) < 2:
        raise ValueError("Need >= 2 non-manual pubs with label.json non-empty.")

    test_manual, valid_manual = manual_usable[0], manual_usable[1]
    test_nonmanual, valid_nonmanual = nonmanual_usable[0], nonmanual_usable[1]

    test_pubs = [("manual", test_manual), ("non-manual", test_nonmanual)]
    valid_pubs = [("manual", valid_manual), ("non-manual", valid_nonmanual)]

    train_manual = [p for p in manual_usable if p not in {test_manual, valid_manual}]
    train_nonmanual = [p for p in nonmanual_usable if p not in {test_nonmanual, valid_nonmanual}]
    train_pubs = [("manual", p) for p in train_manual] + [("non-manual", p) for p in train_nonmanual]

    return train_pubs, valid_pubs, test_pubs

def save_model_bundle(out_dir: str, clf: LogisticRegression, vectorizer: TfidfVectorizer):
    os.makedirs(out_dir, exist_ok=True)
    joblib.dump(clf, os.path.join(out_dir, "lr_model.joblib"))
    joblib.dump(vectorizer, os.path.join(out_dir, "tfidf_vectorizer.joblib"))
    meta = {
        "feature_cols": FEATURE_COLS,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "note": "TFIDF is fitted on TRAIN and reused for eval/inference. Pairs use hard negatives.",
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Saved model bundle to: {out_dir}")

def export_pred_json_score(out_path: str, partition: str, pub_id: str,
                     groundtruth: Dict[str, str],
                     prediction: Dict[str, List[str]],
                     top5_with_score: Dict[str, List[Tuple[str, float]]],
                     stats: Dict[str, int]) -> None:
    obj = {
        "partition": partition,
        "pub_id": pub_id,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "groundtruth": groundtruth,
        "prediction": prediction,
        "top5_with_score": top5_with_score,
        "stats": stats,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def export_pred_json(
    out_path: str,
    partition: str,
    groundtruth: Dict[str, str],
    prediction: Dict[str, List[str]]
) -> None:
    """
    Write pred.json following the required format:
    {
      "partition": "test",
      "groundtruth": { "bibtex_entry_name_1": "arxiv_id_1", ... },
      "prediction": { "bibtex_entry_name_1": ["cand_1", ... "cand_5"], ... }
    }
    """
    obj = {
        "partition": partition,
        "groundtruth": groundtruth,
        "prediction": prediction,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


import os
import json
import time
from typing import Dict, List, Tuple, Any

def export_summary_results_json(
    *,
    outputs_dir: str,
    DATA_ROOT: str,
    train_pubs: List[Tuple[str, str]],
    valid_pubs: List[Tuple[str, str]],
    test_pubs: List[Tuple[str, str]],
    train_mrr: float,
    valid_mrr: float,
    test_mrr: float,
    train_details: List[Dict[str, Any]],
    valid_details: List[Dict[str, Any]],
    test_details: List[Dict[str, Any]],
    train_used_pubs: int,
    train_df_len: int,
    train_positives: int,
    topn_neg: int,
    out_filename: str = "summary_results.json",
) -> str:

    os.makedirs(outputs_dir, exist_ok=True)

    summary = {
        "data_root": os.path.abspath(DATA_ROOT),

        "splits": {
            "train": [{"group": g, "pub_id": p} for g, p in train_pubs],
            "valid": [{"group": g, "pub_id": p} for g, p in valid_pubs],
            "test":  [{"group": g, "pub_id": p} for g, p in test_pubs],
        },

        "metrics": {
            "train_mrr@5": float(train_mrr),
            "valid_mrr@5": float(valid_mrr),
            "test_mrr@5": float(test_mrr),
        },

        "per_publication": {
            "train": train_details,
            "valid": valid_details,
            "test": test_details,
        },

        "training_data_stats": {
            "train_pubs_used": int(train_used_pubs),
            "train_pairs": int(train_df_len),
            "train_positives": int(train_positives),
            "topn_neg": int(topn_neg),
        },
    }


    summary_path = os.path.join(outputs_dir, out_filename)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary_path