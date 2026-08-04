"""
Vyuha L1 - known-attack signature database.

Two near-zero-false-positive signals:
  1. Exact match on a *normalized* key - catches re-submitted known attacks even if
     re-obfuscated (Base64/homoglyph/spacing all collapse to the same key).
  2. A small set of high-precision templates (DAN / developer-mode / override).

The fuzzy/novel-similar case is handled by the SemanticDetector; this layer is the
cheap, high-confidence "we've seen this exact attack" signal.
"""
import re
from ..normalize.normalize import normalize

TEMPLATES = [
    re.compile(r"\bdo anything now\b|\bDAN\b", re.I),
    re.compile(r"developer mode", re.I),
    re.compile(r"\b(ignore|disregard|forget)\b.{0,30}\b(previous|all|prior)\b.{0,20}\b(instruction|rule|prompt)", re.I),
    re.compile(r"\b(no|without)\b.{0,10}\b(restriction|filter|limit|guideline)s?\b", re.I),
    re.compile(r"\b(never|do not)\b.{0,10}refuse\b", re.I),
]


class SignatureDB:
    @staticmethod
    def _key(text):
        # collapse to a normalized, punctuation-free key so disguises map together
        return re.sub(r"\W+", "", normalize(str(text), full=False).lower())[:300]

    def fit(self, X, y):
        self.known = {self._key(t) for t, l in zip(X, y) if int(l) == 1}
        return self

    def hit(self, X):
        import numpy as np
        out = []
        for t in X:
            k = self._key(t)
            if k and k in self.known:
                out.append(1.0)                      # exact known attack
            elif any(p.search(str(t)) for p in TEMPLATES):
                out.append(0.8)                      # high-precision template
            else:
                out.append(0.0)
        return np.asarray(out)

    def proba(self, X):
        return self.hit(X)
