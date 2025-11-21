# scripts/helpers/fetch_stops.py
import requests
from typing import List, Dict


def fetch_stops_for_names(base_url: str, names: List[str]) -> List[Dict]:
    """
    Sucht zu einer Liste von Haltestellennamen die passenden "stop"-Objekte
    via /locations?query=...
    Rückgabe: Liste von Dicts mit name, id, lat, lon.
    """
    results: List[Dict] = []

    for name in names:
        url = f"{base_url}/locations"
        r = requests.get(url, params={"query": name})
        r.raise_for_status()
        data = r.json()

        stop = None
        for item in data:
            if item.get("type") == "stop":
                stop = item
                break

        if stop is None:
            print(f"⚠️ Stop nicht gefunden: {name}")
            results.append(
                {
                    "name": name,
                    "id": None,
                    "lat": None,
                    "lon": None,
                }
            )
            continue

        loc = stop.get("location") or {}
        results.append(
            {
                "name": stop.get("name", name),
                "id": stop.get("id"),
                "lat": loc.get("latitude"),
                "lon": loc.get("longitude"),
            }
        )

        print(f"✓ {name}: {loc.get('latitude')}, {loc.get('longitude')}")

    return results