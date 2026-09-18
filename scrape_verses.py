#!/usr/bin/env python3
"""
BBN Radio Weekly Verses Scraper

Standalone, manually-run script that scrapes BBN Radio's Spanish weekly
verses page and creates any missing notes directly in
`Memorización::1. Versículos`, the entry point of the existing promotion
chain (see `main.py` / `processor.py`). Separate from that pipeline so a
network dependency is never required for a routine promotion run.

Re-running is safe: verses already present in the target deck (matched by
`Cita`) are skipped.
"""

import argparse
import re
import sys
from dataclasses import dataclass

import requests

import anki_client as anki
from anki_client import AnkiConnectError

VERSES_URL = "https://bbn1.bbnradio.org/spanish/versiculos-anteriores"
TARGET_DECK = "Memorización::1. Versículos"
TARGET_MODEL = "Memorización de Versículos"
VERSION_LABEL = "RVR1960"

# Known source-site inconsistencies -> canonical Spanish book name.
BOOK_ALIASES = {
    "Salmo": "Salmos",
    "Gal": "Gálatas",
    "Heb": "Hebreos",
    "Nahún": "Nahúm",
}

# book -> (abbreviation, testament), scoped to the books observed on the
# scraped page. Extend this table if a future scrape surfaces a new book.
BOOK_TABLE = {
    "Génesis": ("gen", "AT"),
    "Deuteronomio": ("deu", "AT"),
    "2 Crónicas": ("2ch", "AT"),
    "Salmos": ("psa", "AT"),
    "Proverbios": ("pro", "AT"),
    "Eclesiastés": ("ecc", "AT"),
    "Isaías": ("isa", "AT"),
    "Jeremías": ("jer", "AT"),
    "Lamentaciones": ("lam", "AT"),
    "Joel": ("jol", "AT"),
    "Miqueas": ("mic", "AT"),
    "Sofonías": ("zep", "AT"),
    "Nahúm": ("nam", "AT"),
    "Mateo": ("mat", "NT"),
    "Lucas": ("luk", "NT"),
    "Juan": ("jhn", "NT"),
    "Romanos": ("rom", "NT"),
    "1 Corintios": ("1co", "NT"),
    "2 Corintios": ("2co", "NT"),
    "Gálatas": ("gal", "NT"),
    "Efesios": ("eph", "NT"),
    "Filipenses": ("php", "NT"),
    "Colosenses": ("col", "NT"),
    "2 Timoteo": ("2ti", "NT"),
    "Hebreos": ("heb", "NT"),
    "Santiago": ("jas", "NT"),
    "1 Pedro": ("1pe", "NT"),
    "1 Juan": ("1jn", "NT"),
}

TABLE_RE = re.compile(
    r'<table\s+id="weekly_verses_previous"[^>]*>(.*?)</table>', re.DOTALL
)
ROW_RE = re.compile(
    r"<tr>\s*<td>(?P<fecha>\d{4}-\d{2}-\d{2})</td>\s*"
    r"<td class='bbntable_verse'>(?P<referencia>.*?)</td>\s*"
    r"<td class='bbntable_verse'>(?P<versiculo>.*?)</td>\s*</tr>",
    re.DOTALL,
)
REFERENCE_RE = re.compile(
    r"^(?P<libro>.+?)\s+(?P<capitulo>\d+):(?P<versiculos>[\d\-]+)$"
)


class ScrapeError(Exception):
    pass


@dataclass
class ScrapedVerse:
    fecha: str
    referencia: str
    versiculo: str


def fetch_page(url: str) -> str:
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.text


def parse_rows(html: str) -> list[ScrapedVerse]:
    table_match = TABLE_RE.search(html)
    if not table_match:
        raise ScrapeError(
            'Could not find <table id="weekly_verses_previous"> on the page. '
            "The site's markup may have changed."
        )

    rows = ROW_RE.findall(table_match.group(1))
    if not rows:
        raise ScrapeError(
            "Found the weekly verses table but no rows matched the expected "
            "structure. The site's markup may have changed."
        )

    return [
        ScrapedVerse(fecha=fecha, referencia=referencia.strip(), versiculo=versiculo.strip())
        for fecha, referencia, versiculo in rows
    ]


