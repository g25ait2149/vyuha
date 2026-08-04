"""
Vyuha evaluation metrics.

Security-grade metrics for a detector, given true labels (1=attack/unsafe, 0=benign)
and predicted attack-probabilities in [0,1]:

  - roc_auc            : threshold-free ranking quality
  - recall_at_fpr      : recall (TPR) while wrongly flagging only `fpr` of benign - the
                         key operating-point metric (default 1% FPR)
  - fpr_at_tpr         : benign false-alarm rate needed to catch `tpr` of attacks
  - frr                : over-refusal - fraction of benign flagged at a threshold
  - asr                : attack success rate = fraction of attacks NOT caught (1 - recall)
  - f1 / precision / recall at a threshold
"""
import time
import numpy as np
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score


def recall_at_fpr(y, scores, fpr=0.01):
    y = np.asarray(y); scores = np.asarray(scores)
    neg = scores[y == 0]
    if len(neg) == 0 or (y == 1).sum() == 0:
        return float("nan")
    thr = np.quantile(neg, 1 - fpr)              # threshold allowing `fpr` of benign through
    return float((scores[y == 1] >= thr).mean())


def fpr_at_tpr(y, scores, tpr=0.95):
    y = np.asarray(y); scores = np.asarray(scores)
    pos = scores[y == 1]
    if len(pos) == 0 or (y == 0).sum() == 0:
        return float("nan")
    thr = np.quantile(pos, 1 - tpr)              # threshold catching `tpr` of attacks
    return float((scores[y == 0] >= thr).mean())


def evaluate(y, scores, threshold=0.5):
    """Return the full metric dict for one detector on one dataset."""
    y = np.asarray(y); scores = np.asarray(scores)
    pred = (scores >= threshold).astype(int)
    both = (y == 0).any() and (y == 1).any()
    rec = float(recall_score(y, pred, zero_division=0))
    return {
        "n": int(len(y)),
        "roc_auc": float(roc_auc_score(y, scores)) if both else float("nan"),
        "recall_at_1pct_fpr": recall_at_fpr(y, scores, 0.01),
        "fpr_at_95_tpr": fpr_at_tpr(y, scores, 0.95),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": rec,
        "asr": float(1.0 - rec),                 # attack success rate against this defense
        "frr": float(pred[y == 0].mean()) if (y == 0).any() else float("nan"),  # over-refusal
    }


def measure_latency(detector, sample, repeats=1):
    """Mean ms/prompt for detector.proba over `sample`."""
    sample = list(sample)
    t0 = time.time()
    for _ in range(repeats):
        detector.proba(sample)
    return 1000.0 * (time.time() - t0) / (len(sample) * repeats)


def format_table(rows, cols=("model", "dataset", "n", "roc_auc", "recall_at_1pct_fpr", "frr", "f1", "latency_ms")):
    """Pretty fixed-width table from a list of metric dicts."""
    hdr = "  ".join(f"{c:>16}" if i else f"{c:<22}" for i, c in enumerate(cols))
    lines = [hdr, "-" * len(hdr)]
    for r in rows:
        cells = []
        for i, c in enumerate(cols):
            v = r.get(c, "")
            if isinstance(v, float):
                v = f"{v:.3f}"
            cells.append(f"{str(v):>16}" if i else f"{str(v):<22}")
        lines.append("  ".join(cells))
    return "\n".join(lines)
