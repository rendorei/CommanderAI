import httpx

from commanderai.models import Card

SPELLBOOK_BASE = "https://backend.commanderspellbook.com"

BRACKET_TAG_ORDER = {"E": 1, "S": 2, "H": 3, "R": 4}
BRACKET_TO_MAX_TAG = {
    1: {"E"},
    2: {"E", "S"},
    3: {"E", "S", "H"},
    4: {"E", "S", "H", "R"},
    5: {"E", "S", "H", "R"},
}


class BracketResult:
    def __init__(self):
        self.excluded_cards: list[tuple[str, str]] = []
        self.excluded_combos: list[tuple[list[str], str]] = []
        self.allowed_names: set[str] = set()
        self.prioritized_names: set[str] = set()


def _card_entry(name: str) -> dict:
    return {"card": name, "quantity": 1}


def check_bracket(
    commander: Card,
    candidates: list[Card],
    bracket: int,
) -> BracketResult:
    result = BracketResult()
    if bracket >= 5:
        result.allowed_names = {c.name for c in candidates}
        return result

    max_tags = BRACKET_TO_MAX_TAG[bracket]

    payload = {
        "commanders": [_card_entry(commander.name)],
        "main": [_card_entry(c.name) for c in candidates],
    }

    try:
        resp = httpx.post(
            f"{SPELLBOOK_BASE}/estimate-bracket",
            json=payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, Exception):
        result.allowed_names = {c.name for c in candidates}
        return result

    excluded_names: set[str] = set()
    game_changers: list[tuple[str, dict]] = []

    for card_info in data.get("cards", []):
        card_data = card_info.get("card", {})
        name = card_data.get("name", "")
        if not name:
            continue

        if card_info.get("banned"):
            excluded_names.add(name)
            result.excluded_cards.append((name, "banned"))
            continue

        if card_info.get("gameChanger"):
            game_changers.append((name, card_info))
            continue

        if bracket <= 3 and card_info.get("extraTurn"):
            excluded_names.add(name)
            result.excluded_cards.append((name, "extra turn"))
            continue

        if bracket <= 3 and card_info.get("massLandDenial"):
            excluded_names.add(name)
            result.excluded_cards.append((name, "mass land denial"))
            continue

    # Bracket 3 allows up to 3 game changers; bracket ≤2 allows none
    max_game_changers = 3 if bracket == 3 else 0 if bracket <= 2 else 999
    if len(game_changers) > max_game_changers:
        kept = game_changers[:max_game_changers]
        excess = game_changers[max_game_changers:]
        for name, _ in kept:
            result.prioritized_names.add(name)
        for name, _ in excess:
            excluded_names.add(name)
            result.excluded_cards.append((name, f"game changer (exceeds {max_game_changers} limit)"))
    elif max_game_changers == 0:
        for name, _ in game_changers:
            excluded_names.add(name)
            result.excluded_cards.append((name, "game changer"))
    else:
        for name, _ in game_changers:
            result.prioritized_names.add(name)

    # Bracket 3 allows 1 late-game two-card combo (mana value ≥6); bracket ≤2 allows none
    max_two_card_combos = 1 if bracket == 3 else 0 if bracket <= 2 else 999
    two_card_combos_found: list[tuple[list[str], str, int]] = []

    for combo_info in data.get("combos", []):
        combo = combo_info.get("combo", {})
        combo_tag = combo.get("bracketTag", "E")
        is_two_card = combo_info.get("definitelyTwoCard") or combo_info.get("arguablyTwoCard")
        mana_needed = combo.get("manaValueNeeded", 0) or 0

        should_exclude = False
        if combo_tag not in max_tags:
            should_exclude = True
        elif bracket <= 3 and is_two_card:
            two_card_combos_found.append((
                [u["card"]["name"] for u in combo.get("uses", []) if "card" in u],
                _combo_reason(combo_info, combo_tag),
                mana_needed,
            ))
            continue

        if should_exclude:
            combo_cards = [
                u["card"]["name"] for u in combo.get("uses", []) if "card" in u
            ]
            reason = _combo_reason(combo_info, combo_tag)
            result.excluded_combos.append((combo_cards, reason))

            if bracket <= 3:
                for card_name in combo_cards:
                    if card_name not in excluded_names:
                        excluded_names.add(card_name)
                        result.excluded_cards.append(
                            (card_name, f"part of {combo_tag}-bracket combo")
                        )

    # Handle two-card combos: bracket 3 keeps the 1 highest-mana-cost combo (late-game)
    if two_card_combos_found:
        two_card_combos_found.sort(key=lambda x: x[2], reverse=True)
        kept = two_card_combos_found[:max_two_card_combos]
        excluded_combos = two_card_combos_found[max_two_card_combos:]

        for combo_cards, _, _ in kept:
            for card_name in combo_cards:
                result.prioritized_names.add(card_name)

        for combo_cards, reason, _ in excluded_combos:
            reason = f"two-card combo, {reason}"
            result.excluded_combos.append((combo_cards, reason))
            for card_name in combo_cards:
                if card_name not in excluded_names:
                    excluded_names.add(card_name)
                    result.excluded_cards.append(
                        (card_name, "part of excluded two-card combo")
                    )

    all_names = {c.name for c in candidates}
    result.allowed_names = all_names - excluded_names
    result.prioritized_names &= result.allowed_names
    return result


def find_combos_in_pool(
    commander: Card,
    cards: list[Card],
) -> list[dict]:
    payload = {
        "commanders": [_card_entry(commander.name)],
        "main": [_card_entry(c.name) for c in cards],
    }

    try:
        resp = httpx.post(
            f"{SPELLBOOK_BASE}/find-my-combos",
            json=payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, Exception):
        return []

    results = data.get("results", {})
    combos = []
    for combo_data in results.get("included", []):
        cards_in_combo = [u["card"]["name"] for u in combo_data.get("uses", []) if "card" in u]
        produces = [p["feature"]["name"] for p in combo_data.get("produces", []) if "feature" in p]
        combos.append({
            "cards": cards_in_combo,
            "produces": produces,
            "bracket_tag": combo_data.get("bracketTag", "?"),
            "description": combo_data.get("description", ""),
        })

    return combos


def _combo_reason(combo_info: dict, tag: str) -> str:
    parts = [f"bracket {tag}"]
    if combo_info.get("lock"):
        parts.append("lock")
    if combo_info.get("extraTurn"):
        parts.append("extra turns")
    if combo_info.get("massLandDenial"):
        parts.append("mass land denial")

    combo = combo_info.get("combo", {})
    produces = combo.get("produces", [])
    for p in produces:
        feat = p.get("feature", {})
        name = feat.get("name", "")
        if "win the game" in name.lower() or "infinite" in name.lower():
            parts.append(name.lower())
            break

    return ", ".join(parts)
