"""Menara Razak from mapped plan and public south-view photos. Run with Blender 4.3."""
import json
import math
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets/architecture"
STYLE = {
    "Concrete": ((0.57, 0.62, 0.62), 0.77, 0.0),
    "WhiteSpandrel": ((0.78, 0.82, 0.82), 0.42, 0.18),
    "Aluminum": ((0.42, 0.52, 0.56), 0.34, 0.63),
    "ShadeFins": ((0.69, 0.73, 0.74), 0.46, 0.48),
    "Glass_0": ((0.072, 0.240, 0.340), 0.25, 0.32),
    "Glass_1": ((0.074, 0.200, 0.296), 0.20, 0.38),
    "Glass_2": ((0.096, 0.242, 0.334), 0.27, 0.30),
    "Glass_3": ((0.054, 0.161, 0.214), 0.31, 0.28),
    "GlassNight": ((0.16, 0.26, 0.32), 0.24, 0.20),
    "Reveal": ((0.045, 0.059, 0.064), 0.52, 0.30),
    "RoofCladding": ((0.48, 0.56, 0.59), 0.42, 0.48),
    "Burgundy": ((0.28, 0.045, 0.044), 0.49, 0.15),
    "Soffit": ((0.26, 0.29, 0.30), 0.67, 0.25),
}
ANGLE = 0.656
COS, SIN = math.cos(ANGLE), math.sin(ANGLE)
TOP = 54.0


def to_plan(x, z):
    return (COS*x + SIN*z, -SIN*x + COS*z)


def coordinate(u, v, h):
    return (COS*u - SIN*v, -SIN*u - COS*v, h)


def roof_height(u):
    return TOP - 0.00105 * (u - 9.0)**2


class Geometry:
    def __init__(self, transform=coordinate, style=STYLE):
        self.parts = {}
        self.transform = transform
        self.style = style

    def face(self, material, points):
        verts, polys = self.parts.setdefault(material, ([], []))
        polys.append(tuple(range(len(verts), len(verts) + len(points))))
        verts.extend(self.transform(*point) for point in points)

    def beam(self, material, a, b, z0, z1, thickness):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 0.01 or z1 <= z0:
            return
        ux, uy = -dy / length * thickness / 2, dx / length * thickness / 2
        ring = [(a[0]+ux, a[1]+uy), (b[0]+ux, b[1]+uy),
                (b[0]-ux, b[1]-uy), (a[0]-ux, a[1]-uy)]
        self.prism(material, ring, z0, z1)

    def prism(self, material, outline, bottom, top, caps=True):
        if caps:
            self.face(material, [(u, v, top) for u, v in outline])
            self.face(material, [(u, v, bottom) for u, v in reversed(outline)])
        for a, b in zip(outline, outline[1:] + outline[:1]):
            self.face(material, [(*a, bottom), (*b, bottom), (*b, top), (*a, top)])

    def box(self, material, u, v, z0, length, depth, height):
        ring = [(u-length/2,v-depth/2),(u-length/2,v+depth/2),
                (u+length/2,v+depth/2),(u+length/2,v-depth/2)]
        self.prism(material, ring, z0, z0+height)

    def to_meshes(self):
        for key, (verts, faces) in self.parts.items():
            mesh = bpy.data.meshes.new(key)
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            uv = mesh.uv_layers.new(name="MeasuredSurface")
            for face in mesh.polygons:
                x, y, z = face.normal
                for loop_i in face.loop_indices:
                    p = mesh.vertices[mesh.loops[loop_i].vertex_index].co
                    if abs(z) > 0.7:
                        pair = (p.x, p.y)
                    elif abs(x) > abs(y):
                        pair = (p.y, p.z)
                    else:
                        pair = (p.x, p.z)
                    uv.data[loop_i].uv = tuple(axis / 2 for axis in pair)
            obj = bpy.data.objects.new(key, mesh)
            bpy.context.collection.objects.link(obj)
            mat = bpy.data.materials.new(key)
            color, rough, metal = self.style[key]
            mat.diffuse_color = (*color, 1)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Base Color"].default_value = (*color, 1)
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metal
            mesh.materials.append(mat)


def clip_u(poly, value, minimum):
    result = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        inside = a[0] >= value if minimum else a[0] <= value
        next_inside = b[0] >= value if minimum else b[0] <= value
        if inside:
            result.append(a)
        if inside != next_inside:
            v = a[1] + (b[1]-a[1]) * (value - a[0]) / (b[0]-a[0])
            result.append((value, v))
    return result


def canopy_roof(g, plan, lod):
    lo, hi = min(p[0] for p in plan), max(p[0] for p in plan)
    count = (46, 24, 12)[lod]
    for idx in range(count):
        u0, u1 = lo + (hi-lo)*idx/count, lo + (hi-lo)*(idx+1)/count
        piece = clip_u(clip_u(plan, u0, True), u1, False)
        if len(piece) < 3:
            continue
        for indices in tessellate_polygon([[Vector(point) for point in piece]]):
            tri = [piece[index] for index in indices]
            g.face("RoofCladding", [(u,v,roof_height(u)) for u,v in tri])
            g.face("Soffit", [(u,v,roof_height(u)-0.62) for u,v in reversed(tri)])
    for a, b in zip(plan, plan[1:] + plan[:1]):
        steps = max(1, int(math.dist(a, b)/(2.1 if lod == 0 else 5.0)))
        for i in range(steps):
            p, q = [tuple(j+(k-j)*f/steps for j,k in zip(a,b)) for f in (i,i+1)]
            g.face("RoofCladding", [(*p, roof_height(p[0])-.63), (*q, roof_height(q[0])-.63),
                                    (*q, roof_height(q[0])), (*p, roof_height(p[0]))])
            if lod == 0:
                g.beam("Aluminum", p, (p[0]+.035,p[1]+.035),
                       roof_height(p[0])-.63, roof_height(p[0])-.03, .06)


