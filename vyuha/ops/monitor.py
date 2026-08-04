"""
Vyuha L5 (P5) - runtime monitoring: score-distribution drift + rate alerts.

Holds a reference distribution of detector scores (from eval/validation) and compares a
live window via PSI (population stability index - the standard drift metric) plus
block-rate threshold alarms. Lets ops catch a shifting attack mix or a model/base update
that quietly degrades the filter: the "attacker moves second" continuous-eval loop.
"""
import numpy as np


def psi(reference, live, bins=10):
    """Population Stability Index between a reference and a live score distribution."""
    ref, liv = np.asarray(reference, float), np.asarray(live, float)
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        edges = np.linspace(0, 1, bins + 1)
    r = np.histogram(ref, bins=edges)[0] / max(len(ref), 1) + 1e-6
    l = np.histogram(liv, bins=edges)[0] / max(len(liv), 1) + 1e-6
    return float(np.sum((l - r) * np.log(l / r)))


class Monitor:
    def __init__(self, reference_scores=None, block_at=0.8,
                 psi_warn=0.10, psi_alert=0.25, block_rate_max=0.5):
        self.reference = list(reference_scores) if reference_scores is not None else None
        self.block_at = block_at
        self.psi_warn, self.psi_alert = psi_warn, psi_alert
        self.block_rate_max = block_rate_max
        self.window = []

    def observe(self, scores):
        self.window.extend(float(s) for s in np.atleast_1d(scores))
        return self

    def report(self, reset=True):
        w = np.asarray(self.window, float)
        out = {"n": int(w.size),
               "block_rate": float((w >= self.block_at).mean()) if w.size else 0.0,
               "mean_score": float(w.mean()) if w.size else 0.0,
               "psi": psi(self.reference, w) if (self.reference and w.size) else None}
        alerts = []
        if out["psi"] is not None and out["psi"] >= self.psi_alert:
            alerts.append(f"DRIFT_ALERT psi={out['psi']:.3f}")
        elif out["psi"] is not None and out["psi"] >= self.psi_warn:
            alerts.append(f"drift_warn psi={out['psi']:.3f}")
        if out["block_rate"] > self.block_rate_max:
            alerts.append(f"HIGH_BLOCK_RATE {out['block_rate']:.2f}")
        out["alerts"] = alerts
        if reset:
            self.window = []
        return out
