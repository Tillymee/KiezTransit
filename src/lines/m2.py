from datetime import datetime
import math

from src.api.vbb import get_departures, bvg_display_time, bvg_minutes

# Richtige M2-Haltestelle
STOP_AM_STEINBERG = "900141507"
M2_LINE = "M2"


def get_m2_am_steinberg():
    raw = get_departures(STOP_AM_STEINBERG, duration=45, results=20)

    data = raw.get("departures", [])
    departures = []

    for dep in data:
        if not isinstance(dep, dict):
            continue

        line = dep.get("line", {}).get("name")
        if line != M2_LINE:
            continue

        direction = dep.get("direction", "Unbekannt")
        when = dep.get("when")
        delay = dep.get("delay", 0)
        delay_min = math.ceil(delay / 60) if delay else 0

        departures.append({
            "direction": direction,
            "when": when,
            "time_display": bvg_display_time(when),
            "in_minutes": bvg_minutes(when),
            "delay": delay_min,
        })

    return departures