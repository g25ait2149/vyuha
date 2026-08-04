"""
Vyuha L4 (P5) - secret / credential leak scanner.

High-signal regexes for the API keys, tokens and private keys that the gitleaks /
trufflehog / detect-secrets rule families look for, plus a Shannon-entropy fallback for
generic high-entropy secrets. Runs on model OUTPUT to stop credential exfiltration (a top
agentic-AI risk). `scan` returns findings with spans; `redact` masks them.
"""
import math
import re
from collections import Counter

RULES = {
    "AWS_ACCESS_KEY": r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA)[0-9A-Z]{16}\b",
    "GITHUB_TOKEN": r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b",
    "OPENAI_KEY": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
    "ANTHROPIC_KEY": r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
    "SLACK_TOKEN": r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
    "GOOGLE_API_KEY": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "PRIVATE_KEY": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----",
    "JWT": r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b",
    "AWS_SECRET": r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})",
    "BEARER": r"(?i)\b(?:authorization|bearer)\b\s*[:=]?\s*['\"]?[A-Za-z0-9._-]{20,}",
}


def shannon_entropy(s):
    if not s:
        return 0.0
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in Counter(s).values())


class SecretScanner:
    def __init__(self, entropy_threshold=4.0, min_entropy_len=24):
        self._compiled = {k: re.compile(v) for k, v in RULES.items()}
        self.entropy_threshold = entropy_threshold
        self.min_entropy_len = min_entropy_len

    def scan(self, text, entropy=True):
        text = str(text)
        found = []
        for typ, rx in self._compiled.items():
            for m in rx.finditer(text):
                found.append({"type": typ, "start": m.start(), "end": m.end(),
                              "value": m.group(), "score": 0.95})
        if entropy:
            for m in re.finditer(r"[A-Za-z0-9/+=_-]{%d,}" % self.min_entropy_len, text):
                if any(f["start"] <= m.start() < f["end"] for f in found):
                    continue
                if shannon_entropy(m.group()) >= self.entropy_threshold:
                    found.append({"type": "HIGH_ENTROPY", "start": m.start(),
                                  "end": m.end(), "value": m.group(), "score": 0.5})
        return found

    def redact(self, text, mask="[REDACTED:{t}]"):
        text = str(text)
        for f in sorted(self.scan(text), key=lambda f: f["start"], reverse=True):
            text = text[:f["start"]] + mask.format(t=f["type"]) + text[f["end"]:]
        return text

    def has_secret(self, text, entropy=False):
        return len(self.scan(text, entropy=entropy)) > 0
