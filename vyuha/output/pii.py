"""
Vyuha L4 (P5) - PII scanner.

Regex + checksum detection of personal data in model OUTPUT (and in tool results before
they re-enter the model), mirroring Microsoft Presidio's predefined recognizers but
dependency-free so it runs on a bare Kaggle box. `scan` returns typed findings with
character spans; `redact` masks them. If `presidio-analyzer` is installed, pass
`use_presidio=True` to defer to it for NER-backed recall.

Patterns are intentionally conservative (e.g. credit cards are Luhn-validated) to keep
false positives low on ordinary prose.
"""
import re

PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "PHONE": r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)",
    "SSN": r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]?){13,19}\b",
    "IPV4": r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b",
    "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
}


def _luhn_ok(s):
    digits = [int(c) for c in re.sub(r"\D", "", s)]
    if not 13 <= len(digits) <= 19:
        return False
    chk = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        chk += d
    return chk % 10 == 0


class PIIScanner:
    def __init__(self, use_presidio=False):
        self.use_presidio = use_presidio
        self._compiled = {k: re.compile(v) for k, v in PATTERNS.items()}
        self._an = None
        if use_presidio:
            try:
                from presidio_analyzer import AnalyzerEngine
                self._an = AnalyzerEngine()
            except Exception:
                self._an = None

    def scan(self, text):
        text = str(text)
        if self._an is not None:
            return [{"type": r.entity_type, "start": r.start, "end": r.end,
                     "value": text[r.start:r.end], "score": float(r.score)}
                    for r in self._an.analyze(text=text, language="en")]
        found = []
        for typ, rx in self._compiled.items():
            for m in rx.finditer(text):
                if typ == "CREDIT_CARD" and not _luhn_ok(m.group()):
                    continue
                found.append({"type": typ, "start": m.start(), "end": m.end(),
                              "value": m.group(), "score": 0.85})
        return found

    def redact(self, text, mask="[REDACTED:{t}]"):
        text = str(text)
        for f in sorted(self.scan(text), key=lambda f: f["start"], reverse=True):
            text = text[:f["start"]] + mask.format(t=f["type"]) + text[f["end"]:]
        return text

    def has_pii(self, text):
        return len(self.scan(text)) > 0
