"""Menara Razak. The photographed facade is broken into distinct envelope sections."""
import json
import math

from architectural_mesh import BuildingMesh, ROOT, clockwise, export_building, line_on_edge

COS, SIN = math.cos(.656), math.sin(.656)
MATERIALS = {
    "Precast": ((.47, .46, .42), .68, 0),
    "Sandstone": ((.43, .36, .25), .77, 0),
    "Granite": ((.14, .134, .125), .65, 0),
    "Paving": ((.36, .345, .31), .75, 0),
    "Silver": ((.49, .51, .49), .46, .52),
    "Anodized": ((.105, .123, .133), .34, .44),
    "GlassSteel": ((.065, .113, .142), .25, 0),
    "GlassBlue": ((.029, .075, .108), .23, 0),
    "GlassWarm": ((.061, .099, .111), .28, 0),
    "GlassLobby": ((.045, .103, .104), .19, 0),
    "Shadow": ((.016, .023, .028), .79, 0),
    "Louvers": ((.096, .124, .138), .56, .3),
    "Wine": ((.25, .035, .032), .62, 0),
    "RoofSeam": ((.30, .34, .35), .48, .58),
    "RoofEdge": ((.50, .52, .50), .42, .48),
    "RoofDeck": ((.19, .20, .19), .83, 0),
    "Lit": ((.65, .50, .28), .72, 0),
}


def coordinates(u, v, h):
    return (COS*u - SIN*v, -SIN*u - COS*v, h)


def plan():
    campus = json.loads((ROOT / "data/map.json").read_text())
    tower = next(b for b in campus["buildings"] if b["id"] == "osm-way-552610255")
    return clockwise([(COS*x + SIN*z, -SIN*x + COS*z) for x, z in tower["footprint"]])


def hollow_panel(g, material, edge, a, b, low, high, recess, lod):
    face = -.04 - recess
    g.wall(material, edge(a, face), edge(b, face), low, high)
    if lod == 2:
        return
    near_a, near_b = edge(a, -.015), edge(b, -.015)
    far_a, far_b = edge(a, face), edge(b, face)
    g.face("Shadow", [(*near_a, low), (*far_a, low), (*far_a, high), (*near_a, high)])
    g.face("Shadow", [(*far_b, low), (*near_b, low), (*near_b, high), (*far_b, high)])
    g.face("Anodized", [(*near_a, low), (*near_b, low), (*far_b, low), (*far_a, low)])


