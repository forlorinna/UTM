"""Create a neutral albedo from Poly Haven's CC0 concrete scan."""
import hashlib,json,requests
import numpy as np
from PIL import Image
from pathlib import Path
d=Path('materials')
asset='concrete_wall_007'
reply=requests.get('https://api.polyhaven.com/files/'+asset,timeout=12)
reply.raise_for_status()
record=reply.json()
new=[]
for channel in ('Diffuse','nor_gl','Rough'):
    spec=record[channel]['4k']['jpg']
    f=d/('clean_'+channel+'.jpg')
    r=requests.get(spec['url'],timeout=45)
    r.raise_for_status()
    assert hashlib.md5(r.content).hexdigest()==spec['md5']
    f.write_bytes(r.content)
    new.append(dict(asset=asset,license='CC0-1.0',channel=channel,file=str(f),source=spec['url'],sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content)))
image=np.asarray(Image.open(d/'clean_Diffuse.jpg').convert('L'),dtype=np.float32)
mid=np.median(image)
albedo=np.uint8(np.clip(230+(image-mid)*.18,207,249))
path=d/'clean_Neutral.jpg'
Image.fromarray(albedo).convert('RGB').save(path,quality=91,subsampling=0)
data=json.loads(Path('materials.json').read_text())+new
data.append(dict(asset=asset,license='CC0-1.0',channel='Neutral',file=str(path),source='Derived from clean_Diffuse.jpg by grayscale and restrained contrast',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))
Path('materials-refined.json').write_text(json.dumps(data,indent=2))
