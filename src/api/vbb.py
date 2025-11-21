import requests
from datetime import datetime, timezone, timedelta
import math

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


# ---- BVG-MINUTENLOGIK ----

def bvg_display_time(when_iso):
    dt = datetime.fromisoformat(when_iso)

    # BVG zeigt IMMER 1 Minute früher an
    dt = dt - timedelta(minutes=1)

    # Sekunden entfernen (BVG zeigt nie Sekunden)
    dt = dt.replace(second=0)

    return dt.strftime("%H:%M")


def bvg_minutes(when_iso):
    dt = datetime.fromisoformat(when_iso)
    now = datetime.now(timezone.utc).astimezone()

    # BVG: IMMER -1 Minute Offset zur realen Zeit
    dt = dt - timedelta(minutes=1)

    diff_sec = (dt - now).total_seconds()

    if diff_sec <= 0:
        return 0

    # alles Positive aufrunden
    return math.ceil(diff_sec / 60)