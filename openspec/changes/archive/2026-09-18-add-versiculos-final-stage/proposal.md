# Proposal

## Why

The promotion chain currently ends at `Memorización::2. Citas::3. Versículos`. There's a next-stage deck, `Memorización::3. Versículos` (note type `Memorización de Versículos sin pista`), that mature cards should graduate into, but nothing in the CLI drives cards there — they pile up in stage 3 once mature instead of continuing the promotion flow.

## What Changes

- Add a 4th `(source_deck, target_deck, target_model)` tuple to `DECK_PAIRS` in `main.py`, chaining `Memorización::2. Citas::3. Versículos` → `Memorización::3. Versículos` using note type `Memorización de Versículos sin pista`.
- Update the module docstring's deck-chain diagram in `main.py` to show the 4th stage.
- Update `README.md`'s description of the promotion chain to include the new stage (if it documents the chain length).

No changes to `processor.py` or `anki_client.py` — `process_deck` is already generic over any `(source, target, model)` triple.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
(none — `process_deck`'s behavior and requirements are unchanged; this only extends the data-driven `DECK_PAIRS` chain by one link. See design.md for verification that this is a safe data-only change.)

## Impact

- **Code**: `main.py` (`DECK_PAIRS` tuple list, docstring). Possibly `README.md`.
- **Anki state**: once run, mature cards in `Memorización::2. Citas::3. Versículos` will be duplicated into `Memorización::3. Versículos` and have their red flag cleared; immature ones get flagged as usual.
- **Verified pre-conditions** (via AnkiConnect): target deck `Memorización::3. Versículos` already exists; note types `Memorización de Citas (Versículos)` and `Memorización de Versículos sin pista` have identical field lists (`Cita, Libro, Capítulo, Versículos cita, Pista, Verso, Versión`), with `Cita` as the shared first field used for dedup.
