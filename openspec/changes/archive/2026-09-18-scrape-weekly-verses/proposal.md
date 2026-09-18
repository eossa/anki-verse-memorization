## Why

New weekly verses are published on BBN Radio's Spanish site
(`https://bbn1.bbnradio.org/spanish/versiculos-anteriores`) but must currently be
entered into Anki by hand. A one-off script can scrape that page and create any
missing verse notes directly in `Memorización::1. Versículos`, the entry point
of the existing promotion chain, eliminating manual transcription.

## What Changes

- Add a new standalone script, `scrape_verses.py`, run manually/occasionally
  and separate from `main.py`'s promotion pipeline.
- Fetch and parse the static HTML verse table (`Fecha | Referencia |
  versículo`, ~100 rows) using only the standard library — no new HTTP/HTML
  parsing dependency.
- Parse each row's `Referencia` into `Libro` / `Capítulo` / `Versículos cita`,
  normalizing known source-site inconsistencies (`Salmo`→`Salmos`,
  `Gal`→`Gálatas`, `Heb`→`Hebreos`, `Nahún`→`Nahúm`) so the created `Cita`
  field always uses the canonical book name.
- Add a book → (abbreviation, testament) lookup table covering the books that
  appear on the scraped page, used to derive tags.
- For each scraped verse, build note fields for the `Memorización de
  Versículos` note type (`Cita`, `Libro`, `Capítulo`, `Versículos cita`,
  `Pista`, `Versículo`, `Versión`) and tags (`testament`, `bible`,
  `abbreviation`), with `Pista` auto-derived as the verse's first ~4 words +
  "…" and `Versión` hardcoded to `RVR1960`.
- Skip creating a note if one with a matching `Cita` already exists in
  `Memorización::1. Versículos` (idempotent re-runs), reusing the same
  first-field dedup pattern as `processor.py`.
- Print a summary of created vs. skipped verses in the same style as
  `main.py`'s existing output.

## Capabilities

### New Capabilities
- `verse-scraping`: Scrapes the BBN Radio weekly-verses page and creates
  missing notes in the `Memorización::1. Versículos` deck, with book-name
  normalization, tag derivation, and idempotent duplicate skipping.

### Modified Capabilities
- None. `card-promotion` (the existing mature/immature promotion pipeline) is
  unaffected — this change only feeds new notes into the deck it already
  reads from.

## Impact

- New file: `scrape_verses.py`.
- No changes to `anki_client.py`, `processor.py`, or `main.py`.
- No new dependencies (`requests` + stdlib only).
- No test suite exists in this project; verification is manual against a
  live Anki instance, consistent with the existing workflow.