def envelope(g, footprint, lod):
    for start, end in zip(footprint, footprint[1:]+footprint[:1]):
        edge, length = line_on_edge(start, end)
        front = end[0] > start[0] and (start[1]+end[1])/2 > 0.7
        rounded = max(start[0], end[0]) < 7.0
        terminal = front and min(start[0], end[0]) > 25
        western_rear = (start[1]+end[1]) / 2 < -8
        count = max(1, round(length / ((1.26 if rounded else 1.61) if lod == 0 else (3.2 if lod == 1 else 6.4))))
        offset = .16 if rounded else (.34 if terminal else .23)
        g.beam("Anodized", edge(0,.1), edge(min(.18/length, 1),.1), 3.7, 49.25, .13)
        if rounded and min(start[0], end[0]) < -20.35:
            g.beam("Wine", edge(0,.16), edge(1,.16), 0.16, crown_height((start[0]+end[0])/2)-.55, .28)
        for floor in range(15):
            bottom = 5.42 + floor*2.92
            top = bottom + 2.92
            band = .83 if front and not rounded else (.37 if rounded else .56)
            glazing = "GlassBlue" if rounded or western_rear else "GlassSteel"
            for bay in range(count):
                u = (bay + .5)/count
                start_t, end_t = bay/count, (bay+1)/count
                if front and terminal and (bay // max(1,count//4)) % 2 == 0:
                    g.beam("Precast", edge(start_t,-.03),edge(end_t,-.03),bottom,top,.10)
                    continue
                hollow_panel(g, glazing if floor not in (5,10) or (bay+2)%7 > 1 else "GlassWarm",
                             edge, start_t, end_t, bottom+band, top-.12, offset, lod)
                if lod <= 1:
                    g.beam("Anodized",edge(start_t,.03),edge(min(start_t+.045/length,1),.03),bottom,top,.13)
                if lod == 0 and front:
                    g.beam("Silver",edge(start_t,.02),edge(end_t,.02),bottom+band+.16,bottom+band+.21,.086)
                    if floor in (3, 7, 11) and 0.34 < u < .61 and (bay + floor) % 13 == 3:
                        g.beam("Lit",edge(start_t+.01/count,-offset+.022),edge(end_t-.01/count,-offset+.022),
                               bottom+band+.33,top-.5,.032)
            band_mat = "Anodized" if rounded else "Precast"
            g.beam(band_mat,edge(0,-.015),edge(1,-.015),bottom,bottom+band,.12)
            g.beam("Silver",edge(0,.026),edge(1,.026),top-.128,top-.067,.105)
            if front and rounded and floor % (1 if lod == 0 else 3) == 0:
                g.beam("Silver",edge(0,.38),edge(1,.38),bottom+band-.14,bottom+band-.04,.36)

        g.wall("Precast",edge(0,-.18),edge(1,-.18),-3.0,0.16)
        if not (front and 3 < (start[0]+end[0])*.5 < 15):
            for bay in range(max(1,round(length/3.1))):
                bays = max(1,round(length/3.1))
                low_t, hi_t = bay/bays, (bay+1)/bays
                g.beam("Sandstone",edge(low_t,0),edge(low_t+(hi_t-low_t)*.19,0),.14,5.42,.24)
                hollow_panel(g,"GlassLobby",edge,low_t+(hi_t-low_t)*.19,hi_t,.27,4.51,.36,lod)
            g.beam("Sandstone",edge(0,.02),edge(1,.02),4.56,5.42,.24)

        mechanical = "Wine" if rounded and front else "Louvers"
        crown_a,crown_b = edge(0,-.66),edge(1,-.66)
        g.face(mechanical,[(*crown_a,49.2),(*crown_b,49.2),
                           (*crown_b,crown_height(crown_b[0])-.47),(*crown_a,crown_height(crown_a[0])-.47)])
        if lod < 2 and not rounded:
            for index in range(max(1,round(length/1.26))):
                sections = max(1,round(length/1.26))
                t = index/sections
                position = edge(t,-.61)
                g.beam("Anodized", position, edge(min(t+.035/length,1),-.61),
                       49.24,crown_height(position[0])-.6,.056)


def crown_height(u):
    return 53.97 - .00077 * (u+2.8)**2 + .012 * (u+2.8)


def cross_section(footprint, u):
    hits = []
    for a,b in zip(footprint, footprint[1:]+footprint[:1]):
        if min(a[0],b[0]) <= u <= max(a[0],b[0]) and abs(b[0]-a[0]) > 1e-5:
            hits.append(a[1] + (b[1]-a[1]) * (u-a[0]) / (b[0]-a[0]))
    return min(hits), max(hits)


def roof_shell(g, footprint, lod):
    left, right = min(p[0] for p in footprint), max(p[0] for p in footprint)
    count = (60, 28, 14)[lod]
    ends = []
    for i in range(count+1):
        u = right if i == count else left+(right-left)*i/count
        bottom, top = cross_section(footprint, u)
        lip = max(.06, min(1.28, (top-bottom)*.18))
        ends.append(((u,bottom-lip,crown_height(u)), (u,top+lip,crown_height(u))))
    for index, ((a,b),(c,d)) in enumerate(zip(ends,ends[1:])):
        g.face("RoofSeam",[a,b,d,c])
        g.face("RoofDeck",[(p[0],p[1],p[2]-.43) for p in (c,d,b,a)])
        for p,q in [(a,c),(d,b)]:
            g.face("RoofEdge",[p,q,(q[0],q[1],q[2]-.43),(p[0],p[1],p[2]-.43)])
        if lod == 0 and index % 2 == 0:
            g.beam("RoofEdge",a[:2],b[:2],a[2],a[2]+.027,.038)
    for a,b in [ends[0],ends[-1][::-1]]:
        g.face("RoofEdge",[a,b,(b[0],b[1],b[2]-.43),(a[0],a[1],a[2]-.43)])


def entrance(g, lod):
    g.box("Paving", -1.4, 16.7, 7.9, 15.3, -.33, .02)
    g.box("Granite", -1.65, 16.95, 14.7, 15.86, -.38, -.13)
    g.box("Granite", -1.87, 17.17, 15.24, 16.38, -.42, -.27)
    g.box("Sandstone", -.7, 1.1, 8.0, 12.8, .02, 5.42)
    g.box("Sandstone", 14.15, 16.25, 8.4, 12.8, .02, 5.42)
    g.box("Sandstone", .92, 14.3, 10.74, 12.76, 3.32, 3.93)
    g.box("Precast", .92, 14.3, 10.74, 12.68, 5.01, 5.61)
    for start, end in [(1.08,4.15),(4.31,7.49),(7.65,10.85),(11.01,14.15)]:
        g.box("GlassSteel",start,end,11.55,12.22,3.94,5.03)
        g.box("Anodized",start,start+.06,12.18,12.25,3.93,5.05)
    for u in (1.04,4.4,11.0,14.2):
        g.box("Silver",u-.12,u+.12,12.27,12.54,.02,3.47)
    for start, end in [(1.24,4.27),(11.13,14.02)]:
        g.box("GlassLobby",start,end,12.27,12.36,.10,3.29)
        middle = (start+end)/2
        g.box("Anodized",middle-.033,middle+.033,12.35,12.46,.08,3.32)

    # Open pedestrian approach and recessed vestibule. Public geometry only.
    g.box("Shadow",4.5,10.94,8.25,8.57,.1,3.6)
    g.box("Granite",4.5,4.65,8.5,12.27,.1,3.31)
    g.box("Granite",10.84,11.01,8.5,12.27,.1,3.31)
    g.box("Shadow",.78,14.65,8.1,12.65,3.18,3.3)
    drip = [(u,15.89 + .57 * (1-((u-7.7)/9)**2)) for u in [-1.55,1.5,4.6,7.7,10.8,13.9,16.95]]
    for a,b in zip(drip,drip[1:]):
        g.beam("Silver",a,b,3.67,3.91,.23)
        g.face("RoofSeam",[(a[0],11.85,4.16),(*a,3.89),(*b,3.89),(b[0],11.85,4.16)])
        g.face("Anodized",[(b[0],11.85,4.07),(*b,3.71),(*a,3.71),(a[0],11.85,4.07)])
    for u, v in ((.6,15.46),(14.72,15.46)):
        g.column("Silver",u,v,.02,3.7,.195,16 if lod == 0 else 8)
    if lod == 0:
        for u in (2.5,5.95,9.45,12.9):
            g.box("Lit",u-.39,u+.39,14.8,14.94,3.707,3.723)
        for u in (2.0,13.39):
            g.column("Silver",u,13.65,.03,.93,.043)
            g.column("Silver",u,15.31,-.06,.93,.043)
            g.beam("Silver",(u,13.65),(u,15.31),.88,.93,.075)
    g.box("Wine",1.29,14.11,12.73,12.79,3.46,3.81)


def generate(lod):
    g = BuildingMesh(coordinates,MATERIALS)
    footprint = plan()
    envelope(g, footprint, lod)
    roof_shell(g, footprint, lod)
    entrance(g, lod)
    return g


def collision():
    g = BuildingMesh(coordinates,MATERIALS)
    g.prism("Precast",plan(),5.42,51.5)
    for start,end in zip(plan(),plan()[1:]+plan()[:1]):
        if end[0]>start[0] and 3 < (start[0]+end[0])*.5 < 15 and (start[1]+end[1])*.5>.7:
            continue
        g.wall("Precast",start,end,-3.0,5.45)
    g.box("Granite",4.5,10.94,8.25,8.58,-.2,3.6)
    for bounds in [(-1.4,16.7,7.9,15.3,-.33,.02),(-1.65,16.95,14.7,15.86,-.38,-.13),
                   (-1.87,17.17,15.24,16.38,-.42,-.27),(-.7,1.1,8,12.8,.02,5.42),
                   (14.15,16.25,8.4,12.8,.02,5.42),(4.5,4.65,8.5,12.27,.02,3.31),
                   (10.84,11.01,8.5,12.27,.02,3.31),(1.24,4.27,12.27,12.36,.02,3.31),
                   (11.13,14.02,12.27,12.36,.02,3.31)]:
        g.box("Granite",*bounds)
    return g


if __name__ == "__main__":
    export_building("menara_razak",generate,collision)
