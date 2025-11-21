import os
import sys
import json
import requests
from typing import Optional, List, Dict

BASE_URL = "http://localhost:3000"

# Projekt-Root
ROOT = os.path.dirname(os.path.dirname(__file__))

# Configs: config/lines/<id>.config.json
CONFIG_DIR = os.path.join(ROOT, "config", "lines")

# Output: public/data
DATA_DIR = os.path.join(ROOT, "public", "data")
LINES_INDEX_PATH = os.path.join(DATA_DIR, "lines.json")


# ------------------------------------------------------------
# Netzwerkfunktionen
# ------------------------------------------------------------
def fetch_departures(seed_stop_id: str) -> List[Dict]:
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
    deps = fetch_departures(seed_stop_id)

    deps = [d for d in deps if d.get("line", {}).get("name") == line_name]

    if direction_hint:
        deps_dir = [
            d for d in deps
            if direction_hint in (d.get("direction") or "")
        ]
        if deps_dir:
            deps = deps_dir

    if not deps:
        raise RuntimeError(
            f"Keine Abfahrten für Linie '{line_name}' an Stop {seed_stop_id} gefunden."
        )

    trip_id = deps[0].get("tripId")
    if not trip_id:
        raise RuntimeError("Abfahrt ohne tripId erhalten")

    print(f"✓ Trip für {line_name}: {trip_id} → {deps[0].get('direction')}")
    return trip_id


def fetch_trip(trip_id: str) -> Dict:
    url = f"{BASE_URL}/trips/{trip_id}?polyline=true"
    print("Requesting trip:", url)

    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    trip = data.get("trip")
    if not trip:
        raise ValueError("Antwort enthält kein trip-Objekt")

    return trip


# ------------------------------------------------------------
# Extraktion Shape + Stops (inkl. Snapping)
# ------------------------------------------------------------
def extract_shape(trip: Dict) -> List[List[float]]:
    poly = trip.get("polyline") or {}
    features = poly.get("features") or []

    coords_list = []

    for feat in features:
        geom = (feat or {}).get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords:
            continue

        if isinstance(coords[0], list):
            for pair in coords:
                if not isinstance(pair, list) or len(pair) < 2:
                    continue
                lng, lat = pair[:2]
                coords_list.append([lat, lng])
        else:
            lng, lat = coords[:2]
            coords_list.append([lat, lng])

    if not coords_list:
        raise ValueError("Polyline leer")

    return coords_list


# SNAPPING-MATH ------------------------------------------------

def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def snap_point_to_segment(px, py, ax, ay, bx, by):
    AP = (px - ax, py - ay)
    AB = (bx - ax, by - ay)

    sq_len_ab = AB[0] * AB[0] + AB[1] * AB[1]
    if sq_len_ab == 0:
        return ax, ay

    t = dot(AP, AB) / sq_len_ab
    t = max(0, min(1, t))

    x = ax + AB[0] * t
    y = ay + AB[1] * t
    return x, y


def snap_to_shape(lat, lon, shape):
    best_dist = float("inf")
    best_point = (lat, lon)

    px, py = lat, lon

    for i in range(len(shape) - 1):
        ax, ay = shape[i]
        bx, by = shape[i + 1]

        sx, sy = snap_point_to_segment(px, py, ax, ay, bx, by)
        d = (px - sx) ** 2 + (py - sy) ** 2

        if d < best_dist:
            best_dist = d
            best_point = (sx, sy)

    return best_point


# EXTRACT_STOPS ------------------------------------------------
def extract_stops(trip: Dict) -> List[Dict]:
    stopovers = trip.get("stopovers", [])
    shape = extract_shape(trip)

    result = []
    seen = set()

    def get_precise_coords(so):
        stop = so.get("stop") or {}

        # 1. platformLocation (falls vorhanden – U-Bahn/S-Bahn, nie Tram)
        pl = stop.get("platformLocation")
        if pl and pl.get("latitude") and pl.get("longitude"):
            return pl["latitude"], pl["longitude"]

        # 2. location (Tram!)
        loc = stop.get("location") or {}
        if loc.get("latitude") and loc.get("longitude"):
            return loc["latitude"], loc["longitude"]

        return None, None

    for so in stopovers:
        stop = so.get("stop") or {}
        sid = stop.get("id")

        if not sid or sid in seen:
            continue
        seen.add(sid)

        lat, lon = get_precise_coords(so)
        if lat is None or lon is None:
            continue

        # SNAPPING
        snapped_lat, snapped_lon = snap_to_shape(lat, lon, shape)

        result.append({
            "id": sid,
            "name": stop.get("name"),
            "lat": snapped_lat,
            "lon": snapped_lon,
        })

    return result


# ------------------------------------------------------------
# Generierung des Line-JSON
# ------------------------------------------------------------
def load_config(line_id: str) -> Dict:
    path = os.path.join(CONFIG_DIR, f"{line_id}.config.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config nicht gefunden: {path}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    for key in ("id", "name", "product", "color", "seedStopId"):
        if key not in cfg:
            raise ValueError(f"Config {path} fehlt Schlüssel '{key}'")

    return cfg


def build_line_json(cfg: Dict) -> Dict:
    line_name = cfg["name"]
    seed_stop_id = cfg["seedStopId"]
    direction_hint = cfg.get("direction")

    trip_id = discover_trip_for_line(line_name, direction_hint, seed_stop_id)
    trip = fetch_trip(trip_id)

    stops = extract_stops(trip)
    shape_coords = extract_shape(trip)

    return {
        "id": cfg["id"],
        "name": line_name,
        "product": cfg.get("product", "tram"),
        "color": cfg.get("color", "#d81e05"),
        "stops": stops,
        "shape": {
            "type": "LineString",
            "coordinates": shape_coords,
        },
    }


# ------------------------------------------------------------
# Storage
# ------------------------------------------------------------
def ensure_data_dir_exists():
    os.makedirs(DATA_DIR, exist_ok=True)


def update_lines_index(line_data: Dict):
    ensure_data_dir_exists()

    if os.path.exists(LINES_INDEX_PATH):
        with open(LINES_INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"lines": []}

    lines = index.get("lines", [])

    for entry in lines:
        if entry.get("id") == line_data["id"]:
            entry["name"] = line_data["name"]
            entry["product"] = line_data["product"]
            entry["color"] = line_data["color"]
            break
    else:
        lines.append({
            "id": line_data["id"],
            "name": line_data["name"],
            "product": line_data["product"],
            "color": line_data["color"],
        })

    index["lines"] = lines

    with open(LINES_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"✔ Aktualisiert: {LINES_INDEX_PATH}")


def build_line(line_id: str):
    print(f"\n=== Baue Linie: {line_id} ===")
    cfg = load_config(line_id)
    line_data = build_line_json(cfg)

    ensure_data_dir_exists()
    out_path = os.path.join(DATA_DIR, f"{line_data['id']}.line.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(line_data, f, indent=2, ensure_ascii=False)

    print(f"✔ Linie gespeichert: {out_path}")
    update_lines_index(line_data)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_line.py <line_id> [...]")
        sys.exit(1)

    for lid in sys.argv[1:]:
        try:
            build_line(lid)
        except Exception as e:
            print(f"❌ Fehler bei '{lid}': {e}")


if __name__ == "__main__":
    main()