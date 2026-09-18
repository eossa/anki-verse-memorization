# Spec: card-promotion

> Auto-extracted by spec-miner (manual pass via /opsx:explore). Last mined: 2026-07-12.
> Source: processor.py, main.py (anki_client.py mined as call-chain expansion, not a separate capability)
> Last verified: 2026-07-12 (commit 6c88266)

---

### Requirement: Mature card is duplicated into the target deck
<!-- id: processor.py.process_deck -->
<!-- entities: Card, Note, Deck -->
<!-- enforced: processor.py.process_deck() -->
<!-- triggers: Red flag is cleared on promotion -->

When a card in the source deck has reached the maturity threshold and no matching note exists yet in the target deck, the system SHALL create a new note in the target deck using the target deck's own note type (never the source card's note type), carrying over the source note's field values and tags.

#### Scenario: Mature card, no existing duplicate
- **WHEN** a card's `interval` is ≥ 21 days AND no note with the same first-field value exists in the target deck
- **THEN** a new note is added to the target deck via `target_model_name`, with the source note's field values and tags; the card's first-field value is recorded in `result.duplicated`

---

### Requirement: Mature card with an existing duplicate is skipped
<!-- id: processor.py.process_deck -->
<!-- entities: Card, Note, Deck -->
<!-- enforced: processor.py.process_deck(), processor.py._note_exists_in_deck() -->

When a card has reached the maturity threshold but a note with a matching first-field value already exists in the target deck, the system SHALL NOT create a duplicate note.

#### Scenario: Mature card, duplicate already present
- **WHEN** a card's `interval` is ≥ 21 days AND a note with the same first-field value already exists in the target deck
- **THEN** no note is added; the card's first-field value is recorded in `result.skipped`

---

### Requirement: Red flag is cleared on promotion
<!-- id: processor.py.process_deck -->
<!-- entities: Card, Note -->
<!-- enforced: processor.py.process_deck() -->
<!-- depends_on: Mature card is duplicated into the target deck -->

When a mature card carries a red flag, the system SHALL clear the flag regardless of whether the promotion resulted in a new duplicate or a skip (already existed).

#### Scenario: Mature, flagged, newly duplicated
- **WHEN** a card is mature, has `flags == 1`, and gets duplicated
- **THEN** `setSpecificValueOfCard` is called with `flags=0`; first-field value recorded in `result.flag_cleared`

#### Scenario: Mature, flagged, already exists in target
- **WHEN** a card is mature, has `flags == 1`, and a duplicate already exists in the target deck
- **THEN** the flag is still cleared and recorded in `result.flag_cleared`, even though no new note was created

---

### Requirement: Immature card is flagged for review
<!-- id: processor.py.process_deck -->
<!-- entities: Card -->
<!-- enforced: processor.py.process_deck() -->

When a card has not reached the maturity threshold and no matching note exists in the target deck, the system SHALL mark the card with a red flag if it is not already flagged.

#### Scenario: Immature, not yet flagged
- **WHEN** a card's `interval` is < 21 days, no duplicate exists in the target deck, and `flags != 1`
- **THEN** `setSpecificValueOfCard` is called with `flags=1`; first-field value recorded in `result.flagged`

#### Scenario: Immature, already flagged
- **WHEN** a card's `interval` is < 21 days, no duplicate exists in the target deck, and `flags == 1` already
- **THEN** no AnkiConnect write is issued (avoids redundant API call), but the first-field value is still recorded in `result.flagged`

---

### Requirement: Immature card with an existing target-deck duplicate has its flag cleared
<!-- id: processor.py.process_deck -->
<!-- entities: Card, Note -->
<!-- enforced: processor.py.process_deck() -->

When a card has not reached the maturity threshold but a matching note already exists in the target deck, the system SHALL clear any red flag on the card and record it as skipped, rather than flagging it as needing review — since a downstream copy already existing means the card no longer needs review before promotion, regardless of whether it matured through this pipeline stage.

#### Scenario: Immature, duplicate already exists downstream
- **WHEN** a card's `interval` is < 21 days AND a note with the same first-field value already exists in the target deck
- **THEN** the card is recorded in `result.skipped`; if `flags == 1` it is cleared and recorded in `result.flag_cleared`; the card is NOT added to `result.flagged`

---

### Invariant: Duplicate matching uses first-field value, not note or card ID
<!-- entities: Card, Note -->
<!-- enforced: processor.py._note_exists_in_deck(), processor.py._first_field_value() -->

Duplicate detection SHALL always match on the value of a note's first field within the target deck's scope, never on note ID or card ID, because a duplicated note is a distinct note (different note type, different note ID) from its source.

---

### Invariant: Target deck note creation always uses the target deck's own note type
<!-- entities: Note, Deck -->
<!-- enforced: main.py (DECK_PAIRS), processor.py.process_deck() -->

Every note added to a target deck SHALL use that target deck's dedicated `target_model_name`, regardless of which note type produced the source card. Anki note-type card templates are global to every note of that type — attaching a new template to the source note to represent promotion would generate a matching card for every note sharing that note type, not just the one being promoted. Creating a distinct note with a dedicated per-stage note type is what keeps a promoted card scoped to exactly one target deck. This is also what allows duplicate-matching by field value to work uniformly across note-type boundaries.

---

### Invariant: Card and note lookups are batched per deck, not per card
<!-- entities: Card, Note -->
<!-- enforced: processor.py.process_deck() -->

For a given source deck, the system SHALL fetch all card IDs and card info in a single `findCards`/`cardsInfo` round trip, then fetch all note info in a single batched `notesInfo` call keyed by unique note ID, rather than issuing one AnkiConnect call per card.

---

### Invariant: Duplicate checks query live state per card, not a pre-computed batch
<!-- entities: Card, Note -->
<!-- enforced: processor.py._note_exists_in_deck() -->

For each source card, the system SHALL issue a fresh `findNotes` query against the target deck to check for an existing duplicate, rather than pre-fetching all target-deck notes once and checking against an in-memory set.

<!-- deferred: batching this into a single pre-read is a known future optimization, not a correctness concern — tracked separately from this baseline spec -->

---

### Invariant: Anki search query escaping covers quotes and colons only
<!-- entities: Note -->
<!-- enforced: processor.py._note_exists_in_deck() -->

Before building an Anki search query from a note's first-field value, the system SHALL escape double-quote (`"`) and colon (`:`) characters. This is sufficient under the assumption that verse/citation field content is plain text and punctuation, and never contains Anki search wildcards (`*`, `_`) or backslashes.
