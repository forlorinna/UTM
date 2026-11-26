"""Generate the Menara Razak architectural asset and saved camera scene."""
import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

P = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=P)
parser.add_argument('--draft', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
args.output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
randomizer = random.Random(76311)

def linear(c):
    return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4

def rgb(hexcode):
    t = hexcode.lstrip('#')
    return tuple(linear(int(t[i:i+2],16)/255) for i in (0,2,4))

def make_material(name, color, rough=.5, metal=0., transmit=0., ior=1.46):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*rgb(color),1)
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    b.inputs['Transmission Weight'].default_value=transmit
    b.inputs['IOR'].default_value=ior
    m.diffuse_color=(*rgb(color),1)
    return m

def texture_material(name, prefix, tint, normal_strength=.45, metal=0., rough=.55, diffuse=True, use_metal_map=False):
    m=make_material(name,tint,rough,metal)
    tree=m.node_tree
    bsdf=tree.nodes.get('Principled BSDF')
    def map_channel(channel, point, raw=False):
        src=next((P/'materials').glob(f'{prefix}_{channel}.*'),None)
        if not src:
            return None
        n=tree.nodes.new('ShaderNodeTexImage')
        n.name=prefix+' • '+channel
        n.location=point
        n.image=bpy.data.images.load(str(src),check_existing=True)
        if raw:
            n.image.colorspace_settings.name='Non-Color'
        return n
    if diffuse and (albedo:=map_channel('Neutral' if prefix=='clean' else 'Diffuse',(-695,310))):
        mix=tree.nodes.new('ShaderNodeMixRGB')
        mix.blend_type='MULTIPLY'
        mix.inputs[0].default_value=1
        mix.inputs[2].default_value=(*rgb(tint),1)
        mix.location=(-420,317)
        tree.links.new(albedo.outputs['Color'],mix.inputs[1])
        tree.links.new(mix.outputs['Color'],bsdf.inputs['Base Color'])
    if n:=map_channel('nor_gl',(-695,-190),True):
        normal=tree.nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value=normal_strength
        normal.location=(-400,-190)
        tree.links.new(n.outputs['Color'],normal.inputs['Color'])
        tree.links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
    if r:=map_channel('Rough',(-700,30),True):
        tree.links.new(r.outputs['Color'],bsdf.inputs['Roughness'])
    if use_metal_map and (n:=map_channel('Metal',(-690,-490),True)):
        tree.links.new(n.outputs['Color'],bsdf.inputs['Metallic'])
    return m

materials={
    'cream':texture_material('Ivory rainscreen · scanned painted concrete','clean','e9e4d3',.22),
    'beige':texture_material('Sandstone-toned entry concrete','clean','d2bfa4',.29),
    'red':texture_material('Burgundy terracotta · fine masonry','clean','a35a51',.22),
    'stone':texture_material('Bush-hammered plaza and stair concrete','granite','c7c3b9',.52),
    'brick':texture_material('Red-brown plaza pavers','brick','c8b3b4',.46),
    'ash':make_material('Neutral photography ground','9b9c97',.92),
    'metal':texture_material('Satin aluminium · scanned microstructure','aluminium','c1c6c6',.10,.55,.4,False,True),
    'roof':texture_material('Crown zinc skin · scanned metal','aluminium','c4cdd0',.26,.55,.37,False,True),
    'shade':make_material('Aluminium sunshade · off-white powder coat','dbded6',.27,.19),
    'bright':make_material('Anodised frame · satin aluminium','a3b0b2',.27,.56),
    'black':make_material('EPDM gasket and shadow gap','252b2c',.85),
    'soffit':make_material('Graphite perforated soffit','424b4e',.47,.40),
    'blind':make_material('Window backing · warm neutral','b4aca0',.8),
    'room':make_material('Shadowed office ceiling and core','706b61',.86),
    'gravel':make_material('Roof service terrace aggregate','95938d',.95),
    'signwhite':make_material('Porcelain enamel sign panel','f0e9d7',.36,.08),
    'signred':make_material('Burgundy lettering','69312c',.38),
    'signblack':make_material('Black metal lettering','1b1f20',.38,.31),
    'gold':make_material('Bronze seal rim','9c7751',.31,.57),
    'light':make_material('Warm opal light diffuser','e3dec9',.3),
    'wet':make_material('Canopy glazing · neutral laminated glass','a6cacc',.106,0.,.90,1.48),
}
for index,(c,transmit) in enumerate((('5486a8',.54),('5187aa',.55),('457b9a',.47),('6793af',.60),('639bb9',.52),('4b7591',.48))):
    m=make_material('Blue solar-control glass %02d'%(index+1),c,.13+(index%3)*.026,0.,transmit,1.47)
    node=m.node_tree.nodes.get('Principled BSDF')
    node.inputs['Coat Weight'].default_value=.32
    node.inputs['Coat Roughness'].default_value=.13
    materials['g'+str(index)]=m

names=['01 Structural slabs and core','02 SW curved curtain wall','03 NE stone elevation','04 End walls','05 Crown and mechanical screen','06 Entrance and canopy','07 Lettering and signage','08 Immediate forecourt','90 Lighting and inspection cameras']
collections={}
for key,name in zip(('frame','front','rear','ends','roof','entry','sign','site','stage'),names):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    collections[key]=c

mesh_parts=defaultdict(lambda:[[],[],[]])

