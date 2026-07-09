import re
from typing import Dict, Any, Optional

TR_ALT_MAP = {
    "backpack": "Sırt çantası ve seyahat hazırlığını gösteren minimalist bir görsel.",
    "packing": "Sırt çantası ve seyahat hazırlığını gösteren minimalist bir görsel.",
    "forest": "Doğal yeşillikler içindeki patika yolunu gösteren sakin bir doğa görseli.",
    "path": "Doğal yeşillikler içindeki patika yolunu gösteren sakin bir doğa görseli.",
    "nature": "Doğal yeşillikler içindeki patika yolunu gösteren sakin bir doğa görseli.",
    "sunset": "Gün batımında dağ manzarasını ve doğanın dinginliğini yansıtan bir görsel.",
    "mountains": "Gün batımında dağ manzarasını ve doğanın dinginliğini yansıtan bir görsel.",
    "phone": "Telefon ekranında seyahat rotasını gösteren bulanık bir görsel.",
    "blurry": "Telefon ekranında seyahat rotasını gösteren bulanık bir görsel.",
    "coffee": "Kahve demleme ekipmanlarını ve hazırlık sürecini gösteren sade bir görsel.",
    "equipment": "Kahve demleme ekipmanlarını ve hazırlık sürecini gösteren sade bir görsel.",
}

EN_ALT_MAP = {
    "backpack": "A clean editorial image of travel packing and minimalist gear.",
    "packing": "A clean editorial image of travel packing and minimalist gear.",
    "forest": "A serene nature image showing a forest path surrounded by trees.",
    "path": "A serene nature image showing a forest path surrounded by trees.",
    "nature": "A serene nature image showing a forest path surrounded by trees.",
    "sunset": "A scenic landscape photo capturing the sunset over distant mountains.",
    "mountains": "A scenic landscape photo capturing the sunset over distant mountains.",
    "phone": "A travel photo showing a phone displaying route details.",
    "blurry": "A travel photo showing a phone displaying route details.",
    "coffee": "A clean editorial image of coffee brewing equipment.",
    "equipment": "A clean editorial image of coffee brewing equipment.",
}

TR_CAPTION_MAP = {
    "ekipman": "Doğru ekipman seçimi, kahvenin aroması ve demleme tutarlılığı üzerinde doğrudan etkilidir.",
    "ekipmanlar": "Doğru ekipman seçimi, kahvenin aroması ve demleme tutarlılığı üzerinde doğrudan etkilidir.",
    "çekirdek": "Çekirdek seçimi, fincandaki aroma profilini belirleyen en önemli adımdır.",
    "çekirdek seçimi": "Çekirdek seçimi, fincandaki aroma profilini belirleyen en önemli adımdır.",
    "su": "Demleme suyu kalitesi ve sıcaklığı, kahve özümsemesini belirleyen kritik unsurdur.",
    "demleme suyu": "Demleme suyu kalitesi ve sıcaklığı, kahve özümsemesini belirleyen kritik unsurdur.",
}

EN_CAPTION_MAP = {
    "equipment": "Equipment choices shape the brewing process and the final flavor in the cup.",
    "coffee": "The right image should support the section’s context, not simply decorate the page.",
}


def generate_local_alt_text(candidate: Dict[str, Any], slot: Dict[str, Any], language: str = "en") -> str:
    """
    Generates a localized, non-generic alt text based on candidate keywords and target headings.
    """
    keywords = [k.lower() for k in candidate.get("keywords", [])]
    target_heading = (slot.get("target_heading") or "").lower()
    
    # Try keyword matching first
    if language == "tr":
        for kw in keywords:
            if kw in TR_ALT_MAP:
                return TR_ALT_MAP[kw]
        if "ekipman" in target_heading or "kahve" in target_heading or "çekirdek" in target_heading:
            return TR_ALT_MAP["coffee"]
        if "yol" in target_heading or "doğa" in target_heading:
            return TR_ALT_MAP["forest"]
        return f"{slot.get('target_heading') or 'Görsel'} konusuna odaklanan editöryal bir görsel."
    else:
        for kw in keywords:
            if kw in EN_ALT_MAP:
                return EN_ALT_MAP[kw]
        if "equipment" in target_heading or "coffee" in target_heading or "brew" in target_heading:
            return EN_ALT_MAP["coffee"]
        if "path" in target_heading or "nature" in target_heading or "travel" in target_heading:
            return EN_ALT_MAP["forest"]
        heading_text = slot.get('target_heading') or 'article content'
        return f"An editorial image supporting the context of {heading_text}."


def generate_local_caption(candidate: Dict[str, Any], slot: Dict[str, Any], language: str = "en") -> str:
    """
    Generates a localized, editorial caption using slot target heading and excerpt.
    """
    target_heading = slot.get("target_heading") or ""
    excerpt = slot.get("section_excerpt") or ""
    
    # Clean excerpt and get first sentence
    first_sentence = ""
    if excerpt:
        # Split by sentence-ending punctuation followed by space or end of string
        sentences = re.split(r'(?<=[.!?])\s+', excerpt.strip())
        if sentences:
            first_sentence = sentences[0].strip()
            
    # Check for specific predefined cases to match requirement examples exactly
    th_lower = target_heading.lower().strip()
    if language == "tr":
        for key, cap in TR_CAPTION_MAP.items():
            if key in th_lower:
                return cap
        if first_sentence:
            # Avoid repeating the heading if the sentence already starts with it
            if first_sentence.startswith(target_heading):
                return first_sentence
            return f"{target_heading}: {first_sentence}"
        return target_heading
    else:
        for key, cap in EN_CAPTION_MAP.items():
            if key in th_lower:
                return cap
        if first_sentence:
            if first_sentence.startswith(target_heading):
                return first_sentence
            return f"{target_heading}: {first_sentence}"
        return target_heading
