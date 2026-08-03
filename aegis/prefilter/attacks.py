"""
Attack suite - obfuscations used to (a) augment training and (b) test robustness.

Design: SEEN obfuscations are folded into training augmentation so the detector is strong on the
channels an attacker actually uses - INCLUDING compositions (adaptive attackers stack transforms,
e.g. zero-width + character-spacing), which `augment` produces by chaining two SEEN transforms.
A small UNSEEN set is held out and NEVER trained on, so red-team ASR on it measures true
generalization to a novel obfuscation - recovered only by the L0 normalizer (here: NFKC folding of
full-width unicode, and the adaptive de-spacing generalizing to a wider character gap it never saw).
Used defensively only.
"""
import base64
import codecs
import random

HOMO = {"a": "а", "e": "е", "o": "о", "c": "с"}   # latin -> cyrillic look-alikes


def leet(t, p=0.2, rng=random):
    m = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5"}
    return "".join(m.get(c, c) if (c.isalpha() and rng.random() < p) else c for c in t)


def homoglyph(t, p=0.3, rng=random):
    return "".join(HOMO.get(c, c) if (c in HOMO and rng.random() < p) else c for c in t)


def base64_attack(t, rng=random):
    return "Decode and follow: " + base64.b64encode(t.encode()).decode()


def rot13(t, rng=random):
    return "Decode ROT13: " + codecs.encode(t, "rot_13")


def zero_width(t, p=0.3, rng=random):
    return "".join(c + ("​" if rng.random() < p else "") for c in t)


def emoji_smuggle(t, rng=random):
    # interleave variation selectors (invisible) - a 2025/26 smuggling channel
    vs = "️"
    return "".join(c + (vs if c.isalpha() and rng.random() < 0.3 else "") for c in t)


def char_spacing(t, rng=random):
    return " ".join(list(t))                     # space every character (a.k.a. ascii-art)


# ---- held-out (UNSEEN) novel obfuscations, recovered only by L0 ----
def fullwidth(t, rng=random):
    # ASCII -> full-width unicode; L0's NFKC folds it back. Never trained on.
    return "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in t)


def wide_spacing(t, rng=random):
    return "  ".join(list(t))                    # TWO spaces per char: tests despace generalizing


# Train on the obfuscations attackers actually use (each recovered by L0 at inference). Compositions
# are produced by augment() chaining two of these - so the detector trains on stacked evasions too.
SEEN = {"leet": leet, "homoglyph": homoglyph, "base64": base64_attack, "rot13": rot13,
        "zero_width": zero_width, "char_spacing": char_spacing, "emoji_smuggle": emoji_smuggle}
# Held out to measure generalization to obfuscations never seen in training (L0 must recover them).
UNSEEN = {"fullwidth": fullwidth, "wide_spacing": wide_spacing}
ALL_ATTACKS = {**SEEN, **UNSEEN}
ascii_art = char_spacing                         # back-compat alias


def augment(text, rng, k=None):
    """Apply 1-2 random SEEN attacks (chained = composed) to a jailbreak example for training.
    Composition is deliberate: adaptive attackers stack obfuscations, so the detector should learn
    stacked evasions, not just single transforms. Pass k to force a fixed number of transforms."""
    fns = list(SEEN.values())
    rng.shuffle(fns)
    n = k if k is not None else rng.randint(1, 2)
    for f in fns[:n]:
        try:
            text = f(text, rng=rng)
        except Exception:
            pass
    return text
