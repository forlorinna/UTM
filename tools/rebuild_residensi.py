"""Residensi UTMKL: four distinct residential wings on a curved public podium."""
from dataclasses import dataclass
import json
import math

from architectural_mesh import BuildingMesh, ROOT, clockwise, export_building, line_on_edge

MATERIALS = {
    "Ivory": ((.62,.59,.50),.71,0),
    "Plinth": ((.43,.40,.34),.78,0),
    "SilkSilver": ((.42,.43,.42),.55,.38),
    "RoofDeck": ((.20,.22,.23),.75,0),
    "Graphite": ((.082,.090,.089),.56,.32),
    "RedSpine": ((.30,.041,.040),.76,0),
    "OchreInlay": ((.53,.39,.14),.67,0),
    "DeepGlass": ((.040,.094,.105),.22,0),
    "LandingGlass": ((.075,.12,.115),.25,0),
    "Lit": ((.62,.46,.27),.65,0),
    "Paving": ((.36,.33,.28),.83,0),
    "Water": ((.065,.22,.23),.13,0),
    "PlantBeds": ((.085,.11,.052),.91,0),
}


@dataclass(frozen=True)
class Wing:
    center: tuple
    length: float
    depth: float
    rotation: float
    levels: int
    balcony_rhythm: tuple
    crown_projection: float
    core_style: str


WINGS = (
    Wing((209.0,114.2),18.3,35.1,-.052,15,(1,2,4),1.11,"RedSpine"),
    Wing((228.2,83.1),23.1,27.2,-.058,22,(2,3,5),.78,"Plinth"),
    Wing((267.5,94.4),19.8,26.9,-.674,11,(1,3),1.32,"RedSpine"),
    Wing((301.4,61.2),20.8,34.1,-.568,16,(2,4),1.49,"RedSpine"),
)


def coordinates(x,z,y):
    return x,-z,y


def outline():
    data=json.loads((ROOT/"data/map.json").read_text())
    entry=next(b for b in data["buildings"] if b["id"] == "osm-way-524812098")
    return clockwise([tuple(p) for p in entry["footprint"]])


def plan(w, overhang=0):
    cs,sn=math.cos(w.rotation),math.sin(w.rotation)
    a=w.length*.5+overhang
    b=w.depth*.5+overhang
    return [(w.center[0]+u*cs-v*sn,w.center[1]+u*sn+v*cs) for u,v in
            [(-a,-b),(-a,b),(a,b),(a,-b)]]


def wing(g, wing, lod, wing_index):
    floor_height=3.12
    base=19.54
    roof=base+floor_height*wing.levels
    edges=plan(wing)
    for face,(a,b) in enumerate(zip(edges,edges[1:]+edges[:1])):
        at,length=line_on_edge(a,b)
        bays=max(3,round(length/(2.7 if lod==0 else (3.8 if lod==1 else 5.6))))
        g.beam("Ivory",at(0,.055),at(1,.055),base-.16,base+.3,.20)
        g.beam(wing.core_style,at(.045,.11),at(.18,.11),base+.1,roof-.15,.36)
        g.beam("Ivory",at(.90,.17),at(1,.17),base+.30,roof,.40)
        for level in range(wing.levels):
            y=base+level*floor_height
            g.wall("Ivory",at(0,-.04),at(1,-.04),y,y+.69)
            g.wall("Ivory",at(0,-.04),at(1,-.04),y+2.61,y+floor_height)
            for bay in range(bays):
                s,t=bay/bays,(bay+1)/bays
                left,right=s+.18/bays,t-.11/bays
                balcony=face in (0,2) and bay in wing.balcony_rhythm
                reveal=.67 if balcony else .21
                g.wall("Ivory",at(s,-.03),at(left,-.03),y+.66,y+2.65)
                g.wall("Ivory",at(right,-.03),at(t,-.03),y+.66,y+2.65)
                g.wall("LandingGlass" if balcony else "DeepGlass",
                       at(left,-reveal),at(right,-reveal),y+.72,y+2.53)
                if lod < 2:
                    g.beam("SilkSilver",at(left,.027),at(right,.027),y+.64,y+.72,.11)
                    if balcony:
                        g.beam("Ivory",at(left,.26),at(right,.26),y+.18,y+.35,.48)
                        g.beam("Graphite",at(left,.44),at(right,.44),y+.82,y+.87,.063)
                        if lod==0:
                            for k in range(9):
                                pos=left+(right-left)*k/8
                                g.beam("SilkSilver",at(pos,.44),at(pos+.014/length,.44),y+.29,y+.87,.027)
                    else:
                        axis=(left+right)/2
                        g.beam("SilkSilver",at(axis,-.186),at(axis+.04/length,-.186),y+.72,y+2.54,.069)
                if level in (wing.levels-5, wing.levels-6) and face == 0 and 2 <= bay <= bays-3:
                    g.wall("OchreInlay",at(s,.015),at(t,.015),y+.03,y+.63)
                if lod==0 and face==0 and level in (6,11) and bay==bays//2+(wing_index%2):
                    g.wall("Lit",at(left+.1/bays,-reveal+.013),at(right-.1/bays,-reveal+.013),y+1.01,y+2.17)
    g.prism("RoofDeck",plan(wing),roof-.11,roof+.18)
    g.prism("Ivory",plan(wing,wing.crown_projection),roof+.16,roof+.41)
    for a,b in zip(edges,edges[1:]+edges[:1]):
        g.beam("SilkSilver",a,b,roof+.41,roof+1.02,.16)
    core=Wing((wing.center[0]+1.0,wing.center[1]-wing.depth*.25),wing.length*.39,
              wing.depth*.28,wing.rotation,1,(),0,"Ivory")
    g.prism("Ivory",plan(core),roof+.41,roof+2.28+(wing_index%2)*.38)


