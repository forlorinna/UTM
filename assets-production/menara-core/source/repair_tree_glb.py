"""Repair degenerate tangents inherited from the runtime tree asset."""
import json
import math
from pathlib import Path
import struct
import sys

source, destination = map(Path, sys.argv[1:3])
raw = bytearray(source.read_bytes())
magic, version, size, json_size, kind = struct.unpack_from('<4sIII4s', raw)
assert (magic, version, size, kind) == (b'glTF', 2, len(raw), b'JSON')
document = json.loads(raw[20:20 + json_size])
binary_start = 28 + json_size


def layout(index, dimensions):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    assert accessor['type'] == f'VEC{dimensions}' and accessor['componentType'] == 5126
    assert not accessor.get('sparse') and view['buffer'] == 0
    base = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return base, view.get('byteStride', 4 * dimensions), accessor['count']


updated = 0
for mesh in document['meshes']:
    for primitive in mesh['primitives']:
        attributes = primitive['attributes']
        if 'TANGENT' not in attributes:
            continue
        normals, normal_stride, normal_count = layout(attributes['NORMAL'], 3)
        tangents, tangent_stride, count = layout(attributes['TANGENT'], 4)
        assert normal_count == count
        for vertex in range(count):
            offset = tangents + vertex * tangent_stride
            x, y, z, sign = struct.unpack_from('<4f', raw, offset)
            length = math.hypot(x, y, z)
            if abs(length - 1.0) <= 1e-5:
                continue
            if length <= 1e-5:
                nx, ny, nz = struct.unpack_from('<3f', raw, normals + vertex * normal_stride)
                x, y, z = (0, nz, -ny) if abs(nx) < .8 else (-nz, 0, nx)
                length = math.hypot(x, y, z)
            struct.pack_into('<4f', raw, offset, x / length, y / length, z / length, sign)
            updated += 1

destination.write_bytes(raw)
print(f'{updated:,} vertex tangents repaired in {destination.name}')
