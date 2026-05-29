# Changelog

## [0.7.0] - 2026-05-29

### Fixed
- Color identities now display in canonical **WUBRG** order everywhere (e.g. `WUBRG` instead of the alphabetical `BGRUW`) across `list commanders`, `suggest-commanders`, auto-pick, partner output, and warnings.

### Added
- **`list` command** — `commanderai list [commanders|decks|colors|themes|tribes|aliases|formats|brackets]`. `list commanders` shows every eligible commander in your collection (with color identity, EDHREC rank, and partner ability); the rest show saved decks and the vocabularies accepted by `--theme`, `--colors`, `-f`, and `-b`.
- **Default collection** — `--collection`/`-c` is now optional across `build`, `suggest`, `suggest-commanders`, and `list commanders`, defaulting to `data/my_collection.txt`. A clear error is shown if the file is missing.
- **`list --head N` / `--tail N`** — limit long `list commanders` / `list decks` output.
- **`.env` support + path overrides** — a project-local `.env` is now loaded automatically. `COMMANDERAI_COLLECTION`, `COMMANDERAI_DECKS_DIR`, and `COMMANDERAI_CACHE` override the default collection, decks directory, and cache location (shell environment still wins). See `.env.example`.
- **Partner / two-commander support** — `build` now accepts a second commander via `--partner/-P`. Handles all pairing rules: plain **Partner**, **Partner with X**, restricted **Partner — group**, **Friends forever**, **Choose a Background** + a **Background**, and **Doctor's companion** + a **Time Lord Doctor**. Illegal pairings are rejected with an explanation.
  - Combined color identity (union of both) drives candidate filtering, the mana base, and validation; both commanders' text feeds synergy scoring.
  - Deck math adjusts to 98 cards + 2 commanders = 100; validation, formatter, and all export formats (text/MTGO/Moxfield `*CMDR*`/Archidekt) list both.
  - In auto-pick mode (no `--commander`), if the chosen commander wants a partner, the best-fit owned partner is auto-selected too (respects `--theme`/`--colors`/`--variety`).

## [0.6.0] - 2026-05-29

### Added
- **Auto-pick commander** — `--commander` is now optional on `build`. Omit it and pass `--theme` and/or `--colors` to have CommanderAI choose the best-fit legal commander you own (scored by on-theme card support in its colors, the commander's own theme fit, and EDHREC rank). Respects `--variety` so a seed can surface a different fitting commander.
- **Expanded archetypes** — `--theme` now understands ~35 strategy archetypes (storm, stax, taxes, enchantress, wheels, burn/group-slug, superfriends, vehicles, sagas, blink/ETB, mill, infect, treasure/food/clues, land-destruction, discard, lifedrain, toolbox, pillow-fort, fog, theft, clone, cascade, extra-combat, and more), creature **tribes** (elves, goblins, dragons, slivers, vampires, zombies, ...), and meme/synonym **aliases** (`go-wide`, `bogles`, `tron`, `death-and-taxes`, `8-rack`, `ponza`, ...).
- **Color-combination names** — `--colors` accepts guild/shard/wedge/four-color/five-color names (`azorius`, `jund`, `esper`, `yore-tiller`, `five-color`) in addition to WUBRG letters, on both `build` and `suggest-commanders`.
- **`suggest-commanders --theme`** — rank the commanders you own by how well they fit an archetype.

## [0.5.0] - 2026-05-29

### Added
- **Deck variety** (`--variety 0.0-1.0`, `--seed`) — builds are no longer near-identical on every run. Variety replaces strict top-N selection with seeded, score-weighted sampling across card picks, the mana base, and (in AI mode) shuffled candidate ordering. `--seed` makes any variety build reproducible; passing `--seed` alone implies a moderate variety level. Default (no flags) output is unchanged and deterministic.
- **Theme steering** (`--theme`) — lean a build into an archetype (`aristocrats`, `tokens`, `spellslinger`, `lifegain`, `counters`, `graveyard`, `reanimator`, `blink`, `voltron`, `landfall`, `control`) so the same commander can produce genuinely different decks instead of always the same staples/combo.
- **LLM anti-repetition** — in variety mode, prior saved decks for the same commander are fed to Claude with an instruction to build something meaningfully different.
- **Variety on `suggest-commanders` and `suggest`** — `--variety`/`--seed` now also surface different commander and upgrade suggestions each run (seeded, reproducible), and `suggest` accepts `--theme` to bias recommendations toward an archetype.

### Changed
- In variety mode, scoring emphasizes commander synergy and de-emphasizes raw EDHREC rank, reducing the "same good-stuff pile regardless of commander" effect.

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
