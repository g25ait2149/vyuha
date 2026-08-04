"""
Vyuha L1 - semantic (embedding) detector.

Scores a prompt by its maximum cosine similarity to a database of KNOWN attacks -
catches novel-but-similar attacks (paraphrases, reworded jailbreaks) the exact/keyword
filters miss.

Backends:
  - "st"    : sentence-transformers. Use `multilingual=True` to load a multilingual
              model so a translated jailbreak lands near its English twin in embedding
              space (the multilingual-attack defense).
  - "tfidf" : char+word TF-IDF nearest-neighbour - no downloads; char n-grams give some
              cross-script signal; used as the offline fallback.
`backend="auto"` uses sentence-transformers if importable, else TF-IDF.
"""
import numpy as np
from sklearn.preprocessing import normalize as l2norm
from sklearn.feature_extraction.text import TfidfVectorizer
from ..normalize.normalize import normalize

ENGLISH_MODEL = "BAAI/bge-small-en-v1.5"
MULTILINGUAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SemanticDetector:
    def __init__(self, backend="auto", model_id=None, multilingual=False):
        self.backend = backend
        self.multilingual = multilingual
        self.model_id = model_id or (MULTILINGUAL_MODEL if multilingual else ENGLISH_MODEL)
        self._mode = None

    def _prep(self, texts):
        return [normalize(str(t), full=False) for t in texts]

    def _try_st(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_id)
            return True
        except Exception:
            return False

    def fit(self, X, y):
        X, y = list(X), list(y)
        attacks = [t for t, l in zip(X, y) if int(l) == 1] or X
        prepped = self._prep(attacks)
        use_st = (self.backend == "st") or (self.backend == "auto" and self._try_st())
        if use_st and getattr(self, "model", None) is not None:
            self._mode = "st"
            self.bank = np.asarray(self.model.encode(prepped, normalize_embeddings=True))
        else:
            self._mode = "tfidf"
            self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True).fit(self._prep(X))
            self.bank = l2norm(self.vec.transform(prepped))
        return self

    def similarity(self, X):
        prepped = self._prep(X)
        if self._mode == "st":
            emb = np.asarray(self.model.encode(prepped, normalize_embeddings=True))
            sims = emb @ self.bank.T
        else:
            q = l2norm(self.vec.transform(prepped))
            sims = (q @ self.bank.T).toarray()
        return np.clip(sims.max(axis=1), 0.0, 1.0)

    def proba(self, X):
        return self.similarity(X)
