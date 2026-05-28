import re

from commanderai.models import Card, DeckSlot, ScoredCard
from commanderai.deckbuilder.slots import classify_card

_SYNERGY_KEYWORDS = {
    "enter": ["etb", "enters the battlefield", "enters under", "when .* enters"],
    "sacrifice": ["sacrifice", "dies", "when .* dies", "death trigger"],
    "counters": [r"\+1/\+1 counter", "counter on", "proliferate"],
    "tokens": ["create.*token", "token"],
    "graveyard": ["graveyard", "return.*from.*graveyard", "mill"],
    "spellcast": ["whenever.*cast", "magecraft", "prowess", "instant or sorcery"],
    "combat": ["attack", "combat damage", "whenever.*attacks"],
    "lifegain": ["gain.*life", "whenever you gain life", "lifelink"],
}


def score_card(card: Card, commander: Card, slot: DeckSlot | None = None) -> ScoredCard:
    if slot is None:
        slot = classify_card(card)

    score = 0.0
    reasons: list[str] = []

    if card.edhrec_rank:
        rank_score = max(0, 100 - (card.edhrec_rank / 300))
        score += rank_score
        if rank_score > 80:
            reasons.append("top EDHREC rank")

    if card.cmc <= 2:
        score += 12
        reasons.append("low CMC")
    elif card.cmc <= 3:
        score += 8
    elif card.cmc >= 6:
        penalty = 5 * (card.cmc - 5)
        score -= penalty

    synergy_hits = _count_synergy(card, commander)
    if synergy_hits > 0:
        bonus = synergy_hits * 15
        score += bonus
        reasons.append(f"{synergy_hits} synergy keywords")

    return ScoredCard(card=card, score=score, slot=slot, reasons=reasons)


def _count_synergy(card: Card, commander: Card) -> int:
    commander_text = (commander.oracle_text or "").lower()
    card_text = (card.oracle_text or "").lower()
    card_kw = {k.lower() for k in card.keywords}

    hits = 0
    for theme, patterns in _SYNERGY_KEYWORDS.items():
        commander_has_theme = any(
            re.search(p, commander_text) for p in patterns
        )
        if not commander_has_theme:
            continue

        card_has_theme = any(re.search(p, card_text) for p in patterns) or any(
            p in card_kw for p in patterns
        )
        if card_has_theme:
            hits += 1

    return hits


def score_cards(
    cards: list[Card], commander: Card
) -> list[ScoredCard]:
    scored = [score_card(card, commander) for card in cards]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored
