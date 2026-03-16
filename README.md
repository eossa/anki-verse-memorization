# Anki Verse Memorization CLI

A Python CLI that connects to Anki via **AnkiConnect** and automates a card-promotion workflow across memorization decks.

## Deck promotion chain

```
Memorización::1. Versículos
    ↓  mature (interval ≥ 21 days) → duplicate card into Libros
    ↓  immature                    → 🚩 red flag
Memorización::2. Citas::1. Libros
    ↓  mature                      → duplicate card into Capítulos
    ↓  immature                    → 🚩 red flag
Memorización::2. Citas::2. Capítulos
    ↓  mature                      → duplicate card into Versículos
    ↓  immature                    → 🚩 red flag
Memorización::2. Citas::3. Versículos
```

Each stage uses the target deck's own note type when creating the duplicate, so cards always have the correct model for their deck.

When a mature card is duplicated (or already exists in the target deck), any red flag on the source card is automatically cleared.

## Note types per deck

| Deck | Note type |
|---|---|
| `Memorización::1. Versículos` | *(source model, unchanged)* |
| `Memorización::2. Citas::1. Libros` | `Memorización de Citas (Libros)` |
| `Memorización::2. Citas::2. Capítulos` | `Memorización de Citas (Capítulos)` |
| `Memorización::2. Citas::3. Versículos` | `Memorización de Citas (Versículos)` |

## Requirements

- Python 3.10+
- [Anki](https://apps.ankiweb.net/) running on your machine
- [AnkiConnect](https://foosoft.net/projects/anki-connect/) add-on installed in Anki (add-on code: `2055492159`)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run the full promotion workflow (Anki must be open)
python3 main.py

# Verbose output — shows individual card details per action
python3 main.py --verbose

# Custom AnkiConnect URL (default: http://localhost:8765)
python3 main.py --url http://localhost:8765
```

### Example output

```
🔗 Connecting to AnkiConnect…
   Connected.

📚 Versículos  →  Libros
   ✅ Duplicated :  2
   ⏭️  Skipped    :  0  (already in target)
   🚩 Flagged    :  6  (immature, red flag set)
   🏳️  Flag cleared:  1  (was red, now promoted)

📚 Libros  →  Capítulos
   ✅ Duplicated :  3
   ⏭️  Skipped    :  1  (already in target)
   🚩 Flagged    :  5  (immature, red flag set)
   🏳️  Flag cleared:  2  (was red, now promoted)

📚 Capítulos  →  Versículos
   ✅ Duplicated :  1
   ⏭️  Skipped    :  0  (already in target)
   🚩 Flagged    :  4  (immature, red flag set)
   🏳️  Flag cleared:  0  (was red, now promoted)

──────────────────────────────────────────────────
📊 Total summary
   ✅ Duplicated :  6
   ⏭️  Skipped    :  1
   🚩 Flagged    : 15
   🏳️  Flag cleared:  3
```

## Behavior details

| Card state | Action |
|---|---|
| Mature (interval ≥ 21 days), not yet in target deck | Duplicated into target deck using the target's note type (all fields and tags copied; scheduling reset) |
| Mature, already exists in target deck | Skipped silently — safe to run multiple times |
| Mature card had a red flag | Red flag cleared (flag → 0) |
| Immature (interval < 21 days) | Red flag set (flag = 1) |

## Manual test steps

1. Open Anki and confirm AnkiConnect is active — visit `http://localhost:8765`, you should receive a JSON response.
2. Create a test note in `Memorización::1. Versículos` with a distinctive first field.
3. Run `python3 main.py --verbose` — the card should appear in the **Flagged** list (new cards have interval 0).
4. In Anki's card browser, manually set the card's interval to ≥ 21 days (`Edit → Change Due Date`).
5. Run the CLI again — the card should appear in **Duplicated** in the `Versículos → Libros` stage, and its red flag should be cleared.
6. Run the CLI a third time — the card should appear in **Skipped** (already exists in the target deck).
