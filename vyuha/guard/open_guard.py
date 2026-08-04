"""
Vyuha L2 - wrappers around open guard models, used as strong baselines and as
ensemble members. Two modes:

  - "classifier": a small text-classification guard (default:
     protectai/deberta-v3-base-prompt-injection-v2) - fast, CPU/GPU.
  - "llm_guard":  an LLM safety guard (e.g. meta-llama/Llama-Guard-4, Qwen/Qwen3Guard)
     via its chat template; we parse the safe/unsafe verdict into a score.

Requires `transformers` (+ a GPU for the LLM guards). Import is lazy and degrades
gracefully so the rest of the harness runs without it.
"""
import numpy as np


class OpenGuard:
    def __init__(self, model_id="protectai/deberta-v3-base-prompt-injection-v2",
                 mode="classifier", device=None, unsafe_label_prefixes=("INJ", "JAIL", "LABEL_1", "UNSAFE")):
        self.model_id = model_id
        self.mode = mode
        self.device = device
        self.unsafe_prefixes = unsafe_label_prefixes
        self._ready = False

    def load(self):
        import torch
        from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                                   AutoModelForCausalLM, pipeline)
        dev = self.device if self.device is not None else (0 if torch.cuda.is_available() else -1)
        if self.mode == "classifier":
            self.pipe = pipeline("text-classification", model=self.model_id,
                                 truncation=True, max_length=512, device=dev)
        else:  # llm_guard
            self.tok = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, torch_dtype="auto",
                device_map="auto" if dev >= 0 else None)
        self._ready = True
        return self

    def _is_unsafe(self, label: str) -> int:
        return int(str(label).upper().startswith(self.unsafe_prefixes))

    def proba(self, texts, batch_size=16):
        """Return P(unsafe/attack) in [0,1] for each text."""
        if not self._ready:
            self.load()
        texts = list(texts)
        if self.mode == "classifier":
            out = self.pipe(texts, batch_size=batch_size)
            # score is confidence of the predicted label; convert to P(unsafe)
            return np.array([r["score"] if self._is_unsafe(r["label"]) else 1 - r["score"] for r in out])
        # llm_guard: ask the guard, read first token verdict
        import torch
        scores = []
        for t in texts:
            try:
                text = self.tok.apply_chat_template([{"role": "user", "content": t}],
                                                    add_generation_prompt=True, tokenize=False)
            except Exception:
                text = t
            enc = self.tok(text, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                gen = self.model.generate(**enc, max_new_tokens=16, do_sample=False,
                                          pad_token_id=self.tok.eos_token_id)
            verdict = self.tok.decode(gen[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            scores.append(1.0 if "unsafe" in verdict.lower() else 0.0)  # Qwen3Guard: Safe/Controversial/Unsafe
        return np.array(scores)
