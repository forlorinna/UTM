#!/usr/bin/env python3
"""Generate the offline map and inventory from OSM XML and an N03E101 HGT tile."""
import argparse
import csv
import gzip
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = (101.719524, 3.172784)
BASE_ELEVATION = 50
TOWER_ID = "552610255"
MJIIT_ID = "733313948"
MODELS = {TOWER_ID: "menara_razak", MJIIT_ID: "mjiit", "524812098": "residensi", "772103594": "masjid"}
CAMPUS_ID = "1076507073"
GRID_X = -180
GRID_Z = -375
STEP = 5
NX = 137
NZ = 123
REFERENCE = "https://utmspace.edu.my/utmspace-homepage/campus-virtual-tour/"
TOWER_PHOTO = "https://commons.wikimedia.org/wiki/File:Menara_Razak_at_UTM_Kuala_Lumpur.JPG"
REFERENCES = {
    TOWER_ID: TOWER_PHOTO + " | https://utmspace.viewin360.co/share/collection/7KNp5",
    "733313948": "https://utmspace.viewin360.co/share/collection/7K4yZ | https://www.myras.org/blog/our-blog-1/mjiit-advanced-robotic-lab-55",
    "524812098": "https://utmspace.viewin360.co/share/collection/7K4yc | https://news.utm.my/2017/05/utm-student-residential-complex-offers-complete-self-contained-accommodation/",
    "772103594": "https://utmspace.viewin360.co/share/collection/7KN5Q | https://news.utm.my/2017/05/utm-student-residential-complex-offers-complete-self-contained-accommodation/",
    "734918595": "https://library.utm.my/branches/",
    "734916985": "https://virtualgallery.utm.my/bangunan-ikonik-dewan-tan-sri-ainuddin-wahid-utm-kuala-lumpur/",
    "606238583": "https://utmspace.viewin360.co/share/collection/7KNp7",
}


def tags(element):
    return {tag.attrib["k"]: tag.attrib["v"] for tag in element.findall("tag")}


def contains(point, polygon):
    px, pz = point
    inside = False
    for (ax, az), (bx, bz) in zip(polygon, polygon[1:] + polygon[:1]):
        if (az > pz) != (bz > pz):
            if px < ax + (bx - ax) * (pz - az) / (bz - az):
                inside = not inside
    return inside


def number(raw, default):
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def stitch(segments):
    remaining = [list(segment) for segment in segments if segment]
    rings = []
    while remaining:
        ring = remaining.pop()
        while ring[0] != ring[-1]:
            for index, segment in enumerate(remaining):
                if ring[-1] in (segment[0], segment[-1]):
                    segment = remaining.pop(index)
                    ring.extend((segment if segment[0] == ring[-1] else segment[::-1])[1:])
                    break
            else:
                break
        if len(ring) > 3 and ring[0] == ring[-1]:
            rings.append(ring)
    return rings


