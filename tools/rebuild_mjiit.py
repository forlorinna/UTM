"""MJIIT reconstruction from its OSM outline and documented western elevation."""
import json
import math

from architectural_mesh import BuildingMesh, ROOT, clockwise, export_building, line_on_edge

FINISHES = {
    "Ivory": ((.61,.59,.51), .65, 0),
    "BluePlaster": ((.25,.34,.39), .83, 0),
    "Ochre": ((.46,.30,.13), .75, 0),
    "Wine": ((.25,.026,.045), .66, 0),
    "Paving": ((.29,.26,.20), .81, 0),
    "GlassGreen": ((.037,.087,.086), .22, 0),
    "GlassBlue": ((.049,.087,.115), .22, 0),
    "Shadow": ((.029,.030,.025), .86, 0),
    "Silver": ((.44,.46,.43), .45, .5),
    "DarkMetal": ((.15,.17,.16), .53, .6),
    "Railings": ((.45,.48,.46), .41, .65),
    "Lit": ((.59,.43,.23), .73, 0),
}


def coordinates(u,v,h):
    return 125-v,-45-u,h


def outline():
    data = json.loads((ROOT/"data/map.json").read_text())
    entry = next(e for e in data["buildings"] if e["id"] == "osm-way-733313948")
    return clockwise([(z-45,125-x) for x,z in entry["footprint"]])


def wing_wall(g, first, last, lod):
    place,length = line_on_edge(first,last)
    visible = last[0] > first[0] and (first[1]+last[1])/2 > 4.5
    wing = (first[0]+last[0])/2
    wing_is_ochre = abs(wing) < 43.0
    slots = max(1,round(length / (3.25 if lod == 0 else (4.5 if lod == 1 else 7.4))))
    g.wall("Ivory",place(0,-.30),place(1,-.30),-3.25,.12)
    for floor in range(10):
        low = .12+floor*3.27
        high = low+3.27
        kind = "Ochre" if floor < 3 and wing_is_ochre else ("BluePlaster" if floor == 3 or not visible else "Ivory")
        g.wall(kind,place(0,0),place(1,0),low,low+.68)
        g.wall(kind,place(0,0),place(1,0),high-.42,high)
        if abs(wing) < 14 and visible:
            g.wall("Shadow",place(0,-.8),place(1,-.8),low+.68,high-.42)
            continue
        for i in range(slots):
            start,stop = i/slots,(i+1)/slots
            a,b = start+.21/slots,stop-.12/slots
            g.wall(kind,place(start,0),place(a,0),low+.67,high-.41)
            g.wall(kind,place(b,0),place(stop,0),low+.67,high-.41)
            g.wall("GlassGreen" if floor < 4 else "GlassBlue",place(a,-.30),place(b,-.30),low+.69,high-.41)
            if lod < 2:
                for t in (a,b):
                    g.beam("Ivory",place(t,.064),place(min(1,t+.045/length),.064),low+.60,high-.38,.10)
                g.beam("Silver",place(a,.067),place(b,.067),low+.60,low+.68,.16)
                if lod == 0:
                    t = (a+b)/2
                    g.beam("Silver",place(t,-.24),place(t+.052/length,-.24),low+.68,high-.40,.073)
                    g.beam("Silver",place(a,-.251),place(b,-.251),low+1.88,low+1.936,.065)
        if visible and floor > 2:
            g.beam("Ivory",place(0,.125),place(1,.125),high-.21,high-.035,.53)
            if lod == 0:
                g.beam("Silver",place(0,.388),place(1,.388),high-.18,high-.127,.075)
    if visible and length > 8 and abs(wing) > 20:
        g.beam("Wine",place(.035,.18),place(.035+.3/length,.18),9.97,32.8,.24)
    g.beam("DarkMetal",place(0,.21),place(1,.21),32.81,33.06,.82)


