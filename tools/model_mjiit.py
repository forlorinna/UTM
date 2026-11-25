"""Build the MJIIT complex exterior from its mapped footprint and west elevation photo."""
import json
import math
from pathlib import Path

import bpy

from model_menara import Geometry, reset

ROOT = Path(__file__).resolve().parents[1]
CENTER_X, CENTER_Z = 125, 45
STYLES = {
    "WarmBase": ((0.69, 0.48, 0.22), .69, 0),
    "PaintCream": ((.77, .79, .73), .68, 0),
    "PaintBlue": ((.34, .50, .63), .64, 0),
    "DarkBlue": ((.16, .31, .47), .69, 0),
    "Mullion": ((.70, .75, .74), .40, .35),
    "Recess": ((.044, .058, .066), .71, .12),
    "GlassGreen": ((.035, .180, .190), .24, .38),
    "GlassDusk": ((.066, .199, .267), .26, .31),
    "Sunshade": ((.67, .73, .73), .47, .30),
    "RedAccent": ((.38, .096, .14), .59, .1),
    "Roof": ((.32, .37, .39), .61, .24),
}


def from_local(u, v, y):
    return (CENTER_X - v, -CENTER_Z - u, y)


def draw_facade(g, ring, lod):
    for side, (a, b) in enumerate(zip(ring, ring[1:] + ring[:1])):
        length = math.dist(a, b)
        dx,dv = b[0]-a[0], b[1]-a[1]
        # The plan transform mirrors the second axis.
        def place(t, outer=0):
            return (a[0] + dx*t - dv/length*outer, a[1] + dv*t + dx/length*outer)
        west = dx > 0.12
        core = 3.4 + (1.5 if side in [12,14,25] else 0)
        for floor in range(9):
            y0 = .28 + floor * 3.48
            y1 = y0 + 3.48
            trim = "WarmBase" if floor < 3 else ("DarkBlue" if floor == 3 else
                      ("PaintBlue" if side % 4 in (0,1) else "PaintCream"))
            g.face(trim, [(*a,y0),(*b,y0),(*b,y1),(*a,y1)])
            if west or length > 8:
                count = max(1, int(length / ([3.00, 5.5, 9.5][lod])))
                for bay in range(count):
                    center = (bay + .5) / count
                    width = min(.76 / count, 2.21 / length)
                    p, q = place(center-width/2, .105), place(center+width/2, .105)
                    g.beam("Recess", p,q,y0+.58,y0+2.62,.095)
                    p, q = place(center-width/2+.045/length, .172), place(center+width/2-.045/length,.172)
                    g.face("GlassGreen" if floor < 4 else "GlassDusk",
                           [(*p,y0+.65),(*q,y0+.65),(*q,y0+2.54),(*p,y0+2.54)])
                    if lod == 0:
                        for j in (0,1,2,3):
                            u = center - width/2 + j * width/3
                            g.beam("Mullion",place(u,.178),place(u+.045/length,.178),y0+.59,y0+2.60,.07)
                        for height in (.62,1.23,2.59):
                            g.beam("Mullion",p,q,y0+height,y0+height+.05,.069)
                g.beam("Sunshade",place(0,.19),place(1,.19),y1-.39,y1-.22,.45 if west else .27)
        g.beam("Roof", place(0,.43), place(1,.43), 31.56, 31.93, 1.05)
        if west and length > 10:
            g.beam("RedAccent",place(.01,.25),place(.03,.25),10.7,31.65,.33)
        if length > core:
            g.beam("PaintCream",place(.00,.17),place(min(.06,.8/length),.17),.26,31.63,.40)

    # Roofing remains inside the mapped complex outline.
    g.face("Roof", [(u,v,31.6) for u,v in ring])


def entrance(g, lod):
    # Two flanking service spines, central bracing and tiered public canopy.
    for u in (-13.4, 15.0):
        g.box("PaintCream",u,10.7,7.8,5.4,4.25,25.1)
        g.box("Roof",u,10.7,32.9,6.75,5.9,.49)
        for k in range(5):
            g.box("Sunshade",u,13.05,14.6+k*3.6,5.7,.58,.19)
    glass_u = 1.0
    g.box("DarkBlue", glass_u, 8.8, 14.2,19.5,2.0,17.9)
    for floor in range(4):
        y = 16.9+floor*3.4
        for u in (-8.1,-5.6,-3.15,-.7,1.75,4.2,6.65,9.1):
            g.box("GlassDusk",u,9.86,y,1.66,.15,1.58)
        for u in (-2.7,4.75):
            g.box("PaintCream",u,10.0,y-.6,.23,.36,3.4)
        if lod == 0:
            for u0,u1 in ((-2.7,4.75),(4.75,-2.7)):
                g.face("Mullion",[(u0,10.23,y-.56),(u1,10.23,y+2.80),
                                  (u1,10.23,y+3.08),(u0,10.23,y-.28)])
    g.box("Roof",.9,8.8,32.7,8.8,7.3,.53)
    for u in (-14.5,-8.4,-2.3,4.2,10.8,17.1):
        g.box("WarmBase", u, 13.0, .0, .48,.46,14.85)
    stages = [(.36,7.7,3.85,"GlassGreen"), (7.2,5.8,.35,"Sunshade"), (10.8,6.5,.44,"RedAccent"),
              (14.55,7.7,.45,"Sunshade")]
    count = 14 if lod == 0 else 8
    for y, depth, thick, style in stages:
        for i in range(count):
            u0,u1 = -18 + 37*i/count, -18 + 37*(i+1)/count
            v0, v1 = 9.5 + depth - .009*u0*u0, 9.5 + depth - .009*u1*u1
            if style == "GlassGreen":
                g.face(style,[(u0,9.5,3.96),(u0,v0,3.66),(u1,v1,3.66),(u1,9.5,3.96)])
                g.beam("Sunshade",(u0,9.5),(u0,v0),3.58,3.65,.14)
            else:
                g.prism(style,[(u0,9.5),(u0,v0),(u1,v1),(u1,9.5)],y,y+thick)
    for u in range(-16, 18, 2):
        g.box("GlassGreen",u,10.0,.12,1.68,.14,3.16)
        if lod == 0:
            g.box("Mullion",u+.86,10.12,.12,.051,.18,3.16)
    g.box("WarmBase",.3,11.5,-.50,35,7.8,.66)


def main():
    data = json.loads((ROOT / "data/map.json").read_text())
    building = next(b for b in data["buildings"] if b["id"] == "osm-way-733313948")
    ring = [(z-CENTER_Z,CENTER_X-x) for x,z in building["footprint"]]
    signed_area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))
    if signed_area > 0:
        ring.reverse()
    for lod in range(3):
        reset()
        g = Geometry(from_local, STYLES)
        g.prism("WarmBase", ring,-4.1,.25)
        draw_facade(g,ring,lod)
        entrance(g,lod)
        g.to_meshes()
        if lod == 0:
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"art/MJIIT.blend"),compress=True)
        bpy.ops.export_scene.gltf(filepath=str(ROOT/f"assets/architecture/mjiit_lod{lod}.glb"),
                                  export_format="GLB",export_draco_mesh_compression_enable=False)
    reset()
    g = Geometry(from_local, STYLES)
    g.prism("WarmBase",ring,-4.3,31.4)
    g.to_meshes()
    bpy.ops.export_scene.gltf(filepath=str(ROOT/"assets/architecture/mjiit_collision.glb"),
                              export_format="GLB",export_materials="NONE",export_draco_mesh_compression_enable=False)


if __name__ == "__main__":
    main()