def sample_height(data, lat, lon):
    side = math.isqrt(len(data) // 2)
    x, z = (lon - 101) * (side - 1), (4 - lat) * (side - 1)
    ix, iz = int(x), int(z)
    def val(i, j):
        return struct.unpack_from(">h", data, (j * side + i) * 2)[0]
    wx, wz = x - ix, z - iz
    return ((1 - wx) * (1 - wz) * val(ix, iz) + wx * (1 - wz) * val(ix + 1, iz)
            + (1 - wx) * wz * val(ix, iz + 1) + wx * wz * val(ix + 1, iz + 1))


def main():
    (ROOT / "data/research").mkdir(exist_ok=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("hgt", type=Path)
    args = parser.parse_args()
    hgt = gzip.decompress(args.hgt.read_bytes())
    forward = Transformer.from_crs("EPSG:4326", "EPSG:32647", always_xy=True)
    reverse = Transformer.from_crs("EPSG:32647", "EPSG:4326", always_xy=True)
    ox, oy = forward.transform(*ORIGIN)

    def local(lon, lat):
        east, north = forward.transform(lon, lat)
        return round(east - ox, 3), round(oy - north, 3)

    def height(x, z):
        lon, lat = reverse.transform(x + ox, oy - z)
        return round(sample_height(hgt, lat, lon), 2)

    source = ROOT / "data/campus.osm"
    root = ET.parse(source).getroot()
    nodes = {n.get("id"): local(float(n.get("lon")), float(n.get("lat"))) for n in root.findall("node")}
    ways = {w.get("id"): w for w in root.findall("way")}
    refs = {key: [n.get("ref") for n in w.findall("nd")] for key, w in ways.items()}

    def points(ids):
        return [nodes[key] for key in ids if key in nodes]

    boundary = points(refs[CAMPUS_ID])[:-1]
    building_members = set()
    features = []
    for relation in root.findall("relation"):
        info = tags(relation)
        if "building" not in info:
            continue
        members = {role: [m.get("ref") for m in relation.findall("member")
                          if m.get("type") == "way" and (m.get("role") or "outer") == role]
                   for role in ("outer", "inner")}
        outer = [points(ring)[:-1] for ring in stitch([refs.get(key, []) for key in members["outer"]])]
        inner = [points(ring)[:-1] for ring in stitch([refs.get(key, []) for key in members["inner"]])]
        if outer:
            building_members.update(members["outer"] + members["inner"])
        for i, ring in enumerate(outer):
            holes = [hole for hole in inner if hole and contains(hole[0], ring)]
            features.append(("relation", relation.get("id"), i, info, ring, holes))
    for key, way in ways.items():
        info = tags(way)
        ring = points(refs[key])
        if key not in building_members and "building" in info and len(ring) > 3 and ring[0] == ring[-1]:
            features.append(("way", key, 0, info, ring[:-1], []))

    buildings = []
    for kind, key, part, info, ring, holes in features:
        if len(ring) < 3:
            continue
        cx, cz = [sum(axis) / len(axis) for axis in zip(*ring)]
        if key not in REFERENCES and not contains((cx, cz), boundary):
            continue
        a, b = max(zip(ring, ring[1:] + ring[:1]), key=lambda pair: math.dist(*pair))
        heading = math.degrees(math.atan2(b[0] - a[0], a[1] - b[1])) % 360
        model = MODELS.get(key)
        buildings.append(dict(id=f"osm-{kind}-{key}" + (f"-{part}" if part else ""), kind=kind,
                              name="Menara Razak" if key == TOWER_ID else info.get("name", ""),
                              building=info["building"], footprint=ring, holes=holes,
                              x=round(cx, 2), z=round(cz, 2), grid_heading=round(heading, 1),
                              altitude_m=height(cx, cz), height_m=number(info.get("height"), None),
                              levels=number(info.get("building:levels"), None),
                              source=f"https://www.openstreetmap.org/{kind}/{key}",
                              reference=REFERENCES.get(key, ""),
                              asset=f"res://assets/architecture/{model}_lod0.glb" if model else "",
                              status="independent model, visual audit pending" if model else "inventory only"))
    buildings.sort(key=lambda row: (row["id"] != "osm-way-" + TOWER_ID, row["id"]))

    roads, greens, parking = [], [], []
    widths = {"secondary": 9.5, "tertiary": 7.0, "service": 5.2, "footway": 1.8,
              "cycleway": 1.5, "path": 1.6, "residential": 6.0, "unclassified": 5.4}
    for key, element in ways.items():
        info = tags(element)
        coords = points(refs[key])
        if len(coords) < 2 or not any(GRID_X <= x <= GRID_X + NX * STEP and GRID_Z <= z <= GRID_Z + NZ * STEP for x, z in coords):
            continue
        use = info.get("highway")
        if use in widths and info.get("tunnel") != "yes" and info.get("layer", "0") == "0" and info.get("area") != "yes":
            road_width = number(info.get("width"), widths[use])
            roads.append(dict(id=key, name=info.get("name", ""), points=coords, type=use,
                              width=road_width, oneway=info.get("oneway") == "yes",
                              roundabout=info.get("junction") == "roundabout"))
        if info.get("amenity") == "parking" and info.get("parking") not in ("underground", "multi-storey") and len(coords) > 3 and coords[0] == coords[-1]:
            parking.append(dict(id=key, points=coords[:-1]))
        if len(coords) > 3 and coords[0] == coords[-1] and (
                info.get("landuse") in ("grass", "forest", "meadow") or
                info.get("leisure") in ("pitch", "garden", "park") or
                info.get("natural") in ("grassland", "wood", "scrub")):
            greens.append(dict(id=key, name=info.get("name", ""), points=coords[:-1]))
    known_family = {"name": "Dewan Azman Hashim", "reference": "https://utmspace.viewin360.co/share/collection/7KNNd",
                    "status": "officially identified, distinct footprint unresolved"}
    grid = [[round(height(GRID_X + x * STEP, GRID_Z + z * STEP) - BASE_ELEVATION, 2)
             for x in range(NX + 1)] for z in range(NZ + 1)]
    tower = buildings[0]
    data = dict(osm_timestamp="downloaded 2026-11-25; OSM API response provides no snapshot timestamp", projection="EPSG:32647",
                origin_lon_lat=ORIGIN, vertical_origin_m=BASE_ELEVATION,
                grid=dict(x=GRID_X, z=GRID_Z, step=STEP, heights=grid),
                boundary=boundary, buildings=buildings, roads=roads, greens=greens, parking=parking,
                unresolved=[known_family], tower_base_y=round(tower["altitude_m"] - BASE_ELEVATION, 2))
    (ROOT / "data/map.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    with (ROOT / "data/research/campus_buildings.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, lineterminator="\n", fieldnames=[*tower, "height_confidence", "lod", "collision", "notes"])
        writer.writeheader()
        for row in buildings:
            is_tower = bool(row["asset"])
            writer.writerow({**row, "height_confidence": "OSM tag, no survey" if row["height_m"] is not None else "unknown",
                             "lod": "LOD0–2" if is_tower else "", "collision": "simplified closed envelope" if is_tower else "",
                             "notes": "Entrance and rear geometry estimated" if is_tower else "No 3D mesh in this build"})
        writer.writerow(dict(id="utmkl-dewan-azman-hashim", **known_family))
        writer.writerow(dict(id="utmkl-razak-read-cafe", name="Read Cafe@UTMKL", reference="https://library.utm.my/branches/",
                             status="public venue within Menara Razak", notes="No extra building footprint"))
    print(f"{len(buildings)} campus OSM footprints, {len(roads)} routes, {len(greens)} landscape polygons")
    print(f"Terrain {min(map(min,grid)) + BASE_ELEVATION:.2f}–{max(map(max,grid)) + BASE_ELEVATION:.2f} m; tower base {tower['altitude_m']:.2f} m")


if __name__ == "__main__":
    main()
