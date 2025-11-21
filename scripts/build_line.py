# scripts/build_line.py
import json
import os
import sys
from typing import List, Dict, Any

import requests

# Damit wir helpers.* importieren können
SCRIPT_DIR = os.path.dirname(__file__)
sys.path.insert(0, SCRIPT_DIR)

from helpers.fetch_stops import fetch_stops_for_names  # type: ignore
from helpers.fetch_shape import fetch_trip_shape  # type: ignore

# Lokales vbb-rest
BASE_URL = "http://localhost:3000"

# Eine M2-Haltestelle, an der wir einen Trip "einsammeln"
M2_SEED_STOP_ID = "900141507"  # Prenzlauer Prom./Am Steinberg

# Reihenfolge der M2-Stationen (Nord → Süd)
M2_STOP_NAMES: List[str] = [
    "Heinersdorf",
    "Rothenbachstr.",
    "Heinersdorf Kirche",
    "Am Wasserturm",
    "Tino-Schwierzina-Str.",
    "Am Steinberg",
    "Prenzlauer Prom./Am Steinberg",
    "Prenzlauer Allee/Ostseestr.",
    "Erich-Weinert-Str.",
    "S Prenzlauer Allee",
    "Fröbelstr.",
    "Prenzlauer Allee/Danziger Str.",
    "Marienburger Str.",
    "Knaackstr.",
    "Prenzlauer Allee/Metzer Str.",
    "Mollstr./Prenzlauer Allee",
    "S+U Alexanderplatz/Memhardstr.",
    "S+U Alexanderplatz/Dircksenstr.",
]


def find_example_m2_trip_id() -> str:
    """
    Holt Abfahrten an M2_SEED_STOP_ID und nimmt den ersten Trip der Linie M2
    Richtung Alexanderplatz als "Beispieltrip" für die Liniengeometrie.
    """
    url = f"{BASE_URL}/stops/{M2_SEED_STOP_ID}/departures"
    params = {
        "duration": 60,
        "tram": True,
        "bus": False,
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    departures: List[Dict[str, Any]] = data.get("departures", [])

    for dep in departures:
        line = dep.get("line", {}).get("name")
        direction = dep.get("direction", "") or ""
        if line == "M2" and "Alexanderplatz" in direction:
            trip_id = dep.get("tripId")
            if trip_id:
                print("✓ Beispiel-M2-Trip gefunden:", trip_id, "→", direction)
                return trip_id

    raise RuntimeError("Kein M2-Trip Richtung Alexanderplatz gefunden!")


def build_m2_json() -> Dict[str, Any]:
    """
    Baut das komplette JSON-Objekt für die Linie M2:
    {
      "id": "M2",
      "name": "Tram M2",
      "color": "#7AB929",
      "stops": [...],
      "shape": { ... }
    }
    """
    # 1) Stops inkl. Koordinaten holen
    stops = fetch_stops_for_names(BASE_URL, M2_STOP_NAMES)

    # 2) Beispiel-TripID finden & Shape laden
    trip_id = find_example_m2_trip_id()
    shape = fetch_trip_shape(BASE_URL, trip_id)

    line_data: Dict[str, Any] = {
        "id": "M2",
        "name": "Tram M2",
        "color": "#7AB929",
        "stops": stops,
        "shape": shape,
    }
    return line_data


def main():
    # Projektroot (= eine Ebene über scripts/)
    root = os.path.dirname(SCRIPT_DIR)

    data_dir = os.path.join(root, "public", "data")
    os.makedirs(data_dir, exist_ok=True)

    # 1) m2.json schreiben
    m2_data = build_m2_json()
    m2_path = os.path.join(data_dir, "m2.json")

    with open(m2_path, "w", encoding="utf-8") as f:
        json.dump(m2_data, f, indent=2, ensure_ascii=False)

    print("✔ Gespeichert:", m2_path)

    # 2) lines.json aktualisieren (hier erstmal nur M2)
    lines_path = os.path.join(data_dir, "lines.json")
    lines_config = [
        {
            "id": "M2",
            "name": "Tram M2",
            "file": "m2.json",
            "color": "#7AB929",
        }
    ]

    with open(lines_path, "w", encoding="utf-8") as f:
        json.dump(lines_config, f, indent=2, ensure_ascii=False)

    print("✔ Gespeichert:", lines_path)


if __name__ == "__main__":
    main()