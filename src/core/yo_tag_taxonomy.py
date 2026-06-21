#!/usr/bin/env python3
"""
Optimized tag taxonomy for travel photography
Hierarchical, with Turkish/English aliases and confidence thresholds
"""
from __future__ import annotations

from typing import Dict, Set

# Hierarchical tag taxonomy
TAG_HIERARCHY = {
    "scene": {
        "landscape": {
            "aliases": ["landscape", "manzara", "scenery"],
            "sub_tags": ["mountain_landscape", "seascape", "valley", "plateau"],
            "min_confidence": 0.55,
        },
        "portrait": {
            "aliases": ["portrait", "portre", "headshot"],
            "sub_tags": ["close_up_portrait", "full_body_portrait", "group_portrait"],
            "min_confidence": 0.60,
        },
        "architecture": {
            "aliases": ["architecture", "mimari", "building", "bina", "yapi"],
            "sub_tags": ["building", "historical", "modern", "monument"],
            "min_confidence": 0.58,
        },
        "nature": {
            "aliases": ["nature", "doga", "natural", "scenery"],
            "sub_tags": ["forest", "jungle", "vegetation", "wildlife"],
            "min_confidence": 0.55,
        },
        "street": {
            "aliases": ["street", "sokak", "cadde", "urban", "city_street"],
            "sub_tags": ["street_scene", "street_vendor", "street_life"],
            "min_confidence": 0.60,
        },
        "food": {
            "aliases": ["food", "yemek", "yiyecek", "dish", "cuisine"],
            "sub_tags": ["prepared_food", "raw_ingredients", "street_food", "restaurant"],
            "min_confidence": 0.65,
        },
        "interior": {
            "aliases": ["interior", "indoor", "ic", "içi", "home", "office"],
            "sub_tags": ["home_interior", "commercial_interior", "museum", "gallery"],
            "min_confidence": 0.58,
        },
        "aerial": {
            "aliases": ["aerial", "havadan", "drone", "bird_eye"],
            "sub_tags": ["drone_photography", "helicopter", "high_angle"],
            "min_confidence": 0.70,
        },
    },
    "objects": {
        "people": {
            "aliases": ["people", "insanlar", "persons"],
            "sub_tags": ["adult", "child", "elderly", "group"],
            "min_confidence": 0.65,
        },
        "person": {
            "aliases": ["person", "insan", "kisi", "adam", "kadin"],
            "sub_tags": ["man", "woman", "child"],
            "min_confidence": 0.70,
        },
        "animals": {
            "aliases": ["animals", "hayvanlar", "wildlife", "creature"],
            "sub_tags": ["dog", "cat", "bird", "horse", "exotic_animal"],
            "min_confidence": 0.65,
        },
        "water": {
            "aliases": ["water", "su", "sea", "ocean", "lake", "river", "pond"],
            "sub_tags": ["ocean", "sea", "lake", "river", "waterfall"],
            "min_confidence": 0.60,
        },
        "vegetation": {
            "aliases": ["vegetation", "bitki", "flora", "plant", "tree", "flower"],
            "sub_tags": ["tree", "flower", "grass", "shrub"],
            "min_confidence": 0.55,
        },
        "vehicle": {
            "aliases": ["vehicle", "arac", "car", "bike", "boat", "airplane"],
            "sub_tags": ["car", "motorcycle", "boat", "plane", "train"],
            "min_confidence": 0.62,
        },
        "sky": {
            "aliases": ["sky", "gok", "clouds", "cloud"],
            "sub_tags": ["clear_sky", "cloudy_sky", "dramatic_sky", "sunset_sky"],
            "min_confidence": 0.55,
        },
    },
    "location": {
        "beach": {
            "aliases": ["beach", "plaj", "sahil", "kiyı", "coast", "seaside"],
            "related_tags": ["sand", "ocean", "sunset"],
            "min_confidence": 0.65,
        },
        "mountain": {
            "aliases": ["mountain", "dag", "dağ", "peak", "summit", "alpine"],
            "related_tags": ["landscape", "snow", "hiking"],
            "min_confidence": 0.60,
        },
        "forest": {
            "aliases": ["forest", "orman", "woodland", "woods"],
            "related_tags": ["trees", "nature", "hiking"],
            "min_confidence": 0.58,
        },
        "market": {
            "aliases": ["market", "pazar", "bazaar", "carsi", "çarşı"],
            "related_tags": ["people", "vendor", "goods"],
            "min_confidence": 0.62,
        },
        "temple": {
            "aliases": ["temple", "tapinak", "tapınak", "mosque", "cami", "kilise", "church", "pagoda"],
            "related_tags": ["architecture", "religious", "cultural"],
            "min_confidence": 0.65,
        },
        "island": {
            "aliases": ["island", "ada", "adası"],
            "related_tags": ["water", "beach", "tropical"],
            "min_confidence": 0.65,
        },
        "urban": {
            "aliases": ["urban", "city", "sehir", "şehir", "downtown", "cityscape"],
            "related_tags": ["building", "street", "people"],
            "min_confidence": 0.58,
        },
    },
    "time": {
        "sunrise": {
            "aliases": ["sunrise", "gundogumu", "gündoğumu", "dawn", "early_morning"],
            "related_tags": ["golden_light", "sky", "morning"],
            "min_confidence": 0.70,
        },
        "sunset": {
            "aliases": ["sunset", "guncesi", "güneş_batışı", "golden_hour", "dusk"],
            "related_tags": ["golden_light", "sky", "evening"],
            "min_confidence": 0.70,
        },
        "golden_hour": {
            "aliases": ["golden_hour", "altin_saat", "altın_saat", "warm_light"],
            "related_tags": ["sunset", "sunrise", "evening"],
            "min_confidence": 0.68,
        },
        "blue_hour": {
            "aliases": ["blue_hour", "mavi_saat", "twilight"],
            "related_tags": ["night", "evening", "lights"],
            "min_confidence": 0.68,
        },
        "night": {
            "aliases": ["night", "gece", "dark", "nighttime"],
            "related_tags": ["lights", "stars", "moon"],
            "min_confidence": 0.65,
        },
        "midday": {
            "aliases": ["midday", "ogle", "öğle", "noon", "daytime"],
            "related_tags": ["bright", "sharp_shadows"],
            "min_confidence": 0.60,
        },
    },
    "mood": {
        "vibrant": {
            "aliases": ["vibrant", "colorful", "renkli", "vivid"],
            "min_confidence": 0.58,
        },
        "muted": {
            "aliases": ["muted", "soft", "yumusak", "pastel"],
            "min_confidence": 0.58,
        },
        "dramatic": {
            "aliases": ["dramatic", "dramatik", "high_contrast", "intense"],
            "min_confidence": 0.62,
        },
        "calm": {
            "aliases": ["calm", "peaceful", "sakin", "tranquil"],
            "min_confidence": 0.55,
        },
        "energetic": {
            "aliases": ["energetic", "dynamic", "lively", "canlı"],
            "min_confidence": 0.58,
        },
        "romantic": {
            "aliases": ["romantic", "dreamy", "soft_focus", "tender"],
            "min_confidence": 0.60,
        },
    },
    "activity": {
        "travel": {
            "aliases": ["travel", "seyahat", "tourism", "tourism", "turism"],
            "related_tags": ["landscape", "architecture", "people"],
            "min_confidence": 0.60,
        },
        "hiking": {
            "aliases": ["hiking", "yuruyus", "yürüyüş", "trekking", "trail"],
            "related_tags": ["mountain", "forest", "people"],
            "min_confidence": 0.62,
        },
        "sports": {
            "aliases": ["sports", "spor", "athletic", "athletic", "active"],
            "sub_tags": ["swimming", "cycling", "skiing"],
            "min_confidence": 0.63,
        },
        "food_culture": {
            "aliases": ["food_culture", "gastronomy", "culinary", "yemek_kulturu"],
            "related_tags": ["food", "market", "people"],
            "min_confidence": 0.62,
        },
        "relaxation": {
            "aliases": ["relaxation", "rest", "dinlenme", "beach_relax"],
            "related_tags": ["beach", "calm", "water"],
            "min_confidence": 0.60,
        },
    },
}

