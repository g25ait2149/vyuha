"""
Vyuha L4 (P5) - response-safety moderation.

Decides whether a model RESPONSE is a safe refusal or a harmful compliance - the
"response classification" mode of guard models like Llama Guard, which judge the
(prompt, response) pair rather than just the prompt. Combines:
  - refusal detection (did the model decline? -> safe), and
  - harmful-content scoring of the response via any guard exposing .proba (TunedGuard,
    GuardEnsemble, or even FastLayer) with a keyword-cue fallback when no guard is given.

A jailbreak only truly "succeeds" if the input was an attack AND the response complied;
this is the last gate that catches that even when the input filter was bypassed.
"""
import re

REFUSALS = [
    r"\bi can('?t|not)\b", r"\bi'?m (sorry|unable|not able)\b", r"\bi won'?t\b",
    r"\bcannot (help|assist|comply|provide|create)\b", r"\bi am not able to\b",
    r"\bas an ai\b", r"\bi (must|have to) decline\b", r"\bnot able to help\b",
    r"\bcan'?t (help|assist|provide|comply)\b", r"\bunable to (help|assist|provide)\b",
    r"\bi'?m not going to\b", r"\bthat'?s not something i can\b", r"\bi will not\b",
]
HARM_CUES = [
    r"\bstep 1\b", r"\bhere'?s how\b", r"\bingredients?\b", r"\byou(?:'?ll| will) need\b",
    r"\bfirst,?\s+(?:you|mix|obtain|acquire|gather)\b", r"\bmix\b.{0,40}\bwith\b",
    r"\bsynthesi[sz]e\b", r"\bdetonat", r"\bprecursor",
]


class ResponseModerator:
    def __init__(self, guard=None, block_at=0.7):
        self.guard = guard            # anything with .proba(list)->P(unsafe)
        self.block_at = block_at
        self._ref = [re.compile(p, re.I) for p in REFUSALS]
        self._harm = [re.compile(p, re.I) for p in HARM_CUES]

    def is_refusal(self, response):
        r = str(response)
        return bool(any(p.search(r) for p in self._ref)) and len(r) < 1200

    def harm_score(self, response):
        if self.guard is not None:
            try:
                return float(self.guard.proba([str(response)])[0])
            except Exception:
                pass
        cues = sum(bool(p.search(str(response))) for p in self._harm)
        return min(1.0, 0.3 * cues)

    def moderate(self, response, prompt=None):
        refusal = self.is_refusal(response)
        harm = 0.0 if refusal else self.harm_score(response)
        unsafe = (not refusal) and harm >= self.block_at
        return {"refusal": refusal, "harm_score": round(harm, 3),
                "unsafe": unsafe, "decision": "block" if unsafe else "allow"}
