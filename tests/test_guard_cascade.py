"""GuardCascade: expert only sees the escalated share; total benign FPR respects the target."""
import numpy as np
from vyuha.guard import GuardCascade


class Stub:
    def __init__(self, table):
        self.table, self.calls = table, 0

    def proba(self, X):
        self.calls += len(X)
        return [self.table[x] for x in X]


def test_cascade_calibration_and_escalation():
    rng = np.random.default_rng(0)
    benign = [f"b{i}" for i in range(1000)]
    unsafe = [f"u{i}" for i in range(200)]
    screen = {**{b: rng.normal(0, 1) for b in benign}, **{u: rng.normal(2, 1) for u in unsafe}}
    expert = {**{b: rng.normal(0, 1) for b in benign}, **{u: rng.normal(3, 1) for u in unsafe}}
    s, e = Stub(screen), Stub(expert)
    cas = GuardCascade(s, e, escalate_share=0.2, target_fpr=0.02).fit(benign)
    e.calls = 0
    fb = cas.predict(benign)
    assert e.calls == int(cas.last_escalated.sum()) <= 0.21 * len(benign)   # expert only on escalated share
    assert fb.mean() <= 0.02 + 1e-9                                          # total benign FPR within target
    fu = cas.predict(unsafe)
    assert fu.mean() > 0.6                                                    # still catches most unsafe
