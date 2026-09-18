## Context

`Memorización::1. Versículos` is the entry point of the existing 3-stage
promotion pipeline (see `processor.py` / `main.py`). New verses currently
enter that deck by manual data entry. The source, BBN Radio's Spanish site,
publishes a static HTML page with a single table of ~100 weekly verses,
confirmed reachable and parseable via a plain `curl`/`requests` GET (no JS
rendering, no pagination). The target note type, `Memorización de
Versículos`, has 7 fields confirmed via AnkiConnect's `modelFieldNames`:
`Cita, Libro, Capítulo, Versículos cita, Pista, Versículo, Versión`.

Inspection of existing notes' tags (via `notesInfo` across the whole
`Memorización::*` tree) showed a consistent standard 3-letter Bible book code
scheme (`gen, deu, jos, psa, pro, isa, mat, jhn, rom, 1co, heb, jas, 1jn`,
etc.), confirmed by the user for all books appearing on the scraped page.
Inspection of the scraped page itself also revealed that the source site is
internally inconsistent for ~14/100 rows, using shortened or misspelled book
names (`Salmo` for `Salmos`, `Gal` for `Gálatas`, `Heb` for `Hebreos`, `Nahún`
for `Nahúm`) — confirmed with the user that these must be normalized to the
canonical form before being written into `Cita`/`Libro`.

## Goals / Non-Goals

**Goals:**
- Create any verse present on the scraped page but missing from
  `Memorización::1. Versículos`, using fields and tags consistent with the
  deck's existing conventions.
- Keep the script idempotent — safe to re-run without duplicating notes.
- Add zero new dependencies.

**Non-Goals:**
- Reproducing the nuanced, hand-curated `Pista` hints found on existing
  cards (sometimes the verse's opening phrase, sometimes its closing phrase).
  A simple, mechanical heuristic is accepted per user decision.
- Handling books not present on the currently scraped page (the lookup table
  covers only the ~30 books observed; extending it is out of scope until a
  future scrape surfaces a new book).
- Integrating into `main.py`'s promotion pipeline — this is a separate,
  manually-run script per user decision.
- Detecting or reconciling verse-text changes on already-existing notes
  (dedup is presence-only, matching `processor.py`'s existing pattern).

## Decisions

**Standalone script vs. pipeline stage.** Chosen: standalone `scrape_verses.py`.
The scrape is an occasional, manual action (pulling new content from an
external site), unlike the promotion chain which is meant to run every time
against already-present Anki state. Bundling it into `main.py` would force a
network dependency into every promotion run. (User-confirmed.)

**HTML parsing approach.** Chosen: Python's standard library only (regex over
the well-formed, single-line table markup, or `html.parser.HTMLParser` if
regex proves fragile in practice). Rejected: adding `beautifulsoup4`. The
project's CLAUDE.md documents "just `requests`" as the dependency
philosophy; the table markup is simple and static enough that stdlib parsing
is sufficient.

**Book name normalization.** Chosen: a small alias map (`Salmo`→`Salmos`,
`Gal`→`Gálatas`, `Heb`→`Hebreos`, `Nahún`→`Nahúm`) applied before book lookup,
and `Cita`/`Libro` are always rebuilt from the canonical name — never the raw
scraped text. Rejected: storing the scraped text verbatim, which would leave
a handful of cards visibly inconsistent with the rest of the deck (confirmed
with user).

**Pista heuristic.** Chosen: first ~4 words of the verse text + "…".
Rejected: leaving blank (user preferred to have a starting point) and
attempting a smarter heuristic (no mechanical rule fits the existing
hand-curated examples, which mix opening- and closing-phrase hints).

**Book → (abbreviation, testament) table.** Chosen: static Python dict/table
in `scrape_verses.py`, built from the standard 3-letter code convention and
scoped to the ~30 books observed on the scraped page. Rejected: querying
AnkiConnect at runtime to infer abbreviations dynamically — the existing
tag data is inconsistent (stray legacy tags, encoding artifacts, one
mistagged testament) and not a reliable runtime source of truth; a vetted
static table avoids re-deriving from noisy data on every run.

**Dedup strategy.** Chosen: reuse the exact pattern from
`processor.py::_note_exists_in_deck` — search
`deck:"Memorización::1. Versículos" "<Cita>"` via `find_notes`, skip if any
match. Rejected: tracking a separate "already scraped" ledger — the project
has no persistence layer by design (state lives in Anki), and this keeps
the script consistent with that invariant.

## Risks / Trade-offs

- [Risk] The source site could change its table markup or move to
  JS-rendered content in the future, silently breaking the parser →
  Mitigation: fail loudly (raise/print a clear error) if the expected table
  id or row shape isn't found, rather than silently producing zero rows.
- [Risk] A future scrape could reference a book not in the static lookup
  table → Mitigation: raise a clear error naming the unrecognized book so it
  can be added, rather than silently skipping or mis-tagging the note.
- [Risk] The naive `Pista` heuristic could occasionally cut a hint mid-word
  or produce an unhelpful clue for very short verses → Mitigation: accepted
  trade-off per user decision; the user can hand-edit `Pista` afterward in
  Anki, same as any other field.
- [Trade-off] Dedup matches on `Cita` text only, not verse content — if the
  site ever republishes the same reference with different wording, the
  existing note wins silently. Consistent with `processor.py`'s existing
  behavior elsewhere in the project, so not a new risk class.
