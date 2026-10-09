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


BLOB_RE = re.compile(r"[A-Za-z0-9+/=]{40,}")        # base64 / base85-alnum / hex run, no code punctuation


def gibberish_fires(text, vocab=None, min_chars=40):
    """Fire on an ENCODED BLOB, not merely on non-English text (reformulated 2026-10-09; the old 'low
    dictionary-ratio window' rule fired on code and non-English prose - 11.7% of benign WildChat).

    (b1) a contiguous base64/hex-like run >= 40 chars that mixes case or carries >=4 digits or is >= 60 chars
         (real ciphertext of a non-trivial payload; a plain long word or snake_case identifier does not match);
    (b2) the whole text (>= 30 non-space chars) dominated by a tiny cipher alphabet: Morse ({.-}) or binary ({01}).
    Code is excluded because it contains (){}[]<>;:= etc. and rarely forms a 40-char pure-alnum run."""
    s = str(text)
    for m in BLOB_RE.findall(s):
        has_digit = sum(c.isdigit() for c in m) >= 4
        mixed = any(c.islower() for c in m) and any(c.isupper() for c in m)
        if has_digit or mixed or len(m) >= 60:
            return True
    nz = [c for c in s if not c.isspace()]
    if len(nz) >= 30:
        morse = sum(c in '.-' for c in nz) / len(nz)
        binr = sum(c in '01' for c in nz) / len(nz)
        if morse >= 0.9 or binr >= 0.9:
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
