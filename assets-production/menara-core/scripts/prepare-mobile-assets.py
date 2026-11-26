"""Build Android-only Basis UASTC GLBs from the shared, versioned models."""
import concurrent.futures
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'public' / 'assets'
OUTPUT = ROOT / 'public' / 'mobile-assets'
BASIS = ROOT / 'node_modules' / '.bin' / 'basisu-linux-x64'
OLD_GAME = ROOT.parents[1] / 'android-real-world' / 'game' / 'public'
CACHE = ROOT / '.texture-cache'


def encode(payload, srgb):
    key = hashlib.sha256(payload + bytes([srgb])).hexdigest()
    cached = CACHE / (key + '.ktx2')
    if cached.exists():
        return cached.read_bytes()
    with tempfile.TemporaryDirectory() as work:
        source = Path(work) / 'texture.png'
        target = source.with_suffix('.ktx2')
        with Image.open(io.BytesIO(payload)) as image:
            image.convert('RGBA').save(source)
        args = [BASIS, '-ktx2', '-uastc', '-uastc_level', '1', '-mipmap', '-no_multithreading']
        if not srgb:
            args.extend(['-linear', '-mip_linear'])
        subprocess.run([*args, '-file', source, '-output_file', target], check=True, stdout=subprocess.DEVNULL)
        result = target.read_bytes()
        cached.write_bytes(result)
        return result


def convert(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20 + size])
    data = memoryview(raw)[28 + size:]
    textures = document['textures']
    color = set()
    for material in document['materials']:
        pbr = material.get('pbrMetallicRoughness', {})
        for slot in (pbr.get('baseColorTexture'), material.get('emissiveTexture'), material.get('extensions', {}).get('KHR_materials_sheen', {}).get('sheenColorTexture')):
            if slot:
                color.add(textures[slot['index']]['source'])

    jobs = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for index, image in enumerate(document['images']):
            view_index = image['bufferView']
            view = document['bufferViews'][view_index]
            offset = view.get('byteOffset', 0)
            payload = bytes(data[offset:offset + view['byteLength']])
            jobs[view_index] = pool.submit(encode, payload, index in color)
            image['mimeType'] = 'image/ktx2'
        replacements = {view: job.result() for view, job in jobs.items()}

    extension = 'KHR_texture_basisu'
    for texture in textures:
        texture.setdefault('extensions', {})[extension] = {'source': texture.pop('source')}
    for key in ('extensionsUsed', 'extensionsRequired'):
        document.setdefault(key, []).append(extension)

    result = bytearray()
    for index, view in enumerate(document['bufferViews']):
        offset = view.get('byteOffset', 0)
        payload = replacements.get(index, data[offset:offset + view['byteLength']])
        view.update(byteOffset=len(result), byteLength=len(payload))
        result.extend(payload)
        result.extend(b'\0' * (-len(result) % 4))
    document['buffers'][0]['byteLength'] = len(result)
    metadata = json.dumps(document, separators=(',', ':')).encode()
    metadata += b' ' * (-len(metadata) % 4)
    out = OUTPUT / path.name
    with out.open('wb') as stream:
        stream.write(struct.pack('<4sIII4s', b'glTF', 2, 28 + len(metadata) + len(result), len(metadata), b'JSON'))
        stream.write(metadata)
        stream.write(struct.pack('<I4s', len(result), b'BIN\0'))
        stream.write(result)
    print(f'{path.name}: {len(document["images"])} compressed textures, {out.stat().st_size:,} bytes', flush=True)


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    for filename in ('park.spz', 'park.json'):
        shutil.copyfile(OLD_GAME / filename, OUTPUT / filename)
    for filename in ('basis_transcoder.js', 'basis_transcoder.wasm'):
        shutil.copyfile(ROOT / 'node_modules' / 'three' / 'examples' / 'jsm' / 'libs' / 'basis' / filename, OUTPUT / filename)
    for path in sorted(INPUT.glob('*.glb')):
        convert(path)
