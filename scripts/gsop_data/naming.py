"""Region names from Natural Earth (decision B12): the desert, plateau or range a centroid lies in or is near,
else the nearest populated place. Labels only; nothing here touches a score.

Reads the raw Natural Earth GeoJSON files in data/reference/raw/ (hashes in data/MANIFEST.csv).
"""
import json
import os

import numpy as np

REGIONS_FILE = "data/reference/raw/ne_10m_geography_regions_polys.geojson"
PLACES_FILE = "data/reference/raw/ne_10m_populated_places_simple.geojson"
REGION_CLASSES = {"Desert", "Plateau", "Range/mtn"}
PLACE_CLASSES = {"Populated place", "Populated Place", "Admin-1 capital", "Admin-0 capital", "Admin-1 region capital", "Admin-0 region capital", "Admin-0 capital alt"}

# Build choice (not set by v1 or the decision text): a physical region counts as "near" within this distance.
NEAR_KM = 200

KM_PER_DEG = 111.195
SOURCE_REGIONS = "Natural Earth 1:10m geography regions (desert, plateau, range), release v5.1.2, public domain"
SOURCE_PLACES = "Natural Earth 1:10m populated places, release v5.1.2, public domain"


_SMALL = {"of", "the", "and", "de", "du", "la", "le", "des", "del"}


def tidy(name):
    """Natural Earth writes large region names in capitals; show them in title case."""
    if not name.isupper():
        return name
    words = name.lower().split(" ")
    return " ".join(w if (i and w in _SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def _rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [[np.array(r, dtype=float) for r in poly] for poly in polys]


def _inside(lon, lat, rings):
    """Even-odd test over one polygon's rings (exterior plus holes). Features are wrapped in a list of polygons."""
    hit = False
    for poly in rings:
        c = False
        for ring in poly:
            x, y = ring[:, 0], ring[:, 1]
            x2, y2 = np.roll(x, -1), np.roll(y, -1)
            cond = (y > lat) != (y2 > lat)
            with np.errstate(divide="ignore", invalid="ignore"):
                xi = (x2 - x) * (lat - y) / (y2 - y) + x
            c ^= bool(np.sum(cond & (lon < xi)) % 2)
        hit = hit or c
    return hit


def _seg_km(lon, lat, rings):
    """Distance in km from a point to the outline segments, on a local flat projection (approximate, fine for labels)."""
    best = np.inf
    k = np.cos(np.radians(lat))
    for poly in rings:
        for ring in poly:
            # Unwrap the ring's longitudes so it is continuous, then shift it by whole turns to sit nearest the point.
            rl = np.degrees(np.unwrap(np.radians(ring[:, 0])))
            rl = rl + 360.0 * np.round((lon - rl.mean()) / 360.0)
            x = (rl - lon) * k
            y = ring[:, 1] - lat
            x2, y2 = np.roll(x, -1), np.roll(y, -1)
            dx, dy = x2 - x, y2 - y
            L = dx * dx + dy * dy
            with np.errstate(divide="ignore", invalid="ignore"):
                t = np.where(L > 0, -(x * dx + y * dy) / L, 0.0)
            t = np.clip(t, 0, 1)
            d = np.hypot(x + t * dx, y + t * dy)
            best = min(best, float(d.min()))
    return best * KM_PER_DEG


def _hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


class Namer:
    def __init__(self, root):
        self.regions_path = os.path.join(root, REGIONS_FILE)
        self.places_path = os.path.join(root, PLACES_FILE)
        self.feats = []
        for f in json.load(open(self.regions_path, encoding="utf-8"))["features"]:
            p = f["properties"]
            if p["FEATURECLA"] not in REGION_CLASSES:
                continue
            rings = _rings(f["geometry"])
            allx = np.concatenate([r[:, 0] for poly in rings for r in poly])
            ally = np.concatenate([r[:, 1] for poly in rings for r in poly])
            self.feats.append(
                {
                    "name": tidy(p["NAME"]),
                    "cls": p["FEATURECLA"],
                    "rings": rings,
                    "bbox": (allx.min(), ally.min(), allx.max(), ally.max()),
                    "area": float((allx.max() - allx.min()) * (ally.max() - ally.min())),
                }
            )
        # Stable order, so ties never depend on the order of the source file.
        self.feats.sort(key=lambda f: (f["cls"], f["name"], f["bbox"]))
        places = []
        for f in json.load(open(self.places_path, encoding="utf-8"))["features"]:
            p = f["properties"]
            if p["featurecla"] in PLACE_CLASSES:
                lon, lat = f["geometry"]["coordinates"][:2]
                places.append((p["name"], p.get("adm0name") or "", float(lat), float(lon)))
        places.sort(key=lambda r: (r[0], r[2], r[3]))
        self.pname = [r[0] for r in places]
        self.pcountry = [r[1] for r in places]
        self.plat = np.array([r[2] for r in places])
        self.plon = np.array([r[3] for r in places])

    def name(self, lat, lon):
        inside = [f for f in self.feats if f["bbox"][0] <= lon <= f["bbox"][2] and f["bbox"][1] <= lat <= f["bbox"][3] and _inside(lon, lat, f["rings"])]
        if inside:
            f = min(inside, key=lambda f: (f["area"], f["name"]))
            return {"name": f["name"], "feature_class": f["cls"], "relation": "inside", "distance_km": 0, "source": SOURCE_REGIONS}
        near = []
        for f in self.feats:
            b = f["bbox"]
            # cheap bbox rejection: skip features whose box is clearly farther than the cut-off
            dlat = max(b[1] - lat, 0, lat - b[3])
            if dlat * KM_PER_DEG > NEAR_KM * 1.5:
                continue
            d = _seg_km(lon, lat, f["rings"])
            if d <= NEAR_KM:
                near.append((d, f["name"], f))
        if near:
            d, _, f = min(near, key=lambda t: (t[0], t[1]))
            return {"name": f["name"], "feature_class": f["cls"], "relation": "near", "distance_km": int(round(d)), "source": SOURCE_REGIONS}
        dist = _hav(lat, lon, self.plat, self.plon)
        i = int(np.argmin(dist))
        return {
            "name": f"{self.pname[i]}, {self.pcountry[i]}" if self.pcountry[i] else self.pname[i],
            "feature_class": "Populated place",
            "relation": "nearest populated place",
            "distance_km": int(round(float(dist[i]))),
            "source": SOURCE_PLACES,
        }
