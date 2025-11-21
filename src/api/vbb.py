import requests
from datetime import datetime, timezone
import math
from typing import Dict, Any

BASE_URL = "http://localhost:3000"


def get_departures(
        stop_id: str,
        duration: int = 30,
        results: int = 10,
        remarks: bool = False,
) -> Dict[str, Any]:
    """
    Wrapper um /stops/{id}/departures am lokalen VBB-Proxy.
    """
    url = f"{BASE_URL}/stops/{stop_id}/departures"
    params = {
        "duration": duration,
        "results": results,
        "remarks": remarks,
        "tram": True,
        "bus": True,
        "suburban": True,
        "subway": True,
        "ferry": True,
        "express": True,
        "regional": True,
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()


def minutes_until(ts: str) -> int:
    """
    Rechnet ein ISO-8601-Datum (z.B. '2025-11-21T15:30:00+01:00')
    in Minuten bis zur Abfahrtszeit um.
    """
    # Kleine Robustheit für …Z am Ende
    if ts.endswith("Z"):
        ts = ts.replace("Z", "+00:00")

    dt = datetime.fromisoformat(ts)
    now = datetime.now(timezone.utc).astimezone()

    diff = (dt - now).total_seconds()
    if diff <= 0:
        return 0
    return math.ceil(diff / 60)