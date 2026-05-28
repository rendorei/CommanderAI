from commanderai.config import CANDIDATES_PER_SLOT_MULTIPLIER, MAX_TOTAL_CANDIDATES, SLOT_QUOTAS
from commanderai.models import Card, DeckSlot, ScoredCard
from commanderai.deckbuilder.rules import color_identity_filter
from commanderai.deckbuilder.scoring import score_card
from commanderai.deckbuilder.slots import classify_card


def build_candidates(
    collection_cards: list[Card], commander: Card
) -> dict[DeckSlot, list[ScoredCard]]:
    legal_cards = color_identity_filter(collection_cards, commander)
    legal_cards = [c for c in legal_cards if c.name != commander.name]

    by_slot: dict[DeckSlot, list[ScoredCard]] = {slot: [] for slot in DeckSlot}

    for card in legal_cards:
        slot = classify_card(card)
        scored = score_card(card, commander, slot)
        by_slot[slot].append(scored)

    for slot in by_slot:
        by_slot[slot].sort(key=lambda s: s.score, reverse=True)

    trimmed = _trim_candidates(by_slot)
    return trimmed


def _trim_candidates(
    by_slot: dict[DeckSlot, list[ScoredCard]],
) -> dict[DeckSlot, list[ScoredCard]]:
    trimmed: dict[DeckSlot, list[ScoredCard]] = {}
    total = 0

    for slot in DeckSlot:
        quota = SLOT_QUOTAS.get(slot.value, 10)
        max_for_slot = quota * CANDIDATES_PER_SLOT_MULTIPLIER
        candidates = by_slot.get(slot, [])[:max_for_slot]
        trimmed[slot] = candidates
        total += len(candidates)

    if total > MAX_TOTAL_CANDIDATES:
        ratio = MAX_TOTAL_CANDIDATES / total
        for slot in trimmed:
            new_len = max(1, int(len(trimmed[slot]) * ratio))
            trimmed[slot] = trimmed[slot][:new_len]

    return trimmed


def heuristic_pick(
    candidates: dict[DeckSlot, list[ScoredCard]], land_count: int = 37
) -> dict[DeckSlot, list[ScoredCard]]:
    picks: dict[DeckSlot, list[ScoredCard]] = {}

    for slot in DeckSlot:
        if slot == DeckSlot.LAND:
            continue
        quota = SLOT_QUOTAS.get(slot.value, 10)
        available = candidates.get(slot, [])
        picks[slot] = available[:quota]

    total_nonland = sum(len(v) for v in picks.values())
    target_nonland = 99 - land_count

    if total_nonland < target_nonland:
        deficit = target_nonland - total_nonland
        all_remaining = []
        for slot, scored_list in candidates.items():
            if slot == DeckSlot.LAND:
                continue
            picked_names = {s.card.name for s in picks.get(slot, [])}
            for s in scored_list:
                if s.card.name not in picked_names:
                    all_remaining.append(s)
        all_remaining.sort(key=lambda s: s.score, reverse=True)
        extra = all_remaining[:deficit]
        for s in extra:
            picks.setdefault(s.slot, []).append(s)

    elif total_nonland > target_nonland:
        excess = total_nonland - target_nonland
        all_picks_flat = []
        for slot, scored_list in picks.items():
            for s in scored_list:
                all_picks_flat.append((slot, s))
        all_picks_flat.sort(key=lambda x: x[1].score)
        to_remove = all_picks_flat[:excess]
        for slot, s in to_remove:
            picks[slot].remove(s)

    return picks
