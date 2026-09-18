# Design

## Context

See proposal.md - Why. `process_deck(source_deck, target_deck, target_model_name)` in `processor.py` is already generic: it takes any deck pair and target note type, and handles duplicate/skip/flag/clear-flag uniformly. `main.py`'s `DECK_PAIRS` is the only place that encodes the chain's shape and length. Extending the chain is purely a data change plus a docs update.

Verified via AnkiConnect before writing this design:
- `deckNames` includes `Memorización::3. Versículos` already.
- `modelFieldNames` for both `Memorización de Citas (Versículos)` and `Memorización de Versículos sin pista` returns the identical ordered list: `Cita, Libro, Capítulo, Versículos cita, Pista, Verso, Versión`.

## Goals / Non-Goals

**Goals:**
- Extend `DECK_PAIRS` with a 4th stage so mature cards in `Memorización::2. Citas::3. Versículos` promote into `Memorización::3. Versículos`.
- Keep docs (`main.py` docstring, `README.md` if applicable) in sync with the new chain length.

**Non-Goals:**
- Changing `process_deck`, dedup logic, or flag semantics — none of that needs to change for this stage.
- Handling the `Pista` (hint) field specially. It exists on both note types with the same name; it will carry over as-is. Whether the target card template renders it is an Anki template concern, not a data concern, and out of scope here.
- Treating stage 4 as a special "terminal" case in code. The pipeline has no concept of a last stage today (it just iterates `DECK_PAIRS`), and none is needed — a 4th tuple with no 5th successor behaves identically to today's 3rd tuple.

## Decisions

- **Append one tuple to `DECK_PAIRS` rather than introducing new chain-modeling logic.** `process_deck` doesn't care about position in the chain; the loop in `main()` already iterates `DECK_PAIRS` in order. No alternative considered seriously — any other approach (e.g., a separate function for a "final" stage) would add complexity the generic pipeline doesn't need.
- **No field remapping / transform step.** Since `modelFieldNames` confirmed identical field names and order between source and target note types, the existing verbatim `{k: v["value"] for k, v in fields.items()}` copy in `processor.py` requires no change. If the field lists had differed, this would have needed either a mapping layer or a note-type fix in Anki itself (out of scope for this CLI).

## Risks / Trade-offs

- [Anki note-type field names could be renamed later without updating this CLI, causing silent field drops on `addNote`] → No code mitigation; this is inherent to the existing verbatim-copy design used by all three prior stages, not something this change introduces. Noted here for awareness.
- [Running the CLI against a deck/model that's renamed or missing] → Already handled by existing error paths: `add_note` / AnkiConnect calls raise `AnkiConnectError`, caught per-stage in `main()`, which logs and continues to the next pair.

## Migration Plan

- No data migration. Deploy is: merge the `DECK_PAIRS` change, run `python3 main.py` as usual. First run after deploy will duplicate any currently-mature cards sitting in `Memorización::2. Citas::3. Versículos` into the new stage — this is the intended one-time "catch-up" and is idempotent if run again.
- Rollback: revert the `DECK_PAIRS` entry. Any notes already duplicated into `Memorización::3. Versículos` remain (rollback doesn't retract Anki data) but simply stop receiving new duplicates.
