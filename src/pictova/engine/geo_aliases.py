"""Coğrafi eş anlamlılar — 'Kapadokya' → 'Nevşehir', 'Ege' → 'İzmir Aydın Muğla' vb."""
from __future__ import annotations

# Her arama terimi → DB'de aranacak terimler listesi
GEO_ALIASES: dict[str, list[str]] = {
    # Kapadokya
    "kapadokya": ["nevşehir", "nevsehir", "goreme", "göreme", "urgup", "ürgüp"],
    "cappadocia": ["nevşehir", "nevsehir", "goreme", "göreme"],

    # Ege kıyısı
    "ege": ["izmir", "aydın", "muğla", "mugla", "bodrum", "marmaris", "fethiye", "cesme", "çeşme"],
    "aegean": ["izmir", "aydın", "muğla", "bodrum"],

    # Karadeniz
    "karadeniz": ["sinop", "samsun", "trabzon", "rize", "artvin", "giresun", "ordu", "bartin", "bartın"],
    "black sea": ["sinop", "trabzon", "samsun"],

    # Antik şehirler
    "efes": ["izmir", "selçuk", "seljuk"],
    "ephesus": ["izmir", "selçuk"],
    "truva": ["çanakkale", "canakkale"],
    "troy": ["çanakkale", "canakkale"],

    # Özel destinasyonlar
    "pamukkale": ["denizli"],
    "nemrut": ["adıyaman", "adiyaman"],
    "mount nemrut": ["adıyaman"],

    # Boğaz
    "bosphorus": ["istanbul", "İstanbul"],
    "boğaz": ["istanbul", "İstanbul"],
    "istanbul": ["İstanbul", "fatih", "beyoglu", "beyoğlu"],
    "İstanbul": ["İstanbul", "fatih", "beyoglu"],
}


def expand_query(query: str) -> list[str]:
    """Sorguyu coğrafi eş anlamlılarla genişlet."""
    q_lower = query.strip().lower()
    expanded = [query]

    for alias_key, expansions in GEO_ALIASES.items():
        if alias_key in q_lower or q_lower in alias_key:
            expanded.extend(expansions)

    # Tekrarları kaldır, sırayı koru
    seen: set[str] = set()
    result = []
    for t in expanded:
        if t.lower() not in seen:
            seen.add(t.lower())
            result.append(t)
    return result


__all__ = ["GEO_ALIASES", "expand_query"]
