import requests
from typing import List, Dict


def fetch_stops_for_names(base_url: str, names: List[str]) -> List[Dict]:
    """
    Sucht zu einer Liste von Haltestellennamen passende "stop"-Objekte
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

        # Präziseste Koordinatenquelle bevorzugen
        platform_loc = stop.get("platformLocation") or {}

        if platform_loc.get("latitude") and platform_loc.get("longitude"):
            lat = platform_loc.get("latitude")
            lon = platform_loc.get("longitude")
        else:
            loc = stop.get("location") or {}
            lat = loc.get("latitude")
            lon = loc.get("longitude")

        results.append(
            {
                "name": stop.get("name", name),
                "id": stop.get("id"),
                "lat": lat,
                "lon": lon,
            }
        )

        print(f"✓ {name}: {lat}, {lon}")

    return results