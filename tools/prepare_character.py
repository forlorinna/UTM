#!/usr/bin/env python3
"""Add the second CC0 Sam animation without duplicating body and texture data."""
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def read_glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20+size])
    binary = bytearray(raw[28+size:])
    return document, binary


def align(data, pad):
    data.extend(pad * (-len(data) % 4))


def append_motion(base, binary, extra, motion):
    nodes = [node["name"] for node in base["nodes"]]
    motion_nodes = [node["name"] for node in extra["nodes"]]
    if nodes != motion_nodes:
        raise ValueError("Animation and character skeletons have different node arrays")
    aliases = {}
    for animation in extra["animations"]:
        for sampler in animation["samplers"]:
            for key in ["input", "output"]:
                original = sampler[key]
                if original not in aliases:
                    accessor = extra["accessors"][original].copy()
                    source = extra["bufferViews"][accessor["bufferView"]]
                    align(binary, b"\0")
                    start = source.get("byteOffset", 0)
                    view = {**source, "byteOffset": len(binary)}
                    accessor["bufferView"] = len(base["bufferViews"])
                    base["bufferViews"].append(view)
                    binary.extend(motion[start:start + source["byteLength"]])
                    aliases[original] = len(base["accessors"])
                    base["accessors"].append(accessor)
                sampler[key] = aliases[original]
        base["animations"].append(animation)


def main():
    base, binary = read_glb(ROOT / "art/characters/Innerscene_Sam_Walk.glb")
    extra, motion = read_glb(ROOT / "art/characters/Innerscene_Sam_Run.glb")
    append_motion(base, binary, extra, motion)
    align(binary, b"\0")
    base["buffers"][0]["byteLength"] = len(binary)
    json_bytes = bytearray(json.dumps(base, separators=(",", ":")).encode())
    align(json_bytes, b" ")
    out = b"glTF" + struct.pack("<II", 2, 28 + len(json_bytes) + len(binary))
    out += struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes
    out += struct.pack("<I4s", len(binary), b"BIN\0") + binary
    (ROOT / "assets/people/sam.glb").write_bytes(out)


if __name__ == "__main__":
    main()