def surface(group, element, mat, points, tile=2.2):
    if len(points)<3:return
    vertices,polygons,uvs=mesh_parts[group,element,mat]
    at=len(vertices)
    vertices.extend(points)
    polygons.append(tuple(range(at,at+len(points))))
    base, b, c=map(Vector,points[:3])
    normal=(b-base).cross(c-base)
    if abs(normal.z)>abs(normal.x)+abs(normal.y)*.65:
        uv=[(p[0]/tile,p[1]/tile) for p in points]
    else:
        direction=Vector((normal.y,-normal.x,0))
        if direction.length<1e-8:
            direction=Vector((1,0,0))
        direction.normalize()
        uv=[(Vector(p).dot(direction)/tile,p[2]/tile) for p in points]
    uvs.append(uv)

def prism(group,name,mat,plan,lo,hi,tile=2.2):
    if hi<=lo:return
    lower=[(x,y,lo) for x,y in plan]
    upper=[(x,y,hi) for x,y in plan]
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(plan,plan[1:]+plan[:1]))<0:
        lower.reverse();upper.reverse()
    surface(group,name,mat,list(reversed(lower)),tile)
    surface(group,name,mat,upper,tile)
    for i in range(len(plan)):
        j=(i+1)%len(plan)
        surface(group,name,mat,[lower[i],lower[j],upper[j],upper[i]],tile)

def axisbox(group,name,mat,x0,x1,y0,y1,z0,z1,tile=2.2):
    prism(group,name,mat,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z0,z1,tile)

def profiled_beam(group,name,mat,a,b,width,height,c=.015,up=(0,0,1)):
    a,b=Vector(a),Vector(b)
    direction=b-a
    if direction.length<.0001:return
    direction.normalize()
    u=direction.cross(Vector(up))
    if u.length<.0001:
        u=direction.cross(Vector((0,1,0)))
    u.normalize()
    v=u.cross(direction).normalized()
    w,h=width*.5,height*.5
    c=min(c,w*.5,h*.5)
    section=[(-w+c,-h),(w-c,-h),(w,-h+c),(w,h-c),(w-c,h),(-w+c,h),(-w,h-c),(-w,-h+c)]
    r0=[tuple(a+u*x+v*z) for x,z in section]
    r1=[tuple(b+u*x+v*z) for x,z in section]
    surface(group,name,mat,r0)
    surface(group,name,mat,list(reversed(r1)))
    for i in range(8):
        j=(i+1)%8
        surface(group,name,mat,[r0[i],r1[i],r1[j],r0[j]])

def cylinder(group,name,mat,a,b,r0,r1=None,segments=24):
    a,b=Vector(a),Vector(b)
    q=(b-a).to_track_quat('Z','Y')
    r1=r1 if r1 is not None else r0
    rings=[]
    for cen,rad in ((a,r0),(b,r1)):
        rings.append([tuple(cen+q@Vector((math.cos(j*2*math.pi/segments)*rad,math.sin(j*2*math.pi/segments)*rad,0))) for j in range(segments)])
    p0,p1=rings
    surface(group,name,mat,list(reversed(p0)))
    surface(group,name,mat,p1)
    for j in range(segments):
        k=(j+1)%segments
        surface(group,name,mat,[p0[j],p0[k],p1[k],p1[j]])

geo=json.loads((P/'footprint.json').read_text())
angle=.66008744836
rot=lambda x,z:(math.cos(angle)*x+math.sin(angle)*z, math.sin(angle)*x-math.cos(angle)*z)
outline=[rot(*p) for p in geo['footprint']]
rear_y=9.915
SW=sorted([(-20.6,4.9),(-18.7,3.24),(-17.24,1.884),(-14.57,.123),(-12.29,-1.156),(-9.49,-2.324),(-6.475,-3.383),(-.566,-5.186),(5.675,-6.856),(11.612,-7.81),(17.668,-8.445),(30.672,-8.782),(37.603,-8.805),(62.288,-8.869)])

def front(x):
    x=max(SW[0][0],min(SW[-1][0],x))
    for (a,y),(b,z) in zip(SW,SW[1:]):
        if x<=b:
            return y+(x-a)/(b-a)*(z-y)
    return SW[-1][1]

def segment_front(group,name,mat,x0,x1,z0,z1,outer=0.,thick=.10):
    y0=front(x0)-outer
    y1=front(x1)-outer
    prism(group,name,mat,[(x0,y0),(x1,y1),(x1,y1+thick),(x0,y0+thick)],z0,z1,1.8)

def trim_front(name,mat,x0,x1,z,depth,height,lead=.06):
    profiled_beam('front',name,mat,(x0,front(x0)-lead,z),(x1,front(x1)-lead,z),depth,height,.014)

levels=[0.,4.65,7.75,10.59]+[13.44+2.85*i for i in range(13)]
core=[(x*.65+5,y*.66+.62) for x,y in outline]
prism('frame','Core enclosure','room',core,-1.2,50.3)
for i,level in enumerate(levels):
    factor=.92 if i>1 else .96
    inner=[(x*factor+(1-factor)*13,y*factor+.014) for x,y in outline]
    prism('frame','Recessed slab edges','room',inner,level-.26,level-.022)
    if i>2:
        band=[(x*.96+.15,y*.91+.10) for x,y in outline]
        prism('frame','Suspended floor soffits','blind',band,level-.66,level-.61)

