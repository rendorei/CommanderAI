"""Archetype/theme definitions for `--theme` steering and commander auto-pick.

Three kinds of themes are supported:
- **Strategy archetypes** (``THEMES``) matched against a card's oracle text.
- **Creature tribes** (``TRIBES``) matched against the type line / oracle text.
- **Aliases** (``ALIASES``) — meme/synonym names that resolve to a canonical
  archetype or tribe (e.g. ``go-wide`` -> ``tokens``, ``bogles`` -> ``auras``).

When a theme is active, matching cards get a scoring bonus so the deck/suggestions
lean into that strategy instead of defaulting to generic staples.
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
        r"\bstorm\b",
        r"copy (target|that) .*spell",
        r"noncreature spell",
    ],
    "lifegain": [
        r"gain .* life",
        r"whenever you gain life",
        r"lifelink",
        r"your life total",
    ],
    "lifedrain": [
        r"each opponent loses .* life",
        r"loses? \d+ life",
        r"drain",
        r"whenever you gain life",
    ],
    "counters": [
        r"\+1/\+1 counter",
        r"counters? on",
        r"proliferate",
        r"doubl.* counters",
    ],
    "graveyard": [
        r"graveyard",
        r"from your graveyard",
        r"\bescape\b",
        r"\bflashback\b",
        r"delirium",
        r"threshold",
    ],
    "reanimator": [
        r"return .*creature card .*from .*graveyard to the battlefield",
        r"\breanimat",
        r"put .*creature card .*from .*graveyard onto the battlefield",
    ],
    "mill": [
        r"\bmill\b",
        r"puts? .* cards? .* library into .* graveyard",
        r"from the top of .* library into .* graveyard",
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
        r"double strike",
    ],
    "equipment": [
        r"\bequip\b",
        r"\bequipment\b",
        r"\battach\b",
    ],
    "auras": [
        r"\baura\b",
        r"enchant creature",
        r"\bbestow\b",
        r"\bconstellation\b",
    ],
    "enchantress": [
        r"\benchantment\b",
        r"\bconstellation\b",
        r"whenever you cast .*enchantment",
    ],
    "landfall": [
        r"landfall",
        r"whenever a land enters",
        r"play an additional land",
        r"search .* for .* land card",
    ],
    "ramp": [
        r"add \{?[wubrgc0-9]",
        r"search your library for .* land",
        r"mana of any (one )?color",
        r"untap target land",
    ],
    "artifacts": [
        r"\bartifact\b",
        r"metalcraft",
        r"\baffinity\b",
        r"improvise",
    ],
    "treasure": [r"treasure"],
    "food": [r"\bfood\b"],
    "clues": [r"investigate", r"\bclue\b"],
    "wheels": [
        r"each player draws",
        r"discards? .* hand",
        r"draws? .* cards? .* for each",
    ],
    "group_hug": [
        r"each player draws",
        r"each player may",
        r"opponents? draw",
        r"each player .* additional",
    ],
    "burn": [
        r"deals? \d+ damage to (any target|each opponent|target player|each player)",
        r"deals damage to each",
        r"whenever .* deals .* damage",
    ],
    "stax": [
        r"don't untap",
        r"doesn't untap",
        r"can't untap",
        r"players? can't",
        r"skip .* (step|phase)",
    ],
    "taxes": [
        r"costs? \{?\d.* more",
        r"unless .* pays",
        r"pay \{?\d",
    ],
    "superfriends": [
        r"\bplaneswalker\b",
        r"loyalty",
        r"proliferate",
    ],
    "vehicles": [r"\bvehicle\b", r"\bcrew\b"],
    "sagas": [r"\bsaga\b", r"lore counter", r"chapter"],
    "toolbox": [
        r"search your library for a .*card",
        r"search your library for .* card",
    ],
    "pillow_fort": [
        r"can't attack you",
        r"attacks? .* only if",
        r"can't be attacked",
        r"prevent .* combat damage",
    ],
    "fog": [
        r"prevent all combat damage",
        r"prevent all damage",
    ],
    "theft": [
        r"gain control of",
        r"exchange control",
        r"you control .* enchanted",
    ],
    "clone": [
        r"copy .* creature",
        r"as a copy",
        r"becomes a copy",
    ],
    "cascade": [r"\bcascade\b"],
    "infect": [r"\binfect\b", r"\btoxic\b", r"poison counter"],
    "discard": [
        r"target player discards",
        r"each player discards",
        r"discards? a card",
    ],
    "land_destruction": [
        r"destroy target land",
        r"destroy .* lands?",
        r"sacrifice a land",
    ],
    "extra_combat": [
        r"additional combat phase",
        r"extra combat",
        r"untap .* attacking",
    ],
    "control": [
        r"counter target",
        r"draw .* cards?",
        r"destroy target",
        r"return target .* to .* hand",
    ],
}

# Creature tribes matched by type line / oracle text.
TRIBES: set[str] = {
    "elf", "goblin", "zombie", "vampire", "dragon", "angel", "demon", "dinosaur",
    "eldrazi", "cat", "knight", "faerie", "merfolk", "human", "wizard", "soldier",
    "sliver", "beast", "spirit", "warrior", "rogue", "snake", "wolf", "elemental",
    "hydra", "sphinx", "pirate", "ninja", "samurai", "rat", "squirrel", "dog",
    "treefolk", "giant", "golem", "construct", "saproling", "insect", "bird",
    "horror", "phyrexian", "shaman", "cleric", "druid",
}

# Irregular plural forms for tribe matching in oracle text.
_TRIBE_PLURALS = {
    "elf": "elves",
    "wolf": "wolves",
    "dwarf": "dwarves",
    "faerie": "faeries",
    "sphinx": "sphinxes",
    "rat": "rats",
}

# Meme / synonym names that map onto a canonical archetype or tribe.
ALIASES: dict[str, str] = {
    "go-wide": "tokens",
    "go_wide": "tokens",
    "weenie": "tokens",
    "storm": "spellslinger",
    "cantrips": "spellslinger",
    "cantrip": "spellslinger",
    "prowess": "spellslinger",
    "self-mill": "mill",
    "self_mill": "mill",
    "dredge": "mill",
    "recursion": "graveyard",
    "escape": "graveyard",
    "unearth": "graveyard",
    "threshold": "graveyard",
    "delirium": "graveyard",
    "sacrifice": "aristocrats",
    "sac": "aristocrats",
    "bogles": "auras",
    "enchantments": "enchantress",
    "planeswalkers": "superfriends",
    "tron": "ramp",
    "big-mana": "ramp",
    "big_mana": "ramp",
    "lands-matter": "landfall",
    "lands_matter": "landfall",
    "affinity": "artifacts",
    "historic": "artifacts",
    "etb": "blink",
    "etb-value": "blink",
    "etb_value": "blink",
    "flicker": "blink",
    "group-slug": "burn",
    "group_slug": "burn",
    "slug": "burn",
    "pingers": "burn",
    "tremor": "burn",
    "prison": "stax",
    "hatebears": "taxes",
    "hatebear": "taxes",
    "death-and-taxes": "taxes",
    "death_and_taxes": "taxes",
    "copy": "clone",
    "fork": "clone",
    "toxic": "infect",
    "8-rack": "discard",
    "8rack": "discard",
    "ponza": "land_destruction",
    "wheel": "wheels",
    "group-hug": "group_hug",
    "lifedrain": "lifedrain",
    "drain": "lifedrain",
    "zombie-tribal": "zombie",
    "elves": "elf",
    "goblins": "goblin",
    "zombies": "zombie",
    "vampires": "vampire",
    "dragons": "dragon",
    "angels": "angel",
}


def resolve_theme(name: str | None) -> str | None:
    """Resolve a user-supplied theme/alias/tribe to a canonical key, or None."""
    if not name:
        return None
    key = name.strip().lower().replace(" ", "-")
    if key in THEMES or key in TRIBES:
        return key
    if key in ALIASES:
        return ALIASES[key]
    key_u = key.replace("-", "_")
    if key_u in THEMES or key_u in TRIBES:
        return key_u
    if key_u in ALIASES:
        return ALIASES[key_u]
    return None


def theme_names() -> list[str]:
    """All accepted theme names (canonical archetypes + tribes + aliases)."""
    return sorted(set(THEMES) | TRIBES | set(ALIASES))


def archetype_names() -> list[str]:
    return sorted(THEMES)


def _tribe_hits(tribe: str, oracle_text: str, type_line: str) -> int:
    tl = type_line.lower()
    tx = oracle_text.lower()
    hits = 0
    if tribe in tl:
        hits += 2
    forms = {tribe, _TRIBE_PLURALS.get(tribe, tribe + "s")}
    if any(re.search(rf"\b{re.escape(f)}\b", tx) for f in forms):
        hits += 1
    return hits


def theme_hits(theme: str, oracle_text: str, type_line: str = "") -> int:
    """Count how strongly a card matches a theme (archetype or tribe)."""
    canonical = resolve_theme(theme)
    if not canonical:
        return 0
    if canonical in TRIBES:
        return _tribe_hits(canonical, oracle_text, type_line)
    patterns = THEMES.get(canonical, [])
    text = (oracle_text or "").lower()
    return sum(1 for p in patterns if re.search(p, text))
