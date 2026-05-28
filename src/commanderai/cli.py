import re
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from commanderai.collection.matcher import get_unique_cards, match_collection
from commanderai.collection.parser import aggregate_entries, convert_to_text, parse_collection
from commanderai.config import DECKS_DIR, DEFAULT_LAND_COUNT
from commanderai.data.card_index import CardIndex
from commanderai.data.scryfall import download_bulk_data, load_cards
from commanderai.deckbuilder.candidates import build_candidates, heuristic_pick
from commanderai.deckbuilder.llm_picker import llm_build
from commanderai.deckbuilder.mana_base import build_mana_base
from commanderai.deckbuilder.rules import is_legal_commander, validate_deck
from commanderai.deckbuilder.slots import classify_card
from commanderai.models import Deck, DeckPick, DeckSlot, ScoredCard
from commanderai.output.export import export_deck
from commanderai.output.formatter import format_deck

app = typer.Typer(name="commanderai", help="AI-powered Commander deck builder")
console = Console()


def _load_index() -> CardIndex:
    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        progress.add_task("Loading card database...", total=None)
        cards = load_cards()
    console.print(f"[dim]Loaded {len(cards)} Commander-legal cards[/dim]")
    return CardIndex(cards)


@app.command()
def build(
    collection: Path = typer.Option(..., "--collection", "-c", help="Path to collection file"),
    commander_name: str = typer.Option(..., "--commander", "-C", help="Commander card name"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM, use heuristic only"),
    lands: int = typer.Option(DEFAULT_LAND_COUNT, "--lands", help="Number of lands"),
    budget: Optional[float] = typer.Option(None, "--budget", help="Max deck price in USD"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write deck to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show scoring details"),
    format: str = typer.Option("text", "--format", "-f", help="Output format"),
):
    """Build a Commander deck from your collection."""
    index = _load_index()

    entries = parse_collection(collection)
    if not entries:
        console.print("[red]Error: No cards found in collection file[/red]")
        raise typer.Exit(1)

    match_result = match_collection(entries, index)
    console.print(
        f"[green]Matched {len(match_result.matched)} cards[/green]"
        f"[dim] ({len(match_result.unmatched)} unmatched)[/dim]"
    )

    if match_result.fuzzy_matched:
        for original, corrected in match_result.fuzzy_matched[:5]:
            console.print(f"  [yellow]~[/yellow] '{original}' → '{corrected}'")

    if match_result.unmatched and verbose:
        for name in match_result.unmatched[:10]:
            console.print(f"  [red]✗[/red] '{name}' not found")

    commander = index.get(commander_name)
    if not commander:
        console.print(f"[red]Commander '{commander_name}' not found[/red]")
        raise typer.Exit(1)

    if not is_legal_commander(commander):
        console.print(f"[red]'{commander.name}' is not a legal commander[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Commander:[/bold] {commander.name} — {commander.type_line}")
    console.print(f"[dim]{commander.oracle_text}[/dim]\n")

    collection_cards = get_unique_cards(match_result.matched)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        progress.add_task("Analyzing candidates...", total=None)
        candidates = build_candidates(collection_cards, commander)

    total_candidates = sum(len(v) for v in candidates.values() if v)
    console.print(f"[dim]Found {total_candidates} candidate cards across all slots[/dim]")

    if no_llm:
        console.print("[dim]Using heuristic selection (--no-llm)[/dim]")
        picked = heuristic_pick(candidates, lands)
        deck_picks = []
        for slot, scored_list in picked.items():
            for sc in scored_list:
                deck_picks.append(DeckPick(card=sc.card, slot=sc.slot, reason=", ".join(sc.reasons)))
        strategy = ""
        upgrades = []
    else:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            progress.add_task("Asking Claude for deck picks...", total=None)
            try:
                deck_picks, strategy, upgrades = llm_build(commander, candidates, lands)
            except Exception as e:
                console.print(f"[yellow]LLM failed ({e}), falling back to heuristic[/yellow]")
                picked = heuristic_pick(candidates, lands)
                deck_picks = []
                for slot, scored_list in picked.items():
                    for sc in scored_list:
                        deck_picks.append(
                            DeckPick(card=sc.card, slot=sc.slot, reason=", ".join(sc.reasons))
                        )
                strategy = ""
                upgrades = []

    land_cards = [c for c in collection_cards if classify_card(c) == DeckSlot.LAND]
    land_picks = build_mana_base(
        [p.card for p in deck_picks], land_cards, commander, lands
    )

    all_picks = deck_picks + land_picks

    deck = Deck(
        commander=commander,
        cards=all_picks,
        strategy_summary=strategy,
        upgrade_suggestions=upgrades,
    )

    errors = validate_deck(commander, all_picks)
    if errors:
        console.print("[yellow]Validation warnings:[/yellow]")
        for err in errors:
            console.print(f"  [yellow]![/yellow] {err}")
        console.print()

    if not output:
        DECKS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^\w\-]", "_", commander.name.split("//")[0].strip()).lower().strip("_")
        ext = "txt"
        output = DECKS_DIR / f"{safe_name}.{ext}"
        # Avoid overwriting — append number
        counter = 1
        while output.exists():
            counter += 1
            output = DECKS_DIR / f"{safe_name}_{counter}.{ext}"

    exported = export_deck(deck, format) if format != "text" else format_deck(deck, verbose)
    output.write_text(exported)
    console.print(f"\n[green]Deck saved → {output}[/green]")
    console.print(format_deck(deck, verbose=verbose))


@app.command("suggest-commanders")
def suggest_commanders(
    collection: Path = typer.Option(..., "--collection", "-c", help="Path to collection file"),
    colors: Optional[str] = typer.Option(None, "--colors", help="Filter by color identity (e.g. WUB)"),
    top: int = typer.Option(5, "--top", help="Number of suggestions"),
):
    """Suggest commanders from your collection."""
    index = _load_index()

    entries = parse_collection(collection)
    match_result = match_collection(entries, index)
    collection_cards = get_unique_cards(match_result.matched)

    color_filter = set(colors.upper()) if colors else None
    owned_commanders = [
        c for c in collection_cards if is_legal_commander(c)
    ]

    if color_filter:
        owned_commanders = [
            c for c in owned_commanders
            if set(c.color_identity) == color_filter or set(c.color_identity).issubset(color_filter)
        ]

    scored_commanders: list[tuple[str, int, int]] = []
    for cmdr in owned_commanders:
        support_cards = [
            c for c in collection_cards
            if set(c.color_identity).issubset(set(cmdr.color_identity))
            and c.name != cmdr.name
        ]
        rank = cmdr.edhrec_rank or 99999
        scored_commanders.append((cmdr.name, len(support_cards), rank))

    scored_commanders.sort(key=lambda x: (-x[1], x[2]))

    console.print(f"\n[bold]Top {top} Commander Suggestions:[/bold]\n")
    for i, (name, support, rank) in enumerate(scored_commanders[:top], 1):
        card = index.get(name)
        identity = "".join(card.color_identity) if card else "?"
        console.print(
            f"  {i}. [bold]{name}[/bold] [{identity}] "
            f"— {support} supporting cards (EDHREC #{rank})"
        )


@app.command("update-data")
def update_data(
    force: bool = typer.Option(False, "--force", help="Force re-download"),
):
    """Download/update Scryfall card database."""
    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        progress.add_task("Downloading Scryfall oracle cards...", total=None)
        path = download_bulk_data(force=force)
    console.print(f"[green]Card database updated: {path}[/green]")


@app.command()
def validate(
    deck_file: Path = typer.Option(..., "--deck", "-d", help="Deck file to validate"),
    commander_name: str = typer.Option(..., "--commander", "-C", help="Commander name"),
):
    """Validate a deck for Commander legality."""
    index = _load_index()

    entries = parse_collection(deck_file)
    match_result = match_collection(entries, index)

    commander = index.get(commander_name)
    if not commander:
        console.print(f"[red]Commander '{commander_name}' not found[/red]")
        raise typer.Exit(1)

    picks = [
        DeckPick(card=e.card, slot=classify_card(e.card))
        for e in match_result.matched
        if e.card and e.card.name != commander.name
    ]

    errors = validate_deck(commander, picks)
    if errors:
        console.print("[red]Deck validation failed:[/red]")
        for err in errors:
            console.print(f"  [red]✗[/red] {err}")
        raise typer.Exit(1)
    else:
        console.print(f"[green]Deck is valid! ({len(picks) + 1} cards)[/green]")


@app.command()
def convert(
    input_file: Path = typer.Option(..., "--input", "-i", help="Input collection file (CSV/text)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
):
    """Convert Archidekt/CSV collection export to simple text format."""
    entries = parse_collection(input_file)
    if not entries:
        console.print("[red]No cards found in input file[/red]")
        raise typer.Exit(1)

    aggregated = aggregate_entries(entries)
    text = convert_to_text(entries)
    unique_cards = len(aggregated)
    total_cards = sum(e.quantity for e in aggregated)

    if output:
        output.write_text(text)
        console.print(
            f"[green]Converted {total_cards} cards ({unique_cards} unique) → {output}[/green]"
        )
    else:
        console.print(text)
        console.print(
            f"\n[dim]--- {total_cards} cards total, {unique_cards} unique ---[/dim]"
        )


@app.command()
def suggest(
    collection: Path = typer.Option(..., "--collection", "-c", help="Path to collection file"),
    commander_name: str = typer.Option(..., "--commander", "-C", help="Commander card name"),
    deck_file: Optional[Path] = typer.Option(None, "--deck", "-d", help="Current deck file (for targeted suggestions)"),
    top: int = typer.Option(15, "--top", help="Number of suggestions"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM, use heuristic only"),
):
    """Suggest cards to BUY that synergize with your commander."""
    from commanderai.deckbuilder.suggester import find_suggestions_heuristic, find_suggestions_llm

    index = _load_index()

    entries = parse_collection(collection)
    match_result = match_collection(entries, index)
    owned_names = {e.card.name for e in match_result.matched if e.card}

    commander = index.get(commander_name)
    if not commander:
        console.print(f"[red]Commander '{commander_name}' not found[/red]")
        raise typer.Exit(1)

    deck_cards = []
    if deck_file:
        deck_entries = parse_collection(deck_file)
        deck_match = match_collection(deck_entries, index)
        deck_cards = [e.card for e in deck_match.matched if e.card and e.card.name != commander.name]

    console.print(f"[bold]Suggesting upgrades for:[/bold] {commander.name}")
    console.print(f"[dim]Collection: {len(owned_names)} unique cards owned[/dim]\n")

    if no_llm:
        suggestions = find_suggestions_heuristic(
            commander, index.all_cards, owned_names, top_n=top
        )
        if not suggestions:
            console.print("[yellow]No synergy suggestions found.[/yellow]")
            raise typer.Exit(0)

        console.print(f"[bold]Top {len(suggestions)} cards to buy:[/bold]\n")
        for i, (card, themes) in enumerate(suggestions, 1):
            price = card.prices.get("usd") or "?"
            rank = card.edhrec_rank or "?"
            console.print(
                f"  {i:2}. [bold]{card.name}[/bold]  {card.mana_cost}  "
                f"[dim](${price}, EDHREC #{rank})[/dim]"
            )
            console.print(f"      [dim]{card.oracle_text[:120]}[/dim]")
            console.print(f"      [green]Synergy: {', '.join(themes)}[/green]")
            console.print()
    else:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            progress.add_task("Asking Claude for upgrade suggestions...", total=None)
            try:
                result = find_suggestions_llm(
                    commander, deck_cards or [], owned_names, index.all_cards, top_n=top
                )
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(1)

        console.print(result)


@app.command()
def explain(
    deck_file: Path = typer.Option(..., "--deck", "-d", help="Deck file to explain"),
    commander_name: Optional[str] = typer.Option(
        None, "--commander", "-C", help="Commander name (auto-detected from Archidekt format)"
    ),
):
    """Explain a deck's strategy, synergies, and win conditions using AI."""
    from commanderai.deckbuilder.explainer import explain_deck

    index = _load_index()

    entries = parse_collection(deck_file)
    if not entries:
        console.print("[red]No cards found in deck file[/red]")
        raise typer.Exit(1)

    match_result = match_collection(entries, index)
    matched_cards = [e.card for e in match_result.matched if e.card]

    commander = None
    if commander_name:
        commander = index.get(commander_name)
    else:
        for entry in match_result.matched:
            if entry.card and is_legal_commander(entry.card):
                commander = entry.card
                break

    if not commander:
        console.print("[red]Could not identify commander. Use --commander flag.[/red]")
        raise typer.Exit(1)

    deck_cards = [c for c in matched_cards if c.name != commander.name]
    console.print(f"[bold]Explaining:[/bold] {commander.name} ({len(deck_cards)} cards)\n")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        progress.add_task("Analyzing deck with Claude...", total=None)
        try:
            explanation = explain_deck(commander, deck_cards)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    console.print(explanation)


if __name__ == "__main__":
    app()
