import os
import sys
import json
import requests
from typing import Optional, List, Dict

BASE_URL = "http://localhost:3000"

# Projekt-Root: eine Ebene über /scripts
ROOT = os.path.dirname(os.path.dirname(__file__))

# Configs: config/lines/<id>.config.json
CONFIG_DIR = os.path.join(ROOT, "config", "lines")

# Output-Daten: public/data
DATA_DIR = os.path.join(ROOT, "public", "data")
LINES_INDEX_PATH = os.path.join(DATA_DIR, "lines.json")


# ------------------------------------------------------------
# Hilfsfunktionen für Netzwerk-Calls
# ------------------------------------------------------------
def fetch_departures(seed_stop_id: str) -> List[Dict]:
    """
    Holt Abfahrten an einer Seed-Haltestelle.
    Wir filtern später nach Linienname & Richtung.
    """
    url = f"{BASE_URL}/stops/{seed_stop_id}/departures"
    params = {
        "duration": 60,
        "results": 50,
        "remarks": False,
        "tram": True,
        "bus": True,
        "suburban": True,
        "subway": True,
        "ferry": True,
        "express": True,
        "regional": True,
    }

    print(f"Requesting departures: {url}")
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    return data.get("departures", [])


def discover_trip_for_line(
        line_name: str,
        direction_hint: Optional[str],
        seed_stop_id: str,
) -> str:
    """
    Sucht eine passende Trip-ID für die gegebene Linie.
    Nutzt die Seed-Haltestelle (idealerweise Endstation).
    """

    deps = fetch_departures(seed_stop_id)

    # 1. Nur die richtige Linie
    deps = [d for d in deps if d.get("line", {}).get("name") == line_name]

    if direction_hint:
        # 2. Optional nach Richtung einschränken
        deps_dir = [
            d
            for d in deps
            if direction_hint in (d.get("direction") or "")
        ]
        if deps_dir:
            deps = deps_dir

    if not deps:
        raise RuntimeError(
            f"Keine Abfahrten für Linie '{line_name}' an Stop {seed_stop_id} gefunden.\n"
            f"→ Läuft die Linie dort gerade? (Seed-Stop ist idealerweise eine Endhaltestelle.)"
        )

    trip_id = deps[0].get("tripId")
    if not trip_id:
        raise RuntimeError("Gefundene Abfahrt hat keine tripId")

    print(f"✓ Beispiel-Trip für {line_name} gefunden: {trip_id} → {deps[0].get('direction')}")
    return trip_id


def fetch_trip(trip_id: str) -> Dict:
    """
    Holt die Trip-Details inklusive Polyline.
    """
    url = f"{BASE_URL}/trips/{trip_id}?polyline=true"
    print("Requesting trip:", url)

    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    trip = data.get("trip")
    if not trip:
        raise ValueError("Antwort enthält kein 'trip'-Objekt")

    return trip


# ------------------------------------------------------------
# Extraktion von Stops & Shape
# ------------------------------------------------------------
def extract_stops(trip: Dict) -> List[Dict]:
    """
    Extrahiert die Stop-Liste in Fahrt-Reihenfolge aus trip['stopovers'].
    Jeder Stop: {id, name, lat, lon}
    """
    stopovers = trip.get("stopovers", [])
    result: List[Dict] = []
    seen_ids = set()

    for so in stopovers:
        stop = so.get("stop")
        if not stop:
            continue

        sid = stop.get("id")
        if not sid or sid in seen_ids:
            continue
        seen_ids.add(sid)

        loc = stop.get("location") or {}
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        result.append(
            {
                "id": sid,
                "name": stop.get("name"),
                "lat": lat,
                "lon": lon,
            }
        )

    return result