# The broad southwest elevation changes rhythm and depth across its photographed zones.
zones=[(-20.55,-15.8,'end'),(-15.8,2.5,'fins'),(2.5,24.05,'bands'),(24.05,35.75,'vertical'),(35.75,60.85,'bands')]
for left,right,section in zones:
    baytarget={'end':1.3,'fins':1.16,'bands':1.42,'vertical':1.08}[section]
    baycount=round((right-left)/baytarget)
    xs=[left+(right-left)*i/baycount for i in range(baycount+1)]
    xs=sorted(set(xs+[x for x,y in SW if left<x<right]))
    for floor,(lo,hi) in enumerate(zip(levels[1:],levels[2:]+[49.5])):
        if floor==0 and right<24.1:continue
        hi=min(hi,49.2)
        for bay,(a,b) in enumerate(zip(xs,xs[1:])):
            if b-a<.11:continue
            width=b-a
            if section=='end':
                segment_front('front','Northwest red return in ceramic panels','red',a+.012,b-.012,lo,hi-.022,.05,.22)
                if width>.65 and floor>3:
                    segment_front('front','Inset ribbon slits',f'g{bay%6}',a+.13,b-.13,lo+1.08,lo+1.71,.078,.035)
                continue
            lower=.64 if section=='bands' else .46 if section=='vertical' else .34
            top=.35 if section!='bands' else .31
            segment_front('front','Recessed spandrel infill','soffit' if section=='fins' else 'shade',a,b,lo,lo+lower,.025,.18)
            top_glass=hi-top
            bottom_glass=lo+lower+.035
            if top_glass>bottom_glass:
                gap=.035
                segment_front('front','Double-glazed vision panels',f'g{randomizer.choices(range(6),[4,7,3,4,3,3])[0]}',a+gap,b-gap,bottom_glass,top_glass,.009,.024)
                if width>.65:
                    z=(lo+hi)*.5+.24
                    trim_front('Intermediate transoms','bright',a,b,z,.065,.043,.042)
                    if section=='fins':
                        depth=.64
                        trim_front('Two-level exposed solar fins','metal',a,b,lo+.48,depth,.075,.18)
                        trim_front('Two-level exposed solar fins','metal',a,b,hi-.23,depth,.075,.18)
                    if section=='vertical' and (bay%3==0 or bay==len(xs)-2):
                        profiled_beam('front','Deep vertical blade fins','shade',(a,front(a)-.39,lo-.04),(a,front(a)-.39,hi),.59,.47,.031)
                    if section in ('bands','vertical') and bay%7==3:
                        segment_front('front','Intermittent interior roller shades','blind',a+.11,b-.11,top_glass-.69,top_glass+.02,-.31,.027)
            segment_front('front','Continuous head spandrels','shade' if section!='fins' else 'soffit',a,b,max(lo+lower,hi-top),hi,.042,.20)
            trim_front('Projecting light bands','shade' if section!='fins' else 'metal',a,b,lo+.045,.53 if section=='bands' else .22,.15 if section=='bands' else .098,.14)
            profiled_beam('front','Split-cover jambs','bright',(a,front(a)-.058,lo),(a,front(a)-.058,hi),.092,.09,.014)
    if section!='end':
        for a,b in zip(xs,xs[1:]):
            segment_front('front','Dark crown clerestory',f'g{int(abs(a))%6}',a+.025,b-.025,49.13,52.22,.019,.06)
            profiled_beam('front','Roof clerestory ribs','metal',(a,front(a)-.08,49.03),(a,front(a)-.08,52.97),.055,.085,.012)

# Straight northeast elevation, including the opaque bays and irregular openings visible in the 03a photo.
def rear_rect(name,mat,x0,x1,z0,z1,offset=0.,depth=.18):
    axisbox('rear',name,mat,x0,x1,rear_y+offset-depth,rear_y+offset,z0,z1,1.85)

def rear_window(x0,x1,z0,z1,index,frame=True):
    rear_rect('Recessed NE glazing',f'g{index%6}',x0+.025,x1-.025,z0+.018,z1-.018,-.25,.021)
    rear_rect('Recessed black jambs','black',x0,x0+.065,z0,z1,-.195,.06)
    rear_rect('Recessed black jambs','black',x1-.065,x1,z0,z1,-.195,.06)
    if frame:
        for j in range(1,math.ceil((x1-x0)/1.18)):
            x=x0+(x1-x0)*j/math.ceil((x1-x0)/1.18)
            rear_rect('Aluminium NE window divisions','bright',x-.027,x+.027,z0,z1,-.21,.045)
        rear_rect('Aluminium sill flashing','bright',x0,x1,z0,z0+.052,-.16,.09)

