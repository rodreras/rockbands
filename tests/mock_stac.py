"""A local mock STAC API with synthetic rasters shaped like the real catalogues.

It lets the example notebooks run offline (see ``test_notebooks.py``). Asset keys, dtypes, no-data
values, scale/offset conventions and projections follow the real collections:

* ``sentinel-2-l2a``  Earth Search: blue/green/red/nir/nir08/..., ``scl``; uint16 DN with a -1000 offset
* ``landsat-c2-l2``   Earth Search: coastal/blue/green/red/nir08/swir16/swir22, ``qa_pixel``; uint16 DN
* ``aster-l1t``       Planetary Computer: multi-band ``VNIR`` (uint8), ``SWIR`` (uint8), ``TIR`` (uint16)

The pixel values are smooth synthetic fields, not real imagery: they exercise the code paths,
they do not say anything about the minerals in a scene.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds

PAD_M = 1500


def _field(shape, seed):
    """Smooth pattern in [0.7, 1.3] so ratios are finite and spatially structured."""
    rng = np.random.default_rng(seed)
    rows, cols = shape
    y, x = np.mgrid[0:rows, 0:cols]
    wave = np.sin(x / (cols / 5.0) + seed) * np.cos(y / (rows / 4.0) - seed)
    return 1.0 + 0.25 * wave + 0.05 * rng.standard_normal(shape)


def _grid(bbox, epsg, resolution):
    west, south, east, north = transform_bounds("EPSG:4326", f"EPSG:{epsg}", *bbox)
    west, south = west - PAD_M, south - PAD_M
    east, north = east + PAD_M, north + PAD_M
    step = 60 * 4  # common multiple of every native resolution, so grids align exactly
    west, north = np.floor(west / step) * step, np.ceil(north / step) * step
    cols = int(np.ceil((east - west) / resolution))
    rows = int(np.ceil((north - south) / resolution))
    return from_origin(west, north, resolution, resolution), rows, cols


def _write(path: Path, data: np.ndarray, transform, epsg: int, nodata=0):
    data = data if data.ndim == 3 else data[None]
    with rasterio.open(
        path, "w", driver="GTiff", height=data.shape[1], width=data.shape[2], count=data.shape[0],
        dtype=data.dtype, crs=f"EPSG:{epsg}", transform=transform, nodata=nodata,
    ) as dst:
        dst.write(data)


def _asset(path: Path, transform, rows, cols, extra=None):
    asset = {
        "href": str(path),
        "type": "image/tiff; application=geotiff; profile=cloud-optimized",
        "roles": ["data"],
        "proj:shape": [rows, cols],
        "proj:transform": [transform.a, transform.b, transform.c, transform.d, transform.e, transform.f, 0, 0, 1],
    }
    asset.update(extra or {})
    return asset


def _item(item_id, collection, bbox, epsg, properties, assets):
    west, south, east, north = bbox
    return {
        "type": "Feature", "stac_version": "1.0.0", "id": item_id, "collection": collection,
        "stac_extensions": ["https://stac-extensions.github.io/projection/v2.0.0/schema.json",
                            "https://stac-extensions.github.io/raster/v1.1.0/schema.json"],
        "bbox": list(bbox),
        "geometry": {"type": "Polygon", "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]]},
        "properties": {"proj:code": f"EPSG:{epsg}", **properties},
        "assets": assets, "links": [],
    }


# approximate surface reflectance of each Sentinel-2 asset
_S2 = {"coastal": (60, .05), "blue": (10, .06), "green": (10, .09), "red": (10, .13), "rededge1": (20, .15),
       "rededge2": (20, .20), "rededge3": (20, .22), "nir": (10, .26), "nir08": (20, .26), "nir09": (60, .27),
       "swir16": (20, .30), "swir22": (20, .22)}
_L8 = {"coastal": .05, "blue": .06, "green": .09, "red": .13, "nir08": .26, "swir16": .30, "swir22": .22}


def sentinel2_items(root: Path, bbox) -> List[dict]:
    epsg = 32723
    out = []
    for n, (name, cloud, date) in enumerate([("A", 3.0, "2025-07-10"), ("B", 1.0, "2025-07-25")]):
        folder = root / f"s2_{name}"
        folder.mkdir(parents=True, exist_ok=True)
        assets = {}
        for key, (res, refl) in _S2.items():
            tr, rows, cols = _grid(bbox, epsg, res)
            dn = np.clip((refl * _field((rows, cols), n + len(key)) * 10000 + 1000), 1, 65000).astype("uint16")
            path = folder / f"{key}.tif"
            _write(path, dn, tr, epsg)
            assets[key] = _asset(path, tr, rows, cols, {"raster:bands": [{"nodata": 0, "data_type": "uint16", "scale": 0.0001, "offset": -0.1}]})
        tr, rows, cols = _grid(bbox, epsg, 20)
        scl = np.full((rows, cols), 5, "uint8")
        scl[: rows // 6, : cols // 5] = 9  # a cloud patch
        scl[rows // 2 : rows // 2 + 10, cols // 2 : cols // 2 + 10] = 3  # a shadow patch
        path = folder / "scl.tif"
        _write(path, scl, tr, epsg)
        assets["scl"] = _asset(path, tr, rows, cols, {"raster:bands": [{"nodata": 0, "data_type": "uint8"}]})
        out.append(_item(f"S2{name}_MOCK_{date}", "sentinel-2-l2a", bbox, epsg,
                         {"datetime": f"{date}T13:05:00Z", "platform": f"sentinel-2{name.lower()}", "eo:cloud_cover": cloud,
                          "s2:processing_baseline": "05.11"}, assets))
    return out


def landsat_items(root: Path, bbox) -> List[dict]:
    epsg = 32750
    out = []
    for n, (platform, cloud, date) in enumerate([("LANDSAT_9", 0.5, "2025-07-02"), ("LANDSAT_8", 4.0, "2025-07-10"), ("LANDSAT_8", 2.0, "2025-08-11")]):
        folder = root / f"l8_{n}"
        folder.mkdir(parents=True, exist_ok=True)
        tr, rows, cols = _grid(bbox, epsg, 30)
        assets = {}
        for key, refl in _L8.items():
            dn = np.clip((refl * _field((rows, cols), n + len(key)) + 0.2) / 2.75e-5, 1, 65000).astype("uint16")
            path = folder / f"{key}.tif"
            _write(path, dn, tr, epsg)
            assets[key] = _asset(path, tr, rows, cols, {"raster:bands": [{"nodata": 0, "data_type": "uint16", "scale": 2.75e-5, "offset": -0.2}]})
        qa = np.full((rows, cols), 21824, "uint16")  # clear land
        qa[: rows // 5, : cols // 4] |= 1 << 3  # cloud
        qa[rows // 2 : rows // 2 + 8, :8] |= 1 << 4  # shadow
        path = folder / "qa_pixel.tif"
        _write(path, qa, tr, epsg, nodata=1)
        assets["qa_pixel"] = _asset(path, tr, rows, cols, {"raster:bands": [{"nodata": 1, "data_type": "uint16"}]})
        out.append(_item(f"{platform}_MOCK_{date}", "landsat-c2-l2", bbox, epsg,
                         {"datetime": f"{date}T02:15:00Z", "platform": platform, "eo:cloud_cover": cloud}, assets))
    return out


def aster_items(root: Path, bbox) -> List[dict]:
    epsg = 32611
    out = []
    for n, (date, cloud, with_swir) in enumerate([("2001-06-12", 0.0, False), ("2004-05-17", 2.0, True), ("2005-09-30", 8.0, True)]):
        folder = root / f"aster_{n}"
        folder.mkdir(parents=True, exist_ok=True)
        assets = {}
        if with_swir:
            for key, (res, count, dtype, lo, hi) in {"VNIR": (15, 3, "uint8", 40, 160), "SWIR": (30, 6, "uint8", 20, 120),
                                                     "TIR": (90, 5, "uint16", 1800, 3000)}.items():
                tr, rows, cols = _grid(bbox, epsg, res)
                layers = [np.clip(lo + (hi - lo) * (_field((rows, cols), n + b + len(key)) - 0.7) / 0.6, 1, np.iinfo(dtype).max)
                          for b in range(count)]
                path = folder / f"{key}.tif"
                _write(path, np.stack(layers).astype(dtype), tr, epsg)
                assets[key] = _asset(path, tr, rows, cols)
        out.append(_item(f"AST_L1T_MOCK_{date}", "aster-l1t", bbox, epsg,
                         {"datetime": f"{date}T18:30:00Z", "platform": "terra", "eo:cloud_cover": cloud}, assets))
    return out


class _Handler(BaseHTTPRequestHandler):
    catalog: Dict[str, List[dict]] = {}

    def log_message(self, *args):  # keep test output quiet
        pass

    def _send(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _base(self):
        return f"http://{self.headers['Host']}"

    def _root(self):
        base = self._base()
        return {
            "type": "Catalog", "id": "mock-stac", "stac_version": "1.0.0", "description": "mock STAC API",
            "conformsTo": ["https://api.stacspec.org/v1.0.0/core", "https://api.stacspec.org/v1.0.0/item-search",
                           "https://api.stacspec.org/v1.0.0/item-search#query"],
            "links": [{"rel": "self", "href": f"{base}/"}, {"rel": "root", "href": f"{base}/"},
                      {"rel": "search", "type": "application/geo+json", "href": f"{base}/search", "method": "GET"},
                      {"rel": "search", "type": "application/geo+json", "href": f"{base}/search", "method": "POST"}],
        }

    def _search(self, params):
        wanted = params.get("collections") or list(self.catalog)
        if isinstance(wanted, str):
            wanted = wanted.split(",")
        items = [i for c in wanted for i in self.catalog.get(c, [])]
        limit = (params.get("query") or {}).get("eo:cloud_cover", {}).get("lt")
        if limit is not None:
            items = [i for i in items if i["properties"].get("eo:cloud_cover", 0) < limit]
        return {"type": "FeatureCollection", "features": items, "links": []}

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path in ("/", ""):
            return self._send(self._root())
        if path == "/conformance":
            return self._send({"conformsTo": self._root()["conformsTo"]})
        if path == "/search":
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            return self._send(self._search(params))
        self._send({"code": "NotFound"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path.split("?")[0] == "/search":
            return self._send(self._search(body))
        self._send({"code": "NotFound"}, 404)


def build_catalog(root: Path) -> Dict[str, List[dict]]:
    root.mkdir(parents=True, exist_ok=True)
    return {
        "sentinel-2-l2a": sentinel2_items(root, (-43.80, -20.45, -43.55, -20.20)),
        "landsat-c2-l2": landsat_items(root, (119.55, -23.45, 119.85, -23.20)),
        "aster-l1t": aster_items(root, (-117.32, 37.48, -117.10, 37.62)),
    }


def serve(root: Path):
    """Start the mock API on a free local port. Returns ``(base_url, stop)``."""
    _Handler.catalog = build_catalog(root)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{server.server_port}", server.shutdown


if __name__ == "__main__":  # python tests/mock_stac.py /tmp/mock : serve until Ctrl-C
    import sys
    import time

    url, stop = serve(Path(sys.argv[1] if len(sys.argv) > 1 else "mock_data"))
    print("mock STAC API at", url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()
