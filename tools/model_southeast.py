"""Independent models for the Residensi complex and Masjid UTMKL public exterior."""
import json
import math
from pathlib import Path

import bpy

from model_menara import Geometry, reset

ROOT = Path(__file__).resolve().parents[1]
STYLE = {
    "Stone": ((.62,.61,.52),.71,.0),
    "PaintWhite": ((.82,.82,.77),.63,.0),
    "PaintWarm": ((.56,.48,.33),.68,.0),
    "Screen": ((.38,.40,.40),.63,.34),
    "Burgundy": ((.37,.072,.088),.62,.0),
    "GoldPanels": ((.62,.42,.105),.53,.17),
    "RoofBlue": ((.15,.28,.43),.66,.22),
    "Glass": ((.095,.22,.23),.30,.35),
    "GlassDark": ((.09,.15,.15),.36,.27),
    "Dark": ((.056,.068,.064),.66,.03),
    "Paving": ((.50,.46,.39),.78,.0),
    "Pool": ((.12,.43,.44),.37,.1),
}


def east_south(x, z, y):
    return (x, -z, y)


def clockwise(ring):
    area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))
    return ring[::-1] if area > 0 else ring


def quad_ring(x, z, width, depth, theta=0):
    cs,sn = math.cos(theta),math.sin(theta)
    return [(x+u*cs-v*sn,z+u*sn+v*cs) for u,v in
            [(-width/2,-depth/2),(-width/2,depth/2),(width/2,depth/2),(width/2,-depth/2)]]


def interpolator(a, b):
    dx,dz = b[0]-a[0],b[1]-a[1]
    d = math.hypot(dx,dz)
    def position(t, outside=0.0):
        return (a[0]+dx*t-dz/d*outside,a[1]+dz*t+dx/d*outside)
    return position,d


def scale_ring(ring, center, factor):
    return [(center[0] + (p[0]-center[0])*factor, center[1]+(p[1]-center[1])*factor) for p in ring]


def cladding(g, style, position, start, end, bottom, top, offset=.0):
    p,q = position(start,offset),position(end,offset)
    g.face(style,[(*p,bottom),(*q,bottom),(*q,top),(*p,top)])


def residensi(g, ring, lod):
    g.prism("Stone",ring,-4.9,.35)
    g.prism("Paving",ring,19.9,20.35)
    for a,b in zip(ring,ring[1:]+ring[:1]):
        at, length = interpolator(a,b)
        count = max(1,round(length/4.2))
        cladding(g,"Dark",at,0,1,.35,19.9)
        g.beam("PaintWhite",at(0,.17),at(1,.17),3.82,4.15,.32)
        g.beam("PaintWhite",at(0,.17),at(1,.17),18.42,18.85,.37)
        for bay in range(count):
            t0,t1 = bay/count,(bay+1)/count
            g.beam("Burgundy" if bay % 5 == 2 else "PaintWarm",
                   at(t0,.23),at(t0+.20/length,.23),.38,7.2,.49)
            cladding(g,"Glass",at,t0+.037/count,t1-.037/count,.55,3.74,.18)
        for level in range(5):
            base = 4.35 + level*2.92
            span = 8 if lod == 0 else (4 if lod == 1 else 2)
            for slat in range(span):
                y = base + slat * (2.69 / span)
                g.beam("Screen",at(0,.24),at(1,.24),y,y+.12,.39)
        if lod < 2:
            for bay in range(count+1):
                t = bay/count
                g.beam("PaintWhite",at(t,.30),at(t+.09/length,.30),4.1,19.1,.14)
    # Tower plate positions and individual heights are estimated from UTM aerial views.
    wings = [
        (208,112,18,40,-.06,15,"Burgundy"),
        (227,83,23,28,-.06,22,"PaintWarm"),
        (265,94,20,28,-.66,11,"PaintWarm"),
        (305,59,22,36,-.56,16,"Burgundy"),
    ]
    for wi,(x,z,w,d,angle,levels,accent) in enumerate(wings):
        plan = quad_ring(x,z,w,d,angle)
        roof_height = 20.35+levels*3.2
        g.prism("PaintWhite",scale_ring(plan,(x,z),1.09),roof_height,roof_height+.48)
        g.prism("RoofBlue",scale_ring(plan,(x,z),.89),roof_height+.48,roof_height+.62)
        g.prism("PaintWhite",quad_ring(x+w*.20,z-d*.17,w*.29,d*.29,angle),roof_height+.62,roof_height+2.42)
        for side,(a,b) in enumerate(zip(plan,plan[1:]+plan[:1])):
            at,length = interpolator(a,b)
            count = max(1,int(length / (2.65 if lod == 0 else 3.75 if lod == 1 else 6.0)))
            spandrel = "PaintWarm" if wi in (1,2) and side == 2 else "PaintWhite"
            cladding(g,spandrel,at,0,1,20.35,roof_height)
            g.beam(accent,at(.135,.20),at(.195,.20),20.42,roof_height,.22)
            g.beam("PaintWhite",at(.85,.19),at(.97,.19),20.42,roof_height,.31)
            for level in range(levels):
                y = 20.35 + level*3.2
                for k in range(count):
                    if side % 2 == 1 and k in (0,count-1):
                        continue
                    start,end = (k+.18)/count,(k+.83)/count
                    glass = "GlassDark" if (k+level+side) % 3 == 0 else "Glass"
                    if level in (levels-5,levels-6) and 2 <= k <= count-3 and side in (0,2):
                        cladding(g,"GoldPanels",at,k/count,(k+1)/count,y+.15,y+2.9,.060)
                    cladding(g,glass,at,start,end,y+.7,y+2.73,.11)
                    if lod == 0:
                        center = (start+end)/2
                        g.beam("PaintWhite",at(center,.114),at(center+.031/length,.114),y+.72,y+2.71,.047)
                if lod < 2 and side in (0,2):
                    g.beam("PaintWhite",at(0,.11),at(1,.11),y+2.8,y+2.91,.22)
    g.box("Pool",235,108,20.37,10.8,17.6,.09)
    g.box("RoofBlue",253,69,20.34,26,17,1.4)