def extract_shape(trip: Dict) -> List[List[float]]:
    """
    Extrahiert die Polyline-Koordinaten in Leaflet-Form:
    [[lat, lon], [lat, lon], ...]
    """
    poly = trip.get("polyline") or {}
    features = poly.get("features") or []

    coords_list: List[List[float]] = []

    for feat in features:
        geom = (feat or {}).get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords:
            continue

        # Erwartet: GeoJSON → [lon, lat] oder verschachtelt
        if isinstance(coords[0], list):
            # LineString etc.
            for pair in coords:
                if not isinstance(pair, list) or len(pair) < 2:
                    continue
                lng, lat = pair[:2]
                coords_list.append([lat, lng])
        else:
            lng, lat = coords[:2]
            coords_list.append([lat, lng])

    if not coords_list:
        raise ValueError("Keine Koordinaten in der Polyline gefunden")

    return coords_list


# ------------------------------------------------------------
# Konfig laden & JSON bauen
# ------------------------------------------------------------
def load_config(line_id: str) -> Dict:
    """
    Lädt z.B. config/lines/m2.config.json
    """
    path = os.path.join(CONFIG_DIR, f"{line_id}.config.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config nicht gefunden: {path}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Minimal-Validierung
    for key in ("id", "name", "product", "color", "seedStopId"):
        if key not in cfg:
            raise ValueError(f"Config {path} fehlt Schlüssel '{key}'")

    return cfg


def build_line_json(cfg: Dict) -> Dict:
    """
    Baut das komplette JSON für eine Linie:
    - Metadaten (id, name, product, color)
    - stops[]
    - shape{coordinates}
    """
    line_name = cfg["name"]  # z.B. "M2"
    seed_stop_id = cfg["seedStopId"]  # z.B. "900141001"
    direction_hint = cfg.get("direction")  # z.B. "S+U Alexanderplatz"

    trip_id = discover_trip_for_line(line_name, direction_hint, seed_stop_id)
    trip = fetch_trip(trip_id)

    stops = extract_stops(trip)
    shape_coords = extract_shape(trip)

    return {
        "id": cfg["id"],  # "m2"
        "name": line_name,  # "M2"
        "product": cfg.get("product", "tram"),
        "color": cfg.get("color", "#d81e05"),
        "stops": stops,
        "shape": {
            "type": "LineString",
            "coordinates": shape_coords,
        },
    }


# ------------------------------------------------------------
# Speicherung in public/data
# ------------------------------------------------------------
def ensure_data_dir_exists() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def update_lines_index(line_data: Dict) -> None:
    """
    Aktualisiert public/data/lines.json:
    - sorgt dafür, dass die Linie eingetragen ist
    - hält Name, Produkt, Farbe aktuell
    """
    ensure_data_dir_exists()

    if os.path.exists(LINES_INDEX_PATH):
        with open(LINES_INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"lines": []}

    lines = index.get("lines", [])

    for entry in lines:
        if entry.get("id") == line_data["id"]:
            # Update bestehender Eintrag
            entry["name"] = line_data["name"]
            entry["product"] = line_data["product"]
            entry["color"] = line_data["color"]
            break
    else:
        # Neuer Eintrag
        lines.append(
            {
                "id": line_data["id"],
                "name": line_data["name"],
                "product": line_data["product"],
                "color": line_data["color"],
            }
        )

    index["lines"] = lines

    with open(LINES_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"✔ Aktualisiert: {LINES_INDEX_PATH}")


def build_line(line_id: str) -> None:
    """
    Baut eine Linie aus <line_id>.config.json
    und speichert sie als public/data/<id>.line.json
    """
    print(f"\n=== Baue Linie: {line_id} ===")
    cfg = load_config(line_id)
    line_data = build_line_json(cfg)

    ensure_data_dir_exists()
    out_path = os.path.join(DATA_DIR, f"{line_data['id']}.line.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(line_data, f, indent=2, ensure_ascii=False)

    print(f"✔ Linie gespeichert: {out_path}")

    update_lines_index(line_data)


def main() -> None:
    # Aufruf:
    #   python scripts/build_line.py m2
    # oder:
    #   python scripts/build_line.py m2 m1 u2
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_line.py <line_id> [<line_id> ...]")
        print("Beispiel: python scripts/build_line.py m2")
        sys.exit(1)

    line_ids = sys.argv[1:]

    for lid in line_ids:
        try:
            build_line(lid)
        except Exception as e:
            print(f"❌ Fehler bei Linie '{lid}': {e}")


if __name__ == "__main__":
    main()