# Every opaque bay is split at its own openings, with facing, return surfaces and reveal depth.
bays=[
    (-19.20,-3.85,'red-spine'),(-3.85,8.9,'recessed-strips'),(8.9,16.3,'recessed-strips'),
    (16.3,24.2,'solid'),(24.2,27.45,'riser'),(27.45,33.6,'solid'),
    (33.6,37.0,'riser'),(37.0,50.94,'grid'),
]
for bi,(a,b,section) in enumerate(bays):
    for floor,(lo,hi) in enumerate(zip(levels,levels[1:]+[52.8])):
        if section!='red-spine':
            hi=min(hi,49.21)
        if hi<=lo:
            continue
        if section=='red-spine':
            z0,z1=lo+1.05,min(lo+1.80,hi)
            holes=[(a+5.4,a+8.7,z0,z1)] if 2<=floor<=14 else []
            mat='red'
        elif section=='recessed-strips':
            holes=[(a+1.3,b-.85,lo+.72,min(lo+1.44,hi))] if floor<16 and floor>1 else []
            if floor==15:holes=[(a+1.3,b-.84,lo+.19,hi-.12)]
            mat='cream'
        elif section=='riser':
            holes=[(a+.55,b-.39,lo+.21,hi-.18)] if 1<=floor<17 else []
            mat='cream'
        elif section=='grid':
            holes=[]
            if 1<=floor<=15:
                for j in range(4):
                    w=(b-a)/4
                    holes.append((a+j*w+.40,a+(j+1)*w-.37,lo+.42,hi-.29))
            mat='cream'
        else:
            holes=[(a+.8,a+2.,lo+1.26,lo+1.54)] if floor in (3,5,7,9,11,13,15) else []
            mat='cream'
        if not holes:
            count=max(1,round((b-a)/2.8)) if mat=='red' else 1
            for j in range(count):
                p=a+(b-a)*j/count
                q=a+(b-a)*(j+1)/count
                rear_rect('Continuous cladding panels',mat,p+.009,q-.009,lo+.008,hi-.009,.034 if mat=='red' else .022,.25)
            continue
        cursor=a
        for x0,x1,z0,z1 in holes:
            rear_rect('Cladding between window openings',mat,cursor+.008,x0,lo+.009,hi-.009,.024,.29)
            rear_rect('Lower wall panel and sill',mat,x0,x1,lo+.008,z0,.024,.42)
            rear_rect('Upper wall panel and lintel',mat,x0,x1,z1,hi-.009,.024,.42)
            rear_window(x0,x1,z0,z1,bi+floor)
            if section=='recessed-strips':
                profiled_beam('rear','Recessed ribbon overhang','cream',(x0-.05,rear_y+.30,z1+.07),(x1+.05,rear_y+.30,z1+.07),.73,.21,.024)
                if floor>=14:
                    for j in range(1,math.ceil((x1-x0)/.92)):
                        x=x0+j*.88
                        if x<x1-.1:rear_rect('Deep tall-window fins','cream',x-.071,x+.071,z0,z1,.40,.68)
            if section=='grid':
                axisbox('rear','Deep concrete window grids','cream',cursor+.037,x0,rear_y-.055,rear_y+.64,lo+.03,hi-.023,1.8)
                axisbox('rear','Deep concrete window grids','cream',x0,x1,rear_y-.055,rear_y+.64,hi-.26,hi-.03,1.8)
            cursor=x1
        rear_rect('Cladding between window openings',mat,cursor,b-.008,lo+.012,hi-.012,.024,.29)
        if mat=='red':
            for j in range(1,5):
                y=lo+j*(hi-lo)/5
                rear_rect('Burgundy panel horizontal joints','black',a+.015,b-.016,y-.004,y+.004,.028,.014)
    if section!='red-spine':
        for j in range(1,math.ceil((b-a)/.45)):
            x=a+j*.45
            rear_rect('Crown vent blade ribs','soffit',x-.066,x+.064,49.18,52.77,.028,.39)
        rear_rect('Dark crown mechanical opening','black',a,b,49.15,52.84,-.41,.1)

# Infill the two end returns between the surveyed long faces.
for kind,points in [('NW',[p for p in outline if p[0]<-16.8]),('SE',[(51.03,rear_y),(62.288,-8.869)])]:
    if kind=='NW':
        points=sorted(points,key=lambda p:p[1],reverse=True)
        points=[(x,y) for x,y in points if y>=1.88]
    for (a,b) in zip(points,points[1:]):
        step=max(1,math.ceil(math.dist(a,b)/1.30))
        for tile in range(step):
            s,t=tile/step,(tile+1)/step
            x,y=a[0]*(1-s)+b[0]*s,a[1]*(1-s)+b[1]*s
            u,v=a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t
            for i,(lo,hi) in enumerate(zip(levels,levels[1:]+[52.0])):
                if kind=='NW' and tile%3==0:
                    surface('ends','Burgundy wrap on the rounded end','red',[(x,y,lo),(u,v,lo),(u,v,hi),(x,y,hi)])
                    continue
                surface('ends','Glazed end returns',f'g{(tile+i)%6}',[(x,y,lo+.35),(u,v,lo+.35),(u,v,hi-.21),(x,y,hi-.21)])
                profiled_beam('ends','End bay pressure caps','bright',(x,y,lo),(x,y,hi),.10,.10,.013)
                profiled_beam('ends','Exterior end sunshade tracks','metal',(x,y,lo+.22),(u,v,lo+.22),.32,.091,.019)

# Structural edge walls remain behind the open face systems. They are inset to retain window depth.
prism('frame','Recessed southeast stair core','room',[(42.9,6.1),(49.3,8.2),(59.2,-6.8),(46.7,-6.65)],-.25,50.3)

def roof_z(x,f):
    t=(x+23)/88
    return 52.86+1.18*math.sin(math.pi*t)+.29*(1-t)+.25*math.sin(math.pi*f)

def roof_point(i,j):
    f=j/12
    q=i/64
    x=-23+88*q
    edge=math.sin(math.pi*q)**.55
    near=front(x)-1.84*edge
    far=rear_y+1.49*edge
    center=(near+far)*.5
    # Rounded eave ends contract to the nosing while the main spans remain broad.
    envelope=min(1., math.sqrt(max(0.,1-((q-.045)/.045)**2))) if q<.045 else min(1.,math.sqrt(max(0.,1-((q-.952)/.048)**2))) if q>.952 else 1.
    y=center+(near+(far-near)*f-center)*max(.027,envelope)
    return (x,y,roof_z(x,f))

