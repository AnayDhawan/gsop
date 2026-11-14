"""EPSG:6933 6 km grid used by v1. tile_id = iy * ncols + ix. Pure coordinate conversion, no scoring."""
import numpy as np
from pyproj import Transformer

_INV = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True)
_FWD = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)


class Grid:
    def __init__(self, g):
        self.ncols = int(g["ncols"])
        self.nrows = int(g["nrows"])
        self.cell = float(g["cell_m"])
        self.x0 = float(g["x0"])
        self.y_top = float(g["y_top"])

    def ixiy(self, tile_id):
        iy, ix = np.divmod(np.asarray(tile_id, dtype=np.int64), self.ncols)
        return ix, iy

    def lonlat(self, tile_id):
        ix, iy = self.ixiy(tile_id)
        x = self.x0 + (ix + 0.5) * self.cell
        y = self.y_top - (iy + 0.5) * self.cell
        lon, lat = _INV.transform(x, y)
        return np.asarray(lon), np.asarray(lat)

    def cell_of(self, lon, lat):
        x, y = _FWD.transform(lon, lat)
        ix = int(np.floor((x - self.x0) / self.cell))
        iy = int(np.floor((self.y_top - y) / self.cell))
        return ix, iy


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(np.asarray(lon2) - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))
