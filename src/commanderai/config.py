import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DECKS_DIR = PROJECT_DIR / "decks"

CACHE_DIR = Path(os.environ.get("COMMANDERAI_CACHE", Path.home() / ".commanderai"))
ORACLE_CARDS_PATH = CACHE_DIR / "oracle_cards.json"
BULK_DATA_MAX_AGE_DAYS = 7

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LLM_MODEL = "claude-sonnet-4-20250514"

DECK_SIZE = 100
DEFAULT_LAND_COUNT = 37

SLOT_QUOTAS = {
    "LAND": 37,
    "RAMP": 10,
    "DRAW": 10,
    "REMOVAL": 8,
    "WIPE": 4,
    "THREAT": 20,
    "UTILITY": 10,
}

SCRYFALL_BULK_URL = "https://api.scryfall.com/bulk-data"
SCRYFALL_USER_AGENT = "CommanderAI/0.5.0"

CANDIDATES_PER_SLOT_MULTIPLIER = 3
MAX_TOTAL_CANDIDATES = 300
