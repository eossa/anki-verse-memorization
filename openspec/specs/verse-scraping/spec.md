# verse-scraping

## Purpose

Scrapes the weekly Bible verses published on the BBN Radio Spanish site and
creates corresponding Anki notes in `Memorización::1. Versículos`, so new
verses enter the promotion pipeline without manual data entry.

## Requirements

### Requirement: Scrape the weekly verses page
The system SHALL fetch
`https://bbn1.bbnradio.org/spanish/versiculos-anteriores` and parse the
`<table id="weekly_verses_previous">` rows into `(fecha, referencia,
versículo)` tuples.

#### Scenario: Page structure matches expectations
- **WHEN** the script fetches the page and locates the expected table
- **THEN** it parses every data row into a `(fecha, referencia, versículo)`
  tuple, skipping the header row

#### Scenario: Page structure is unrecognized
- **WHEN** the script fetches the page but cannot find the expected table id
  or row structure
- **THEN** it raises a clear error instead of silently producing zero rows

### Requirement: Normalize book name variants
The system SHALL normalize known book-name inconsistencies found on the
source site (`Salmo`→`Salmos`, `Gal`→`Gálatas`, `Heb`→`Hebreos`,
`Nahún`→`Nahúm`) to their canonical Spanish form before using them in any
note field.

#### Scenario: Site uses a shortened or misspelled book name
- **WHEN** a scraped reference uses `Salmo`, `Gal`, `Heb`, or `Nahún`
- **THEN** the note's `Cita` and `Libro` fields use the canonical form
  (`Salmos`, `Gálatas`, `Hebreos`, `Nahúm` respectively), not the raw
  scraped text

### Requirement: Parse reference into structured fields
The system SHALL parse each canonicalized `Referencia` into `Libro`,
`Capítulo`, and `Versículos cita` components.

#### Scenario: Single verse reference
- **WHEN** the reference is `Isaías 50:7`
- **THEN** `Libro` = `Isaías`, `Capítulo` = `50`, `Versículos cita` = `7`

#### Scenario: Verse range reference
- **WHEN** the reference is `Lamentaciones 3:22-23`
- **THEN** `Libro` = `Lamentaciones`, `Capítulo` = `3`,
  `Versículos cita` = `22-23`

#### Scenario: Multi-word book name
- **WHEN** the reference is `1 Corintios 13:12`
- **THEN** `Libro` = `1 Corintios`, `Capítulo` = `13`,
  `Versículos cita` = `12`

### Requirement: Derive tags from book lookup table
The system SHALL derive tags for each note from a static book →
(abbreviation, testament) lookup table covering the books observed on the
scraped page.

#### Scenario: Recognized book
- **WHEN** a scraped verse's canonical `Libro` is present in the lookup table
- **THEN** the note's tags include the testament (`AT` or `NT`), `bible`,
  and the book's abbreviation

#### Scenario: Unrecognized book
- **WHEN** a scraped verse's canonical `Libro` is not present in the lookup
  table
- **THEN** the system raises a clear error naming the unrecognized book
  rather than creating a mistagged or partially-tagged note

### Requirement: Build note fields with derived Pista and fixed Versión
The system SHALL build the remaining note fields for each scraped verse:
`Pista` as the verse text's first ~4 words followed by "…", `Versículo` as
the scraped verse text unchanged, and `Versión` as `RVR1960`.

#### Scenario: Pista derivation
- **WHEN** a verse's text is "Nuevas son cada mañana; grande es tu
  fidelidad."
- **THEN** `Pista` is set to the first ~4 words of that text followed by "…"

### Requirement: Create only missing verses
The system SHALL create a note only if no existing note in
`Memorización::1. Versículos` has a matching `Cita` value, using the same
first-field dedup pattern as the existing promotion pipeline.

#### Scenario: Verse already exists in the target deck
- **WHEN** a scraped verse's canonical `Cita` matches an existing note's
  `Cita` in `Memorización::1. Versículos`
- **THEN** the system does not create a new note for that verse

#### Scenario: Verse is missing from the target deck
- **WHEN** a scraped verse's canonical `Cita` has no match among existing
  notes in `Memorización::1. Versículos`
- **THEN** the system creates a new note using the `Memorización de
  Versículos` note type with the derived fields and tags

### Requirement: Report a summary of results
The system SHALL print a summary of how many verses were created versus
skipped after processing the scraped page.

#### Scenario: Run completes
- **WHEN** the script finishes processing all scraped rows
- **THEN** it prints the count of verses created and the count skipped as
  already existing
