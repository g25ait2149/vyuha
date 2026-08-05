"""
Vyuha L2 (P3) - load the fine-tuned guard and ensemble guards.

  - TunedGuard   : loads our LoRA adapter (from train_guard / the HF Hub) and returns
                   P(unsafe) per prompt.
  - GuardEnsemble: combines several detectors (TunedGuard, OpenGuard, FastLayer) by
                   max ("ANY-flag", high recall) or mean. The 2026 best-practice is to
                   ensemble models with non-overlapping strengths.

Heavy deps (torch/transformers/peft) are imported lazily so this module is cheap to
import and the rest of Vyuha runs without a GPU.
"""
import numpy as np
from ..normalize.normalize import normalize


class TunedGuard:
    def __init__(self, path="vyuha_guard", base_model=None, max_len=256, device_map="auto"):
        self.path = path
        self.base_model = base_model
        self.max_len = max_len
        self.device_map = device_map
        self._ready = False

    def load(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        from peft import PeftModel, PeftConfig
        cfg = PeftConfig.from_pretrained(self.path)
        base = self.base_model or cfg.base_model_name_or_path
        self.tok = AutoTokenizer.from_pretrained(self.path)
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        m = AutoModelForSequenceClassification.from_pretrained(
            base, num_labels=2, torch_dtype=torch.float16, device_map=self.device_map)
        m.config.pad_token_id = self.tok.pad_token_id
        self.model = PeftModel.from_pretrained(m, self.path).eval()
        self._torch = torch
        self._ready = True
        return self

    def proba(self, texts, batch_size=16):
        if not self._ready:
            self.load()
        torch = self._torch
        texts = [normalize(t, full=True) for t in list(texts)]
        out = []
        for i in range(0, len(texts), batch_size):
            enc = self.tok(texts[i:i + batch_size], truncation=True, max_length=self.max_len,
                           padding=True, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                logits = self.model(**enc).logits
            out.append(torch.softmax(logits, -1)[:, 1].float().cpu().numpy())
        return np.concatenate(out) if out else np.array([])


class GuardEnsemble:
    """Combine fitted/loaded detectors (each exposing .proba) by 'max' or 'mean'.

    The 2026 best practice is to ensemble guards with *non-overlapping* strengths (e.g. a fast
    injection classifier + an LLM safety guard + a reasoning/multilingual guard) so the union
    catches what any one misses. `mode='max'` is the recall-preserving ANY-flag union.

    Beyond scoring, this class can *measure the value of adding a guard*: `fit_thresholds` pins
    each member to a low benign FPR, and `report` shows each member's standalone recall/FPR, the
    ensemble's, and the **marginal recall** each member uniquely contributes (attacks the union
    catches that every other member misses) - the evidence that a member is genuinely
    non-overlapping rather than redundant.

        ens = GuardEnsemble({"rjd2": fast, "granite": granite_guard})   # named members
        ens.report(X, y, target_fpr=0.01)   # -> per-member + ensemble recall/FPR + marginal recall
    """
    def __init__(self, members, mode="max", weights=None, names=None):
        # members may be a list of guards OR a dict {name: guard}
        if isinstance(members, dict):
            self.names = list(members.keys())
            self.members = list(members.values())
        else:
            self.members = list(members)
            self.names = list(names) if names is not None else \
                [getattr(m, "name", None) or type(m).__name__ + (f"#{i}" if names is None else "")
                 for i, m in enumerate(self.members)]
        self.mode = mode
        self.weights = weights
        self.thresholds = {n: 0.5 for n in self.names}   # per-member decision thresholds

    def proba_matrix(self, X):
        """Per-member P(attack): {name: np.array}."""
        return {n: np.asarray(m.proba(X), dtype=float) for n, m in zip(self.names, self.members)}

    def proba(self, X):
        P = np.vstack([np.asarray(m.proba(X), dtype=float) for m in self.members])
        if self.mode == "mean":
            return np.average(P, axis=0, weights=self.weights)
        return P.max(axis=0)        # ANY-flag: high recall for high-stakes use

    def fit_thresholds(self, benign_X, target_fpr=0.01):
        """Set each member's threshold at the (1 - target_fpr) quantile of its benign scores, so
        every member operates at ~target_fpr false-positive rate and the union FPR stays bounded."""
        for n, s in self.proba_matrix(benign_X).items():
            self.thresholds[n] = float(np.quantile(s, 1 - target_fpr)) if len(s) else 0.5
        return self

    def predict(self, X):
        """Union OR at per-member thresholds (recall-preserving). A member fires when its score is
        strictly above its fitted threshold, which keeps each member at-or-under its FPR budget
        (and avoids an all-ties threshold flagging everything). Returns an int flag array."""
        M = self.proba_matrix(X)
        return np.vstack([(M[n] > self.thresholds[n]).astype(int) for n in self.names]).max(axis=0)

    def report(self, X, y, target_fpr=None):
        """Complementarity report: standalone recall/FPR per member, the ensemble's, and the
        marginal recall each member uniquely adds. If target_fpr is given, thresholds are (re)fit
        on the benign subset of X first."""
        y = np.asarray([int(v) for v in y])
        if target_fpr is not None:
            benign = [x for x, l in zip(X, y) if not l]
            self.fit_thresholds(benign, target_fpr)
        M = self.proba_matrix(X)
        pos, neg = y == 1, y == 0

        def rc_fpr(flag):
            rec = float(flag[pos].mean()) if pos.any() else 0.0
            fpr = float(flag[neg].mean()) if neg.any() else 0.0
            return round(rec, 3), round(fpr, 3)

        flags, members = {}, {}
        for n in self.names:
            f = (M[n] > self.thresholds[n]).astype(int)
            flags[n] = f
            rec, fpr = rc_fpr(f)
            members[n] = {"recall": rec, "fpr": fpr, "threshold": round(self.thresholds[n], 3)}
        ens = np.vstack([flags[n] for n in self.names]).max(axis=0)
        erec, efpr = rc_fpr(ens)
        marginal = {}
        for n in self.names:
            others = [flags[o] for o in self.names if o != n]
            others_flag = np.vstack(others).max(axis=0) if others else np.zeros_like(ens)
            gained = int(((ens == 1) & (others_flag == 0) & pos).sum())   # caught only because of n
            marginal[n] = {"unique_attacks_caught": gained,
                           "recall_added": round(gained / max(int(pos.sum()), 1), 3)}
        return {"ensemble": {"recall": erec, "fpr": efpr, "mode": "union@thresholds"},
                "members": members, "marginal": marginal,
                "n_pos": int(pos.sum()), "n_neg": int(neg.sum())}
