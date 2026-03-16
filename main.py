#!/usr/bin/env python3
"""
Anki Verse Memorization CLI

Promotes mature cards (interval ≥ 21 days) across citation decks and flags
immature ones for review.

Each deck pair is processed in order. For every card in the source deck:
  - Mature (interval ≥ 21 days): duplicated into the target deck using the
    target deck's note type. If a matching card already exists in the target
    deck it is skipped silently (idempotent). Any red flag on the source card
    is cleared after promotion.
  - Immature (interval < 21 days): marked with a red flag (flag = 1).

Deck promotion chain:

  Memorización::1. Versículos                    [Memorización de Versículos]
      ↓ mature → duplicate   immature → 🚩 flag
  Memorización::2. Citas::1. Libros              [Memorización de Citas (Libros)]
      ↓ mature → duplicate   immature → 🚩 flag
  Memorización::2. Citas::2. Capítulos           [Memorización de Citas (Capítulos)]
      ↓ mature → duplicate   immature → 🚩 flag
  Memorización::2. Citas::3. Versículos          [Memorización de Citas (Versículos)]
"""

import sys
import argparse

import anki_client as anki
from anki_client import AnkiConnectError
from processor import ProcessResult, process_deck

DECK_PAIRS = [
    (
        "Memorización::1. Versículos",
        "Memorización::2. Citas::1. Libros",
        "Memorización de Citas (Libros)",
    ),
    (
        "Memorización::2. Citas::1. Libros",
        "Memorización::2. Citas::2. Capítulos",
        "Memorización de Citas (Capítulos)",
    ),
    (
        "Memorización::2. Citas::2. Capítulos",
        "Memorización::2. Citas::3. Versículos",
        "Memorización de Citas (Versículos)",
    ),
]


def print_result(result: ProcessResult, verbose: bool) -> None:
    src = result.source_deck.split("::")[-1]
    tgt = result.target_deck.split("::")[-1]
    print(f"\n📚 {src}  →  {tgt}")
    print(f"   ✅ Duplicated : {len(result.duplicated)}")
    print(f"   ⏭️  Skipped    : {len(result.skipped)}  (already in target)")
    print(f"   🚩 Flagged    : {len(result.flagged)}  (immature, red flag set)")
    print(f"   🏳️  Flag cleared: {len(result.flag_cleared)}  (was red, now promoted)")

    if verbose:
        if result.duplicated:
            print("\n   Duplicated cards:")
            for v in result.duplicated:
                print(f"     + {v[:80]}")
        if result.skipped:
            print("\n   Skipped (already exist):")
            for v in result.skipped:
                print(f"     ~ {v[:80]}")
        if result.flagged:
            print("\n   Flagged (immature):")
            for v in result.flagged:
                print(f"     🚩 {v[:80]}")
        if result.flag_cleared:
            print("\n   Flag cleared (promoted):")
            for v in result.flag_cleared:
                print(f"     🏳️  {v[:80]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote mature Anki citation cards across decks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print individual card details for each action.",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8765",
        metavar="URL",
        help="AnkiConnect URL (default: http://localhost:8765).",
    )
    args = parser.parse_args()

    # Allow overriding the URL at runtime
    anki.ANKI_CONNECT_URL = args.url

    print("🔗 Connecting to AnkiConnect…")
    try:
        anki.check_connection()
    except AnkiConnectError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)
    print("   Connected.\n")

    total_duplicated = total_skipped = total_flagged = total_cleared = 0

    for source_deck, target_deck, target_model in DECK_PAIRS:
        try:
            result = process_deck(source_deck, target_deck, target_model)
        except AnkiConnectError as exc:
            print(f"❌ Error processing '{source_deck}': {exc}", file=sys.stderr)
            continue

        print_result(result, verbose=args.verbose)
        total_duplicated += len(result.duplicated)
        total_skipped += len(result.skipped)
        total_flagged += len(result.flagged)
        total_cleared += len(result.flag_cleared)

    print("\n" + "─" * 50)
    print("📊 Total summary")
    print(f"   ✅ Duplicated : {total_duplicated}")
    print(f"   ⏭️  Skipped    : {total_skipped}")
    print(f"   🚩 Flagged    : {total_flagged}")
    print(f"   🏳️  Flag cleared: {total_cleared}")


if __name__ == "__main__":
    main()
