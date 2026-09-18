# Tasks

## Implementation

- [x] 1.1 Add a 4th tuple to `DECK_PAIRS` in `main.py`: `("Memorización::2. Citas::3. Versículos", "Memorización::3. Versículos", "Memorización de Versículos sin pista")`
- [x] 1.2 Update the module docstring's deck-chain diagram in `main.py` to show the new 4th stage (mirroring the existing 3-stage format)

## Docs

- [x] 2.1 Update `README.md`'s "Deck promotion chain" diagram to add the 4th stage
- [x] 2.2 Update `README.md`'s "Note types per deck" table to add the `Memorización::3. Versículos` → `Memorización de Versículos sin pista` row
- [x] 2.3 Update `CLAUDE.md`'s "The promotion chain" diagram (in "Architecture") to add the 4th stage

## Verification

- [x] 3.1 Manual test per README's "Manual test steps" pattern, extended one stage: with a mature card already sitting in `Memorización::2. Citas::3. Versículos`, run `python3 main.py --verbose` and confirm it appears in **Duplicated** for the new `Versículos → Versículos` stage, with its red flag (if any) cleared
- [x] 3.2 Run `python3 main.py` a second time and confirm the same card now appears in **Skipped** (idempotency holds for the new stage)
- [x] 3.3 Spot-check in Anki's card browser that the duplicated note in `Memorización::3. Versículos` has all 7 fields (`Cita, Libro, Capítulo, Versículos cita, Pista, Verso, Versión`) populated correctly, not just a subset
