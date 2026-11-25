#!/usr/bin/env python3
"""Record runtime bindings for the downloaded originals and derived assets."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/assets_manifest.json"

USAGE = {
    "aerial_asphalt_01": "roads and surface parking",
    "concrete_wall_008": "Menara Razak, Masjid and Residensi exterior concrete",
    "painted_concrete": "MJIIT, Masjid, Residensi and reading room",
    "concrete_floor_02": "material retained for exterior evaluation; no visible binding",
    "concrete_pavers": "footpaths and Menara Razak forecourt",
    "grass_ground": "terrain",
    "red_laterite_soil_stones": "Menara Razak planted bed",
    "box_profile_metal_sheet": "roofing and Residensi horizontal screens",
    "interior_tiles": "fictional reading room floor",
    "old_wood_floor": "fictional reading room furniture",
    "palm_tree_bark": "retained for future palm asset; no visible binding",
    "kloofendal_48d_partly_cloudy_puresky": "daytime sky and reflection",
    "overcast_soil_puresky": "overcast and rain sky and reflection",
    "painted_wooden_bench": "plaza and reading room",
    "street_lamp_01": "plaza and service road street lamps",
    "island_tree_02": "decimated CC0 scan instanced at campus forecourts",
    "metal_trash_can": "Menara Razak forecourt",
    "planter_box_01": "Menara Razak forecourt",
}

OTHER = [
    ("Innerscene", "white-four-door-sedan-1f271353", "sedan", "drivable sedan and rotating wheel pivots",
     ["art/Innerscene_White_Sedan_original.glb", "assets/vehicles/sedan.glb"]),
    ("Innerscene; based on MakeHuman/MPFB CC0 data", "relaxed-walk-sam-3d-person-animated-732f1206", "sam_walk",
     "third-person player and visitors", ["art/characters/Innerscene_Sam_Walk.glb", "assets/people/sam.glb"]),
    ("Innerscene; based on MakeHuman/MPFB CC0 data", "run-sam-3d-person-animated-fa008c06", "sam_run",
     "run animation merged into playable character", ["art/characters/Innerscene_Sam_Run.glb", "assets/people/sam.glb"]),
    ("Innerscene; based on MakeHuman/MPFB CC0 data", "walk-carrying-phone-maya-3d-person-animated-06ba936a", "maya_phone",
     "visitors carrying a phone", ["assets/people/maya.glb"]),
]


def describe(path):
    binary = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(binary), "sha256": hashlib.sha256(binary).hexdigest()}


def main():
    data = json.loads(MANIFEST.read_text())
    for record in data["assets"]:
        use = USAGE[record["id"]]
        record["runtime_binding"] = use
        record["status"] = "downloaded and checked; retained" if "no visible" in use else "downloaded and bound in Godot"
    data["other_assets"] = [
        {"id": asset, "author": author, "license": "CC0-1.0",
         "source": "https://www.innerscene.com/tools/library/3d-parts/" + slug,
         "download": "https://www.innerscene.com/api/library/" + slug + "/download",
         "runtime_binding": use, "files": [describe(p) for p in paths]}
        for author, slug, asset, use, paths in OTHER
    ]
    for asset, author, page, original, path, use in [
        ("rain", "Kresiek The Furry", "amb-rain-loop-1", "amb_rain_loop_1.ogg", "assets/audio/rain.ogg", "looped wet-weather ambience"),
        ("birds", "Isaiah658", "ambient-bird-sounds", "birds-isaiah658.ogg", "assets/audio/birds.ogg", "outdoor daytime ambience"),
    ]:
        data["other_assets"].append({
            "id": asset, "author": author, "license": "CC0-1.0",
            "source": "https://opengameart.org/content/" + page,
            "download": "https://opengameart.org/sites/default/files/" + original,
            "runtime_binding": use, "files": [describe(path)],
        })
    data["other_assets"].append({
        "id": "noto_sc_subset", "author": "Google, Adobe and Noto contributors", "license": "OFL-1.1",
        "source": "https://github.com/notofonts/noto-cjk", "runtime_binding": "Chinese, English and Malay UI font",
        "files": [describe("assets/i18n/NotoSansSC-subset.otf")],
    })
    data["derivatives"] = [
        {"source": "island_tree_02", "license": "CC0-1.0", "modification": "Blender decimation by material",
         "files": [describe("assets/landscape/island_tree_realtime.glb")]},
        {"source": "painted_concrete", "license": "CC0-1.0", "modification": "neutral albedo for colored paint matching",
         "files": [describe("assets/materials/paint_neutral.jpg")]},
        {"source": "box_profile_metal_sheet", "license": "CC0-1.0", "modification": "desaturated albedo for silver metal",
         "files": [describe("assets/materials/roof_silver.jpg")]},
    ]
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