def podium(g, lod):
    # Bowed entrance bridge, lower window wall and two separate service towers.
    for u in (-11.8, 11.8):
        g.box("Ivory",u-2.63,u+2.63,8.4,12.46,9.89,34.85)
        g.box("DarkMetal",u-3.22,u+3.22,7.92,13.14,34.86,35.12)
        for floor in range(5):
            y=14.2+floor*3.77
            g.box("Silver",u-2.71,u+2.71,12.36,12.86,y,y+.15)
        for ku in (u-2.01,u+2.07):
            g.box("Ivory",ku-.20,ku+.20,12.39,12.72,16.31,34.91)
    g.box("BluePlaster",-7.9,7.9,7.8,10.34,14.0,33.1)
    for floor in range(5):
        y=15.3+floor*3.31
        for u in (-5.7,-2.96,-.02,2.85,5.67):
            g.box("GlassBlue",u-.96,u+.96,10.38,10.423,y,y+1.51)
            if lod==0:
                g.box("Silver",u-.023,u+.023,10.421,10.456,y,y+1.51)
        for a,b in [(-3.2,3.2),(3.2,-3.2)]:
            g.face("Ivory",[(a,10.69,y-.28),(b,10.69,y+2.45),
                            (b,10.69,y+2.68),(a,10.69,y-.05)])
    g.box("DarkMetal",-5.09,5.09,6.4,11.6,33.06,33.52)
    g.box("Ivory",-4.97,4.97,7.7,11.52,33.52,33.69)
    g.box("Paving",-16.3,16.3,9.1,17.42,-.29,.12)
    for u in (-11.7,-6.2,-.7,4.8,10.3):
        g.column("Ochre",u,13.7,.12,13.68,.34,16 if lod==0 else 8)
    for y,depth,material in [(3.55,19.63,"GlassGreen"),(6.63,15.9,"Silver"),(10.49,16.85,"Wine"),(13.32,17.3,"Ivory")]:
        sections = (16,10,7)[lod]
        rings = [(-15.8+31.6*i/sections, depth-1.44*((i-sections*.5)/(sections*.5))**2)
                 for i in range(sections+1)]
        for p,q in zip(rings,rings[1:]):
            if material == "GlassGreen":
                g.face(material,[(p[0],11.4,y+.14),(*p,y),(*q,y),(q[0],11.4,y+.14)])
                g.beam("DarkMetal",(p[0],11.4),p,y-.07,y+.022,.082)
            else:
                height = .42 if material == "Wine" else .23
                g.beam(material,p,q,y,y+height,.32)
                g.face("DarkMetal",[(*q,y+.03),(*p,y+.03),(p[0],11.39,y+.03),(q[0],11.39,y+.03)])
    for i in range(11):
        u=-14.5+i*2.84
        if i not in (4,5,6):
            g.box("GlassGreen",u,u+2.61,10.77,10.87,.14,3.44)
        g.box("DarkMetal",u-.056,u+.056,10.76,10.97,.13,3.48)
    g.box("Shadow",-4.05,5.12,7.63,8.08,.12,3.72)
    if lod == 0:
        for u in (-11,-6.1,-1.2,3.75,8.7,13.6):
            g.box("Lit",u-.42,u+.42,15.15,15.28,3.43,3.465)
        for u in (-11.5,-6.3,3.8,9.5):
            for sign in (-1,1):
                points = [(u,17.7,3.55),(u+sign*2.63,13.7,6.65),
                          (u+sign*2.7,13.7,6.49),(u,17.7,3.39)]
                g.face("Railings",points if sign < 0 else points[::-1])


def generate(lod):
    plan = outline()
    g = BuildingMesh(coordinates,FINISHES)
    g.roof("DarkMetal",plan,[32.85]*len(plan))
    for a,b in zip(plan,plan[1:]+plan[:1]):
        wing_wall(g,a,b,lod)
    podium(g,lod)
    return g


def collision():
    g = BuildingMesh(coordinates,FINISHES)
    plan = outline()
    g.prism("Ivory",plan,3.51,32.85)
    for a,b in zip(plan,plan[1:]+plan[:1]):
        if b[0]>a[0] and (a[1]+b[1])*.5>4.5 and abs((a[0]+b[0])*.5)<14.0:
            continue
        g.wall("Ivory",a,b,-3.4,3.51)
    g.box("Paving",-16.3,16.3,9.1,17.42,-.29,.12)
    g.box("Ivory",-4.05,5.12,7.63,8.08,.12,3.72)
    for u in (-11.7,-6.2,-.7,4.8,10.3):
        g.column("Ochre",u,13.7,.12,3.72,.34,8)
    return g


if __name__ == "__main__":
    export_building("mjiit",generate,collision)
