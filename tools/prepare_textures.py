#!/usr/bin/env python3
"""Prepare selected, verified PBR maps with no synthetic texture substitution."""
from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
from PIL import Image

from asset_catalog import ROOT
from verify_assets import digest

RUNTIME = {
    "concrete_panels": (2, "Menara slab bands and portal piers"),
    "rectangular_facade_tiles_02": (2.0, "Menara portal cladding"),
    "anti_slip_concrete": (2, "Menara stair tread and gate plinth"),
    "brushed_concrete_03": (2, "MJIIT piers and shade-slab faces"),
    "metal_plate_02": (2, "Architectural metalwork"),
    "painted_plaster_wall": (2, "MJIIT painted wall base"),
    "asphalt_03": (4, "Campus roads and parking"),
    "worn_asphalt": (5, "Campus road repair zones"),
    "grey_stone_path": (2.2, "Entrance and plaza paving"),
    "interlocking_concrete_pavers": (3, "Campus footways"),
    "leafy_grass": (3.7, "Fine-scale campus turf"),
    "aerial_grass_rock": (15, "Site-wide scanned turf variation"),
    "forest_ground_05": (3.3, "Tree and planting beds"),
    "gravel_embedded_concrete": (2, "Curbs and concrete hardscape"),
    "concrete_moss": (1.8, "Localized planted edging"),
    "anti_skid_tiles": (1.8, "Granite-look exterior entry treads"),
    "grey_roof_tiles": (2.6, "Roof material study"),
    "metal_grate_rusty": (1.4, "Slot-drain frames"),
    "red_brick_pavers": (2.2, "Decorative access-path borders"),
}


def channel_name(path):
    return path.stem


def main():
    parser = ArgumentParser()
    parser.add_argument("staging", type=Path)
    args = parser.parse_args()
    acquired = json.loads((args.staging/"downloaded.json").read_text())
    runtime = []
    for asset in acquired["assets"]:
        name = asset["id"]
        if name not in RUNTIME:
            continue
        meters, use = RUNTIME[name]
        destination = ROOT/"assets/runtime/materials"/name
        destination.mkdir(parents=True, exist_ok=True)
        resolved = {}
        for entry in asset["files"]:
            source = args.staging/entry["path"]
            channel = channel_name(source)
            normal = channel == "normal"
            rgb = normal or channel == "albedo"
            with Image.open(source) as original:
                image = original.convert("RGB" if rgb else "L")
                image.thumbnail((2048, 2048),Image.Resampling.LANCZOS)
            extension = ".png" if normal else ".jpg"
            output = destination / (channel + extension)
            if normal:
                value = np.asarray(image).astype(np.float32)/127.5-1.0
                length = np.maximum(np.linalg.norm(value,axis=2,keepdims=True), .00001)
                image = Image.fromarray(np.clip((value/length+1)*127.5,0,255).astype(np.uint8))
                image.save(output, compress_level=5)
            else:
                image.save(output,quality=91,subsampling=0,optimize=True)
            resolved[channel] = {"path": output.relative_to(ROOT).as_posix(), "source": entry["path"],
                                 "sha256": digest(output), "size": [image.width, image.height]}
        if {"albedo","normal","roughness"} <= resolved.keys():
            runtime.append({"id": name, "license": asset["license"], "source_url": asset["source_url"],
                            "intended_use": use, "uv_meters_approx": meters, "channels": resolved})
            print("Prepared", name, flush=True)
    (ROOT/"data/v2/runtime_textures.json").write_text(json.dumps(runtime,indent=2)+"\n")


if __name__ == "__main__":
    main()
