from enum import Enum
from pydantic import BaseModel, Field


class DeckSlot(str, Enum):
    LAND = "LAND"
    RAMP = "RAMP"
    DRAW = "DRAW"
    REMOVAL = "REMOVAL"
    WIPE = "WIPE"
    THREAT = "THREAT"
    UTILITY = "UTILITY"


class Card(BaseModel):
    name: str
    mana_cost: str = ""
    cmc: float = 0.0
    type_line: str = ""
    oracle_text: str = ""
    color_identity: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    edhrec_rank: int | None = None
    power: str | None = None
    toughness: str | None = None
    legalities: dict[str, str] = Field(default_factory=dict)
    prices: dict[str, str | None] = Field(default_factory=dict)
    set_code: str = ""
    collector_number: str = ""
    card_faces: list[dict] | None = None


class CollectionEntry(BaseModel):
    quantity: int
    card_name: str
    set_code: str | None = None
    collector_number: str | None = None
    card: Card | None = None


class ScoredCard(BaseModel):
    card: Card
    score: float
    slot: DeckSlot
    reasons: list[str] = Field(default_factory=list)


class DeckPick(BaseModel):
    card: Card
    slot: DeckSlot
    reason: str = ""


class Deck(BaseModel):
    commander: Card
    cards: list[DeckPick] = Field(default_factory=list)
    strategy_summary: str = ""
    upgrade_suggestions: list[str] = Field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.cards) + 1

    @property
    def avg_cmc(self) -> float:
        nonland = [p.card.cmc for p in self.cards if p.slot != DeckSlot.LAND]
        return sum(nonland) / len(nonland) if nonland else 0.0

    @property
    def total_price(self) -> float:
        total = 0.0
        for pick in self.cards:
            usd = pick.card.prices.get("usd")
            if usd:
                try:
                    total += float(usd)
                except ValueError:
                    pass
        return total
