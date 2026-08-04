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
    def __init__(self, path="aegis_guard", base_model=None, max_len=256, device_map="auto"):
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
    """Combine fitted/loaded detectors (each exposing .proba) by 'max' or 'mean'."""
    def __init__(self, members, mode="max", weights=None):
        self.members = members
        self.mode = mode
        self.weights = weights

    def proba(self, X):
        P = np.vstack([np.asarray(m.proba(X), dtype=float) for m in self.members])
        if self.mode == "mean":
            return np.average(P, axis=0, weights=self.weights)
        return P.max(axis=0)        # ANY-flag: high recall for high-stakes use
