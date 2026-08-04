"""
Vyuha L1 - FastLayer: the cheap first tier of the cascade.

Stacks three complementary signals (each covering a different failure mode):
  - RJD-v2 detector  : de-obfuscation + TF-IDF + features (strong on obfuscation)
  - SemanticDetector : similarity to known attacks (novel-but-similar / paraphrase;
                       set multilingual=True so translated attacks are also caught)
  - SignatureDB      : exact known-attack + high-precision templates

Combiner is a recall-preserving max: FastLayer's score is always >= RJD's, so it can
only add recall, never regress. The semantic signal is gated (sem_gate) so it only fires
on near-duplicate attacks; a high gate keeps over-refusal (FRR) low on clean traffic.
"""
import numpy as np

from .rjd import RJDDetector
from .semantic import SemanticDetector
from .signatures import SignatureDB


class FastLayer:
    def __init__(self, semantic_backend="auto", multilingual=False, name="Vyuha-Fast", sem_gate=0.85):
        self.rjd = RJDDetector(norm=True, char=True, feats_on=True, aug=True, calib=True, name="RJD-v2")
        self.sem = SemanticDetector(backend=semantic_backend, multilingual=multilingual)
        self.sig = SignatureDB()
        self.name = name
        self.sem_gate = sem_gate

    def _signals(self, X):
        X = list(X)
        return (np.asarray(self.rjd.proba(X)),
                np.asarray(self.sem.similarity(X)),
                np.asarray(self.sig.hit(X)))

    def fit(self, X, y):
        X, y = list(X), list(y)
        self.rjd.fit(X, y); self.sem.fit(X, y); self.sig.fit(X, y)
        return self

    def _combine(self, rjd, sem, sig):
        sem_c = np.clip((sem - self.sem_gate) / (1.0 - self.sem_gate), 0.0, 1.0)
        return np.maximum.reduce([rjd, sem_c, sig])

    def proba(self, X):
        rjd, sem, sig = self._signals(X)
        return self._combine(rjd, sem, sig)

    def explain(self, text):
        rjd, sem, sig = self._signals([text])
        return {"rjd": float(rjd[0]), "semantic": float(sem[0]), "signature": float(sig[0]),
                "fast_score": float(self._combine(rjd, sem, sig)[0])}
