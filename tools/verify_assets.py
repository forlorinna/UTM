#!/usr/bin/env python3
"""Validate downloaded masters and retain structured, per-file verification evidence."""
from argparse import ArgumentParser
from hashlib import file_digest
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

from PIL import Image


def digest(path, algorithm="sha256"):
    with path.open("rb") as stream:
        return file_digest(stream, algorithm).hexdigest()


def safe_target(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError(f"unsafe asset path: {relative}")
    return root.joinpath(*path.parts)


def verify(path, specification):
    size = path.stat().st_size
    if size != specification["size"]:
        raise ValueError(f"size {size} differs from {specification['size']}: {path.name}")
    if specification.get("md5") and digest(path, "md5") != specification["md5"]:
        raise ValueError(f"published MD5 mismatch: {path.name}")
    evidence = {"sha256": digest(path), "bytes": size}
    if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
        with Image.open(path) as image:
            image.load()
            evidence.update(width=image.width, height=image.height, channels=image.mode)
    elif path.suffix == ".hdr":
        with path.open("rb") as stream:
            header = stream.read(4096)
        if not header.startswith((b"#?RADIANCE", b"#?RGBE")):
            raise ValueError(f"invalid HDR header: {path.name}")
        dimensions = next(line.split() for line in header.splitlines() if line.startswith(b"-Y "))
        evidence.update(width=int(dimensions[3]), height=int(dimensions[1]), channels="RGBE")
    elif path.suffix == ".zip":
        unpack = path.with_suffix("")
        unpack.mkdir(exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            if sum(member.file_size for member in archive.infolist()) > 1024**3:
                raise ValueError("uncompressed texture archive exceeds 1 GiB")
            for member in archive.infolist():
                safe_target(unpack, member.filename)
                if stat.S_ISLNK(member.external_attr >> 16):
                    raise ValueError("texture archive contains a symbolic link")
                if not member.is_dir() and Path(member.filename).suffix.lower() not in (".jpg", ".png", ".txt", ".usda", ".usdc", ".mtlx", ".blend", ".tif", ".tres"):
                    raise ValueError(f"unexpected archive entry {member.filename}")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"bad archive CRC: {bad_member}")
            for member in archive.infolist():
                if not member.is_dir() and Path(member.filename).suffix.lower() in (".jpg", ".png", ".txt", ".tif"):
                    archive.extract(member, unpack)
        for channel in unpack.rglob("*.jpg"):
            with Image.open(channel) as image:
                image.load()
    elif path.suffix == ".gltf":
        document = json.loads(path.read_text())
        if document["asset"]["version"] != "2.0":
            raise ValueError("unsupported glTF asset version")
        for item in document.get("buffers", []) + document.get("images", []):
            uri = item.get("uri", "")
            if uri and not uri.startswith("data:"):
                resolved = safe_target(path.parent, uri)
                if not resolved.is_file():
                    raise ValueError(f"missing glTF dependency {uri}")
    return evidence


def main():
    parser = ArgumentParser()
    parser.add_argument("staging", type=Path)
    args = parser.parse_args()
    inventory = json.loads((args.staging / "downloaded.json").read_text())
    records = inventory["assets"]
    for record in records:
        for entry in record["files"]:
            path = safe_target(args.staging, entry["path"])
            if digest(path) != entry["sha256"]:
                raise SystemExit(f"Mismatch: {entry['path']}")
    print(f"{len(records)} verified masters; {sum(len(a['files']) for a in records)} files match SHA256")


if __name__ == "__main__":
    main()
