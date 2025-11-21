from src.api.vbb import get_departures, minutes_until

STOP_AM_STEINBERG = "900141507"  # Prenzlauer Promenade/Am Steinberg
LINE_NAME = "M2"
DIRECTION_HINT = "S+U Alexanderplatz"


def print_m2_towards_alex() -> None:
    """
    Gibt die nächsten Abfahrten der M2 Richtung Alex an Am Steinberg aus.
    """
    data = get_departures(STOP_AM_STEINBERG, duration=60, results=30)
    deps = data.get("departures", [])

    filtered = [
        d for d in deps
        if d.get("line", {}).get("name") == LINE_NAME
           and DIRECTION_HINT in (d.get("direction") or "")
    ]

    print("\n🚋 M2 Richtung S+U Alexanderplatz – Abfahrten Am Steinberg\n")

    if not filtered:
        print("Keine passenden Abfahrten gefunden. Läuft die M2 gerade an diesem Halt?")
        return

    for d in filtered:
        when = d.get("when")
        mins = minutes_until(when) if when else "?"
        line = d.get("line", {}).get("name", "?")
        direction = d.get("direction", "?")
        print(f"{line:<3} → {direction:<40} in {mins:>2} min")