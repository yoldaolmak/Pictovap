import re
from typing import Optional

TURKISH_MARKERS = {
    "bir", "ve", "için", "ile", "kahve", "seçimi", "nasıl", "ekipman", 
    "demleme", "çekirdek", "su", "öğütme", "gerekir", "kullanılır", 
    "nerede", "gezilecek", "lezzet", "fiyat", "rota"
}

ENGLISH_MARKERS = {
    "the", "and", "for", "with", "guide", "how", "travel", "coffee", 
    "equipment", "section", "local", "route", "food", "recipe", "place", "city"
}

def detect_language(text: str, fallback_lang: str = "en") -> str:
    """
    Detects language (tr or en) based on word count markers.
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
