"""Render the saved Menara Razak cameras through Cycles CPU."""
import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

parser=argparse.ArgumentParser()
parser.add_argument('--draft',action='store_true')
parser.add_argument('--camera',type=int,nargs='+',default=[1,2,3])
parser.add_argument('--output',type=Path,default=Path(bpy.path.abspath('//renders')))
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
args.output.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
assert scene.render.engine=='CYCLES'
scene.render.resolution_percentage=46 if args.draft else 100
scene.cycles.samples=18 if args.draft else scene.cycles.samples
sun=bpy.data.objects['Architectural sunlight']
fill=bpy.data.objects['Forecourt reflected daylight']
presets={
    1:((.24,.55,-.69),2.65,(1.0,.923,.86),.41),
    2:((.36,-.64,-.75),2.22,(1.0,.94,.88),.43),
    3:((.46,.48,-.72),2.55,(1.0,.907,.82),.36),
}
for index in args.camera:
    camera=next(obj for obj in scene.objects if obj.type=='CAMERA' and obj.name.startswith(f'{index:02d}_'))
    scene.camera=camera
    fill.hide_render=index!=3
    direction,energy,color,exposure=presets[index]
    sun.rotation_euler=Vector(direction).to_track_quat('-Z','Y').to_euler()
    sun.data.energy=energy
    sun.data.color=color
    scene.view_settings.exposure=exposure
    scene.render.filepath=str(args.output/(camera.name+'.png'))
    print(f'RENDER {camera.name} {scene.render.resolution_x}x{scene.render.resolution_y} @ {scene.render.resolution_percentage}% | Cycles {scene.cycles.device}',flush=True)
    bpy.ops.render.render(write_still=True)
