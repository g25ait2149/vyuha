"""
Aegis L3 (P4) - indirect prompt-injection scanner for untrusted content.

Indirect injection hides *instructions to the assistant* inside data an agent reads
(retrieved web pages, emails, tool outputs, MCP tool descriptions). Unlike a jailbreak,
the giveaway is an imperative aimed at the model + exfiltration/override language.

`scan(content)`  -> verdict + which rules fired (+ optional ML detector signal).
`sanitize(content)` -> the content with injected-instruction sentences stripped
                       (the "CommandSans" surgical-sanitization pattern), so the agent
                       can still use the benign data without obeying the injection.
"""
import re
import numpy as np

from ..normalize.normalize import normalize

# High-precision indirect-injection signals.
RULES = {
    "override":   re.compile(r"\b(ignore|disregard|forget|override|bypass)\b.{0,40}\b(previous|prior|above|earlier|all|the)\b.{0,20}\b(instruction|prompt|rule|message|system)", re.I),
    "directive":  re.compile(r"\b(you (must|should|are now|will now|are required)|now (send|forward|delete|transfer|execute|reply|email)|instead,? (do|send|reply))\b", re.I),
    "exfil":      re.compile(r"\b(send|forward|email|transfer|wire|post|upload|leak|share|exfiltrate|cc)\b.{0,40}(@|http|to\s+\w+@|attacker|external)", re.I),
    "secret":     re.compile(r"\b(api[_-]?key|password|credential|access[_-]?token|secret|ssh key|private key)\b", re.I),
    "syscue":     re.compile(r"(system\s*prompt|as an ai|assistant\s*:|\[/?INST\]|<\|im_start\|>|###\s*instruction)", re.I),
    "tool":       re.compile(r"(<tool_call|function_call|\bsudo\b|\brm\s+-rf\b|os\.system|subprocess|eval\()", re.I),
}
WEIGHT = {"override": 0.95, "directive": 0.7, "exfil": 0.95, "secret": 0.6, "syscue": 0.8, "tool": 0.85}
_SENT = re.compile(r"(?<=[.!?\n])\s+")


class InjectionScanner:
    def __init__(self, detector=None, threshold=0.5, normalize_content=True):
        self.detector = detector            # optional Aegis FastLayer / guard (has .proba)
        self.threshold = threshold
        self.normalize_content = normalize_content   # de-obfuscate before the rules (L0)

    def scan(self, content):
        content = str(content)
        # de-obfuscate first so a Base64 / homoglyph / char-spaced injection is scored in
        # readable form; the multi-view normalize() output exposes the recovered instruction.
        text = normalize(content, full=True) if self.normalize_content else content
        fired = {k: bool(rx.search(text)) for k, rx in RULES.items()}
        rule_score = max([WEIGHT[k] for k, v in fired.items() if v] + [0.0])
        ml = float(self.detector.proba([content])[0]) if self.detector is not None else 0.0
        score = max(rule_score, ml)
        return {"is_injection": score >= self.threshold, "score": round(score, 3),
                "rules": [k for k, v in fired.items() if v], "ml": round(ml, 3)}

    def sanitize(self, content):
        """Drop sentences that look like injected instructions; keep benign data."""
        content = str(content)
        keep = []
        for s in _SENT.split(content):
            if any(rx.search(s) for k, rx in RULES.items() if k in ("override", "directive", "exfil", "syscue", "tool")):
                continue
            keep.append(s)
        return " ".join(keep).strip()
