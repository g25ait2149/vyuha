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
import re
import numpy as np

_UNSAFE_FIRST = ("yes", "unsafe", "harmful", "true", "risky")
_SAFE_FIRST = ("no", "safe", "false")


def _verdict_unsafe(verdict):
    """Map a guard's short generated verdict to unsafe=1.0 / safe=0.0 across output styles:
    Qwen3Guard 'Safe/Controversial/Unsafe', Granite Guardian 'Yes/No' (Yes = unsafe), Llama Guard
    'safe/unsafe'. Strips any <think>...</think> reasoning first, then reads the first answer token."""
    v = re.sub(r"<think>.*?</think>", " ", str(verdict), flags=re.S | re.I).strip().lower()
    if not v:
        return 0.0
    first = v.split()[0].strip(".,:;\"'*`-")
    if first in _UNSAFE_FIRST:
        return 1.0
    if first in _SAFE_FIRST:
        return 0.0
    return 1.0 if ("unsafe" in v or "harmful" in v) else 0.0

# Recommended NON-OVERLAPPING guard members for the L2 ensemble (each brings a different strength).
# Model ids verified on the Hugging Face Hub (Aug 2026); pin an exact revision before a real run.
GUARD_PRESETS = {
    # fast prompt-injection classifier (CPU/GPU) - the injection axis
    "deberta-injection": {"model_id": "protectai/deberta-v3-base-prompt-injection-v2", "mode": "classifier"},
    # IBM Granite Guardian - reportedly strong on prompt injection; small MoE fits a free T4
    "granite-guardian": {"model_id": "ibm-granite/granite-guardian-3.2-3b-a800m", "mode": "llm_guard"},
    "granite-guardian-4": {"model_id": "ibm-granite/granite-guardian-4.1-8b", "mode": "llm_guard"},
    # LLM safety guards - the harmful-content / policy axis
    "llama-guard": {"model_id": "meta-llama/Llama-Guard-3-8B", "mode": "llm_guard"},
    "qwen3guard": {"model_id": "Qwen/Qwen3Guard-Gen-0.6B", "mode": "llm_guard"},
}


class OpenGuard:
    def __init__(self, model_id="protectai/deberta-v3-base-prompt-injection-v2",
                 mode="classifier", device=None, unsafe_label_prefixes=("INJ", "JAIL", "LABEL_1", "UNSAFE"),
                 load_in_4bit=True):
        self.model_id = model_id
        self.mode = mode
        self.device = device
        self.unsafe_prefixes = unsafe_label_prefixes
        # 4-bit quantise llm_guard weights on GPU so a 3B guard (e.g. Granite) fits a 16GB T4 without
        # the silent OOM that kills the kernel mid-scoring. No effect on the classifier path.
        self.load_in_4bit = load_in_4bit
        self.name = model_id.split("/")[-1]
        self._ready = False

    @classmethod
    def preset(cls, name, **overrides):
        """Build an OpenGuard from a named GUARD_PRESETS entry (e.g. 'granite-guardian')."""
        cfg = dict(GUARD_PRESETS[name]); cfg.update(overrides)
        g = cls(**cfg); g.name = name
        return g

    def unload(self):
        """Free the model from (GPU) memory so an ensemble can score one guard at a time without
        co-loading two models on a small GPU. Safe to call even if not loaded."""
        import gc
        for attr in ("model", "pipe", "tok"):
            try:
                delattr(self, attr)
            except Exception:
                pass
        self._ready = False
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        return self

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
            kw = dict(torch_dtype="auto", device_map="auto" if dev >= 0 else None)
            if dev >= 0 and self.load_in_4bit:   # quantise on GPU to fit a 3B guard on a 16GB T4
                try:
                    import bitsandbytes  # noqa: F401 - presence check
                    from transformers import BitsAndBytesConfig
                    kw["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True, bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
                    kw.pop("torch_dtype", None)
                    kw["device_map"] = {"": dev}   # keep the whole ~2GB 4-bit model on ONE GPU
                except Exception as e:                 # (multi-GPU 'auto' splits it, adding overhead)
                    print(f"[OpenGuard] 4-bit unavailable ({e}); loading {self.name} in fp16")
            self.model = AutoModelForCausalLM.from_pretrained(self.model_id, **kw)
            # decoder-only batched generation needs left padding + a pad token
            if self.tok.pad_token_id is None:
                self.tok.pad_token = self.tok.eos_token
            self.tok.padding_side = "left"
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
        # llm_guard: ask the guard, read the verdict tokens. BATCHED - one generate() per prompt is the
        # throughput killer (~1.6k sequential calls = hours); batching with left-padding is 10-30x faster.
        import torch
        tok = self.tok
        prompts = []
        for t in texts:
            try:
                prompts.append(tok.apply_chat_template([{"role": "user", "content": t}],
                                                       add_generation_prompt=True, tokenize=False))
            except Exception:
                prompts.append(t)
        idxs = range(0, len(prompts), batch_size)
        if len(prompts) > batch_size:
            try:
                from tqdm.auto import tqdm
                idxs = tqdm(list(idxs), desc=f"{self.name} scoring", unit="batch")
            except Exception:
                pass
        scores = []
        for i in idxs:
            batch = prompts[i:i + batch_size]
            enc = tok(batch, return_tensors="pt", padding=True, truncation=True,
                      max_length=1024).to(self.model.device)
            with torch.no_grad():
                gen = self.model.generate(**enc, max_new_tokens=16, do_sample=False,
                                          pad_token_id=tok.pad_token_id)
            new = gen[:, enc["input_ids"].shape[1]:]     # left-padded -> new tokens align per row
            for row in new:
                verdict = tok.decode(row, skip_special_tokens=True)
                scores.append(_verdict_unsafe(verdict))  # Qwen 'Unsafe', Granite 'Yes', Llama 'unsafe'
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
        _pairs = list(zip(prompts, responses))
        if len(_pairs) > 20:
            try:
                from tqdm.auto import tqdm
                _pairs = tqdm(_pairs, desc=f"{self.name} scoring", unit="pair")
            except Exception:
                pass
        for p, r in _pairs:
            msgs = [{"role": "user", "content": str(p)}, {"role": "assistant", "content": str(r)}]
            try:
                text = self.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
            except Exception:
                text = f"User: {p}\nAssistant: {r}"
            enc = self.tok(text, return_tensors="pt", truncation=True, max_length=1024).to(self.model.device)
            with torch.no_grad():
                gen = self.model.generate(**enc, max_new_tokens=16, do_sample=False,
                                          pad_token_id=self.tok.eos_token_id)
            verdict = self.tok.decode(gen[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            scores.append(_verdict_unsafe(verdict))   # response-side: same guard-agnostic parse
        return np.array(scores)
