"""
AnkiConnect HTTP client.

Wraps the JSON-over-HTTP API exposed by the AnkiConnect add-on.
Reference: https://foosoft.net/projects/anki-connect/
"""

import json
from typing import Any
import requests

ANKI_CONNECT_URL = "http://localhost:8765"
ANKI_CONNECT_VERSION = 6


class AnkiConnectError(Exception):
    pass


def invoke(action: str, **params: Any) -> Any:
    payload = {"action": action, "version": ANKI_CONNECT_VERSION, "params": params}
    try:
        response = requests.post(ANKI_CONNECT_URL, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise AnkiConnectError(
            f"Cannot connect to AnkiConnect at {ANKI_CONNECT_URL}. "
            "Make sure Anki is running and the AnkiConnect add-on is installed."
        )

    body = response.json()
    if body.get("error"):
        raise AnkiConnectError(f"AnkiConnect error [{action}]: {body['error']}")
    return body["result"]


def check_connection() -> None:
    """Raise AnkiConnectError if AnkiConnect is unreachable."""
    version = invoke("version")
    if version < ANKI_CONNECT_VERSION:
        raise AnkiConnectError(
            f"AnkiConnect version {version} is too old. Version {ANKI_CONNECT_VERSION}+ required."
        )


def find_cards(query: str) -> list[int]:
    return invoke("findCards", query=query)


def cards_info(card_ids: list[int]) -> list[dict]:
    return invoke("cardsInfo", cards=card_ids)


def notes_info(note_ids: list[int]) -> list[dict]:
    return invoke("notesInfo", notes=note_ids)


def find_notes(query: str) -> list[int]:
    return invoke("findNotes", query=query)


def add_note(deck_name: str, model_name: str, fields: dict[str, str], tags: list[str]) -> int:
    note = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "tags": tags,
        "options": {"allowDuplicate": False, "duplicateScope": "deck"},
    }
    return invoke("addNote", note=note)


def set_card_flag(card_id: int, flag: int) -> None:
    """Set the flag on a card. flag=0 clears it; flag=1 is red."""
    invoke("setSpecificValueOfCard", card=card_id, keys=["flags"], newValues=[flag])
