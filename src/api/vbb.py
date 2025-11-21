# src/api/vbb.py
import math
from datetime import datetime
from datetime import timezone

import requests

# Lokales vbb-rest (Docker)
BASE_URL = "http://localhost:3000"


def get_departures(stop_id: str, duration: int = 30, results: int = 10):
    """
    Holt Abfahrten von vbb-rest für eine Haltestelle.
    Nutzt /stops/{id}/departures.
    """
    url = f"{BASE_URL}/stops/{stop_id}/departures"

    params = {
        "duration": duration,
        "results": results,
        "remarks": True,
        "tram": True,
        "bus": True,
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    # vbb-rest liefert normalerweise {"departures": [...]}
    if isinstance(data, dict) and "departures" in data:
        return data["departures"]
    return data


def minutes_until(timestamp: str) -> int:
    """
    Rechnet 'when' (ISO-String mit Offset, z.B. 2025-11-21T13:04:00+01:00)
    in Minuten bis zur Abfahrt um – möglichst nah an der BVG-App.

    Hack:
    - Wir ziehen pauschal 60 Sekunden ab, weil die API oft 1 Minute
      „später“ erscheint als die BVG-App.
    - Negative Werte → 0 (Zug ist quasi "jetzt" oder gerade weg).
    """
    # Zeitstempel parsen (inkl. +01:00 Offset)
    dt = datetime.fromisoformat(timestamp)

    # Lokale Zeit jetzt
    now = datetime.now(timezone.utc).astimezone()

    # Differenz in Sekunden
    diff_sec = (dt - now).total_seconds()

    # ⚙️ 1-Minuten-Offset zur BVG-App:
    diff_sec -= 60

    if diff_sec <= 0:
        return 0

    # Aufrunden auf volle Minuten
    minutes = math.ceil(diff_sec / 60)
    return max(minutes, 0)