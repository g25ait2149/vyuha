"""
Vyuha L0 - language signal.

Multilingual attacks (a jailbreak written in Hindi/Spanish/Chinese) evade English-only
filters. This module tags the language/script so the pipeline can (a) route to the
multilingual semantic layer + multilingual guard, and (b) flag non-English content for
extra scrutiny. Uses `langdetect` if available, else a Unicode-script heuristic.
"""
import unicodedata

# Unicode script -> coarse language hint (heuristic fallback).
_SCRIPT_HINT = {
    "CYRILLIC": "ru", "DEVANAGARI": "hi", "ARABIC": "ar", "HEBREW": "he",
    "HANGUL": "ko", "HIRAGANA": "ja", "KATAKANA": "ja", "CJK": "zh",
    "THAI": "th", "GREEK": "el", "BENGALI": "bn", "TAMIL": "ta",
}


def dominant_script(text):
    counts = {}
    for ch in str(text)[:400]:
        if ch.isalpha():
            try:
                name = unicodedata.name(ch)
            except ValueError:
                continue
            key = next((k for k in _SCRIPT_HINT if k in name), "LATIN" if "LATIN" in name else "OTHER")
            counts[key] = counts.get(key, 0) + 1
    return max(counts, key=counts.get) if counts else "LATIN"


def detect_language(text):
    """Return a best-effort ISO-ish language code ('en','es','hi','zh',...)."""
    text = str(text)
    try:
        from langdetect import detect          # pip install langdetect
        return detect(text)
    except Exception:
        return _SCRIPT_HINT.get(dominant_script(text), "en")


def is_non_english(text):
    """True if the content is likely not English (non-Latin script or detected non-en)."""
    if dominant_script(text) != "LATIN":
        return True
    lang = detect_language(text)
    return lang not in ("en",)
