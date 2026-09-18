#!/usr/bin/env python3
"""
Field-drift audit for the deck promotion chain.

When a mature card is duplicated into its target deck, the pipeline copies
every field once, at creation time (see processor.py). It never re-syncs
after that: if you later edit a field on the source note (typically `Pista`),
the already-existing duplicate in the target deck silently goes stale.

This script walks the full chain (source deck of the first pair through the
target deck of the last pair), matches notes across decks by their first
field's value (the same key `_note_exists_in_deck` uses), and reports any
note whose fields differ from its counterpart elsewhere in the chain.

It never writes to Anki — read-only by design. Use it to spot drift, then
resolve each mismatch by hand.

Usage:
    python3 check_field_drift.py
    python3 check_field_drift.py --url http://localhost:8765
"""

import argparse
import sys

import anki_client as anki
from anki_client import AnkiConnectError
from main import DECK_PAIRS


def _chain_decks() -> list[str]:
    """Ordered list of every deck in the promotion chain, source through final target."""
    decks = [DECK_PAIRS[0][0]]
    decks.extend(target for _source, target, _model in DECK_PAIRS)
    return decks


def _deck_notes(deck: str) -> list[dict]:
    card_ids = anki.find_cards(f'deck:"{deck}"')
    if not card_ids:
        return []
    cards = anki.cards_info(card_ids)
    note_ids = list({c["note"] for c in cards})
    return anki.notes_info(note_ids)


def _first_field_value(note: dict) -> str:
    fields = note["fields"]
    if not fields:
        return ""
    first_key = next(iter(fields))
    return fields[first_key]["value"]


def find_drift(decks: list[str]) -> dict[str, dict[str, dict]]:
    """Return {first_field_value: {deck: note}} for every value that appears
    with differing field content in more than one deck."""
    notes_by_deck = {deck: _deck_notes(deck) for deck in decks}

    by_value: dict[str, dict[str, dict]] = {}
    for deck in decks:
        for note in notes_by_deck[deck]:
            value = _first_field_value(note)
            by_value.setdefault(value, {})[deck] = note

    drifted = {}
    for value, per_deck in by_value.items():
        if len(per_deck) < 2:
            continue
        field_names = {name for note in per_deck.values() for name in note["fields"]}
        for field_name in field_names:
            values = {
                note["fields"][field_name]["value"]
                for note in per_deck.values()
                if field_name in note["fields"]
            }
            if len(values) > 1:
                drifted[value] = per_deck
                break

    return drifted


def print_report(drifted: dict[str, dict[str, dict]], decks: list[str]) -> None:
    if not drifted:
        print("No field drift detected across the chain.")
        return

    print(f"{len(drifted)} note(s) with field drift across the chain:\n")
    for value, per_deck in sorted(drifted.items()):
        print(f"=== {value} ===")
        for deck in decks:
            if deck not in per_deck:
                continue
            note = per_deck[deck]
            deck_label = deck.split("::")[-1]
            mod = note.get("mod")
            when = f" (mod {mod})" if mod else ""
            for field_name, field in note["fields"].items():
                print(f"  [{deck_label}]{when} {field_name}={field['value']!r}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Override AnkiConnect URL")
    args = parser.parse_args()

    if args.url:
        anki.ANKI_CONNECT_URL = args.url

    try:
        anki.check_connection()
    except AnkiConnectError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)

    decks = _chain_decks()
    drifted = find_drift(decks)
    print_report(drifted, decks)


if __name__ == "__main__":
    main()
