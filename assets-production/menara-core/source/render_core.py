"""Cycles CPU cameras and reproducible lighting presets."""
from pathlib import Path
import math,sys,bpy
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
out=Path(args[0]);out.mkdir(parents=True,exist_ok=True)
selected={int(index) for index in args[1:]} or set(range(1,7))
scene=bpy.context.scene
sun=bpy.data.objects['Architectural sunlight']
fill=bpy.data.objects['Forecourt reflected daylight']
world=scene.world.node_tree
sky=next(n for n in world.nodes if n.type=='TEX_SKY')
background=world.nodes.get('Background')
visible=next(n for n in world.nodes if n.type=='BACKGROUND' and n!=background)
dry={}
for name in ('Road','Plaza','Walk','Platform'):
    o=bpy.data.objects.get(name)
    if o:
        m=o.data.materials[0];wet=m.copy();nd=wet.node_tree.nodes.get('Principled BSDF')
        for link in list(nd.inputs['Roughness'].links):wet.node_tree.links.remove(link)
        nd.inputs['Roughness'].default_value=.22 if name=='Road' else .29
        nd.inputs['Coat Weight'].default_value=.62
        nd.inputs['Coat Roughness'].default_value=.10
        dry[o]=(m,wet)
presets=[
 ((.24,.55,-.69),2.7,(1,.94,.85),.51,50,.64,.43,46),
 ((.38,.57,-.68),2.75,(1,.94,.86),.48,48,.63,.37,42),
 ((.43,.45,-.70),2.2,(1,.94,.84),.58,47,.69,.40,44),
 ((.28,.56,-.68),2.85,(1,.94,.86),.52,51,.65,.38,40),
 ((.43,.78,-.16),1.72,(1,.52,.28),.47,5,.29,.57,46),
 ((.31,.49,-.53),.65,(.83,.91,1),.74,30,.65,.48,52)
]
for ix,(vector,energy,color,exposure,elevation,env,cam_brightness,samples) in enumerate(presets,1):
    if ix not in selected:
        continue
    camera=next(o for o in bpy.data.collections['Core · Lighting and cameras'].objects if o.type=='CAMERA' and o.name.startswith(f'{ix:02d}_'))
    scene.camera=camera;scene.cycles.samples=samples
    fill.hide_render=ix not in (3,6)
    sun.rotation_euler=Vector(vector).to_track_quat('-Z','Y').to_euler()
    sun.data.energy=energy;sun.data.color=color
    scene.view_settings.exposure=exposure
    sky.sun_elevation=math.radians(elevation);sky.dust_density=2.1 if ix==5 else .59
    background.inputs['Strength'].default_value=env
    visible.inputs['Strength'].default_value=cam_brightness
    for lamp in bpy.data.collections['Core · Lighting and cameras'].objects:
        if lamp.type=='LIGHT':lamp.hide_render=ix!=5
    for o in bpy.data.collections['Core · Weather only'].objects:o.hide_render=ix!=6
    for o,(base,wet) in dry.items():o.data.materials[0]=wet if ix==6 else base
    scene.render.filepath=str(out/(camera.name+'.png'))
    print('RENDER',camera.name,'1920×1080 Cycles CPU max',samples,flush=True)
    bpy.ops.render.render(write_still=True)
