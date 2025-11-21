import requests
import json


def fetch_trip_shape(base_url, trip_id):
    """
    Robust fetch: holt Polyline aus dem Trip.
    Egal ob:
    - data["polyline"]["features"]
    - data["trip"]["polyline"]["features"]
    """

    url = f"{base_url}/trips/{trip_id}"
    params = {"polyline": "true"}

    print("Requesting trip polyline:", url)

    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    # Variante A: polyline auf Top-Level
    if "polyline" in data and "features" in data["polyline"]:
        features = data["polyline"]["features"]
        if features:
            return {
                "type": "LineString",
                "coordinates": [
                    f["geometry"]["coordinates"] for f in features
                ]
            }

    # Variante B: polyline unter data["trip"]
    trip = data.get("trip", {})
    poly = trip.get("polyline")
    if poly and "features" in poly and poly["features"]:
        features = poly["features"]
        return {
            "type": "LineString",
            "coordinates": [
                f["geometry"]["coordinates"] for f in features
            ]
        }

    # Falls wir *trotzdem* nichts finden
    raise ValueError("Keine Polyline im Trip gefunden – weder in /polyline noch trip.polyline!")