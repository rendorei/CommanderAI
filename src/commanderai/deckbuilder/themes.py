"""Archetype/theme definitions for `--theme` steering.

Each theme maps to a list of regex patterns matched against a card's oracle
text. When a theme is active, matching cards get a scoring bonus so the deck
leans into that strategy instead of defaulting to the same generic staples.
"""

import re

THEMES: dict[str, list[str]] = {
    "aristocrats": [
        r"sacrifice",
        r"\bdies\b",
        r"whenever .* dies",
        r"when .* dies",
        r"each opponent loses",
        r"loses? \d+ life",
    ],
    "tokens": [
        r"create .*token",
        r"\btoken\b",
        r"populate",
        r"\bamass\b",
        r"for each .* you control",
    ],
    "spellslinger": [
        r"instant or sorcery",
        r"whenever you cast",
        r"magecraft",
        r"prowess",
        r"copy (target|that) .*spell",
        r"noncreature spell",
    ],
    "lifegain": [
        r"gain .* life",
        r"whenever you gain life",
        r"lifelink",
        r"your life total",
    ],
    "counters": [
        r"\+1/\+1 counter",
        r"counters? on",
        r"proliferate",
        r"\bdoubl.* counters",
    ],
    "graveyard": [
        r"graveyard",
        r"return .* from .*graveyard",
        r"\bmill\b",
        r"from your graveyard",
    ],
    "reanimator": [
        r"return .*creature card .*from .*graveyard to the battlefield",
        r"\breanimat",
        r"put .*creature card .*from .*graveyard onto the battlefield",
    ],
    "blink": [
        r"exile .* return",
        r"enters the battlefield",
        r"\bflicker\b",
        r"\bblink\b",
    ],
    "voltron": [
        r"\bequip\b",
        r"\bequipment\b",
        r"enchant creature",
        r"\baura\b",
        r"attach",
    ],
    "landfall": [
        r"landfall",
        r"whenever a land enters",
        r"play an additional land",
        r"search .* for .* land card",
    ],
    "control": [
        r"counter target",
        r"draw .* cards?",
        r"destroy target",
        r"return target .* to .* hand",
    ],
}


def theme_names() -> list[str]:
    return sorted(THEMES.keys())


def theme_hits(theme: str, oracle_text: str) -> int:
    """Count how many of a theme's patterns the oracle text matches."""
    patterns = THEMES.get(theme.lower())
    if not patterns:
        return 0
    text = (oracle_text or "").lower()
    return sum(1 for p in patterns if re.search(p, text))
