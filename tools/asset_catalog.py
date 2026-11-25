#!/usr/bin/env python3
"""Resolve the V2 procurement list using provider metadata and cache it on disk."""
from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "UTMKLCampusLife/2.0 (+https://github.com/forlorinna/UTM)"
PH = "https://api.polyhaven.com/"
ACG = "https://ambientcg.com/api/v3/assets?"


def retrieve(url, cache):
    if cache.is_file():
        return json.loads(cache.read_text())
    data = subprocess.check_output(
        ["curl", "-fLsS", "--retry", "2", "--max-time", "40", "-A", USER_AGENT, url]
    )
    contents = json.loads(data)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(data)
    return contents


def select_polyhaven(asset, kind, catalog, cache):
    metadata = catalog[asset]
    expected_type = {"hdri": 0, "material": 1, "prop": 2, "vegetation": 2}
    if metadata["type"] != expected_type[kind]:
        raise ValueError("unexpected provider asset type")
    variants = retrieve(PH + "files/" + asset, cache / f"ph-{asset}.json")
    if kind == "material":
        files = {}
        for channel, provider_name in {
            "albedo": "Diffuse", "normal": "nor_gl", "roughness": "Rough",
            "ao": "AO", "metallic": "Metal",
        }.items():
            component = variants.get(provider_name)
            if component is None:
                if channel in ("albedo", "normal", "roughness"):
                    raise ValueError(f"missing required PBR channel {channel}")
                continue
            options = component.get("4k", {})
            if "jpg" in options:
                files[f"{channel}.jpg"] = options["jpg"]
            elif "png" in options:
                files[f"{channel}.png"] = options["png"]
        resolution = "4K"
    elif kind == "hdri":
        files = {f"{asset}.hdr": variants["hdri"]["4k"]["hdr"]}
        resolution = "4K"
    else:
        gltf = variants["gltf"]["1k"]["gltf"]
        files = {f"{asset}.gltf": gltf, **gltf["include"]}
        resolution = "1K model maps"
    return {"id": asset, "kind": kind, "provider": "polyhaven", "author": metadata["authors"],
            "license": "CC0-1.0", "source_url": "https://polyhaven.com/a/" + asset,
            "source_resolution": resolution, "files": files}


def select_ambientcg(asset, kind, cache):
    data = retrieve(ACG + urlencode({"q": asset, "type": kind, "include": "downloads", "limit": 20}),
                    cache / f"acg-{asset}.json")
    exact = next(row for row in data["assets"] if row["id"] == asset)
    variant = next(row for row in exact["downloads"] if row["attributes"] == "4K-JPG")
    return {"id": asset, "kind": kind, "provider": "ambientcg", "author": "ambientCG contributors",
            "license": "CC0-1.0", "source_url": "https://ambientcg.com/view?id=" + asset,
            "source_resolution": "4K", "files": {asset + ".zip": variant}}


def main():
    parser = ArgumentParser()
    parser.add_argument("staging", type=Path)
    args = parser.parse_args()
    cache = args.staging / "api"
    wanted = json.loads((ROOT / "data/v2/procurement.json").read_text())
    catalog = retrieve(PH + "assets", cache / "polyhaven-assets.json")
    resolved, failures = [], []
    for provider in ("polyhaven", "ambientcg"):
        for kind, ids in wanted[provider].items():
            for asset in ids:
                try:
                    if provider == "polyhaven":
                        item = select_polyhaven(asset, kind, catalog, cache)
                    else:
                        item = select_ambientcg(asset, kind, cache)
                    resolved.append(item)
                    print("Resolved", asset, flush=True)
                except (KeyError, ValueError, subprocess.CalledProcessError, StopIteration) as error:
                    failures.append({"id": asset, "reason": str(error)})
                    print("Unresolved", asset, error, flush=True)
    (args.staging / "catalog.json").write_text(json.dumps({"assets": resolved, "errors": failures}, indent=2) + "\n")


if __name__ == "__main__":
    main()
