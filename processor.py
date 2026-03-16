"""
Business logic for the Anki card promotion workflow.

For each (source_deck, target_deck) pair:
- Mature cards (interval ≥ 21 days) → duplicate into target_deck (skip if exists);
  clear red flag if the card had one.
- Immature cards → mark with red flag (flag = 1).
"""

from dataclasses import dataclass, field

import anki_client as anki

MATURE_INTERVAL = 21  # days
RED_FLAG = 1
NO_FLAG = 0


@dataclass
class ProcessResult:
    source_deck: str
    target_deck: str
    duplicated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)   # already in target
    flagged: list[str] = field(default_factory=list)   # red flag set
    flag_cleared: list[str] = field(default_factory=list)  # flag removed on promotion


def _first_field_value(fields: dict) -> str:
    """Return the value of the first field in the note's field dict."""
    if not fields:
        return ""
    first_key = next(iter(fields))
    return fields[first_key]["value"]


def _note_exists_in_deck(deck_name: str, first_field_value: str) -> bool:
    """Check whether a note with matching first-field value exists in deck_name."""
    escaped = first_field_value.replace('"', '\\"').replace(':', '\\:')
    query = f'deck:"{deck_name}" "{escaped}"'
    matches = anki.find_notes(query)
    return len(matches) > 0


def process_deck(source_deck: str, target_deck: str, target_model_name: str) -> ProcessResult:
    result = ProcessResult(source_deck=source_deck, target_deck=target_deck)

    card_ids = anki.find_cards(f'deck:"{source_deck}"')
    if not card_ids:
        return result

    cards = anki.cards_info(card_ids)

    # Collect unique note IDs to batch-fetch note info
    note_id_to_cards: dict[int, list[dict]] = {}
    for card in cards:
        note_id_to_cards.setdefault(card["note"], []).append(card)

    notes = anki.notes_info(list(note_id_to_cards.keys()))
    note_map = {n["noteId"]: n for n in notes}

    for card in cards:
        note = note_map.get(card["note"])
        if note is None:
            continue

        card_id: int = card["cardId"]
        interval: int = card.get("interval", 0)
        current_flag: int = card.get("flags", 0)
        model_name: str = note["modelName"]
        fields: dict = note["fields"]
        tags: list[str] = note.get("tags", [])
        first_val = _first_field_value(fields)

        if interval >= MATURE_INTERVAL:
            already_exists = _note_exists_in_deck(target_deck, first_val)

            if already_exists:
                result.skipped.append(first_val)
            else:
                plain_fields = {k: v["value"] for k, v in fields.items()}
                anki.add_note(target_deck, target_model_name, plain_fields, tags)
                result.duplicated.append(first_val)

            # Clear red flag if set
            if current_flag == RED_FLAG:
                anki.set_card_flag(card_id, NO_FLAG)
                result.flag_cleared.append(first_val)
        else:
            # Mark immature card with red flag (only if not already set)
            if current_flag != RED_FLAG:
                anki.set_card_flag(card_id, RED_FLAG)
            result.flagged.append(first_val)

    return result
