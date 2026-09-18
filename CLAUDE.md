# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -r requirements.txt   # install deps (just `requests`)

python3 main.py                   # run the full promotion workflow (Anki + AnkiConnect must be running)
python3 main.py --verbose         # print individual card details per stage
python3 main.py --url http://localhost:8765   # override AnkiConnect URL
```

There is no test suite, linter, or build step. Verification is manual against a live Anki instance — see "Manual test steps" in README.md (create a note in the source deck, run the CLI, change the card's due date via Anki's card browser to make it mature, run again, confirm duplication + flag clearing).

To sanity-check AnkiConnect connectivity directly: `curl http://localhost:8765` should return a JSON response.

## Architecture

Three-file pipeline, no persistence layer — all state lives in Anki itself (deck membership, card interval, card flag).

- **`anki_client.py`** — thin wrapper around the AnkiConnect JSON-over-HTTP API (`invoke()` posts `{action, version, params}` to `ANKI_CONNECT_URL`). All Anki I/O goes through here. Raises `AnkiConnectError` on connection failure or an `error` field in the response body.
- **`processor.py`** — the core business logic in `process_deck(source_deck, target_deck, target_model_name)`. For every card in the source deck, decides one of four outcomes (duplicate / skip / flag / clear-flag) and returns a `ProcessResult` dataclass tallying each. Card maturity threshold is `MATURE_INTERVAL = 21` days; red flag value is `1`.
- **`main.py`** — defines `DECK_PAIRS`, the ordered chain of `(source_deck, target_deck, target_model)` tuples, and drives the CLI: connects, calls `process_deck` for each pair in sequence, prints per-stage and total summaries.

### The promotion chain

`main.py`'s `DECK_PAIRS` encodes a 3-stage pipeline where each stage's target deck becomes the next stage's source deck:

```
Memorización::1. Versículos
    ↓ mature → duplicate (note type: Memorización de Citas (Libros))   immature → 🚩 flag
Memorización::2. Citas::1. Libros
    ↓ mature → duplicate (note type: Memorización de Citas (Capítulos))   immature → 🚩 flag
Memorización::2. Citas::2. Capítulos
    ↓ mature → duplicate (note type: Memorización de Citas (Versículos))   immature → 🚩 flag
Memorización::2. Citas::3. Versículos
    ↓ mature → duplicate (note type: Memorización de Versículos sin pista)   immature → 🚩 flag
Memorización::3. Versículos
```

Each target deck always uses its own dedicated note type (never the source card's model) — this is what lets duplicate-detection work by matching the first field's value within the target deck (`_note_exists_in_deck` in `processor.py`), regardless of which note type produced the source card.

### Key invariants

- **Idempotency**: re-running the CLI is always safe. A mature card whose duplicate already exists in the target deck is silently skipped (not re-duplicated).
- **Flag semantics**: red flag (`flags=1`) marks "immature, needs more review." It is set when a card is immature and cleared the moment that same card becomes mature (or is found to already exist in the target deck) — whichever pipeline stage processes it.
- **Duplicate matching**: uses the *first field's value* of the note, not the note ID or card ID, since duplicated cards are new notes (different note type) in a different deck.
- **Batching**: `process_deck` fetches all cards in the source deck in one `findCards`/`cardsInfo` call, then batches note lookups via `notesInfo` — avoid re-introducing per-card round trips to AnkiConnect.
