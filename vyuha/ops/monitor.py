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


class SessionMonitor:
    """Per-conversation escalation detector for multi-turn / Crescendo jailbreaks.

    Crescendo-style attacks stay *below the per-message block threshold on every single turn* but climb
    toward harmful content over the conversation - the signal a single-message moderator, by
    construction, cannot see ("the unit of defense is the session, not the prompt"). Feed it each user
    turn's detector score (and whether the assistant refused); it flags the session on a rising trend,
    sustained elevation, or a refusal-then-rephrase-and-retry pattern.

        sm = SessionMonitor()
        for score, refused in turns:
            st = sm.observe(score, refused)
        st["escalating"]   # True if the conversation's trajectory is climbing toward harm
    """

    def __init__(self, per_msg_block=0.8, session_block=0.55, rise=0.25, window=6):
        self.per_msg_block = per_msg_block   # a single turn at/above this is the per-message layer's job
        self.session_block = session_block   # lower bar the CONVERSATION must not sustain or climb to
        self.rise = rise                     # min early->late increase to count as escalation
        self.window = window
        self.scores, self.refused = [], []

    def observe(self, score, refused=False):
        self.scores.append(float(score))
        self.refused.append(bool(refused))
        return self.status()

    def status(self):
        s = self.scores[-self.window:]
        rf = self.refused[-self.window:]
        n = len(s)
        if n == 0:
            return {"escalating": False, "reasons": [], "n": 0, "peak": 0.0, "trend": 0.0}
        flags, trend = [], 0.0
        # rising trend: late half notably higher than early half, and now in the suspicious zone
        if n >= 4:
            h = n // 2
            early, late = sum(s[:h]) / h, sum(s[h:]) / (n - h)
            trend = late - early
            if trend >= self.rise and late >= self.session_block:
                flags.append("rising_trend")
        # sustained elevation: the last few turns all park in the suspicious zone
        tail = s[-min(3, n):]
        if len(tail) >= 2 and all(x >= self.session_block for x in tail):
            flags.append("sustained_elevation")
        # refusal then rephrase-and-retry: a refusal earlier in the window, then a later turn climbs
        if any(rf[:-1]):
            first_ref = next(i for i, r in enumerate(rf) if r)
            if s[-1] - s[first_ref] >= self.rise and s[-1] >= self.session_block:
                flags.append("refusal_retry")
        return {"escalating": bool(flags), "reasons": flags, "n": n,
                "peak": round(max(s), 3), "trend": round(trend, 3)}
