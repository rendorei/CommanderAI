from commanderai.models import Card, DeckPick, DeckSlot


def is_legal_commander(card: Card) -> bool:
    type_line = card.type_line.lower()
    if "legendary" in type_line and "creature" in type_line:
        return True
    if "legendary" in type_line and "planeswalker" in type_line:
        oracle = (card.oracle_text or "").lower()
        if "can be your commander" in oracle:
            return True
    oracle = (card.oracle_text or "").lower()
    if "can be your commander" in oracle:
        return True
    return False


def color_identity_filter(cards: list[Card], commander: Card) -> list[Card]:
    identity = set(commander.color_identity)
    return [c for c in cards if set(c.color_identity).issubset(identity)]


def validate_deck(commander: Card, picks: list[DeckPick]) -> list[str]:
    errors = []

    if len(picks) != 99:
        errors.append(f"Deck has {len(picks)} cards, need exactly 99 (+ commander)")

    identity = set(commander.color_identity)
    names_seen: dict[str, int] = {}
    for pick in picks:
        card = pick.card
        if not set(card.color_identity).issubset(identity):
            errors.append(
                f"{card.name} has color identity {card.color_identity}, "
                f"outside commander's {list(identity)}"
            )

        is_basic = _is_basic_land(card)
        if not is_basic:
            names_seen[card.name] = names_seen.get(card.name, 0) + 1

    for name, count in names_seen.items():
        if count > 1:
            errors.append(f"Duplicate: {name} appears {count} times")

    return errors


def _is_basic_land(card: Card) -> bool:
    type_line = card.type_line.lower()
    return "basic" in type_line and "land" in type_line
