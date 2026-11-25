"""Join sedan surfaces and put separate wheel assemblies on their axles."""
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / "art/Innerscene_White_Sedan_original.glb"))
groups = defaultdict(list)
for mesh in [ob for ob in bpy.context.scene.objects if ob.type == "MESH"]:
    # glTF X points rearward, glTF Z is the axle. Blender Y is minus glTF Z.
    name = mesh.name.lower()
    original_transform = mesh.matrix_world.copy()
    mesh.parent = None
    mesh.matrix_world = original_transform
    if "rotor drill recess" in name:
        bpy.data.objects.remove(mesh, do_unlink=True)
        continue
    if name.startswith(("107 reused ", "siped tread", "brake rotor hat", "ventilated brake rotor")):
        center = sum((mesh.matrix_world @ Vector(v) for v in mesh.bound_box), Vector()) / 8.0
        group = ("Front" if center.x < 0 else "Rear") + ("Left" if center.y < 0 else "Right")
    else:
        group = "Body"
    groups[group].append(mesh)

for group, meshes in groups.items():
    bpy.ops.object.select_all(action="DESELECT")
    for mesh in meshes:
        mesh.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    mesh = bpy.context.object
    mesh.name = group
    origin = Vector((0, 0, 0))
    if group != "Body":
        origin = Vector((-1.4016 if group.startswith("Front") else 1.4016,
                         -.8225 if group.endswith("Left") else .8225, .334))
    bpy.context.scene.cursor.location = origin
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

bpy.ops.export_scene.gltf(filepath=str(ROOT / "assets/vehicles/sedan.glb"), export_format="GLB")
