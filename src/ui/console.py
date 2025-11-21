from datetime import datetime
from src.lines.m2 import get_m2_am_steinberg

WIDTH = 48


def _border(top=True):
    print(("╔" if top else "╚") + "═" * (WIDTH - 2) + ("╗" if top else "╝"))


def _sep():
    print("╠" + "═" * (WIDTH - 2) + "╣")


def _center(txt):
    print(f"║{txt.center(WIDTH - 2)}║")


def _row(line, ziel, zeit, abf, status):
    print(f"║{line:<4} {ziel:<16} {zeit:<5} {abf:<6} {status:<10}║")


def print_m2_towards_alex():
    deps = get_m2_am_steinberg()
    deps = [d for d in deps if "Alexanderplatz" in d["direction"]]

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
        return

    for d in deps:
        status = "pünktlich" if d["delay"] == 0 else f"+{d['delay']} min"
        _row("M2", "Alexanderplatz", d["time_display"], f"{d['in_minutes']} min", status)

    _border(False)
    print()