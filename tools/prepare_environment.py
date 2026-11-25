"""Build runtime derivatives of selected HDR probes and vegetation masters."""
import json
from pathlib import Path
import shutil
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[sys.argv.index("--") + 1])
SKIES = (
    "qwantani_morning_puresky",
    "qwantani_noon_puresky",
    "kloofendal_overcast_puresky",
    "qwantani_dusk_1_puresky",
    "qwantani_night_puresky",
)
POLY_MODELS = {
    "island_tree_01": ("vegetation", .043),
    "island_tree_03": ("vegetation", .042),
    "fern_02": ("vegetation", .37),
    "periwinkle_plant": ("vegetation", .42),
    "grass_bermuda_01": ("vegetation", 1.0),
    "planter_box_02": ("props", 1.0),
    "concrete_road_barrier": ("props", 1.0),
}
INNER_MODELS = ("royal_palm","coconut_palm","travelers_palm","areca_palm")


def prepare_hdri(name):
    folder = ROOT/"assets/runtime/hdri"
    source = SOURCE/"masters/polyhaven"/name/(name+".hdr")
    image = bpy.data.images.load(str(source))
    image.scale(2048,1024)
    image.file_format = "HDR"
    image.filepath_raw = str(folder/(name+".hdr"))
    image.save()
    bpy.data.images.remove(image)


def prepare_model(name, folder, ratio):
    source = SOURCE/"masters/polyhaven"/name/(name+".gltf")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    polygons = 0
    for node in bpy.data.objects:
        if node.type != "MESH":
            continue
        if ratio < 1:
            bpy.context.view_layer.objects.active = node
            modifier = node.modifiers.new("Runtime reduction", "DECIMATE")
            modifier.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        polygons += len(node.data.polygons)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/"assets/runtime"/folder/(name+".glb")),
                              export_format="GLB",export_tangents=True)
    print(name, polygons, "polygons")


if __name__ == "__main__":
    for name in SKIES:
        prepare_hdri(name)
    for name, (folder, ratio) in POLY_MODELS.items():
        prepare_model(name,folder,ratio)
    for name in INNER_MODELS:
        source = SOURCE/"masters/innerscene"/(name+".glb")
        if source.is_file():
            shutil.copyfile(source, ROOT/"assets/runtime/vegetation"/source.name)
