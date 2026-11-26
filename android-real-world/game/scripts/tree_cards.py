import bpy, math, sys
from mathutils import Vector
from pathlib import Path
input_dir=Path(sys.argv[-2])
out_dir=Path(sys.argv[-1])
out_dir.mkdir(exist_ok=True,parents=True)
for index,model in enumerate(('tree_small_02','island_tree_02')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(input_dir/model/(model+'.gltf')))
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=12
    scene.cycles.use_denoising=False
    scene.render.film_transparent=True
    scene.render.resolution_x=448
    scene.render.resolution_y=512
    scene.render.resolution_percentage=100
    scene.render.image_settings.color_mode='RGBA'
    scene.render.image_settings.compression=35
    scene.render.threads_mode='FIXED'
    scene.render.threads=4
    scene.view_settings.view_transform='Standard'
    scene.world=bpy.data.worlds.new('Ambient')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.58,.67,.72,1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.72
    light=bpy.data.lights.new('Sun','SUN')
    light.energy=1.4
    sun=bpy.data.objects.new('Sun',light)
    scene.collection.objects.link(sun)
    sun.rotation_euler=(.48,-.30,-.47)
    corners=[obj.matrix_world @ Vector(corner) for obj in scene.objects if obj.type=='MESH' for corner in obj.bound_box]
    high=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    low=Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    size=high-low
    mid=(high+low)*.5
    cam=bpy.data.cameras.new('Sprite camera')
    cam.type='ORTHO'
    cam.ortho_scale=max(size.x,size.y,size.z*.875)*1.18
    obj=bpy.data.objects.new('Sprite camera',cam)
    scene.collection.objects.link(obj)
    scene.camera=obj
    for n,angle in enumerate((.4,1.36,2.55)):
        obj.location=mid+Vector((math.cos(angle),math.sin(angle),.035))*28
        obj.rotation_euler=(mid-obj.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out_dir/f'tree{index}-{n}.png')
        bpy.ops.render.render(write_still=True)
    print(model, 'size', tuple(size))
