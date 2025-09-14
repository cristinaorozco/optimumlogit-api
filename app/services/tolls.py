# app/services/tolls.py
from fastapi import Request

def count_tolls_on_route(request: Request, route_coords):
    tolls_geo = getattr(request.app.state, "tolls_geojson", None)
    if not tolls_geo:
        return 0
    # ... tu lógica de intersección/buffer contra los features del GeoJSON ...
    return tolls_count


# app/services/tolls.py
from math import radians, sin, cos, asin, sqrt

def haversine_m(p1, p2):
    # p1=(lon,lat), p2=(lon,lat)
    lon1, lat1 = map(radians, p1)
    lon2, lat2 = map(radians, p2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2*asin(sqrt(a))
    return 6371000 * c  # metros

def count_tolls_on_route(route_coords, tolls_geojson, radius_m=60):
    """
    route_coords: lista de (lon,lat) decodificados de la polyline de Mapbox
    tolls_geojson: dict FeatureCollection (tu archivo cargado)
    """
    if not tolls_geojson or not route_coords:
        return 0, 0.0

    seen = set()
    total_fee = 0.0

    for feat in tolls_geojson["features"]:
        gate_id = feat["properties"]["id"]
        fee = float(feat["properties"].get("fee_aed", 0) or 0)
        gate = tuple(feat["geometry"]["coordinates"])  # (lon,lat)

        # chequear si algún punto del camino está cerca del gate
        near = any(haversine_m(gate, p) <= radius_m for p in route_coords)
        if near and gate_id not in seen:
            seen.add(gate_id)
            total_fee += fee

    return len(seen), total_fee