def loop(x, z, radius, count):
    return [(x+math.cos(-i*math.tau/count)*radius,z+math.sin(-i*math.tau/count)*radius) for i in range(count)]


def roof_tier(g, rim, top, bottom, rise, style):
    for i in range(len(rim)):
        j = (i+1)%len(rim)
        g.face(style,[(*rim[i],bottom),(*rim[j],bottom),(*top[j],rise),(*top[i],rise)])


def mosque(g, ring, lod):
    g.prism("Stone",ring,-3.5,.21)
    for i,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
        at,length = interpolator(a,b)
        cladding(g,"PaintWarm",at,0,1,.21,4.7)
        if length < 3.0:
            continue
        windows = max(1,round(length/3.6))
        for j in range(windows):
            u0,u1 = (j+.29)/windows,(j+.73)/windows
            cladding(g,"GlassDark",at,u0,u1,1.09,3.76,.091)
            if lod == 0:
                g.beam("Stone",at(u0,.17),at(u1,.17),3.65,3.86,.26)
        g.beam("Stone",at(0,.15),at(1,.15),.24,.52,.35)
    center = (106.7,164)
    hood = scale_ring(ring,center,1.029)
    tier = scale_ring(ring,center,.75)
    terrace = scale_ring(ring,center,.65)
    roof_tier(g,hood,tier,4.63,7.29,"RoofBlue")
    g.prism("PaintWhite",tier,7.29,7.51)
    roof_tier(g,tier,terrace,7.50,8.84,"RoofBlue")
    g.face("RoofBlue",[(*q,8.84) for q in terrace])
    segments = [32,20,12][lod]
    g.prism("Stone",loop(*center,7.55,segments),8.84,9.69)
    rims = [(7.42,9.66),(7.05,10.57),(5.7,11.47),(3.4,12.1),(.45,12.65)]
    for (r0,h0),(r1,h1) in zip(rims,rims[1:]):
        roof_tier(g,loop(*center,r0,segments),loop(*center,r1,segments),h0,h1,"GoldPanels")
    g.prism("GoldPanels",loop(*center,.16,8),12.64,14.02)
    for tx,tz in [(116.7,146.4),(100.8,187.2)]:
        g.prism("Stone",quad_ring(tx,tz,3.0,2.6,-.364),0,9.2)
        g.prism("PaintWhite",loop(tx,tz,1.04,10),8.7,19.5)
        g.prism("Stone",loop(tx,tz,1.43,10),17.2,18.0)
        g.prism("PaintWhite",loop(tx,tz,.73,10),19.4,22.02)
        roof_tier(g,loop(tx,tz,.95,10),loop(tx,tz,.13,10),22.0,24.3,"RoofBlue")
    # Public entry porch and pointed arch geometry. Walls remain a closed collision shell.
    u, v = 116.1, 178.3
    g.box("Stone",u,v,-.43,8.0,7.8,.67)
    g.box("Stone",u,v,4.54,7.4,6.5,.83)
    for col in (-3.05,3.05):
        g.box("PaintWarm",u+col,v,.21,1.28,6.0,4.35)
    span = 2.93
    shape = [(-span,2.0),(-2.6,2.68),(-2.03,3.18),(-1.25,3.65),(0,4.32),(1.25,3.65),(2.03,3.18),(2.6,2.68),(span,2.0)]
    for (s0,h0),(s1,h1) in zip(shape,shape[1:]):
        g.face("PaintWarm",[(u+s1,v+3,h1),(u+s0,v+3,h0),(u+s0,v+3,4.62),(u+s1,v+3,4.62)])


def export_model(spec):
    slug, ident, builder, h = spec
    data = json.loads((ROOT / "data/map.json").read_text())
    row = next(entry for entry in data["buildings"] if entry["id"] == ident)
    perimeter = clockwise([tuple(p) for p in row["footprint"]])
    for lod in range(3):
        reset()
        geom = Geometry(east_south,STYLE)
        builder(geom,perimeter,lod)
        geom.to_meshes()
        if lod == 0:
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f"art/{slug}.blend"),compress=True)
        bpy.ops.export_scene.gltf(filepath=str(ROOT/f"assets/architecture/{slug}_lod{lod}.glb"),
                                  export_format="GLB",export_draco_mesh_compression_enable=False)
    reset()
    geom = Geometry(east_south,STYLE)
    geom.prism("Stone",perimeter,-5.,h)
    geom.to_meshes()
    bpy.ops.export_scene.gltf(filepath=str(ROOT/f"assets/architecture/{slug}_collision.glb"),
                             export_format="GLB",export_materials="NONE",export_draco_mesh_compression_enable=False)


def main():
    export_model(("residensi", "osm-way-524812098",residensi,20.2))
    export_model(("masjid", "osm-way-772103594",mosque,8.1))


if __name__ == "__main__":
    main()
