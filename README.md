# CommanderAI

AI-powered Magic: The Gathering Commander deck builder that works with **your actual collection**. No more browsing decklists you can't build — get a playable 100-card deck from cards you already own.

## What it does

- **Builds decks** from your collection using heuristic scoring + optional AI (Claude) for smarter picks
- **Suggests commanders** from cards you own, ranked by how many supporting cards you have
- **Suggests upgrades** — cards to buy that synergize with your commander
- **Explains decks** — AI breakdown of strategy, synergies, and how to play
- **Lists tokens** — shows all tokens your deck can create (so you can grab the right token cards)
- **Exports** to Moxfield, Archidekt, MTGO formats

## Quick Start

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Download card database (~165MB, one-time)
commanderai update-data

# Import your collection from Archidekt CSV export
commanderai convert -i ~/Downloads/archidekt-collection-export.csv -o data/my_collection.txt

# Build a deck (heuristic — free, no API key needed)
commanderai build -c data/my_collection.txt -C "Atraxa, Praetors' Voice" --no-llm

# Build with AI (smarter picks + explanations)
export ANTHROPIC_API_KEY=sk-ant-...
commanderai build -c data/my_collection.txt -C "Atraxa, Praetors' Voice"
```

## Commands

| Command | Description |
|---------|-------------|
| `build` | Build a Commander deck from your collection |
| `suggest-commanders` | Find the best commanders in your collection |
| `suggest` | Recommend cards to buy for a specific commander |
| `explain` | AI explanation of a deck's strategy and synergies |
| `tokens` | List all tokens a deck can create |
| `convert` | Convert Archidekt/CSV export to simple text format |
| `update-data` | Download/refresh Scryfall card database |
| `validate` | Check a deck for Commander legality |

## Build Options

```bash
commanderai build \
  -c data/my_collection.txt \    # Your collection file
  -C "Commander Name" \          # Commander to build around
  --no-llm \                     # Skip AI (free, fast)
  --lands 35 \                   # Adjust land count
  --budget 50 \                  # Max deck price (USD)
  --bracket 2 \                  # Power bracket 1-5 (see below)
  -f archidekt \                 # Export format: text/mtgo/moxfield/archidekt
  -o decks/my_deck.txt \         # Output path (default: decks/<commander>.txt)
  -v                             # Verbose — show why each card was picked
```

## Power Brackets

Control deck power level with `--bracket` (`-b`). Uses [Commander Spellbook](https://commanderspellbook.com/) API to detect combos and problematic cards in real time.

| Bracket | Style | What's allowed |
|---------|-------|----------------|
| 1 | Exhibition | No game changers, no combos, no extra turns, no MLD |
| 2 | Core | No game changers, no two-card combos, no extra turns, no MLD |
| 3 | Upgraded | Up to 3 game changers, 1 late-game combo (≥6 mana), no extra turn chains, no MLD |
| 4 | Optimized | No restrictions (only banlist) |
| 5 | cEDH | Same as 4, no filtering applied |

```bash
# Casual game night — no Rhystic Study, no Cyclonic Rift, no infinite combos
commanderai build -c data/my_collection.txt -C "Atraxa, Praetors' Voice" -b 2

# Focused but fair — strong synergy allowed, no instant-win combos
commanderai build -c data/my_collection.txt -C "Atraxa, Praetors' Voice" -b 3

# Full power
commanderai build -c data/my_collection.txt -C "Atraxa, Praetors' Voice" -b 5
```

The bracket filter shows exactly which cards and combos were excluded, so you can see what got cut and why.

## Output

Decks auto-save to `decks/` directory. Running build with the same commander creates numbered files (`atraxa.txt`, `atraxa_2.txt`, `atraxa_3.txt`...) — previous builds are never overwritten.

## How It Works

1. **Parse** your collection (supports "1 CardName" text or CSV from Archidekt/Moxfield)
2. **Filter** to commander's color identity + Commander-legal cards
3. **Classify** each card into roles: ramp, draw, removal, wipes, threats, utility
4. **Score** using EDHREC rank + keyword synergy with commander + mana curve
5. **Pick** final 99 via heuristics or Claude AI (hybrid mode)
6. **Build mana base** proportional to color pip distribution, prioritizing duals/fetches you own

## Collection Format

Supports multiple formats:

```
# Simple text (one per line)
1 Sol Ring
1 Command Tower
2 Forest

# With set code
1 Sol Ring (C21)

# CSV (Archidekt export)
Quantity,Name,Edition Code,...
1,Sol Ring,c21,...
```

## Token Tracking

```bash
# See all tokens your deck needs
commanderai tokens -d decks/atraxa.txt
```

Shows each unique token with P/T, colors, keywords, and which cards create it — so you know which token cards to bring to the table.

## Upgrade Suggestions

```bash
# Heuristic (free, instant)
commanderai suggest -c data/my_collection.txt -C "Avatar Aang // Aang, Master of Elements" --no-llm --top 20

# AI-powered (needs API key, explains WHY each card is good)
commanderai suggest -c data/my_collection.txt -C "Avatar Aang // Aang, Master of Elements"
```

## Edge Cases

- **Small collections** (<100 cards): warns you upfront, builds best possible deck with available cards, fills remaining slots with basic lands
- **Not enough on-color cards**: detects thin pools, adjusts land count upward, notifies you
- **Tokens/special cards in collection**: automatically detected and skipped (not reported as errors)
- **LLM returns too few picks**: backfills from heuristic candidates, then pads with basics to guarantee 100 cards

## Requirements

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com) (optional — only for AI features)

## Project Structure

```
CommanderAI/
├── src/commanderai/
│   ├── cli.py              # All CLI commands
│   ├── config.py           # Settings and constants
│   ├── models.py           # Card, Deck, DeckSlot models
│   ├── collection/         # Parse + match collection files
│   ├── data/               # Scryfall bulk data + card index
│   ├── deckbuilder/        # Scoring, slots, candidates, LLM, mana base
│   └── output/             # Formatting and export
├── decks/                  # Generated decks (gitignored)
├── data/                   # Local collection + cached card DB
└── tests/
```

## License

MIT
