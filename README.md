# CommanderAI

AI-powered Magic: The Gathering Commander deck builder that works with **your actual collection**. No more browsing decklists you can't build — get a playable 100-card deck from cards you already own.

## What it does

- **Builds decks** from your collection using heuristic scoring + optional AI (Claude) for smarter picks
- **Suggests commanders** from cards you own, ranked by how many supporting cards you have
- **Suggests upgrades** — cards to buy that synergize with your commander
- **Explains decks** — AI breakdown of strategy, synergies, and how to play
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
  -f archidekt \                 # Export format: text/mtgo/moxfield/archidekt
  -o decks/my_deck.txt \         # Output path (default: decks/<commander>.txt)
  -v                             # Verbose — show why each card was picked
```

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

## Upgrade Suggestions

```bash
# Heuristic (free, instant)
commanderai suggest -c data/my_collection.txt -C "Avatar Aang // Aang, Master of Elements" --no-llm --top 20

# AI-powered (needs API key, explains WHY each card is good)
commanderai suggest -c data/my_collection.txt -C "Avatar Aang // Aang, Master of Elements"
```

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
