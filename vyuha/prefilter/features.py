"""Vyuha L1 - engineered tamper features (13 signals)."""
import re
import math
import numpy as np
from ..normalize.normalize import ZERO_WIDTH, B64_RE

OVERRIDE = re.compile(r"\b(ignore|disregard|forget|bypass)\b.{0,30}\b(previous|all|instruction|rule)", re.I)
DEVMODE = re.compile(r"\b(developer mode|do anything now|DAN|jailbreak|sudo)\b", re.I)
REFUSAL = re.compile(r"\b(never refuse|no restrictions|unfiltered|uncensored)\b", re.I)


def featurize(texts):
    """Return an (n, 13) float array of tamper/attack signals for each text."""
    rows = []
    for t in texts:
        t = str(t)
        n = len(t) or 1
        b64 = B64_RE.findall(t)
        rows.append([
            len(t.split()),                                         # word count
            math.log1p(len(t)),                                     # log length
            sum(ord(c) > 127 for c in t) / n,                       # non-ASCII ratio
            sum(c.isdigit() for c in t) / n,                        # digit ratio
            sum((not c.isalnum() and not c.isspace()) for c in t) / n,  # punct ratio
            len(b64),                                               # base64-run count
            max([len(x) for x in b64] + [0]),                       # longest base64 run
            len(OVERRIDE.findall(t)),                               # instruction-override hits
            len(DEVMODE.findall(t)),                                # dev-mode / DAN hits
            len(REFUSAL.findall(t)),                                # refusal-suppression hits
            t.count(" ") / n,                                       # space ratio
            len(set(t)) / n,                                        # char diversity
            sum(c in ZERO_WIDTH for c in t),                        # zero-width count
        ])
    return np.array(rows, dtype=float)
