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

    def proba_response(self, prompts, responses, batch_size=16):
        """P(unsafe) for each ASSISTANT RESPONSE given its prompt - the correct way to moderate
        an output. An llm_guard (e.g. Qwen3Guard) classifies the assistant turn of the
        [user, assistant] chat, so it judges whether the model COMPLIED with something harmful,
        not whether the text looks like a jailbreak. A classifier guard has no turn structure, so
        it falls back to scoring the response text alone. Use this (not proba) for L4 output
        moderation; a surface L1 jailbreak detector is the wrong signal here."""
        if not self._ready:
            self.load()
        responses = list(responses)
        prompts = list(prompts) if prompts is not None else [""] * len(responses)
        if len(prompts) != len(responses):                      # be forgiving about mismatch
            prompts = (prompts + [""] * len(responses))[:len(responses)]
        if self.mode == "classifier":
            return self.proba(responses, batch_size=batch_size)
        import torch
        scores = []
        for p, r in zip(prompts, responses):
            msgs = [{"role": "user", "content": str(p)}, {"role": "assistant", "content": str(r)}]
            try:
                text = self.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
            except Exception:
                text = f"User: {p}\nAssistant: {r}"
            enc = self.tok(text, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                gen = self.model.generate(**enc, max_new_tokens=16, do_sample=False,
                                          pad_token_id=self.tok.eos_token_id)
            verdict = self.tok.decode(gen[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            scores.append(1.0 if "unsafe" in verdict.lower() else 0.0)
        return np.array(scores)