def podium(g, lod):
    perimeter=outline()
    g.prism("Plinth",perimeter,-3.4,.11)
    g.prism("Paving",perimeter,19.29,19.55)
    for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):
        position,length=line_on_edge(a,b)
        east = (a[0]+b[0])/2 > 235
        g.beam("Ivory",position(0,.25),position(1,.25),18.81,19.36,.64)
        g.wall("Graphite",position(0,-.24),position(1,-.24),3.61,18.83)
        levels=5
        for level in range(levels):
            y=3.79+level*2.99
            g.beam("Ivory",position(0,.12),position(1,.12),y,y+.24,.34)
            count=10 if lod == 0 else (6 if lod == 1 else 4)
            for slat in range(count):
                h=y+.37+slat*(2.44/count)
                g.beam("SilkSilver",position(0,.30),position(1,.30),h,h+.09,.18)
        count=max(1,round(length/3.82))
        for i in range(count):
            start,end=i/count,(i+1)/count
            g.beam("RedSpine" if east and i%4==1 else "Plinth",position(start,.29),
                   position(start+.17/count,.29),.12,3.62,.37)
            g.wall("DeepGlass",position(start+.17/count,-.22),position(end,-.22),.17,3.49)
            if lod==0:
                middle=(start+end)*.5
                g.beam("SilkSilver",position(middle,-.184),position(middle+.04/length,-.184),.14,3.49,.095)
        g.beam("Plinth",position(0,.62),position(1,.62),.055,.18,1.12)
    g.box("Ivory",230.2,240.8,101.2,117.5,19.55,19.73)
    g.box("Water",230.66,240.34,101.65,117.09,19.68,19.74)
    g.box("PlantBeds",226.5,228.8,101.2,117.1,19.54,19.96)
    g.box("PlantBeds",241.4,243.5,102.1,111.85,19.54,19.99)
    g.box("Ivory",247.5,261.2,71.2,83.4,19.52,23.6)
    g.box("RoofDeck",246.91,261.79,70.62,83.98,23.6,23.82)


def generate(lod):
    g=BuildingMesh(coordinates,MATERIALS)
    podium(g,lod)
    for index, model in enumerate(WINGS):
        wing(g,model,lod,index)
    return g


def collision():
    g=BuildingMesh(coordinates,MATERIALS)
    g.prism("Plinth",outline(),-3.4,19.46)
    for model in WINGS:
        g.prism("Ivory",plan(model),19.38,19.54+3.12*model.levels)
    return g


if __name__ == "__main__":
    export_building("residensi_utmkl",generate,collision)
