# Changelog

## [0.4.0] - 2026-05-29

### Added
- **Budget cap** (`--budget` USD) — now functional. Caps the deck's total estimated price: candidates priced above the budget are dropped up front, the LLM is told the target, and after assembly the most expensive cards are greedily swapped for cheaper same-slot owned alternatives (non-basic lands downgrade to basics). Reports the final price vs. budget and warns if the pool can't meet it.

## [0.3.0] - 2026-05-29

### Added
- **Power brackets** (`--bracket/-b 1-5`) — controls deck power level using Commander Spellbook API to detect and exclude combos, game changers, extra turns, and mass land denial based on target bracket
  - Bracket 1-2: no game changers, no two-card combos
  - Bracket 3: up to 3 game changers, 1 late-game combo allowed; prioritized cards get score boost
  - Bracket 4-5: no restrictions
  - Bracket-excluded lands (Ancient Tomb, Field of the Dead) also filtered from mana base
- **Token tracking** (`commanderai tokens -d deck.txt`) — lists all tokens a deck can create with P/T, colors, keywords, and which cards produce them
- **Non-legal card detection** — planes, schemes, phenomena, vanguards, and conspiracies from collection exports are now silently skipped instead of reported as errors
- **Upgrade swap refinement** — if LLM suggests upgrades you already own, they get swapped into the deck (replacing backfill cards or strictly weaker picks)

### Fixed
- Fuzzy match cutoff raised from 0.85 → 0.90 to prevent garbage matches ("Contract" → "Contradict", "Ood Sphere" → "Wooden Sphere")
- Cards like "Contract", "Spirit" that exist in Scryfall as non-Commander-legal are now detected before fuzzy matching runs
- Upgrade suggestions no longer recommend cards you already own
- Bracket-excluded lands no longer sneak into mana base via separate land picker path

## [0.2.0] - 2026-05-28

### Added
- **Deck explanation** (`commanderai explain -d deck.txt`) — AI breakdown of strategy, synergies, win conditions
- **Upgrade suggestions** (`commanderai suggest`) — recommends cards to buy with direct synergy detection (transform enablers, creature type references, keyword matches)
- **Collection converter** (`commanderai convert`) — Archidekt/CSV to text format with aggregation
- **Auto-naming** — deck files auto-save to `decks/` with counter (`atraxa.txt`, `atraxa_2.txt`, ...)
- **Small collection handling** — warns on <100 cards, backfills with basics when pool is thin
- **Token/special card detection** in collection matching — single-word names, DFC substitutes skipped

### Fixed
- Off-color lands in mono-colored decks (mana_base now filters by color identity)
- LLM returning <99 cards (backfill from heuristic + extra basics)
- Comment lines triggering CSV format detection
- Regex error in synergy scoring (`+1/+1 counter` pattern)

## [0.1.0] - 2026-05-28

### Added
- Initial release
- `commanderai build` — build Commander deck from collection (heuristic or AI)
- `commanderai suggest-commanders` — find best commanders in your collection
- `commanderai update-data` — download Scryfall bulk data
- `commanderai validate` — check deck legality
- `commanderai export` — export to text/MTGO/Moxfield/Archidekt formats
- Scryfall bulk data integration with local caching
- EDHREC rank + keyword synergy + CMC curve scoring
- Slot classification (ramp/draw/removal/wipe/threat/utility)
- Proportional mana base with dual/fetch priority
- Claude Sonnet integration for intelligent card selection
