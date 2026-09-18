## 1. Scaffolding

- [x] 1.1 Create `scrape_verses.py` with a `main()` entry point and CLI arg
      parsing consistent with `main.py` (e.g. `--url` for AnkiConnect,
      `--verbose`)

## 2. Page fetching and parsing

- [x] 2.1 Fetch `https://bbn1.bbnradio.org/spanish/versiculos-anteriores`
      via `requests`
- [x] 2.2 Parse the `<table id="weekly_verses_previous">` rows into
      `(fecha, referencia, versículo)` tuples using stdlib only
- [x] 2.3 Raise a clear error if the expected table id or row structure is
      not found

## 3. Reference normalization and parsing

- [x] 3.1 Implement the book-name alias map (`Salmo`→`Salmos`,
      `Gal`→`Gálatas`, `Heb`→`Hebreos`, `Nahún`→`Nahúm`)
- [x] 3.2 Implement reference parsing into `Libro` / `Capítulo` /
      `Versículos cita`, handling multi-word book names (e.g.
      `1 Corintios`) and verse ranges (e.g. `22-23`)
- [x] 3.3 Rebuild `Cita` from the canonicalized `Libro` + `Capítulo` +
      `Versículos cita`, never from the raw scraped text

## 4. Book lookup table and tagging

- [x] 4.1 Add the static book → (abbreviation, testament) table for the
      ~30 books observed on the scraped page
- [x] 4.2 Derive tags (`testament`, `bible`, `abbreviation`) from the table
      for each parsed verse
- [x] 4.3 Raise a clear error naming any book not found in the table

## 5. Field construction

- [x] 5.1 Derive `Pista` as the verse text's first ~4 words + "…"
- [x] 5.2 Set `Versículo` to the scraped verse text and `Versión` to
      `RVR1960`

## 6. Dedup and note creation

- [x] 6.1 Reuse `processor.py`'s dedup pattern to check for an existing
      note with matching `Cita` in `Memorización::1. Versículos`
- [x] 6.2 Create the note via `anki_client.add_note` using the
      `Memorización de Versículos` note type when no match exists
- [x] 6.3 Skip creation when a match exists

## 7. Reporting

- [x] 7.1 Track and print counts of verses created vs. skipped, in the
      style of `main.py`'s existing summaries
- [x] 7.2 Print per-verse detail under `--verbose`, consistent with
      `main.py`'s verbose output

## 8. Manual verification

- [x] 8.1 Run against the live Anki instance and confirm missing verses
      are created with correct `Cita`/`Libro`/`Capítulo`/`Versículos cita`/
      `Pista`/`Versículo`/`Versión` and tags
- [x] 8.2 Re-run and confirm no duplicates are created (idempotency)
- [x] 8.3 Spot-check the normalized rows (`Salmo`, `Gal`, `Heb`, `Nahún`
      variants) produce canonical `Cita`/`Libro` values
