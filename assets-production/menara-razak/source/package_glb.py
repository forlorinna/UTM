"""Restore linear texture color multipliers and compact 4K ORM buffer views."""
import argparse
import io
import json
import struct
from pathlib import Path

from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('export_dir',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
raw=(args.export_dir/'menara-export.glb').read_bytes()
magic,version,length=struct.unpack_from('<4sII',raw)
assert (magic,version,length)==(b'glTF',2,len(raw))
jsonlen,kind=struct.unpack_from('<I4s',raw,12)
assert kind==b'JSON'
tail=20+jsonlen
binlen,kind=struct.unpack_from('<I4s',raw,tail)
assert kind==b'BIN\0' and tail+8+binlen==len(raw)
asset=json.loads(raw[20:tail])
buffer=memoryview(raw)[tail+8:]
factors=json.loads((args.export_dir/'material_factors.json').read_text())
affected=set()
for mat in asset['materials']:
    pbr=mat['pbrMetallicRoughness']
    if mat['name'] in factors:
        assert 'baseColorTexture' in pbr
        pbr['baseColorFactor']=factors[mat['name']]
    if 'metallicRoughnessTexture' in pbr:
        affected.add(asset['textures'][pbr['metallicRoughnessTexture']['index']]['source'])

replacements={}
for index in affected:
    picture=asset['images'][index]
    view=asset['bufferViews'][picture['bufferView']]
    offset=view.get('byteOffset',0)
    data=buffer[offset:offset+view['byteLength']]
    image=Image.open(io.BytesIO(data)).convert('RGB')
    packed=io.BytesIO()
    image.save(packed,format='JPEG',quality=94,subsampling=0,optimize=True)
    replacements[picture['bufferView']]=packed.getvalue()
    picture['mimeType']='image/jpeg'

result=bytearray()
for index,view in enumerate(asset['bufferViews']):
    assert view['buffer']==0
    prior=view.get('byteOffset',0)
    data=replacements.get(index)
    if data is None:
        data=buffer[prior:prior+view['byteLength']]
    view['byteOffset']=len(result)
    view['byteLength']=len(data)
    result.extend(data)
    result.extend(b'\0'*(-len(result)%4))

asset['buffers'][0]['byteLength']=len(result)
asset['asset']['generator']+=' · 4K material packaging'
descriptor=json.dumps(asset,ensure_ascii=False,separators=(',',':')).encode()
descriptor+=b' '*(-len(descriptor)%4)
total=28+len(descriptor)+len(result)
with args.output.open('wb') as f:
    f.write(struct.pack('<4sIII4s',b'glTF',2,total,len(descriptor),b'JSON'))
    f.write(descriptor)
    f.write(struct.pack('<I4s',len(result),b'BIN\0'))
    f.write(result)
print(f'Compressed {len(raw):,} to {total:,} bytes. Retained source texel resolution.')
