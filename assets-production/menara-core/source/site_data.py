"""Clip the existing OSM extract to the immediate Menara Razak site."""
import json,math,sys
from pathlib import Path
from shapely.geometry import box,Polygon,LineString,mapping
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles

source=Path(sys.argv[1]);out=Path(sys.argv[2])
data=json.loads(source.read_text())
a=.66008744836;c=math.cos(a);s=math.sin(a)
def rotate(p):
    x,z=p
    return (c*x+s*z,s*x-c*z)
def shapes(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    return [p for part in getattr(g,'geoms',[]) for p in shapes(part)]
def encode(g):
    return [[[list(p) for p in r.coords[:-1]] for r in [a.exterior,*a.interiors]] for a in shapes(g) if a.area>.04]
clip=box(-56,-49,71,34)
tower=next(p for p in data['buildings'] if p['id']=='osm-way-552610255')
footprint=Polygon([rotate(p) for p in tower['footprint']])
neighbors=[]
for p in data['buildings']:
    if p is tower:continue
    poly=Polygon([rotate(v) for v in p['footprint']]).buffer(0).intersection(clip)
    if poly.area>1:neighbors.append(poly)
reserved=unary_union(neighbors)
drive=[];paths=[];roads=[]
for r in data['roads']:
    line=LineString([rotate(v) for v in r['points']])
    local=line.intersection(clip)
    if local.length<1.1:continue
    walk=r['type'] in ('path','footway','steps','pedestrian')
    # Unmeasured service width is drawn at 4.8 m rather than the extract's generic 5.2 m.
    width=r['width'] if walk else min(r['width'],4.80)
    area=line.buffer(width/2,quad_segs=6).intersection(clip)
    (paths if walk else drive).append(area)
    roads.append({'id':r['id'],'kind':r['type'],'width':width})
road_union=unary_union(drive).difference(footprint.buffer(.3)).difference(reserved)
plaza=box(-22.7,-25.5,22.6,-8.5).difference(road_union.buffer(.14)).difference(footprint)
platform=box(-13.9,-12.0,22.7,-8.85).difference(footprint)
margin=road_union.buffer(2.05,quad_segs=6).difference(road_union.buffer(.19)).intersection(clip).difference(footprint.buffer(.15)).difference(reserved).difference(plaza.buffer(.15))
walk=unary_union([margin,*paths]).intersection(clip).difference(road_union.buffer(.11)).difference(plaza.buffer(.11)).difference(footprint).difference(reserved)
curbs=road_union.buffer(.22,quad_segs=6).difference(road_union).intersection(clip).difference(footprint)
grid=data['grid']; level=grid['heights']; dx=grid['step']
def dem(x,y):
    e=c*x+s*y;n=s*x-c*y
    i=(e-grid['x'])/dx;j=(n-grid['z'])/dx
    a=math.floor(i);b=math.floor(j)
    u=i-a;v=j-b
    if not (0<=a<len(level[0])-1 and 0<=b<len(level)-1):return None
    return (level[b][a]*(1-u)+level[b][a+1]*u)*(1-v)+(level[b+1][a]*(1-u)+level[b+1][a+1]*u)*v
sample=[dem(*p) for p in [(-3,-11),(-3,-30),(-35,-9),(25,-36),(45,20),(-35,20)]]
assert all(v is not None for v in sample)
print('DEM at entrance / road / corners',sample)
gx,gy,span= -110,-145,1.25
nx,ny=168,166
# Outside the local extract the base is a neutral transition, not a mapped campus surface.
height=[]
settled=footprint.buffer(5.0)
hard=box(-23,-26,23,-8).union(settled)
from shapely.geometry import Point
for j in range(ny):
    y=gy+j*span
    for i in range(nx):
        x=gx+i*span
        dist=hard.distance(Point(x,y))
        w=min(1.,dist/20)**1.6
        z=dem(x,y)
        z=0.0 if z is None else max(-2.8,min(2.4,(z-sample[0])*.75))
        height.append(round(-.095*(1-w)+z*w,4))
# Walkable coverage is the cropped site minus adjacent building reservations.
walkable=clip.buffer(-.5).difference(reserved.buffer(1.0)).difference(footprint).difference(box(-13.91,-9.44,22.70,-.75))
trees_candidates=[(-44,-22,8),(-44,-39,11),(-17,-38,8),(10,-44,9),(32,-35,8),(29,-15,6),(59,21,9),
    (51,25,10),(31,27,8),(7,19,8),(-12,19,8),(-27,15,7),(-36,16,9),(-49,-10,11),(-42,-5,7),
    (-54,-45,12),(-36,-44,8),(28,-43,10),(65,7,8),(-33.7,3.8,6),(15,-27,3.3)]
trees=[]
for x,y,h in trees_candidates:
    p=Point(x,y)
    if clip.buffer(-.2).covers(p) and not (road_union.buffer(.55).covers(p) or footprint.buffer(1.1).covers(p) or reserved.buffer(.65).covers(p) or platform.covers(p)):
        trees.append([x,y,h])
lamps=[[-24,-16],[-24,-32],[-35,-18],[25,-36],[25,-18],[-25,13],[47,17]]
lamps=[p for p in lamps if clip.covers(Point(*p)) and not (road_union.buffer(.4).covers(Point(*p)) or reserved.covers(Point(*p)) or footprint.covers(Point(*p)))]
doc={'source':'© OpenStreetMap contributors · ODbL 1.0','extent':list(clip.bounds),'grid':{'x':gx,'y':gy,'spacing':span,'nx':nx,'ny':ny,'height':height},'geometry':{k:encode(g) for k,g in [('road',road_union),('walk',walk),('curb',curbs),('plaza',plaza),('platform',platform),('reserve',reserved),('roundabout',Point(14.9,-26.65).buffer(3.7))]},'walkable':encode(walkable),'outline':encode(footprint),'trees':trees,'lamps':lamps,'roads':roads}
out.write_text(json.dumps(doc,separators=(',',':')))
print('Trees',len(trees),'lamps',len(lamps),'ways',len(roads))
# Split before triangulating so roads and paving have enough samples to follow the local grade.
def triangles(g,step=2.5):
    result=[]
    if not g.is_empty:
        ax,ay,bx,by=g.bounds
        for x in range(math.floor(ax/step),math.ceil(bx/step)):
            for y in range(math.floor(ay/step),math.ceil(by/step)):
                region=g.intersection(box(x*step,y*step,(x+1)*step,(y+1)*step))
                for piece in shapes(region):
                    if piece.area>.0005:
                        result.extend([list(k.exterior.coords)[:3] for k in constrained_delaunay_triangles(piece).geoms])
    return result
doc['triangles']={name:triangles(poly) for name,poly in [('road',road_union),('walk',walk),('curb',curbs),('plaza',plaza),('platform',platform),('roundabout',Point(14.9,-26.65).buffer(3.7))]}
out.write_text(json.dumps(doc,separators=(',',':')))