for i in range(64):
    for j in range(12):
        quad=[roof_point(i,j),roof_point(i+1,j),roof_point(i+1,j+1),roof_point(i,j+1)]
        surface('roof','Continuous double-curvature zinc envelope','roof',quad,3.8)
        below=[(x,y,z-.55) for x,y,z in quad]
        surface('roof','Segmented dark crown soffit','soffit',list(reversed(below)),3.8)
        if i%2==0:
            a,b=quad[0],quad[3]
            profiled_beam('roof','Standing-seam ribs','metal',(a[0],a[1],a[2]+.024),(b[0],b[1],b[2]+.024),.050,.040,.008)
    for j in [0,12]:
        a,b=roof_point(i,j),roof_point(i+1,j)
        surface('roof','Silver curved eave fascia','metal',[a,b,(b[0],b[1],b[2]-.56),(a[0],a[1],a[2]-.56)])
        x,y,z=b
        profiled_beam('roof','Eave panel joints','soffit',(x,y,z-.55),(x,y,z),.032,.045,.006)
    if i%5==0 and 3<i<61:
        a=roof_point(i,0);b=roof_point(i,12)
        profiled_beam('roof','Under-eave rib members','soffit',(a[0],a[1],a[2]-.60),(b[0],b[1],b[2]-.60),.17,.22,.016)
for i in range(2):
    x=-16.2+i*7.45
    c=front(x)
    profiled_beam('roof','Burgundy clerestory posts','red',(x,c+.025,48.15),(x,c+.025,53.32),.30,.33,.024)

# Original 2022 and 2025 photos show a curved glazed canopy with two round columns,
# a recessed ground-floor entrance and a projecting clad deck on its right.
entry_y=-9.39
portal=(-7.55,1.70)
door_left,door_right=-5.79,-.00
def entry_face(name,mat,x0,x1,z0,z1,y=entry_y,depth=.27):
    axisbox('entry',name,mat,x0,x1,y,y+depth,z0,z1,1.52)

for a,b in [(-13.80,-11.92),(-9.12,-7.65),(1.70,2.70),(5.98,7.15),(11.19,11.70),(16.38,17.34),(21.66,22.60)]:
    entry_face('Champagne concrete pier panels','beige',a,b,.27,6.62)
for a,b in [(-11.92,-9.12),(-7.61,1.67),(2.7,5.98),(7.15,11.19),(11.7,16.38),(17.34,21.66)]:
    entry_face('Staggered warm-stone cladding','beige',a,b,.28,.67)
    if not (a>=-7.7 and b<2):
        entry_face('Continuous cladding above doors','beige',a,b,3.96,4.78)
    entry_face('Continuous cladding above windows','beige',a,b,6.16,6.65)
    if a>=-7.7 and b<2:
        entry_face('Entry fascia backing for independently mounted letters','beige',a,b,3.54,4.92)
    for lo,hi in ([(.67,3.75),(4.82,6.16)] if not (a>-8 and b<2) else [(4.94,6.16)]):
        for j in range(math.ceil((b-a)/1.55)):
            n=math.ceil((b-a)/1.55)
            u=a+j*(b-a)/n;v=a+(j+1)*(b-a)/n
            entry_face('Recessed lobby insulating glass',f'g{(j+2)%6}',u+.042,v-.041,lo+.051,hi-.049,entry_y+.134,.027)
            entry_face('Recessed fixed glazing edge frame','bright',u+.011,u+.061,lo,hi,entry_y+.093,.10)
            entry_face('Recessed fixed glazing head','bright',u,v,hi-.058,hi,entry_y+.095,.09)
            if hi-lo>1.8:
                entry_face('Lobby horizontal transom','bright',u,v,lo+.63,lo+.675,entry_y+.092,.08)
for a,b in [(-7.60,door_left-.20),(door_right+.20,1.70)]:
    entry_face('Narrow entry sidelights','g4',a+.055,b-.055,.78,3.65,entry_y+.19,.033)
    entry_face('Recessed jamb flashing','bright',a,a+.07,.74,3.69,entry_y+.16,.09)
entry_face('Portal sill threshold','stone',door_left-.45,door_right+.46,.55,.64,entry_y-.36,.68)
entry_face('Angular silver portal header','metal',door_left-.37,door_right+.38,3.26,3.69,entry_y-.13,.48)
entry_face('Door jamb channel','metal',door_left-.35,door_left-.06,.64,3.28,entry_y-.12,.49)
entry_face('Door jamb channel','metal',door_right+.06,door_right+.36,.64,3.28,entry_y-.12,.49)
for i in range(4):
    a=door_left+i*(door_right-door_left)/4
    b=door_left+(i+1)*(door_right-door_left)/4
    entry_face('Tempered automatic doors','g4',a+.055,b-.055,.70,3.19,entry_y+.40,.018)
    entry_face('Automatic door edge profile','bright',a,a+.052,.63,3.22,entry_y+.38,.051)
    entry_face('Kick plate','bright',a+.028,b-.030,.635,.728,entry_y+.365,.075)
    entry_face('Top door rail','bright',a+.032,b-.034,3.166,3.242,entry_y+.367,.078)
    if i in (1,2):
        x=(a+b)*.5
        cylinder('entry','Door pull','bright',(x,entry_y+.302,1.54),(x,entry_y+.302,2.10),.014,segments=12)