def make_tower(plan, lod):
    g = Geometry()
    rng = Random(5428)
    # Foundation clears the low-resolution elevation raster at the tower perimeter.
    g.prism("Concrete", plan, -5.7, 0.45)
    for ei, (a, b) in enumerate(zip(plan, plan[1:] + plan[:1])):
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy/length, dx/length
        bays = max(1, round(length / (1.55 if lod == 0 else 3.15 if lod == 1 else 7.0)))
        front = ny > 0.19

        def ab(t, offset=0):
            return a[0]+dx*t+nx*offset, a[1]+dy*t+ny*offset

        for floor in range(18):
            low = 0.47 + floor*2.74
            tall_band = front and (ei in (8,9,10,11) or (a[0] < 8 and floor % 3 == 2))
            band = .76 if tall_band else .32
            if floor == 0:
                band = .44
            for bay in range(bays):
                s, t = bay/bays, (bay+1)/bays
                p, q = ab(s), ab(t)
                glass = "GlassNight" if rng.random() < 0.12 else f"Glass_{rng.randrange(4)}"
                g.face(glass, [(*p,low),(*q,low),(*q,low+2.74),(*p,low+2.74)])
                if lod != 2:
                    g.beam("Aluminum", ab(s, .07), ab(s+.044/length, .07), low, low+2.74, .10)
                    if lod == 0:
                        g.beam("Aluminum", ab(s,.055), ab(t,.055), low+1.05, low+1.09, .061)
            g.beam("WhiteSpandrel", ab(0, .095), ab(1, .095), low+2.74-band, low+2.74, .16)
            if lod == 0 and front and not tall_band:
                g.beam("ShadeFins", ab(0, .26), ab(1, .26), low+2.26, low+2.34, .35)
        p,q = ab(0),ab(1)
        detail = "Burgundy" if front and (a[0]+b[0])/2 < 0 else "Reveal"
        g.face(detail, [(*p,49.79),(*q,49.79),(*q,roof_height(q[0])-.56),(*p,roof_height(p[0])-.56)])
        if lod < 2:
            g.beam("WhiteSpandrel", ab(0,.12), ab(.36/length,.12),0.45,49.80,.34)
        if lod == 0 and length > 6.0:
            g.beam("Concrete", ab(.25,.22), ab(.25+.32/length,.22),0.45,4.0,.45)
            g.beam("Concrete", ab(.76,.22), ab(.76+.32/length,.22),0.45,4.0,.45)

    center = (16, 0)
    expanded = [(u + (u-center[0])*.031, v + (v-center[1])*.12) for u,v in plan]
    canopy_roof(g, expanded, lod)
    # Separate southwest entrance canopy, glazing reveals and forecourt steps.
    g.box("Concrete", 8.3, 9.5, -.34, 14.2, 5.8, .65)
    g.box("Concrete", 8.3, 12.9, -.53, 14.2, 1.0, .60)
    g.box("RoofCladding", 8.3, 9.9, 3.81, 14.4, 5.9, .27)
    g.box("Soffit", 8.3, 9.9, 3.73, 14.1, 5.6, .08)
    for u in (2.3,6.3,10.3,14.3):
        g.box("WhiteSpandrel", u, 12.02, .31, .29, .40, 3.42)
    if lod == 0:
        for u in range(2,15):
            g.box("ShadeFins", u, 9.9, 3.70, .045, 5.5, .075)
        g.box("Burgundy", 8.3, 12.77, 3.48, 6.6, .07, .44)
    return g


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    geo = json.loads((ROOT / "data/map.json").read_text())
    plan = [to_plan(x,z) for x,z in geo["buildings"][0]["footprint"]]
    # Positive area in Blender XY means counterclockwise with outward-facing walls.
    winding = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(plan,plan[1:]+plan[:1]))
    if winding > 0:
        plan.reverse()
    DEST.mkdir(parents=True, exist_ok=True)
    for lod in range(3):
        reset()
        make_tower(plan, lod).to_meshes()
        if lod == 0:
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "art/Menara_Razak.blend"), compress=True)
        bpy.ops.export_scene.gltf(filepath=str(DEST / f"menara_razak_lod{lod}.glb"),
                                  export_format="GLB", export_cameras=False,
                                  export_lights=False, export_tangents=True)
    reset()
    collision = Geometry()
    collision.prism("Concrete", plan, -6, 49.5)
    collision.to_meshes()
    bpy.ops.export_scene.gltf(filepath=str(DEST / "menara_razak_collision.glb"),
                              export_format="GLB", export_materials="NONE")


if __name__ == "__main__":
    main()
