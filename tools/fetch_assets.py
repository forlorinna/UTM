#!/usr/bin/env python3
"""Download selected Poly Haven originals and verify against provider checksums."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "UTMKLCampusLifeResearch/0.1"
ASSETS = {
    "aerial_asphalt_01": "Campus roads",
    "concrete_wall_008": "Menara Razak facade panels",
    "painted_concrete": "Painted concrete and entrance",
    "concrete_floor_02": "Entrance plinth and canopy structure",
    "concrete_pavers": "Paths and plaza",
    "grass_ground": "Landscape ground",
    "red_laterite_soil_stones": "Planted beds",
    "box_profile_metal_sheet": "Canopy cladding",
    "interior_tiles": "Fictional reading room floor",
    "old_wood_floor": "Fictional reading room furniture",
    "palm_tree_bark": "Palm reference material",
    "kloofendal_48d_partly_cloudy_puresky": "Clear-sky lighting",
    "overcast_soil_puresky": "Overcast lighting",
    "painted_wooden_bench": "Plaza and reading room seating",
    "street_lamp_01": "Plaza lighting fixtures",
    "island_tree_02": "Scanned tropical streetscape canopy",
    "metal_trash_can": "Plaza furniture",
    "planter_box_01": "Entrance furniture",
}
API = "https://api.polyhaven.com/"


def get(url, output=None):
    cmd = ["curl", "-fLsS", "--retry", "1", "--max-time", "65", "-A", USER_AGENT]
    if output is not None:
        cmd.extend(["-o", str(output)])
    return subprocess.run(cmd + [url], check=True, stdout=subprocess.PIPE).stdout


def store_file(folder, name, info):
    target = folder / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file() or hashlib.md5(target.read_bytes()).hexdigest() != info["md5"]:
        temp = target.with_suffix(target.suffix + ".download")
        try:
            get(info["url"], temp)
            if hashlib.md5(temp.read_bytes()).hexdigest() != info["md5"]:
                raise ValueError(f"Provider checksum mismatch for {name}")
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
    data = target.read_bytes()
    record = dict(path=str(target.relative_to(ROOT)), bytes=len(data),
                  sha256=hashlib.sha256(data).hexdigest(), download=info["url"])
    if target.suffix.lower() in (".jpg", ".png"):
        dimensions = subprocess.check_output(["identify", "-ping", "-format", "%w %h %[channels]", str(target)], text=True)
        width, height, channels = dimensions.split(maxsplit=2)
        record.update(width=int(width), height=int(height), channels=channels)
    if target.suffix.lower() == ".hdr":
        resolution = data.split(b"\n\n", 1)[1].split(b"\n", 1)[0].decode().split()
        record.update(width=int(resolution[3]), height=int(resolution[1]), channels="RGBE")
    return record


def fetch(name, catalog):
    meta = catalog[name]
    variants = json.loads(get(API + "files/" + name))
    folder = ROOT / "assets" / "polyhaven" / name
    files = {}
    if meta["type"] == 2:
        model = variants["gltf"]["1k"]["gltf"]
        files = {f"{name}.gltf": model, **model["include"]}
    elif meta["type"] == 0:
        files[f"{name}_2k.hdr"] = variants["hdri"]["2k"]["hdr"]
    else:
        for component, alias, extension in (("Diffuse", "albedo", "jpg"), ("nor_gl", "normal", "png"), ("Rough", "roughness", "jpg")):
            files[f"{alias}.{extension}"] = variants[component]["1k"][extension]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda pair: store_file(folder, *pair), files.items()))
    return dict(id=name, authors=meta["authors"], license="CC0-1.0",
                source="https://polyhaven.com/a/" + name, intended_use=ASSETS[name],
                resolution="2K" if meta["type"] == 0 else "1K", files=records)


def main():
    catalog = json.loads(get(API + "assets"))
    results = []
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        jobs = {pool.submit(fetch, name, catalog): name for name in ASSETS}
        for job in concurrent.futures.as_completed(jobs):
            name = jobs[job]
            try:
                results.append(job.result())
                print("Verified", name, flush=True)
            except Exception as error:
                failures.append(dict(id=name, error=str(error)))
                print("Failed", name, error, flush=True)
    manifest = {"license_source": "https://polyhaven.com/license",
                "assets": sorted(results, key=lambda asset: asset["id"]), "failures": failures}
    (ROOT / "data/assets_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