entry_face('Lobby recess backwall','room',-9.03,3.90,.73,6.60,entry_y+3.20,.38)
entry_face('Recessed lobby ceiling','blind',-8.70,3.60,3.22,3.39,entry_y+.64,2.55)

def canopy_point(i,j):
    x=-10.0+i*1.31
    t=i/10
    b=j/5
    y=entry_y+b*(-8.22-.46*math.sin(math.pi*t))
    z=6.77-.45*b+.23*(2*t-1)**2
    return (x,y,z)
for i in range(10):
    for j in range(5):
        p,q,r,s=(canopy_point(i,j),canopy_point(i+1,j),canopy_point(i+1,j+1),canopy_point(i,j+1))
        center=Vector(p)+Vector(q)+Vector(r)+Vector(s)
        points=[tuple(Vector(point).lerp(center*.25,.019)) for point in (s,r,q,p)]
        surface('entry','Curved laminated canopy panels','wet',points,1.35)
        for a,b in ((p,q),(p,s)):
            aa,bb=((a[0],a[1],a[2]-.055),(b[0],b[1],b[2]-.055))
            profiled_beam('entry','Glazed canopy pressure plates','bright',aa,bb,.11,.135,.013)
        if i%2==0 and j in (2,4):
            for point in (p,s):
                x,y,z=point
                cylinder('entry','Stainless glazing point fixings','bright',(x,y,z-.16),(x,y,z+.025),.047,segments=12)
    a,b=canopy_point(i,5),canopy_point(i+1,5)
    profiled_beam('entry','Rolled silver canopy nose','metal',(a[0],a[1],a[2]-.25),(b[0],b[1],b[2]-.25),.28,.49,.040)
for x in (-8.05,.90):
    y=entry_y-7.71
    cylinder('entry','Round white canopy columns','shade',(x,y,.22),(x,y,6.16),.22,.185,36)
    cylinder('entry','Round canopy column shoes','bright',(x,y,.22),(x,y,.39),.226,.219,36)
    cylinder('entry','Round canopy bracket collars','bright',(x,y,5.94),(x,y,6.13),.212,.204,36)
    profiled_beam('entry','Canopy diagonal ties','bright',(x,y,6.02),(x+.78,y+1.86,6.34),.067,.068,.008)
    profiled_beam('entry','Canopy diagonal ties','bright',(x,y,6.02),(x-.65,y+1.80,6.34),.067,.068,.008)

deck=[(3.25,-9.34),(16.9,-9.34),(16.9,-13.61),(12.83,-13.61),(12.83,-16.36),(7.19,-16.36),(7.19,-13.92),(3.25,-13.20)]
prism('entry','Offset deck supporting slab','stone',deck,3.57,4.05)
for (a,b) in zip(deck[1:],deck[2:]+[deck[0]]):
    length=math.dist(a,b)
    count=max(1,round(length/.72))
    for i in range(count):
        p=Vector((*a,3.87)).lerp(Vector((*b,3.87)),(i+.012)/count)
        q=Vector((*a,3.87)).lerp(Vector((*b,3.87)),(i+.987)/count)
        profiled_beam('entry','Individually jointed deck fascia','metal',p,q,.16,1.126,.017)
    for height,rad in ((4.98,.026),(4.76,.014),(4.55,.014),(4.33,.014),(4.15,.016)):
        cylinder('entry','Stainless deck rail tubes','bright',(*a,height),(*b,height),rad,segments=12)
    for i in range(count+1):
        x,y,z=Vector((*a,4.03)).lerp(Vector((*b,4.03)),i/count)
        if i%2==0:cylinder('entry','Stainless baluster posts','bright',(x,y,z),(x,y,5.01),.025,segments=12)
for a in (5.55,11.49,15.51):
    axisbox('entry','Supporting entrance pilasters','beige',a-.28,a+.29,-12.75,-12.12,.31,3.73,1.38)

for i in range(4):
    y=entry_y-1.83+i*.36
    axisbox('entry','Bush-hammered shallow entry stair','stone',door_left-2.5,door_right+1.83,y,entry_y+.08,.00,.16+i*.133,1.3)
    profiled_beam('entry','Rounded stone stair nosing','stone',(door_left-2.50,y-.013,.155+i*.133),(door_right+1.83,y-.013,.155+i*.133),.072,.053,.022)
for x in (door_left-2.18,door_right+1.48):
    for j in range(3):
        y=entry_y-1.75+j*.50
        cylinder('entry','Stair rail stanchions','bright',(x,y,.16+j*.13),(x,y,1.00+j*.13),.021,segments=12)
    cylinder('entry','Stair handrail','bright',(x,entry_y-1.80,1.00),(x,entry_y-.55,1.34),.031,segments=16)

# The ground storey retains recessed glazed bays, jambs and opaque floor-edge cladding.
for (a,_),(b,_) in zip(SW,SW[1:]):
    a,b=max(-20.55,a),min(62.23,b)
    if b-a<.15:
        continue
    edges=sorted(set([a,b]+[x for x in (-13.80,22.60) if a<x<b]))
    for left,right in zip(edges,edges[1:]):
        if right-left<.15:
            continue
        covered=-13.80<=left and right<=22.60
        if covered:
            segment_front('front','Recessed structural fascia behind the entrance','beige',left,right,6.47,7.74,-.055,.33)
            continue
        bay_count=max(1,round((right-left)/1.68))
        for n in range(bay_count):
            x=left+(right-left)*n/bay_count
            u=left+(right-left)*(n+1)/bay_count
            segment_front('front','Ground-floor stone base band','cream',x,u,.14,.66,.027,.25)
            segment_front('front','Ground-floor head fascia','shade',x,u,3.96,4.66,.031,.24)
            z0,z1=.665,3.961
            segment_front('front','Ground-floor framed vision glazing',f'g{n%6}',x+.056,u-.054,z0,z1,-.045,.026)
            trim_front('Ground-floor aluminium transom','bright',x,u,2.03,.123,.070,.010)
            profiled_beam('front','Ground-floor jamb cover','bright',(x,front(x)-.026,z0),(x,front(x)-.026,z1),.110,.130,.013)
            if right<=-13.79:
                segment_front('front','Western flank behind the ground-level return','red',x,u,4.63,7.75,.025,.21)
