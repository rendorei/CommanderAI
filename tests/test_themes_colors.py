from commanderai.deckbuilder.colors import color_name, format_colors, resolve_colors, wubrg_sort
from commanderai.deckbuilder.themes import (
    archetype_names,
    resolve_theme,
    theme_hits,
)


def test_resolve_canonical_theme():
    assert resolve_theme("aristocrats") == "aristocrats"
    assert resolve_theme("Spellslinger") == "spellslinger"


def test_resolve_alias_theme():
    assert resolve_theme("go-wide") == "tokens"
    assert resolve_theme("storm") == "spellslinger"
    assert resolve_theme("bogles") == "auras"
    assert resolve_theme("death and taxes") == "taxes"
    assert resolve_theme("tron") == "ramp"


def test_resolve_tribe_theme():
    assert resolve_theme("elf") == "elf"
    assert resolve_theme("dragons") == "dragon"


def test_resolve_unknown_theme():
    assert resolve_theme("not-a-real-theme") is None
    assert resolve_theme(None) is None


def test_theme_hits_archetype():
    assert theme_hits("aristocrats", "Sacrifice a creature: draw a card.") >= 1
    assert theme_hits("tokens", "Create two 1/1 Soldier tokens.") >= 1
    assert theme_hits("aristocrats", "Flying. Vigilance.") == 0


def test_theme_hits_tribe_uses_type_line():
    assert theme_hits("elf", "", "Creature — Elf Druid") >= 2
    assert theme_hits("dragon", "Other Dragons you control get +1/+1.", "Creature — Dragon") >= 2
    assert theme_hits("goblin", "Draw a card.", "Creature — Human Wizard") == 0


def test_archetype_names_nonempty():
    names = archetype_names()
    assert "aristocrats" in names
    assert "stax" in names


def test_resolve_colors_letters_and_names():
    assert resolve_colors("WUB") == {"W", "U", "B"}
    assert resolve_colors("esper") == {"W", "U", "B"}
    assert resolve_colors("Jund") == {"B", "R", "G"}
    assert resolve_colors("five-color") == {"W", "U", "B", "R", "G"}
    assert resolve_colors("azorius") == {"W", "U"}


def test_resolve_colors_invalid():
    assert resolve_colors("XYZ") is None
    assert resolve_colors(None) is None


def test_color_name_roundtrip():
    assert color_name({"W", "U", "B"}) == "esper"
    assert color_name({"B", "R", "G"}) == "jund"
    assert color_name({"W", "U"}) == "azorius"


def test_wubrg_ordering():
    # Alphabetical input must render in canonical WUBRG order
    assert format_colors(["B", "G", "R", "U", "W"]) == "WUBRG"
    assert format_colors({"B", "R", "G"}) == "BRG"
    assert format_colors(["G", "W"]) == "WG"
    assert format_colors([]) == "C"
    assert format_colors([], empty="colorless") == "colorless"
    assert wubrg_sort(["G", "W", "B"]) == ["W", "B", "G"]
