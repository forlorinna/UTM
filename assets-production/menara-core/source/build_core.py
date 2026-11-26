"""Attach the clipped Menara site to the authored tower and export shared site meshes."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector

repo,work=map(Path,sys.argv[-2:])
out=work/'public'/'assets'
j=json.loads((out/'site.json').read_text())
scene=bpy.context.scene
for o in list(bpy.data.objects):
    if o.name.startswith('Photography ground only') or any(c.name.startswith('08 Immediate') for c in o.users_collection):
        bpy.data.objects.remove(o,do_unlink=True)
cols={}
for name in ['Shared ground','Lighting and cameras','Vegetation','Weather only']:
    col=bpy.data.collections.new('Core · '+name)
    scene.collection.children.link(col)
    cols[name]=col

g=j['grid']; gx,gy,d,nx,ny=g['x'],g['y'],g['spacing'],g['nx'],g['ny']; hs=g['height']
def h(x,y):
    px=min(nx-1.001,max(0,(x-gx)/d)); py=min(ny-1.001,max(0,(y-gy)/d))
    i,k=int(px),int(py)
    u,v=px-i,py-k
    a,b,c,e=hs[k*nx+i],hs[k*nx+i+1],hs[(k+1)*nx+i],hs[(k+1)*nx+i+1]
    return a+(b-a)*u+(c-a)*v if u+v<=1 else e+(c-e)*(1-u)+(b-e)*(1-v)
def look(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def mat(name,color,rough,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=metal
    return m
def scan(label,prefix,tint,rough,strength):
    m=mat(label,tint,rough);nodes=m.node_tree.nodes;links=m.node_tree.links; bsdf=nodes.get('Principled BSDF')
    for channel in ['diff','nor_gl','rough']:
        src=work/'source-assets'/'grass-runtime'/f'{channel}.jpg' if prefix=='leafy' else repo/'android-real-world'/'game'/'public'/'textures'/f'{prefix}_{channel}.jpg'
        image=bpy.data.images.load(str(src),check_existing=True)
        tex=nodes.new('ShaderNodeTexImage');tex.image=image
        if channel=='diff':links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        elif channel=='nor_gl':
            image.colorspace_settings.name='Non-Color'
            n=nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=strength
            links.new(tex.outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],bsdf.inputs['Normal'])
        else:
            image.colorspace_settings.name='Non-Color';links.new(tex.outputs['Color'],bsdf.inputs['Roughness'])
    return m
grass=scan('Grass · Poly Haven leafy grass','leafy',(.25,.34,.2),.88,.32)
asphalt=scan('Asphalt · Poly Haven asphalt track','road',(.13,.15,.15),.82,.43)
paver=bpy.data.materials['Red-brown plaza pavers']
sand=bpy.data.materials['Bush-hammered plaza and stair concrete']
white=mat('Faded service road paint',(.64,.64,.52),.73)
metal=mat('Dark grey facility metal',(.12,.143,.126),.44,.55)
seat=mat('Oiled meranti bench slats',(.25,.113,.058),.62)
lamp_emission=mat('Diffuser lens',(.75,.72,.6),.27)
lamp_emission.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(1,.68,.33,1)
lamp_emission.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=1.8
def mesh(name,verts,faces,material,scale,col='Shared ground'):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    uv=data.uv_layers.new(name='Metres')
    for face in data.polygons:
        for li in face.loop_indices:
            x,y,z=verts[data.loops[li].vertex_index];uv.data[li].uv=(x/scale,y/scale)
    obj=bpy.data.objects.new(name,data);cols[col].objects.link(obj);data.materials.append(material)
    return obj
vs=[(gx+i*d,gy+k*d,hs[k*nx+i]) for k in range(ny) for i in range(nx)]
fs=[]
for y in range(ny-1):
    for x in range(nx-1):
        n=y*nx+x;fs.extend(((n,n+1,n+nx),(n+1,n+1+nx,n+nx)))
terrain=mesh('Terrain',vs,fs,grass,5.2)
def patch(kind,label,mat,scale,off):
    vs=[];fs=[]
    for t in j['triangles'][kind]:
        if (t[1][0]-t[0][0])*(t[2][1]-t[0][1])-(t[1][1]-t[0][1])*(t[2][0]-t[0][0])<0:t=list(reversed(t))
        n=len(vs);vs.extend((x,y,h(x,y)+off) for x,y in t);fs.append((n,n+1,n+2))
    if vs:return mesh(label,vs,fs,mat,scale)
road=patch('road','Road',asphalt,6.3,.030)
plaza=patch('plaza','Plaza',paver,2.75,.069)
walk=patch('walk','Walk',sand,2.8,.099)
curb=patch('curb','Curb',sand,1.8,.162)
platform=patch('platform','Platform',sand,2.75,.105)
island=patch('roundabout','Roundabout',grass,4,.085)

def solid_edge(obj,depth):
    mod=obj.modifiers.new('Vertical kerb edge','SOLIDIFY');mod.thickness=depth
if curb:solid_edge(curb,.139)
if platform:solid_edge(platform,.099)

def quad(cx,cy,rx,ry,yaw):
    co=math.cos(yaw);si=math.sin(yaw)
    return [(cx+x*co-y*si,cy+x*si+y*co) for x,y in [(-rx,-ry),(rx,-ry),(rx,ry),(-rx,ry)]]
def stencil(name,quads,material,offset,tile=1):
    vs=[];faces=[]
    for poly in quads:
        n=len(vs)
        vs.extend([(x,y,h(x,y)+offset) for x,y in poly])
        faces.append(tuple(range(n,len(vs))))
    return mesh(name,vs,faces,material,tile)
stencil('Entry crossing markings · inferred', [quad(-23.7+i*.71,-20.15,.20,1.72,-.02) for i in range(6)],white,.042)
def link_obj(obj,col):
    for src in list(obj.users_collection):src.objects.unlink(obj)
    cols[col].objects.link(obj)
def cube(name,location,size,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location); o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(material)
    link_obj(o,'Shared ground')
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=o.modifiers.new('Rounded edges','BEVEL');bevel.width=.016;bevel.segments=2
    return o

for bx,by in [(-13,-15.8),(-18,-15.6)]:
    bz=h(bx,by)+.07
    for xx in [bx-.69,bx+.69]:
        for yy in [by-.19,by+.19]:cube('Bench leg',(xx,yy,bz+.21),(.067,.065,.42),metal)
    for k in range(5):cube('Bench slat',(bx,by-.208+k*.103,bz+.44),(1.66,.088,.057),seat)
    for k in range(3):cube('Bench back',(bx,by+.230,bz+.58+k*.097),(1.66,.062,.090),seat)

def load_proto(path,col):
    old=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    added=[o for o in bpy.data.objects if o not in old]
    bpy.context.view_layer.update()
    meshes=[(o.data,o.matrix_world.copy()) for o in added if o.type=='MESH']
    corners=[o.matrix_world@Vector(c) for o in added if o.type=='MESH' for c in o.bound_box]
    lo=Vector([min(q[i] for q in corners) for i in range(3)]); hi=Vector([max(q[i] for q in corners) for i in range(3)])
    for o in added:bpy.data.objects.remove(o,do_unlink=True)
    return meshes,lo,hi
from mathutils import Matrix
def instance(proto,name,x,y,size,yaw,col):
    meshes,lo,hi=proto
    factor=size/(hi.z-lo.z)
    pt=(x,y,h(x,y)+.02)
    center=Vector(((hi.x+lo.x)/2,(hi.y+lo.y)/2,lo.z))
    transform=Matrix.Translation(pt)@Matrix.Rotation(yaw,4,'Z')@Matrix.Scale(factor,4)@Matrix.Translation(-center)
    for data,world in meshes:
        obj=bpy.data.objects.new(name,data);cols[col].objects.link(obj);obj.matrix_world=transform@world
    return pt
tree_file=repo/'assets/landscape/island_tree_realtime.glb'
lamp_file=repo/'assets/polyhaven/street_lamp_01/street_lamp_01.gltf'
tree=load_proto(tree_file,'Vegetation'); lamp=load_proto(lamp_file,'Shared ground')
for i,(x,y,size) in enumerate(j['trees']):instance(tree,'Tree %02d'%i,x,y,size,(i*2.399)%6.283,'Vegetation')
for i,(x,y) in enumerate(j['lamps']):
    p=instance(lamp,'Street fixture %02d'%i,x,y,5.7,.4+i*.94,'Shared ground')
    data=bpy.data.lights.new('Warm luminaire %02d'%i,'POINT');data.energy=96;data.color=(1,.69,.39);data.shadow_soft_size=.36
    o=bpy.data.objects.new(data.name,data);cols['Lighting and cameras'].objects.link(o);o.location=(x+.24,y,p[2]+5.38);o.hide_render=True
# Wet weather film and discrete puddles are enabled only by the rain render.
water=mat('Rainwater over dark damp asphalt',(.037,.041,.037),.065,.08)
n=water.node_tree.nodes.get('Principled BSDF')
n.inputs['Coat Weight'].default_value=.85;n.inputs['Coat Roughness'].default_value=.042
def pool(x,y,rx,ry,offset):
    vs=[(x,y,h(x,y)+offset)];faces=[]
    for i in range(44):
        a=i*math.tau/44;wave=1+.12*math.sin(a*5+.6)+.044*math.cos(11*a)
        px=x+math.cos(a)*rx*wave;py=y+math.sin(a)*ry*wave;vs.append((px,py,h(px,py)+offset))
    for i in range(44):faces.append((0,i+1,(i+1)%44+1))
    o=mesh('Rain film puddle',vs,faces,water,1,'Weather only');o.hide_render=True
for x,y,rx,ry,z in [(5.6,-30.15,4.2,.72,.051),(10.8,-34.35,2.7,1.01,.059),(-3.8,-30.42,4.1,.76,.055),(-6.6,-16.8,1.5,.50,.090),(-12.4,-21.1,2.1,.52,.069)]:pool(x,y,rx,ry,z)

def cam(name,pos,target,lens,shift=0):
    d=bpy.data.cameras.new(name);d.lens=lens;d.shift_y=shift
    o=bpy.data.objects.new(name,d);o.location=pos;cols['Lighting and cameras'].objects.link(o);look(o,target)
    return o
cameras=[
 cam('01_Daylight_Front',(17,-124,8.5),(18,0,9),35.5,.144),
 cam('02_Daylight_Oblique',(-76,-76,9),(9,-1,19),27.5,.104),
 cam('03_Entrance',(3.55,-35.4,2.05),(-1.3,-9,3.35),31,.106),
 cam('04_Crown_Detail',(-51,-67,45),(-5,0,47.1),68),
 cam('05_Dusk',(-18,-96,4.8),(17,-1,15),28,.10),
 cam('06_After_Rain',(5.8,-42,1.35),(6.5,-9,5.12),22,-.013),
]
scene.camera=cameras[0];scene.render.resolution_x=1920;scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.cycles.samples=40;scene.cycles.adaptive_threshold=.055;scene.cycles.use_denoising=True
scene.cycles.max_bounces=7;scene.cycles.transmission_bounces=4
scene['scope']='Menara Razak and immediate 127 × 83 m site. Adjacent buildings excluded.'
bounds=tree[1:];j['treeBounds']=[list(v) for v in bounds]
j['lampHeight']=5.7
(out/'site.json').write_text(json.dumps(j,separators=(',',':')))
# Only the shared ground and fixtures are exported. The walk scene uses the same tower and tree sources.
for o in bpy.context.selected_objects:o.select_set(False)
for o in cols['Shared ground'].objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'Core_Site.glb'),use_selection=True,export_apply=True,export_format='GLB',export_yup=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(work/'Menara_Core.blend'),compress=True)
