import os
import json
import joblib
from model.label_filter import clean_and_filter_labels
from model.load_data import load_publication
from model.build_model import predict_topk_for_publication_with_scores

DATA_ROOT = "./clean-data"
MODEL_DIR = os.path.join(DATA_ROOT, "model_ckpt_v2")

clf = joblib.load(os.path.join(MODEL_DIR, "lr_model.joblib"))
vec = joblib.load(os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib"))

PUB_ID = "2212-11481"
pub_dir = os.path.join(DATA_ROOT, "manual", PUB_ID)

bib_entries, ref_entries, raw_label = load_publication(pub_dir)
label, st = clean_and_filter_labels(bib_entries, ref_entries, raw_label, verbose=True)

pred_ids, pred_scored = predict_topk_for_publication_with_scores(
    clf, bib_entries, ref_entries, label, vec, k=5, predict_only_labeled=False  # False nếu muốn predict ALL bibkeys
)

out_path = os.path.join(DATA_ROOT, "outputs", "inference_pred_v2.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"pred": pred_ids, "top5": pred_scored, "label_stats": st}, f, ensure_ascii=False, indent=2)

print("Saved:", out_path)
