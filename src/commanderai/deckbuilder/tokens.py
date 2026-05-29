import re
from dataclasses import dataclass, field

from commanderai.models import Card


@dataclass
class TokenInfo:
    name: str
    power: str | None = None
    toughness: str | None = None
    colors: list[str] = field(default_factory=list)
    types: str = ""
    keywords: list[str] = field(default_factory=list)
    created_by: list[str] = field(default_factory=list)


_NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3,
    "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10,
}

_COLORS = {"white", "blue", "black", "red", "green", "colorless"}

_TOKEN_PATTERN = re.compile(
    r"creates?\s+"
    r"(?:(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+)"
    r"(.*?)"
    r"\s+tokens?\b"
    r"((?:\s+with\s+[^.,]+)?)",
    re.IGNORECASE,
)

_PT_PATTERN = re.compile(r"(\d+)/(\d+)")
_X_PT_PATTERN = re.compile(r"(X|\*)/(\d+|X|\*)")


_FALSE_POSITIVE_NAMES = {"or more", "twice", "that many", "those", "additional"}


def extract_tokens(cards: list[Card]) -> list[TokenInfo]:
    tokens_map: dict[str, TokenInfo] = {}

    for card in cards:
        oracle = card.oracle_text
        if not oracle:
            continue

        for match in _TOKEN_PATTERN.finditer(oracle):
            desc = match.group(1).strip()
            with_clause = (match.group(2) or "").strip()
            token = _parse_token_description(desc)
            if not token.name or token.name.lower() in _FALSE_POSITIVE_NAMES:
                continue
            if with_clause and with_clause.lower().startswith("with "):
                extra_kw = with_clause[5:].strip().rstrip(".,")
                for kw in extra_kw.split(" and "):
                    kw = kw.strip()
                    if kw and kw.capitalize() not in token.keywords:
                        token.keywords.append(kw.capitalize())

            key = f"{token.name}|{token.power}/{token.toughness}"
            if key in tokens_map:
                if card.name not in tokens_map[key].created_by:
                    tokens_map[key].created_by.append(card.name)
            else:
                token.created_by.append(card.name)
                tokens_map[key] = token

    result = sorted(tokens_map.values(), key=lambda t: t.name.lower())
    return result


def _parse_token_description(desc: str) -> TokenInfo:
    token = TokenInfo(name="")
    words = desc.split()
    if not words:
        return token

    colors = []
    keywords = []
    type_words = []
    name_parts = []
    pt_found = False

    i = 0
    while i < len(words):
        word = words[i].strip(",").lower()

        pt_match = _PT_PATTERN.fullmatch(words[i].strip(","))
        xpt_match = _X_PT_PATTERN.fullmatch(words[i].strip(","))
        if pt_match:
            token.power = pt_match.group(1)
            token.toughness = pt_match.group(2)
            pt_found = True
            i += 1
            continue
        if xpt_match:
            token.power = xpt_match.group(1)
            token.toughness = xpt_match.group(2)
            pt_found = True
            i += 1
            continue

        if word in _COLORS:
            colors.append(word.capitalize())
            i += 1
            continue

        if word == "and" and i + 1 < len(words) and words[i + 1].strip(",").lower() in _COLORS:
            i += 1
            continue

        if word in ("creature", "artifact", "enchantment", "land"):
            type_words.append(word.capitalize())
            i += 1
            continue

        if word in ("with", "that", "named"):
            if word == "named" and i + 1 < len(words):
                name_parts = [w.strip(",") for w in words[i + 1:]]
            break

        if word in ("flying", "haste", "vigilance", "trample", "lifelink",
                    "deathtouch", "first", "strike", "double", "menace",
                    "reach", "hexproof", "indestructible", "defender"):
            if word == "first" and i + 1 < len(words) and words[i + 1].lower().startswith("strike"):
                keywords.append("First strike")
                i += 2
                continue
            if word == "double" and i + 1 < len(words) and words[i + 1].lower().startswith("strike"):
                keywords.append("Double strike")
                i += 2
                continue
            keywords.append(word.capitalize())
            i += 1
            continue

        name_parts.append(words[i].strip(","))
        i += 1

    token.colors = colors
    token.keywords = keywords

    if type_words:
        token.types = " ".join(type_words)

    if name_parts:
        token.name = " ".join(name_parts)
    elif type_words:
        parts = []
        if colors:
            parts.extend(colors)
        parts.extend(type_words)
        token.name = " ".join(parts)
    else:
        token.name = "Token"

    return token
