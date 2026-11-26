import concurrent.futures,hashlib,json,requests
from pathlib import Path
Path('materials').mkdir(exist_ok=True)
choices={
  'aluminium':('metal_plate_02',('nor_gl','Rough','Metal')),
  'granite':('concrete_floor_02',('Diffuse','nor_gl','Rough')),
  'brick':('brick_floor_003',('Diffuse','nor_gl','Rough')),
  'sky':('urban_street_04',('hdri',)),
}
def fetch(pair):
 alias,(asset,channels)=pair
 response=requests.get('https://api.polyhaven.com/files/'+asset,timeout=15)
 response.raise_for_status()
 files=response.json()
 result=[]
 for ch in channels:
  formats=files[ch]['2k' if ch=='hdri' else '4k']
  suffix=next(s for s in ('jpg','png','hdr','exr') if s in formats)
  spec=formats[suffix];dest=Path('materials')/f'{alias}_{ch}.{suffix}'
  with requests.get(spec['url'],timeout=90) as response:
   response.raise_for_status()
   data=response.content
  assert hashlib.md5(data).hexdigest()==spec['md5']
  dest.write_bytes(data)
  result.append(dict(asset=asset,license='CC0-1.0',channel=ch,file=str(dest),source=spec['url'],sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
  print(dest,len(data),flush=True)
 return result
with concurrent.futures.ThreadPoolExecutor(5) as e:
 result=list(e.map(fetch,choices.items()))
Path('materials.json').write_text(json.dumps(sum(result,[]),indent=2))
