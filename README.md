# Anki Verse Memorization CLI

A Python CLI that connects to Anki via **AnkiConnect** and automates a card-promotion workflow across citation decks.

## Deck promotion chain

```
Memorización::2. Citas::1. Libros
    ↓  mature (interval ≥ 21 days) → duplicate card
    ↓  immature                    → 🚩 red flag
Memorización::2. Citas::2. Capítulos
    ↓  mature                      → duplicate card
    ↓  immature                    → 🚩 red flag
Memorización::2. Citas::3. Versículos
```

When a mature card is duplicated (or already exists in the target deck), any existing red flag on that card is automatically cleared.

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
# Run the promotion workflow (Anki must be open)
python main.py

# Verbose output — shows individual card details
python main.py --verbose

# Custom AnkiConnect URL
python main.py --url http://localhost:8765
```

### Example output

```
🔗 Connecting to AnkiConnect…
   Connected.

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
   ✅ Duplicated :  4
   ⏭️  Skipped    :  1
   🚩 Flagged    :  9
   🏳️  Flag cleared:  2
```

## Behavior details

| Card state | Action |
|---|---|
| Mature (interval ≥ 21 days), not yet in target deck | Duplicated into target deck (all fields, tags; scheduling reset) |
| Mature, already exists in target deck | Skipped silently (idempotent) |
| Mature card had a red flag | Flag cleared (set to 0) |
| Immature (interval < 21 days) | Red flag (flag = 1) set on the card |

## Manual test steps

1. Open Anki and confirm AnkiConnect is active (visit `http://localhost:8765` — you should get a JSON response).
2. Create a test note in `Memorización::2. Citas::1. Libros` with a distinctive front field.
3. Run `python main.py --verbose` — the card should appear in the **Flagged** list (new cards have interval 0).
4. Manually set the card's interval to ≥ 21 days in Anki's card browser (`Edit → Change Due Date` or via the browser).
5. Run the CLI again — the card should appear in **Duplicated** and the flag should be cleared.
6. Run the CLI a third time — the card should appear in **Skipped** (already in target).
