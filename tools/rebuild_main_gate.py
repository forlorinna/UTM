"""Nonfunctional public entrance canopy and facade based on the 2024 Bernama photograph."""
from architectural_mesh import BuildingMesh, export_building

STYLE = {
    "Silver": ((.48,.49,.46),.49,.49),
    "DarkMetal": ((.14,.16,.15),.53,.41),
    "Ochre": ((.47,.36,.19),.74,0),
    "Ivory": ((.65,.60,.49),.78,0),
    "Wine": ((.28,.055,.03),.68,0),
    "GlassLobby": ((.033,.070,.077),.22,0),
    "Paving": ((.32,.286,.23),.83,0),
}


def coordinates(u,v,h):
    return .567*u+.824*v, .824*u-.567*v,h


def canopy_height(u):
    return 3.9 + abs(u-.8)*(.145 if u>.8 else .091)


def create(lod):
    g=BuildingMesh(coordinates,STYLE)
    for role,lo,hi,y0,y1 in [("Paving",-2.35,2.33,-.23,.05),("Ochre",-1.82,1.83,.05,.94),
                              ("Ochre",-1.9,1.93,2.91,3.37),("Ivory",-1.94,1.98,3.37,3.56)]:
        g.box(role,lo,hi,-1.37,1.69,y0,y1)
    for u in (-1.96,1.9):
        g.box("Wine",u-.087,u+.087,-1.45,1.75,.08,3.65)
    g.box("GlassLobby",-1.78,1.82,-1.44,-1.32,.94,2.93)
    for axis in (-1.78,-.57,.55,1.77):
        g.box("Silver",axis-.024,axis+.024,-1.46,-1.32,.98,2.91)
    g.box("Silver",-1.76,1.81,-1.47,-1.33,1.83,1.88)
    g.box("Wine",-1.86,1.85,1.52,1.76,.84,2.9)
    for u in (-1.46,1.46):
        g.box("Wine",u-.108,u+.11,-1.1,-.85,3.32,5.34)
    span = [-9.8,-7.4,-4.5,-2.1,.8,3.7,6.6,9.6,12.4]
    for a,b in zip(span,span[1:]):
        la,lb=canopy_height(a),canopy_height(b)
        front_a=-1.62+.027*abs(a)
        front_b=-1.62+.027*abs(b)
        g.face("Silver",[(a,front_a,la),(b,front_b,lb),(b,front_b,lb+.52),(a,front_a,la+.52)])
        g.face("Silver",[(b,1.66,lb),(a,1.66,la),(a,1.66,la+.52),(b,1.66,lb+.52)])
        g.face("Silver",[(a,front_a,la+.52),(a,1.66,la+.52),(b,1.66,lb+.52),(b,front_b,lb+.52)])
        g.face("DarkMetal",[(b,front_b,lb),(b,1.66,lb),(a,1.66,la),(a,front_a,la)])
        if lod==0:
            g.box("DarkMetal",a,a+.025,front_a,front_a+.026,la+.03,la+.51)
    for u in (-9.8,12.4):
        y = canopy_height(u)
        g.box("Silver",u-.028,u+.028,-1.62+.027*abs(u),1.66,y,y+.52)
    g.box("Wine",-1.92,1.88,-1.31,-1.22,4.69,5.61)
    g.box("Ivory",-1.74,1.71,-1.34,-1.29,4.81,5.49)
    return g


def collision():
    g=BuildingMesh(coordinates,STYLE)
    g.box("Paving",-2.35,2.33,-1.37,1.69,-.23,.05)
    g.box("Ochre",-1.94,1.98,-1.45,1.75,.04,3.55)
    return g


if __name__ == "__main__":
    export_building("main_gate",create,collision)
