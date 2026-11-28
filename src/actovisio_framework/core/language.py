"""Lightweight language detection for article text.

This is a deliberately dependency-free heuristic: it counts hits against
small sets of high-frequency function words (stopwords) per language and
picks the language with more hits. It currently distinguishes Turkish and
English; anything else falls back to ``fallback_lang``. For finer-grained
detection, callers can swap in a dedicated library and pass the result
through ``fallback_lang`` / profile language overrides.
"""

import re

TURKISH_MARKERS = {
    "bir", "ve", "için", "ile", "bu", "ama", "gibi", "daha", "çok",
    "ne", "nasıl", "neden", "olarak", "olan", "sonra", "önce", "kadar",
    "her", "veya", "çünkü", "değil", "var", "yok", "gerekir", "olur",
}

ENGLISH_MARKERS = {
    "the", "and", "for", "with", "this", "that", "from", "are", "was",
    "were", "has", "have", "had", "not", "but", "you", "your", "they",
    "will", "can", "more", "when", "which", "about", "into", "than",
}


def detect_language(text: str, fallback_lang: str = "en") -> str:
    """
    Detects language (tr or en) based on stopword marker counts.
    If markers are equal or no markers are matched, falls back to fallback_lang.
    """
    if not text:
        return fallback_lang

    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    tr_count = len(words & TURKISH_MARKERS)
    en_count = len(words & ENGLISH_MARKERS)

    if tr_count > en_count:
        return "tr"
    elif en_count > tr_count:
        return "en"

    return fallback_lang