# Tag aliases for quick lookup
TAG_ALIASES: Dict[str, str] = {}
for category, tags in TAG_HIERARCHY.items():
    for tag_name, tag_data in tags.items():
        TAG_ALIASES[tag_name] = tag_name
        for alias in tag_data.get("aliases", []):
            TAG_ALIASES[alias.lower()] = tag_name


def get_canonical_tag(user_input: str) -> str | None:
    """Convert user input to canonical tag name."""
    normalized = user_input.lower().replace("ş", "s").replace("ç", "c").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ı", "i")
    return TAG_ALIASES.get(normalized)


def get_tag_min_confidence(tag_name: str) -> float:
    """Get minimum confidence threshold for a tag."""
    for category, tags in TAG_HIERARCHY.items():
        if tag_name in tags:
            return tags[tag_name].get("min_confidence", 0.55)
    return 0.55  # Default


def get_related_tags(tag_name: str) -> list[str]:
    """Get related tags that often co-occur."""
    for category, tags in TAG_HIERARCHY.items():
        if tag_name in tags:
            return tags[tag_name].get("sub_tags", []) + tags[tag_name].get("related_tags", [])
    return []


def get_all_aliases_for_tag(tag_name: str) -> list[str]:
    """Get all aliases for a canonical tag."""
    for category, tags in TAG_HIERARCHY.items():
        if tag_name in tags:
            return tags[tag_name].get("aliases", [])
    return []


def suggest_tags_for_category(category: str) -> list[str]:
    """Get all tags in a category."""
    if category in TAG_HIERARCHY:
        return list(TAG_HIERARCHY[category].keys())
    return []


if __name__ == "__main__":
    print("=== Tag Taxonomy ===\n")

    # Example lookups
    print(f"Canonical tag for 'plaj': {get_canonical_tag('plaj')}")
    print(f"Canonical tag for 'sunset': {get_canonical_tag('sunset')}")
    print(f"Min confidence for 'beach': {get_tag_min_confidence('beach')}")
    print(f"Related tags for 'beach': {get_related_tags('beach')}")

    print("\n=== Scene Tags ===")
    print(suggest_tags_for_category("scene"))

    print("\n=== Activity Tags ===")
    print(suggest_tags_for_category("activity"))
