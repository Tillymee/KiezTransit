# src/ui/console.py
from datetime import datetime

from src.lines.m2 import get_m2_towards_alex

WIDTH = 48  # Gesamtbreite der Tafel


def _border(top: bool = True):
    if top:
        print("╔" + "═" * (WIDTH - 2) + "╗")
    else:
        print("╚" + "═" * (WIDTH - 2) + "╝")


def _sep():
    print("╠" + "═" * (WIDTH - 2) + "╣")


def _center(txt: str):
    print(f"║{txt.center(WIDTH - 2)}║")


def _row(line: str, ziel: str, zeit: str, abf: str, status: str):
    # Spaltenbreiten feinabgestimmt
    print(f"║{line:<4} {ziel:<16} {zeit:<5} {abf:<6} {status:<10}║")


def print_m2_towards_alex():
    deps = get_m2_towards_alex()

    now = datetime.now().strftime("%H:%M")

    print()
    _border(True)
    _center("BVG – Abfahrten")
    _center("Am Steinberg (M2 → Alex)")
    _center(f"Stand: {now} Uhr")
    _sep()
    _row("Linie", "Ziel", "Zeit", "Abf.", "Status")
    _sep()

    if not deps:
        _center("Keine Abfahrten gefunden")
        _border(False)
        print()
        return

    for d in deps:
        mins = d["in_minutes"]
        delay = d["delay"]

        # Uhrzeit aus ISO-String extrahieren (…T13:04:00+01:00)
        when_str = d["when"]
        time_part = when_str.split("T")[1]  # 13:04:00+01:00
        hhmm = time_part[:5]  # 13:04

        abf_txt = f"{mins} min"

        if delay == 0:
            status = "pünktlich"
        else:
            status = f"+{delay} min"

        _row("M2", "Alexanderplatz", hhmm, abf_txt, status)

    _border(False)
    print()


if __name__ == "__main__":
    print_m2_towards_alex()