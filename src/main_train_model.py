import os
from typing import List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from model.build_model import predict_topk_for_publication_with_scores, train_classifier
from model.evaluation import mrr_at_k
from model.feature_engineering import build_pairs_hardneg, fit_vectorizer_from_train
from model.helpers import (
    export_pred_json,
    list_publications,
    pick_splits,
    save_model_bundle,
    export_pred_json_score,
    export_summary_results_json
)
from model.label_filter import clean_and_filter_labels, filter_pubs_with_nonempty_label, has_usable_label
from model.load_data import load_publication

def main(DATA_ROOT: str, OUTPUTS_DIR: str, topn_neg: int = 50):
    manual_dir = os.path.join(DATA_ROOT, "manual")
    nonmanual_dir = os.path.join(DATA_ROOT, "non-manual")

    manual_pubs = list_publications(manual_dir)
    nonmanual_pubs = list_publications(nonmanual_dir)
    # Information about dataset
    print(f"[INFO] found manual pubs: {len(manual_pubs)}")
    print(f"[INFO] found non-manual pubs: {len(nonmanual_pubs)}")

    print(f"[INFO] filtering pubs with non-empty label.json")
    manual_usable = filter_pubs_with_nonempty_label(manual_dir, manual_pubs, "manual")
    nonmanual_usable = filter_pubs_with_nonempty_label(nonmanual_dir, nonmanual_pubs, "non-manual")

    if len(manual_usable) < 5:
        print(f"[WARN] manual pubs with non-empty label.json = {len(manual_usable)} < 5")

    # split pubs
    train_pubs, valid_pubs, test_pubs = pick_splits(manual_usable, nonmanual_usable)

    print("\n[INFO] Split:")
    print("  Train pubs:", [p for _, p in train_pubs])
    print("  Valid pubs:", [p for _, p in valid_pubs])
    print("  Test  pubs:", [p for _, p in test_pubs])

    outputs_dir = os.path.join(OUTPUTS_DIR, "outputs")
    outputs_dir_score = os.path.join(OUTPUTS_DIR, "outputs_with_scores")
    model_dir = os.path.join(OUTPUTS_DIR, "model_ckpt")
    
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(outputs_dir_score, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    # 1) Fit vectorizer on TRAIN only
    vectorizer = fit_vectorizer_from_train(train_pubs, manual_dir, nonmanual_dir)

    # 2) Build train pairs with hard negatives
    train_rows = []
    train_used_pubs = 0

    for group, pub_id in tqdm(train_pubs, desc="Building TRAIN pairs"):
        base_dir = manual_dir if group == "manual" else nonmanual_dir
        pub_dir = os.path.join(base_dir, pub_id)

        bib_entries, ref_entries, raw_label = load_publication(pub_dir)
        if not has_usable_label(raw_label):
            continue
        label, st = clean_and_filter_labels(bib_entries, ref_entries, raw_label, verbose=False)
        if not label:
            print(f"[WARN] skip train pub {pub_id}: no valid labels after filtering. stats={st}")
            continue

        df = build_pairs_hardneg(bib_entries, ref_entries, label, vectorizer, topn_neg=topn_neg)
        if len(df) == 0:
            continue
        df["pub_id"] = pub_id
        df["group"] = group
        df["partition"] = "train"
        train_rows.append(df)
        train_used_pubs += 1

    if not train_rows:
        raise ValueError("[ERROR] No usable TRAIN pairs. Check labels & candidates.")

    train_df = pd.concat(train_rows, ignore_index=True)
    print(f"[INFO] train pubs used = {train_used_pubs}")
    print(f"[INFO] Train pairs = {len(train_df)} | positives = {int(train_df['y'].sum())}")

    clf = train_classifier(train_df)
    save_model_bundle(model_dir, clf, vectorizer)

    # 3) Eval on valid and test pubs
    def eval_partition(pubs: List[Tuple[str,str]], name: str):
        mrrs = []
        details = []

        for group, pub_id in pubs:
            base_dir = manual_dir if group == "manual" else nonmanual_dir
            pub_dir = os.path.join(base_dir, pub_id)

            bib_entries, ref_entries, raw_label = load_publication(pub_dir)
            if not has_usable_label(raw_label):
                print(f"[WARN] skip {name} pub {pub_id}: empty label")
                details.append({
                    "partition": name, "group": group, "pub_id": pub_id,
                    "skipped": True, "reason": "empty_label"
                })
                continue

            label, st = clean_and_filter_labels(bib_entries, ref_entries, raw_label, verbose=True)
            if not label:
                print(f"[WARN] skip {name} pub {pub_id}: no valid labels after filtering. stats={st}")
                details.append({
                    "partition": name, "group": group, "pub_id": pub_id,
                    "skipped": True, "reason": "no_valid_labels_after_filtering",
                    "filter_stats": dict(st),
                    "parsed_bibkeys": int(len(bib_entries)),
                    "candidates": int(len(ref_entries)),
                })
                continue

            pred_ids, pred_scored = predict_topk_for_publication_with_scores(
                clf, bib_entries, ref_entries, label, vectorizer, k=5, predict_only_labeled=True
            )

            extra = set(pred_ids.keys()) - set(label.keys())
            miss = set(label.keys()) - set(pred_ids.keys())
            if extra or miss:
                print(f"[SANITY] key mismatch pub={pub_id} extra={len(extra)} missing={len(miss)}")

            mrr = mrr_at_k(label, pred_ids, k=5)
            print(f"\n[RESULT] pub={pub_id} partition={name} MRR@5={mrr:.4f} (label_kept={len(label)})")

            out_path = os.path.join(outputs_dir, f"{name}_{pub_id}_pred.json")
            out_path_score = os.path.join(outputs_dir_score, f"{name}_{pub_id}_pred_with_scores.json")

            stats = dict(st)
            stats.update({
                "label_kept": int(len(label)),
                "pred_keys": int(len(pred_ids)),
                "candidates": int(len(ref_entries)),
                "parsed_bibkeys": int(len(bib_entries)),
            })

            export_pred_json_score(out_path_score, name, pub_id, label, pred_ids, pred_scored, stats)
            print(f"[INFO] exported predictions to {out_path_score}")

            export_pred_json(out_path, name, label, pred_ids)
            print(f"[INFO] exported predictions to {out_path}")

            mrrs.append(mrr)

            details.append({
                "partition": name,
                "group": group,
                "pub_id": pub_id,
                "skipped": False,
                "mrr@5": float(mrr),
                "label_kept": int(len(label)),
                "pred_keys": int(len(pred_ids)),
                "candidates": int(len(ref_entries)),
                "parsed_bibkeys": int(len(bib_entries)),
                "filter_stats": dict(st),
                "pred_json": out_path,
                "pred_json_with_scores": out_path_score,
                "sanity": {"extra_keys": int(len(extra)), "missing_keys": int(len(miss))}
            })

        mean_mrr = float(np.mean(mrrs)) if mrrs else 0.0
        return mean_mrr, details


    train_mrr, train_details = eval_partition(train_pubs, "train")
    valid_mrr, valid_details = eval_partition(valid_pubs, "valid")
    test_mrr, test_details = eval_partition(test_pubs, "test")

    print("\n[FINAL RESULTS]")
    print(f"[FINAL] Train MRR@5 = {train_mrr:.4f}")
    print(f"\n[FINAL] Valid MRR@5 = {valid_mrr:.4f}")
    print(f"[FINAL] Test  MRR@5 = {test_mrr:.4f}")
    print(f"[INFO] outputs: {outputs_dir}")
    print(f"[INFO] model bundle: {model_dir}")
    print(f"[INFO] Size of dataset used to train the model: {len(train_df)} pairs from {train_used_pubs} publications.")
    print(f"[INFO] Size of data valid: {len(valid_pubs)} publications.")
    print(f"[INFO] Size of data test: {len(test_pubs)} publications.")
    summary_path = export_summary_results_json(
        outputs_dir=outputs_dir, 
        DATA_ROOT=DATA_ROOT,
        train_pubs=train_pubs,
        valid_pubs=valid_pubs,
        test_pubs=test_pubs,
        train_mrr=train_mrr,
        valid_mrr=valid_mrr,
        test_mrr=test_mrr,
        train_details=train_details,
        valid_details=valid_details,
        test_details=test_details,
        train_used_pubs=train_used_pubs,
        train_df_len=len(train_df),
        train_positives=int(train_df["y"].sum()),
        topn_neg=topn_neg,
    )
    print(f"[INFO] exported overall summary to {summary_path}")

if __name__ == "__main__":
    DATA_ROOT = r"./clean-data"
    OUTPUTS_DIR = r"./outputs"
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    main(DATA_ROOT, OUTPUTS_DIR, topn_neg=50)