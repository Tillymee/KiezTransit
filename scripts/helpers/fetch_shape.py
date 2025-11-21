import requests
from typing import Dict, Any


def fetch_trip_shape(base_url: str, trip_id: str) -> Dict[str, Any]:
    """
    Holt die Polyline eines Trips und gibt sie in einem für Leaflet passenden Format zurück:

    {
      "type": "LineString",
      "coordinates": [
        [lat, lon],
        [lat, lon],
        ...
      ]
    }

    Dabei wird angenommen, dass die API GeoJSON-ähnliche Koordinaten im Format [lon, lat] liefert.
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
        coords_list = _features_to_latlon(features)
        if coords_list:
            return {
                "type": "LineString",
                "coordinates": coords_list,
            }

    # Variante B: polyline unter data["trip"]
    trip = data.get("trip", {})
    poly = trip.get("polyline")
    if poly and "features" in poly:
        features = poly["features"]
        coords_list = _features_to_latlon(features)
        if coords_list:
            return {
                "type": "LineString",
                "coordinates": coords_list,
            }

    raise ValueError("Keine Polyline im Trip gefunden – weder in polyline noch trip.polyline!")


def _features_to_latlon(features) -> list[list[float]]:
    """
    Hilfsfunktion: wandelt GeoJSON-Features mit Koordinaten [lon, lat]
    in eine einfache Liste [[lat, lon], ...] um.
    """
    coords_list: list[list[float]] = []

    for feat in features:
        geom = (feat or {}).get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords:
            continue

        # LineString / MultiLineString o.ä.
        if isinstance(coords[0], list):
            # Beispiel für LineString: [[lon, lat], [lon, lat], ...]
            for pair in coords:
                if not isinstance(pair, list) or len(pair) < 2:
                    continue
                lng, lat = pair[:2]
                coords_list.append([lat, lng])
        else:
            # Einzelpunkt [lon, lat]
            lng, lat = coords[:2]
            coords_list.append([lat, lng])

    return coords_list