for x in (-13.80,22.60):
    y=front(x)+.08
    if y>entry_y:
        axisbox('entry','Solid lobby side returns','beige',x-.16,x+.15,entry_y,y,.27,6.63)

def signage(name,word,x,y,z,size,mat,face='front',serif=False):
    curve=bpy.data.curves.new(name,'FONT')
    curve.body=word
    curve.align_x='CENTER'
    curve.align_y='CENTER'
    curve.size=size
    curve.space_character=1.05
    curve.extrude=.013 if size<1 else .021
    curve.bevel_depth=.006 if size<1 else .010
    curve.bevel_resolution=2
    font=Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSerif.ttf' if serif else 'DejaVuSans-Bold.ttf')
    if font.exists():
        curve.font=bpy.data.fonts.load(str(font),check_existing=True)
    ob=bpy.data.objects.new(name,curve)
    collections['sign'].objects.link(ob)
    ob.rotation_euler=(math.pi/2,0,0 if face=='front' else math.pi)
    ob.location=(x,y,z)
    ob.data.materials.append(materials[mat])
    bpy.context.view_layer.objects.active=ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob.select_set(False)

def seal(x,y,z,r,reverse=False):
    forward=.018 if reverse else -.018
    cylinder('sign','Approximate circular enamel medallion','gold',(x,y,z),(x,y+forward,z),r,segments=48)
    cylinder('sign','Burgundy concentric seal inset','signred',(x,y+forward,z),(x,y+forward*1.3,z),r*.81,segments=48)
    cylinder('sign','Inner gold detail of lettering plate','gold',(x,y+forward*1.3,z),(x,y+forward*1.6,z),r*.59,segments=48)
    cylinder('sign','Centre of lettering plate','signred',(x,y+forward*1.6,z),(x,y+forward*1.9,z),r*.45,segments=48)

signage('Cast metal entry lettering','MENARA RAZAK',-2.94,entry_y-.024,4.116,.46,'signblack')
signage('Smaller upper university lettering','UTM',-2.86,entry_y-.031,4.64,.43,'signred',serif=True)
seal(-3.64,entry_y-.016,4.63,.234)
for side,x,y in [('front',-14.4,front(-14.4)-1.30),('rear',-13.05,rear_y+.31)]:
    axisbox('sign','West-end crown enamel sign plate','signwhite',x-3.08,x+3.08,y-.054,y+.057,48.48,50.79)
    for dx in (-2.24,2.24):
        yy=front(x+dx)+.17 if side=='front' else rear_y-.045
        axisbox('sign','Crown sign supporting strut','bright',x+dx-.077,x+dx+.077,min(yy,y),max(yy,y)+.01,49.49,49.66)
    yface=y-.065 if side=='front' else y+.068
    signage('Raised roof-level letters '+side,'UTM',x+.63*(1 if side=='front' else -1),yface,49.80,1.32,'signred',side,True)
    signage('Roof-level university line '+side,'UNIVERSITI TEKNOLOGI MALAYSIA',x+.31*(1 if side=='front' else -1),yface,49.06,.23,'signred',side)
    seal(x+(-2.08 if side=='front' else 2.11),yface,49.64,.543,side=='rear')

# Only the immediate plinth and entry paving are built. Beyond that, a render ground catches light.
axisbox('site','Immediate plaza seatwall and kerb','stone',-22.5,25.8,-24.0,-23.65,-.14,.13)
axisbox('site','Curved canopy forecourt paving','brick',-21.2,23.9,-23.65,-8.91,-.18,.016,2.75)
axisbox('site','Light concrete perimeter walk on northeast','stone',-22.85,55.0,9.90,13.86,-.20,.008,2.55)
axisbox('site','Light concrete apron on southwest','stone',-23.85,63.9,-13.08,-8.91,-.19,.012,2.57)
axisbox('stage','Photography ground only','ash',-380,380,-380,380,-.35,-.23,2.55)
for x0,x1 in [(-18.0,-14.4),(19.3,22.40)]:
    axisbox('site','Seatwall stone planter','stone',x0,x1,-18.7,-17.38,-.13,.51,1.8)
    axisbox('site','Inset dark planter bed','room',x0+.12,x1-.12,-18.57,-17.48,.512,.525)
    for j in range(8):
        x=x0+.31+j*(x1-x0-.59)/7
        y=-18.06+randomizer.uniform(-.31,.31)
        angle2=randomizer.random()*6.28
        for leaf in range(9):
            a=angle2+leaf*2*math.pi/9
            length=randomizer.uniform(.37,.63)
            m=make_material('Plaza planter leaf','58795c',.61) if 'leaf' not in materials else materials['leaf']
            if 'leaf' not in materials:materials['leaf']=m
            base=(x,y,.53)
            mid=(x+math.cos(a)*length*.61,y+math.sin(a)*length*.61,.65+length*.62)
            tip=(x+math.cos(a)*length,y+math.sin(a)*length,.64+length*.56)
            for sy in [-1,1]:
                ridge=(mid[0]+math.sin(a)*.042*sy,mid[1]-math.cos(a)*.042*sy,mid[2]-.026)
                surface('site','Small forecourt planting','leaf',[base,ridge,tip,mid],1.1)

