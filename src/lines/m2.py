# src/lines/m2.py
import math
from typing import List, Dict, Any

from src.api.vbb import get_departures, minutes_until

# M2-Haltestelle, an der du schauen willst:
# Prenzlauer Promenade/Am Steinberg (Berlin)
STOP_PRENZLAUER_PROM_AM_STEINBERG = "900141507"
M2_LINE_NAME = "M2"


def get_m2_at_prenzlauer_prom_am_steinberg(
        duration: int = 45,
        results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Holt alle M2-Abfahrten an 'Prenzlauer Prom./Am Steinberg'.
    Gibt eine Liste von dicts zurück:
    {
      "direction": str,
      "when": str,
      "in_minutes": int,
      "delay": int
    }
    """
    raw = get_departures(STOP_PRENZLAUER_PROM_AM_STEINBERG, duration=duration, results=results)

    departures = []

    for dep in raw:
        if not isinstance(dep, dict):
            continue

        line = dep.get("line", {}).get("name")
        if line != M2_LINE_NAME:
            continue

        direction = dep.get("direction", "Unbekannt")
        when = dep.get("when")
        delay = dep.get("delay", 0) or 0  # kann auch None sein

        # Delay in Minuten (aufgerundet)
        delay_min = math.ceil(delay / 60) if delay else 0

        departures.append(
            {
                "direction": direction,
                "when": when,
                "in_minutes": minutes_until(when),
                "delay": delay_min,
            }
        )

    return departures


def get_m2_towards_alex(duration: int = 45, results: int = 20) -> List[Dict[str, Any]]:
    """
    Filtert nur die M2-Abfahrten Richtung Alexanderplatz heraus.
    """
    all_deps = get_m2_at_prenzlauer_prom_am_steinberg(duration=duration, results=results)
    return [d for d in all_deps if "Alexanderplatz" in d["direction"]]