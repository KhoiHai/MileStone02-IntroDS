
from typing import Dict, List, Tuple
import numpy as np


def mrr_at_k(groundtruth: Dict[str, str], prediction: Dict[str, List[str]], k: int = 5) -> float:
    scores = []
    for bibkey, gt in groundtruth.items():
        preds = prediction.get(bibkey, [])[:k]
        rr = 0.0
        for idx, cand in enumerate(preds, start=1):
            if cand == gt:
                rr = 1.0 / idx
                break
        scores.append(rr)
    return float(np.mean(scores)) if scores else 0.0