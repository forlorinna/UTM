import bpy, math, sys
from mathutils import Vector
from pathlib import Path

model, sky, output = [Path(p) for p in sys.argv[-4:-1]]
samples=int(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(model))
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=samples
scene.cycles.use_denoising=False
scene.cycles.adaptive_threshold=.055
scene.cycles.max_bounces=6
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED'
scene.render.threads=4
scene.render.image_settings.file_format='JPEG'
scene.render.image_settings.quality=94
scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Daylight')
scene.world.use_nodes=True
nodes=scene.world.node_tree.nodes
connections=scene.world.node_tree.links
env=nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(sky))
bg=nodes.get('Background')
bg.inputs['Strength'].default_value=.62
connections.new(env.outputs['Color'],bg.inputs['Color'])
sun=bpy.data.lights.new('November sun','SUN')
sun.energy=1.65
sun.angle=math.radians(4)
key=bpy.data.objects.new('November sun',sun)
scene.collection.objects.link(key)
key.rotation_euler=Vector((.72,.41,-.62)).normalized().to_track_quat('-Z','Y').to_euler()
camera=bpy.data.cameras.new('Campus overlook')
camera.lens=30
camera.clip_end=4500
eye=bpy.data.objects.new('Campus overlook',camera)
scene.collection.objects.link(eye)
eye.location=(-158,-82,76)
look=Vector((-306,111,19))
eye.rotation_euler=(look-eye.location).to_track_quat('-Z','Y').to_euler()
scene.camera=eye
scene.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
