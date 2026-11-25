"""Shared mesh export primitives. Building plans, elevations and envelopes live in their own scripts."""
from collections import defaultdict
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parents[1]


class BuildingMesh:
    def __init__(self, to_blender, materials):
        self.to_blender = to_blender
        self.materials = materials
        self.geometry = defaultdict(lambda: ([], []))

    def face(self, material, corners):
        points, faces = self.geometry[material]
        count = len(points)
        points.extend(self.to_blender(*corner) for corner in corners)
        faces.append(tuple(range(count, len(points))))

    def prism(self, material, clockwise_plan, low, high, caps=True):
        if caps:
            self.face(material, [(*p, high) for p in clockwise_plan])
            self.face(material, [(*p, low) for p in reversed(clockwise_plan)])
        for a, b in zip(clockwise_plan, clockwise_plan[1:] + clockwise_plan[:1]):
            self.wall(material, a, b, low, high)

    def box(self, material, u0, u1, v0, v1, low, high):
        self.prism(material, [(u0, v0), (u0, v1), (u1, v1), (u1, v0)], low, high)

    def wall(self, material, a, b, low, high):
        self.face(material, [(*a, low), (*b, low), (*b, high), (*a, high)])

    def beam(self, material, a, b, low, high, width):
        dx, dy = b[0]-a[0], b[1]-a[1]
        size = math.hypot(dx, dy)
        if size < 1e-4 or high <= low:
            return
        sx, sy = -dy/size*width/2, dx/size*width/2
        self.prism(material, [
            (a[0]+sx, a[1]+sy), (b[0]+sx, b[1]+sy),
            (b[0]-sx, b[1]-sy), (a[0]-sx, a[1]-sy),
        ], low, high)

    def column(self, material, u, v, low, high, radius, segments=12):
        ring = [(u + math.cos(-math.tau*i/segments)*radius,
                 v + math.sin(-math.tau*i/segments)*radius) for i in range(segments)]
        self.prism(material, ring, low, high)

    def roof(self, material, plan, heights):
        for triangle in tessellate_polygon([[Vector(p) for p in plan]]):
            self.face(material, [(*plan[i], heights[i]) for i in triangle])

    def finish(self):
        for name, (points, faces) in self.geometry.items():
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(points, [], faces)
            mesh.validate(verbose=False)
            mesh.update()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.triangulate(bm, faces=list(bm.faces))
            bm.to_mesh(mesh)
            bm.free()
            uv = mesh.uv_layers.new(name="Metric UV")
            for face in mesh.polygons:
                n = face.normal
                along = Vector((-n.y, n.x, 0.0)).normalized()
                for loop in face.loop_indices:
                    p = mesh.vertices[mesh.loops[loop].vertex_index].co
                    uv.data[loop].uv = (p.x / 2, p.y / 2) if abs(n.z) > .62 else (along.dot(p) / 2, p.z / 2)
            color, roughness, metallic = self.materials[name]
            material = bpy.data.materials.new(name)
            material.diffuse_color = (*color, 1.0)
            material.use_nodes = True
            bsdf = material.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Base Color"].default_value = (*color, 1)
            bsdf.inputs["Roughness"].default_value = roughness
            bsdf.inputs["Metallic"].default_value = metallic
            mesh.materials.append(material)
            node = bpy.data.objects.new(name, mesh)
            bpy.context.collection.objects.link(node)
            print("SURFACE", name, len(mesh.polygons), "triangles")


def export_building(slug, generator, collider):
    destination = ROOT / "assets/runtime/buildings" / slug
    destination.mkdir(parents=True, exist_ok=True)
    for lod in range(3):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        generator(lod).finish()
        if lod == 0:
            art = ROOT / "art" / "v2"
            art.mkdir(exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=str(art / f"{slug}.blend"), compress=True)
        bpy.ops.export_scene.gltf(filepath=str(destination / f"{slug}_lod{lod}.glb"),
                                  export_format="GLB", export_tangents=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collider().finish()
    bpy.ops.export_scene.gltf(filepath=str(destination / f"{slug}_collision.glb"),
                              export_format="GLB", export_materials="NONE")


def clockwise(plan):
    area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(plan, plan[1:]+plan[:1]))
    return plan if area < 0 else list(reversed(plan))


def line_on_edge(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    def position(t, outward=0.0):
        return (a[0] + dx*t - dy/length*outward, a[1] + dy*t + dx/length*outward)
    return position, length
