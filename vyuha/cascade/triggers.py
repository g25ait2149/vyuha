"""Manipulation-aware escalation triggers (Preregistration_v4_FullStudy.md §3.2). Defined before any v4 data.

E1  noise trigger    : case_noise(text) >= 0.3                       (unchanged from the pilot)
E1b encoding trigger : (a) a decoding view of L0-v2 that reads as words, or
                       (b) a gibberish span (8-token window >= 40 chars with < 30% vocabulary words, or one
                           >= 40-char token without '/', '\\' or '.'), or
                       (c) an explicit decoding cue word.
L0 itself stays frozen at v2; E1b only READS its decoding views (de-leet / de-space views are ignored because
they fire on any digit or short token - pre-mortem M2).
"""
import re
from collections import Counter

from vyuha.normalize.normalize import case_noise, normalize_views

WORD_RE = re.compile(r"[a-z]+")
DECODE_TAGS = ('[decoded]', '[hex]', '[tags]', '[reversed]', '[rot13]')
# Cue = a decoding verb AND an instruction-following phrase in the same text (a bare word such as "binary" or
# "hex" is common in benign programming questions; tightened 8 Oct 2026 before any v4 data, see prereg §3.2).
CUE_VERB = re.compile(r"\b(decode|decipher|decrypt|reverse|unscramble|translate from)\b", re.I)
CUE_ACT = re.compile(r"\b(follow|execute|answer|respond to|carry out|do what|comply)\b", re.I)


def build_vocab(texts, min_count=3):
    """Lower-cased alphabetic tokens seen >= min_count times (built from screen-TRAINING prompts only)."""
    c = Counter(w for t in texts for w in WORD_RE.findall(str(t).lower()))
    return frozenset(w for w, n in c.items() if n >= min_count)


def _wordlike(tok, vocab):
    w = ''.join(WORD_RE.findall(tok.lower()))
    return bool(w) and w in vocab


def word_ratio(text, vocab):
    toks = [w for w in WORD_RE.findall(str(text).lower())]
    return (sum(w in vocab for w in toks) / len(toks)) if toks else 0.0, len(toks)


def noise_trigger(text):
    return case_noise(text) >= 0.3


def decode_view_fires(text, vocab):
    for v in normalize_views(text, version=2)[1:]:
        if v.startswith(DECODE_TAGS):
            body = v.split('] ', 1)[-1]
            r, n = word_ratio(body, vocab)
            if n >= 3 and r >= 0.5:
                return True
    return False


def gibberish_fires(text, vocab, win=8, min_chars=40, max_ratio=0.3):
    toks = str(text).split()
    for t in toks:
        if len(t) >= min_chars and not any(ch in t for ch in '/\\.'):
            return True
    if len(toks) < win:
        span = ' '.join(toks)
        if len(span) >= min_chars and toks:
            return sum(_wordlike(t, vocab) for t in toks) / len(toks) < max_ratio
        return False
    ok = [_wordlike(t, vocab) for t in toks]
    for i in range(len(toks) - win + 1):
        if len(' '.join(toks[i:i + win])) >= min_chars and sum(ok[i:i + win]) / win < max_ratio:
            return True
    return False


def cue_fires(text):
    t = str(text)
    return bool(CUE_VERB.search(t) and CUE_ACT.search(t))


def encoding_trigger(text, vocab):
    return decode_view_fires(text, vocab) or gibberish_fires(text, vocab) or cue_fires(text)


def trigger_flags(texts, vocab):
    """Per text: dict of booleans {noise, enc, enc_a, enc_b, enc_c}. Computed on the RAW text."""
    out = []
    for t in texts:
        a, b, c = decode_view_fires(t, vocab), gibberish_fires(t, vocab), cue_fires(t)
        out.append({'noise': noise_trigger(t), 'enc': a or b or c, 'enc_a': a, 'enc_b': b, 'enc_c': c})
    return out
