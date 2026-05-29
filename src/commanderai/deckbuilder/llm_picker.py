import json

import anthropic

from commanderai.config import ANTHROPIC_API_KEY, LLM_MODEL, SLOT_QUOTAS
from commanderai.models import Card, DeckPick, DeckSlot, ScoredCard

_SYSTEM_PROMPT = """You are an expert Magic: The Gathering Commander deck builder.
Given a commander and candidate cards organized by role, select cards to build a cohesive, synergistic deck.
Respond ONLY with valid JSON matching the specified schema. No markdown, no explanation outside the JSON."""

_LAND_COUNT_DEFAULT = 37


def build_prompt(
    commander: Card,
    candidates: dict[DeckSlot, list[ScoredCard]],
    land_count: int = _LAND_COUNT_DEFAULT,
    extra_instructions: str = "",
    owned_names: set[str] | None = None,
) -> str:
    nonland_slots = 99 - land_count
    lines = []
    lines.append(f"## Commander")
    lines.append(f"**{commander.name}** — {commander.type_line}")
    lines.append(f"Mana Cost: {commander.mana_cost}")
    lines.append(f"Color Identity: {', '.join(commander.color_identity)}")
    lines.append(f"Text: {commander.oracle_text}")
    lines.append("")
    lines.append(f"## Deck Slots (pick {nonland_slots} non-land cards total)")
    lines.append(f"Lands will be selected separately ({land_count} total).")
    lines.append("")

    for slot in DeckSlot:
        if slot == DeckSlot.LAND:
            continue
        quota = SLOT_QUOTAS.get(slot.value, 10)
        slot_candidates = candidates.get(slot, [])
        if not slot_candidates:
            continue
        lines.append(f"### {slot.value} (pick ~{quota})")
        for i, sc in enumerate(slot_candidates, 1):
            card = sc.card
            price = card.prices.get("usd") or "?"
            lines.append(
                f"{i}. {card.name} [{card.mana_cost}] "
                f"(Score: {sc.score:.0f}, ${price}) — "
                f"{card.oracle_text[:120]}"
            )
        lines.append("")

    lines.append("## Instructions")
    if extra_instructions:
        lines.append(f"- **{extra_instructions}**")
    lines.append(f"- Select exactly {nonland_slots} cards total across all slots")
    lines.append("- Respect approximate quotas per slot (±2 is fine for synergy reasons)")
    lines.append("- Prioritize synergy with the commander's strategy")
    lines.append("- Ensure a smooth mana curve (target avg CMC ~2.8-3.2)")
    lines.append("- You can ONLY pick cards from the candidates listed above")
    if owned_names:
        lines.append("- For upgrade_suggestions: ONLY suggest cards the user does NOT own")
        lines.append(f"- The user owns {len(owned_names)} cards total — all candidates above are owned")
    lines.append("")
    lines.append("## Response Format (JSON only)")
    lines.append("""```json
{
  "picks": [
    {"name": "Card Name", "slot": "RAMP", "reason": "short reason"}
  ],
  "strategy_summary": "2-3 sentence overview of the deck strategy",
  "upgrade_suggestions": ["Card Name 1", "Card Name 2", "...up to 5 cards the user does NOT own that would improve the deck"]
}
```""")

    return "\n".join(lines)


def call_llm(
    commander: Card,
    candidates: dict[DeckSlot, list[ScoredCard]],
    land_count: int = _LAND_COUNT_DEFAULT,
    extra_instructions: str = "",
    owned_names: set[str] | None = None,
) -> dict:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Use --no-llm flag or set the environment variable."
        )

    prompt = build_prompt(commander, candidates, land_count, extra_instructions, owned_names)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=8192,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]

    return json.loads(text)


def parse_llm_response(
    response: dict,
    candidates: dict[DeckSlot, list[ScoredCard]],
    owned_names: set[str] | None = None,
) -> tuple[list[DeckPick], str, list[str]]:
    name_to_card: dict[str, tuple[Card, DeckSlot]] = {}
    for slot, scored_list in candidates.items():
        for sc in scored_list:
            name_to_card[sc.card.name.lower()] = (sc.card, slot)

    picks: list[DeckPick] = []
    for item in response.get("picks", []):
        name = item.get("name", "")
        slot_str = item.get("slot", "UTILITY")
        reason = item.get("reason", "")

        lookup = name_to_card.get(name.lower())
        if lookup:
            card, _ = lookup
            try:
                slot = DeckSlot(slot_str)
            except ValueError:
                slot = DeckSlot.UTILITY
            picks.append(DeckPick(card=card, slot=slot, reason=reason))

    strategy = response.get("strategy_summary", "")
    upgrades = response.get("upgrade_suggestions", [])

    return picks, strategy, upgrades


def llm_build(
    commander: Card,
    candidates: dict[DeckSlot, list[ScoredCard]],
    land_count: int = _LAND_COUNT_DEFAULT,
    extra_instructions: str = "",
    owned_names: set[str] | None = None,
) -> tuple[list[DeckPick], str, list[str]]:
    response = call_llm(commander, candidates, land_count, extra_instructions, owned_names)
    return parse_llm_response(response, candidates, owned_names)