def normalize_book(raw_book: str) -> str:
    return BOOK_ALIASES.get(raw_book, raw_book)


def parse_reference(referencia: str) -> tuple[str, str, str]:
    # Some rows carry a trailing occasion annotation, e.g. "Juan 11:25  (Pascua)".
    # It isn't part of the book/chapter/verse structure, so it's dropped here.
    referencia = re.sub(r"\s*\([^)]*\)\s*$", "", referencia)

    match = REFERENCE_RE.match(referencia)
    if not match:
        raise ScrapeError(f"Could not parse reference: {referencia!r}")

    libro = normalize_book(match.group("libro").strip())
    return libro, match.group("capitulo"), match.group("versiculos")


def build_tags(libro: str) -> list[str]:
    entry = BOOK_TABLE.get(libro)
    if entry is None:
        raise ScrapeError(
            f"Unrecognized book {libro!r}. Add it to BOOK_TABLE in scrape_verses.py "
            "before re-running."
        )
    abbreviation, testament = entry
    return [testament, "bible", abbreviation]


def build_pista(versiculo: str) -> str:
    return " ".join(versiculo.split()[:4]) + "…"


def build_fields(libro: str, capitulo: str, versiculos: str, versiculo: str) -> dict[str, str]:
    return {
        "Cita": f"{libro} {capitulo}:{versiculos}",
        "Libro": libro,
        "Capítulo": capitulo,
        "Versículos cita": versiculos,
        "Pista": build_pista(versiculo),
        "Versículo": versiculo,
        "Versión": VERSION_LABEL,
    }


def note_exists(cita: str) -> bool:
    escaped = cita.replace('"', '\\"').replace(":", "\\:")
    query = f'deck:"{TARGET_DECK}" "{escaped}"'
    return len(anki.find_notes(query)) > 0


def process_verse(scraped: ScrapedVerse, verbose: bool) -> str:
    libro, capitulo, versiculos = parse_reference(scraped.referencia)
    fields = build_fields(libro, capitulo, versiculos, scraped.versiculo)
    cita = fields["Cita"]

    if note_exists(cita):
        if verbose:
            print(f"   ~ {cita}")
        return "skipped"

    tags = build_tags(libro)
    anki.add_note(TARGET_DECK, TARGET_MODEL, fields, tags)
    if verbose:
        print(f"   + {cita}")
    return "created"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape BBN Radio's weekly verses page and create any missing notes.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print per-verse detail as each row is processed.",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8765",
        metavar="URL",
        help="AnkiConnect URL (default: http://localhost:8765).",
    )
    args = parser.parse_args()

    anki.ANKI_CONNECT_URL = args.url

    print("🔗 Connecting to AnkiConnect…")
    try:
        anki.check_connection()
    except AnkiConnectError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)
    print("   Connected.\n")

    print(f"🌐 Fetching {VERSES_URL}…")
    try:
        html = fetch_page(VERSES_URL)
        verses = parse_rows(html)
    except (requests.RequestException, ScrapeError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"   Parsed {len(verses)} verses.\n")

    if args.verbose:
        print("Processing verses:")

    created = skipped = 0
    for scraped in verses:
        try:
            outcome = process_verse(scraped, args.verbose)
        except (ScrapeError, AnkiConnectError) as exc:
            print(f"❌ Error processing {scraped.referencia!r}: {exc}", file=sys.stderr)
            sys.exit(1)

        if outcome == "created":
            created += 1
        else:
            skipped += 1

    print("\n" + "─" * 50)
    print("📊 Summary")
    print(f"   ✅ Created : {created}")
    print(f"   ⏭️  Skipped : {skipped}  (already in target)")


if __name__ == "__main__":
    main()