for (group,name,mat),(vertices,faces,uvs) in mesh_parts.items():
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    uv=mesh.uv_layers.new(name='Metric scaled UV')
    for face,coordinates in zip(mesh.polygons,uvs):
        for loop,coord in zip(face.loop_indices,coordinates):
            uv.data[loop].uv=coord
    obj=bpy.data.objects.new(name,mesh)
    mesh.materials.append(materials[mat])
    collections[group].objects.link(obj)

def camera(name,pos,target,lens,shift=0):
    d=bpy.data.cameras.new(name)
    d.lens=lens
    d.clip_end=950
    d.shift_y=shift
    ob=bpy.data.objects.new(name,d)
    collections['stage'].objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob

cameras=[
    camera('01_SW_Curtain_Wall',(0.0,-145.0,10.8),(17.5,0.,10.8),42,.138),
    camera('02_NE_Stone_and_Crown',(-88.,130.,14.5),(15.,0.,14.5),43,.118),
    camera('03_Entry_Canopy',(3.6,-34.55,2.20),(-1.65,-9,3.16),30,.105),
]
scene.camera=cameras[0]
background=bpy.data.worlds.new('HDR environment and neutral sky')
background.use_nodes=True
scene.world=background
world=background.node_tree
bg=world.nodes.get('Background')
source=world.nodes.new('ShaderNodeTexEnvironment')
source.image=bpy.data.images.load(str(P/'materials'/'sky_hdri.hdr'))
world.links.new(source.outputs['Color'],bg.inputs['Color'])
bg.inputs['Strength'].default_value=.75
sky=world.nodes.new('ShaderNodeTexSky')
sky.sky_type='NISHITA'
sky.sun_disc=False
sky.sun_elevation=math.radians(49)
sky.sun_rotation=math.radians(243)
sky.air_density=1.1
sky.dust_density=.6
visible=world.nodes.new('ShaderNodeBackground')
visible.inputs['Strength'].default_value=.36
world.links.new(sky.outputs['Color'],visible.inputs['Color'])
rays=world.nodes.new('ShaderNodeLightPath')
mix=world.nodes.new('ShaderNodeMixShader')
world.links.new(rays.outputs['Is Camera Ray'],mix.inputs[0])
world.links.new(bg.outputs[0],mix.inputs[1])
world.links.new(visible.outputs[0],mix.inputs[2])
world.links.new(mix.outputs[0],world.nodes.get('World Output').inputs['Surface'])

sun_d=bpy.data.lights.new('Architectural sunlight','SUN')
sun_d.energy=2.65
sun_d.angle=math.radians(2.7)
sun_d.color=(1.0,.906,.81)
sun=bpy.data.objects.new('Architectural sunlight',sun_d)
collections['stage'].objects.link(sun)
sun.rotation_euler=Vector((.33,.57,-.63)).to_track_quat('-Z','Y').to_euler()

fill_d=bpy.data.lights.new('Forecourt reflected daylight','AREA')
fill_d.energy=2500.
fill_d.shape='DISK'
fill_d.size=14.
fill_d.color=(1.0,.94,.84)
fill=bpy.data.objects.new('Forecourt reflected daylight',fill_d)
collections['stage'].objects.link(fill)
fill.location=(-5,-25,7.3)
fill.rotation_euler=(Vector((-2.,-9.,3.5))-fill.location).to_track_quat('-Z','Y').to_euler()
fill.hide_render=True

scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=80
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.028
scene.cycles.use_denoising=True
scene.cycles.denoiser='OPENIMAGEDENOISE'
scene.cycles.max_bounces=8
scene.cycles.transmission_bounces=5
scene.cycles.transparent_max_bounces=8
scene.cycles.diffuse_bounces=3
scene.cycles.glossy_bounces=4
scene.cycles.sample_clamp_indirect=8.0
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED'
scene.render.threads=4
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.compression=32
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.37
scene.render.filepath='//renders/01_SW_Curtain_Wall.png'
scene['source_footprint']='OpenStreetMap way 552610255 · ODbL 1.0'
scene['reference_elevations']='Wikimedia Commons Khairul hazim and CEphoto, Uwe Aranas. Entrance: UTM NewsHub photo sets 2022 and 2025.'
scene['vertical_reference']='approx. 54 m roof / 18 OSM levels. No survey or scan verified. Architectural detailing is reconstructed from photographs.'
scene['scope']='Only Menara Razak. Local metre axes X along the southwest elevation, Y toward northeast, Z up.'
stats={'objects_asset':0,'vertices':0,'triangles':0}
for obj in scene.objects:
    if obj.type!='MESH' or collections['stage'] in obj.users_collection:continue
    obj.data.calc_loop_triangles()
    stats['objects_asset']+=1
    stats['vertices']+=len(obj.data.vertices)
    stats['triangles']+=len(obj.data.loop_triangles)
print('MENARA_STATS',json.dumps(stats),flush=True)
(args.output/'geometry.json').write_text(json.dumps(stats,indent=2))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(args.output/('review.blend' if args.draft else 'Menara_Razak.blend')),compress=True)
