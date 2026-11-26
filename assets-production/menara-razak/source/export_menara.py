"""Export a triangulated copy without changing the authored Blender mesh."""
import json
import sys
from pathlib import Path
import bpy

out=Path(sys.argv[-1])
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
factors={}
for obj in scene.objects:
    exported=obj.type=='MESH' and not any(c.name.startswith('90 ') for c in obj.users_collection)
    obj.select_set(exported)
    if not exported:
        continue
    for material in obj.data.materials:
        mix=next((n for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeMixRGB' and n.blend_type=='MULTIPLY'),None)
        if mix is not None:
            factors[material.name]=list(mix.inputs[2].default_value)
    if any(len(p.vertices)>4 for p in obj.data.polygons):
        triangulation=obj.modifiers.new('glTF export n-gon triangulation','TRIANGULATE')
        triangulation.min_vertices=5

(out/'material_factors.json').write_text(json.dumps(factors,indent=2))
bpy.ops.export_scene.gltf(
    filepath=str(out/'menara-export.glb'),export_format='GLB',use_selection=True,
    export_yup=True,export_materials='EXPORT',export_image_format='AUTO',
    export_tangents=True,export_apply=True,
)
