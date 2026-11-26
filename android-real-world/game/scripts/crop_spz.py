import gzip,json,struct,sys
from pathlib import Path
import numpy as np

src,out=map(Path,sys.argv[1:])
raw=gzip.decompress((src/'splats_lite.spz').read_bytes())
magic,version,count,sh,fraction,flags,reserved=struct.unpack_from('<4sIIBBBB',raw)
assert (magic,version,sh)==(b'NGSP',3,1)
sizes=[9,1,3,3,4,9]
assert len(raw)==16+count*sum(sizes)
data=np.frombuffer(raw,np.uint8,offset=16,count=count*9).reshape(count,3,3).astype(np.int32)
integer=data[:,:,0]+data[:,:,1]*256+data[:,:,2]*65536
points=np.where(integer>=2**23,integer-2**24,integer)/(2**fraction)
keyframes=json.loads((src/'keyframes.json').read_text())['keyframes']
up=json.loads((src/'traj.json').read_text())['up']
focus=next(k for k in keyframes if k['t']>130)
matrix=np.array(focus['T_map_cam'])
eye=matrix[:3,3]
forward=matrix[:3,2]
middle=eye+forward*7
difference=points-middle
radius=np.linalg.norm(difference,axis=1)
keep=np.flatnonzero(radius<20)
if len(keep)>255000:keep=np.sort(keep[np.argsort(radius[keep])[:255000]])
assert len(keep)>10000
head=struct.pack('<4sIIBBBB',magic,version,len(keep),sh,fraction,flags,reserved)
offset=16
parts=[head]
for width in sizes:
 layer=np.frombuffer(raw,np.uint8,offset=offset,count=count*width).reshape(count,width)
 parts.append(layer[keep].tobytes())
 offset+=count*width
(out/'park.spz').write_bytes(gzip.compress(b''.join(parts),compresslevel=6,mtime=0))
(out/'park.json').write_text(json.dumps({'eye':eye.tolist(),'forward':forward.tolist(),'up':up,'count':len(keep),'title':'Shaded park walk','credit':'Necessity Robotics (xclean) · CC BY 4.0','source':'https://necessityrobotics.github.io/explore.html?map=oak_160543'}))
print('cropped to',len(keep),'of',count,'gaussians')
