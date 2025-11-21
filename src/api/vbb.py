import requests
from datetime import datetime, timezone

# Lokale vbb-rest API
BASE_URL = "http://localhost:3000"


def get_departures(stop_id, duration=30, results=10):
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
    return r.json()


def minutes_until(timestamp):
    # vbb-rest liefert z. B. 2025-11-21T12:12:00+01:00
    dt = datetime.fromisoformat(timestamp)
    now = datetime.now(timezone.utc).astimezone()
    diff = (dt - now).total_seconds() / 60
    return int(diff)