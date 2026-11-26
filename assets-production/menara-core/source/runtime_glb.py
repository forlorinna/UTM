"""Repack GLB image buffer views for the walk build, preserving mesh and extensions."""
import io,json,struct,sys
from pathlib import Path
from PIL import Image

src,dst=map(Path,sys.argv[1:3])
raw=src.read_bytes()
magic,ver,length,n,kind=struct.unpack_from('<4sIII4s',raw)
assert (magic,ver,length,kind)==(b'glTF',2,len(raw),b'JSON')
doc=json.loads(raw[20:20+n])
data=memoryview(raw)[28+n:]
color_roles=set()
for material in doc.get('materials',[]):
    extensions=material.get('extensions',{})
    pbr=material.get('pbrMetallicRoughness',{})
    if src.name=='Core_Site.glb' and pbr.get('baseColorTexture'):
        tint={'Red-brown plaza pavers':'c8b3b4','Bush-hammered plaza and stair concrete':'c7c3b9'}.get(material['name'])
        if tint:
            rgb=[int(tint[i:i+2],16)/255 for i in (0,2,4)]
            pbr['baseColorFactor']=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]+[1]
    for slot in [pbr.get('baseColorTexture'),material.get('emissiveTexture')]:
        if slot:color_roles.add(doc['textures'][slot['index']]['source'])
replacements={}
for ix,image in enumerate(doc.get('images',[])):
    if 'bufferView' not in image:continue
    info=doc['bufferViews'][image['bufferView']];offset=info.get('byteOffset',0)
    im=Image.open(io.BytesIO(data[offset:offset+info['byteLength']]))
    if 'A' in im.getbands() and ix in color_roles and im.getchannel('A').getextrema()!=(255,255):continue
    if max(im.size)<=1536 and image.get('mimeType')=='image/jpeg':continue
    im=im.convert('RGB')
    im.thumbnail((1536,1536),Image.Resampling.LANCZOS)
    buf=io.BytesIO();im.save(buf,'JPEG',quality=91,subsampling=0,optimize=True)
    replacements[image['bufferView']]=buf.getvalue();image['mimeType']='image/jpeg'
result=bytearray()
for i,info in enumerate(doc['bufferViews']):
    o=info.get('byteOffset',0)
    content=replacements.get(i,data[o:o+info['byteLength']])
    info['byteOffset']=len(result);info['byteLength']=len(content)
    result.extend(content);result.extend(b'\0'*(-len(result)%4))
doc['buffers'][0]['byteLength']=len(result)
j=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*(-len(j)%4)
dst.write_bytes(struct.pack('<4sIII4s',b'glTF',2,28+len(j)+len(result),len(j),b'JSON')+j+struct.pack('<I4s',len(result),b'BIN\0')+result)
print(src.name,len(raw),'→',dst.name,dst.stat().st_size)
