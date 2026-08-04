"""
Vyuha L4 (P5) - system-prompt / canary leak detection.

Catches the model regurgitating its hidden system prompt or a planted canary token.
Two signals:
  1. exact canary match - plant a random token in the system prompt; if it ever appears
     in an output the prompt has leaked (zero false positives).
  2. n-gram overlap between the response and the protected system prompt - a fuzzy leak
     signal that fires even when the prompt is reworded or partially quoted.
"""
import re


def _norm(s):
    return re.sub(r"\s+", " ", str(s).lower()).strip()


def _ngrams(s, n=5):
    toks = _norm(s).split()
    return {" ".join(toks[i:i + n]) for i in range(max(0, len(toks) - n + 1))}


class SystemPromptLeakDetector:
    def __init__(self, system_prompt="", canary=None, n=5, overlap_block=0.18):
        self.system_prompt = system_prompt
        self.canary = canary
        self.n = n
        self.overlap_block = overlap_block
        self._sys_ngrams = _ngrams(system_prompt, n) if system_prompt else set()

    def scan(self, response):
        response = str(response)
        canary_hit = bool(self.canary) and self.canary in response
        overlap = 0.0
        if self._sys_ngrams:
            inter = self._sys_ngrams & _ngrams(response, self.n)
            overlap = len(inter) / max(1, len(self._sys_ngrams))
        leaked = canary_hit or overlap >= self.overlap_block
        score = 1.0 if canary_hit else round(min(1.0, overlap / max(self.overlap_block, 1e-6)), 3)
        return {"leaked": leaked, "canary_hit": canary_hit,
                "system_overlap": round(overlap, 3), "score": score}
