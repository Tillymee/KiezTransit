from src.api.vbb import get_departures, minutes_until

STOP_AM_STEINBERG = "900141507"  # Die richtige Haltestelle für die M2
M2_LINE = "M2"


def get_m2_am_steinberg():
    raw = get_departures(STOP_AM_STEINBERG, duration=45, results=10)

    # vbb-rest liefert: {"departures": [...]}
    data = raw.get("departures", [])

    departures = []

    for dep in data:
        # Sicherheit: nur dicts verarbeiten
        if not isinstance(dep, dict):
            continue

        line = dep.get("line", {}).get("name")
        if line != M2_LINE:
            continue

        direction = dep.get("direction", "Unbekannt")
        when = dep.get("when")
        delay = dep.get("delay", 0)

        departures.append({
            "direction": direction,
            "in_minutes": minutes_until(when),
            "delay": int(delay / 60) if delay else 0
        })

    return departures