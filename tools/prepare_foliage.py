"""Reduce the scanned Poly Haven canopy for real-time use."""
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
source = ROOT / "assets/polyhaven/island_tree_02/island_tree_02.gltf"
bpy.ops.import_scene.gltf(filepath=str(source))
tree = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
bpy.context.view_layer.objects.active = tree
bpy.ops.object.select_all(action="DESELECT")
tree.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.separate(type="MATERIAL")
bpy.ops.object.mode_set(mode="OBJECT")
for part in list(bpy.context.scene.objects):
    if part.type != "MESH":
        continue
    material = part.data.materials[0]
    label = material.name
    bpy.context.view_layer.objects.active = part
    part.select_set(True)
    modifier = part.modifiers.new("Mobile mesh reduction", "DECIMATE")
    modifier.ratio = 0.022 if "leaves" in label else 0.055
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    print(label, len(part.data.polygons), "polygons")
    part.name = "Leaves" if "leaves" in label else ("Fine branches" if "branches" in label else "Main branches")
    # The scan represents leaf shapes as geometry. Alpha blending is unnecessary.
    if "leaves" in label:
        material.surface_render_method = "DITHERED"
        principal = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if principal and principal.inputs["Alpha"].is_linked:
            material.node_tree.links.remove(principal.inputs["Alpha"].links[0])
            principal.inputs["Alpha"].default_value = 1.0

output = ROOT / "assets/landscape/island_tree_realtime.glb"
output.parent.mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", export_tangents=True)
