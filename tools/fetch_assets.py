#!/usr/bin/env python3
"""Fetch declared provider files into a resumable, verified staging directory."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time

from asset_catalog import USER_AGENT
from verify_assets import safe_target, verify


def acquire(url, partial):
    subprocess.run(
        ["curl", "-fLsS", "--retry", "2", "--retry-delay", "2", "--max-time", "95",
         "--continue-at", "-", "-A", USER_AGENT, "-o", str(partial), url],
        check=True,
    )


def fetch(item, staging):
    root = staging / "masters" / item["provider"] / item["id"]
    ordered = sorted(item["files"].items(), key=lambda entry: entry[0].endswith(".gltf"))
    records = []
    try:
        for relative, spec in ordered:
            target = safe_target(root, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(target.name + ".part")
            if not target.is_file() or target.stat().st_size != spec["size"]:
                if temp.is_file() and temp.stat().st_size > spec["size"]:
                    temp.unlink()
                if not temp.is_file() or temp.stat().st_size < spec["size"]:
                    try:
                        acquire(spec["url"], temp)
                    except subprocess.CalledProcessError as error:
                        if error.returncode != 33:
                            raise
                        temp.unlink(missing_ok=True)
                        acquire(spec["url"], temp)
                    time.sleep(0.18)
                if temp.stat().st_size != spec["size"]:
                    raise ValueError(f"incomplete transfer: {relative}")
                os.replace(temp, target)
            details = verify(target, spec)
            records.append({"path": target.relative_to(staging).as_posix(), "url": spec["url"], **details})
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        return None, {"id": item["id"], "reason": str(error)}
    return {**item, "files": records, "status": "downloaded_and_verified"}, None


def main():
    parser = ArgumentParser()
    parser.add_argument("staging", type=Path)
    parser.add_argument("--workers", type=int, default=3, choices=range(1, 5))
    args = parser.parse_args()
    catalog_path = args.staging / "catalog.json"
    manifest = json.loads(catalog_path.read_text())
    result = []
    errors = list(manifest["errors"])
    def process(item):
        record, error = fetch(item, args.staging)
        print("Verified" if record else "Failed", item["id"], error or "", flush=True)
        return record, error
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for record, error in pool.map(process, manifest["assets"]):
            if record:
                result.append(record)
            else:
                errors.append(error)
    (args.staging / "downloaded.json").write_text(json.dumps({"assets": result, "errors": errors}, indent=2) + "\n")


if __name__ == "__main__":
    main()
