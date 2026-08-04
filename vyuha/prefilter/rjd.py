"""
Vyuha L1 - RJD fast detector (the millisecond pre-filter).

Carries the RJD-v2 design forward: de-obfuscation normalization + word/char TF-IDF
+ 13 engineered features + calibrated soft-vote ensemble, with optional adversarial
augmentation. CPU-only, ~5 ms/prompt. This is the cheap first tier of the cascade.
"""
import random
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier

from ..normalize.normalize import normalize, normalize_views
from .features import featurize, OVERRIDE, DEVMODE, REFUSAL
from .attacks import augment

SEED = 42


class KeywordBaseline:
    """Trivial regex-count baseline (lower bound for comparison)."""
    def _counts(self, X):
        return np.array([[len(OVERRIDE.findall(str(t))) + len(DEVMODE.findall(str(t))) +
                          len(REFUSAL.findall(str(t)))] for t in X], dtype=float)

    def fit(self, X, y):
        self.lr = LogisticRegression(max_iter=1000, class_weight="balanced").fit(self._counts(X), np.asarray(y))
        return self

    def proba(self, X):
        return self.lr.predict_proba(self._counts(X))[:, 1]


class RJDDetector:
    """
    Configurable detector. Defaults reproduce RJD-v2 (normalize + char-grams +
    features + augmentation + calibration). Toggle flags for ablations / baselines.
    """
    def __init__(self, norm=True, char=True, feats_on=True, aug=True, calib=True, name="RJD-v2"):
        self.norm, self.char, self.feats_on = norm, char, feats_on
        self.aug, self.calib, self.name = aug, calib, name

    def _prep(self, t):
        return normalize(t) if self.norm else str(t)

    def _vec(self, Xn):
        blocks = [self.wv.transform(Xn)]
        if self.char:
            blocks.append(self.cv.transform(Xn))
        return hstack(blocks).tocsr()

    def _mix(self, X, Xn):
        pt = self.txt.predict_proba(self._vec(Xn))[:, 1]
        if self.feats_on:
            return 0.65 * pt + 0.35 * self.feat.predict_proba(featurize(X))[:, 1]
        return pt

    def fit(self, X, y):
        X, y = list(X), list(y)
        if self.aug:
            rng = random.Random(SEED)
            for t, l in list(zip(X, y)):
                if l == 1:
                    for _ in range(2):
                        X.append(augment(t, rng)); y.append(1)
        y = np.asarray(y)
        Xn = [self._prep(t) for t in X]
        self.wv = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2,
                                  max_features=20000, sublinear_tf=True).fit(Xn)
        if self.char:
            self.cv = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2,
                                      max_features=40000, sublinear_tf=True).fit(Xn)
        self.txt = LogisticRegression(max_iter=3000, C=10, class_weight="balanced").fit(self._vec(Xn), y)
        if self.feats_on:
            self.feat = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.12,
                                                       max_iter=200, random_state=SEED).fit(featurize(X), y)
        if self.calib:
            p = self._mix(X, Xn)
            self.cal = LogisticRegression(max_iter=1000).fit(p.reshape(-1, 1), y)
        return self

    def proba(self, X):
        X = list(X)
        if not self.norm:
            p = self._mix(X, [str(t) for t in X])
            return self.cal.predict_proba(p.reshape(-1, 1))[:, 1] if self.calib else p
        # Recall-preserving multi-view max: score each de-obfuscation view on its own and keep the
        # highest, so a long obfuscation (character-spacing) can't dilute a short recovered
        # instruction inside one concatenated string. Non-obfuscated text has only [base], so its
        # score is unchanged (no over-refusal cost). Views are flattened and scored in one batch.
        flat, owner = [], []
        for i, t in enumerate(X):
            for v in normalize_views(t):
                flat.append(v); owner.append(i)
        pv = self._mix(flat, flat)
        owner = np.asarray(owner)
        p = np.array([float(pv[owner == i].max()) if (owner == i).any() else 0.0
                      for i in range(len(X))])
        return self.cal.predict_proba(p.reshape(-1, 1))[:, 1] if self.calib else p
