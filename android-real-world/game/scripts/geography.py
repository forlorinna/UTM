from pathlib import Path
import json, math, re, sys, xml.etree.ElementTree as ET
from io import BytesIO
from urllib.request import urlopen
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1])
LON, LAT = 101.7226, 3.1717
X_SCALE, Y_SCALE = 111150, 110575
EXTENT = 735
GRID = 97
BOUNDS = box(-EXTENT, -EXTENT, EXTENT, EXTENT)
COLORS = {'park':'#587a59','forest':'#345841','pitch':'#55926d','parking':'#4b5356','water':'#49939c'}
PLACE = {
    '552610255': ('razak','Menara Razak',54,18,'osm:height'),
    '733313948': ('mjiit','MJIIT',33.4,9,'estimate'),
    '524812098': ('residensi','Residensi UTMKL',93.2,27,'estimate'),
    '772103594': ('mosque','Masjid UTM',10,2,'estimate'),
    '606238583': ('inn',"Scholar’s Inn",15,4,'estimate'),
    '734916985': ('hall','Dewan Tan Sri Ainuddin Wahid',10,2,'estimate'),
}
LANDMARK_NOTES = {
    'razak':'The campus tower houses academic and administrative functions. Its footprint and 54 m height come from OpenStreetMap.',
    'mjiit':'The Malaysia–Japan International Institute of Technology operates here. The perimeter follows mapped geometry. Façade detailing is approximate.',
    'mosque':'The campus mosque is mapped with its actual footprint. Roof and minaret details are approximations.',
    'inn':'The campus lodging is accessed from Jalan Maktab. Storeys and exterior details are estimated.',
    'residensi':'Four residential towers and a shared podium. The footprint is mapped. Exterior details and individual tower heights are approximate.',
    'hall':'An event venue on campus. The building footprint is mapped, with an approximate exterior.',
}

def tags(element):
    return {tag.get('k'):tag.get('v') for tag in element.findall('tag')}

def round_points(points):
    return [[round(x,2),round(y,2)] for x,y in points]

def polygon_parts(geometry):
    if geometry.geom_type == 'Polygon' and not geometry.is_empty:
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for piece in geometry.geoms:
            yield from polygon_parts(piece)

def rings(poly):
    return [round_points(poly.exterior.coords[:-1]), *[round_points(ring.coords[:-1]) for ring in poly.interiors]]

def number(value, default):
    match = re.match(r'^\s*(\d+(?:\.\d+)?)', value or '')
    return float(match[1]) if match else default

def elevations():
    zoom = 14
    scale = (2 ** zoom) * 256
    def address(lon, lat):
        return (lon + 180) / 360 * scale, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) * scale / 2
    cache = {}
    def height(px, py):
        tx, ty = int(px)//256, int(py)//256
        dest = SOURCE.parent / f'terrarium-{zoom}-{tx}-{ty}.png'
        if (tx,ty) not in cache:
            url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{tx}/{ty}.png'
            if not dest.exists():
                with urlopen(url, timeout=20) as response:
                    dest.write_bytes(response.read())
            cache[tx,ty] = Image.open(BytesIO(dest.read_bytes())).convert('RGB')
        r,g,b = cache[tx,ty].getpixel((int(px)%256,int(py)%256))
        return r*256+g+b/256-32768
    def at(x,z):
        a,b=address(LON+x/X_SCALE,LAT-z/Y_SCALE)
        i,j=math.floor(a),math.floor(b)
        p,q=a-i,b-j
        return (height(i,j)*(1-p)+height(i+1,j)*p)*(1-q)+(height(i,j+1)*(1-p)+height(i+1,j+1)*p)*q
    base = at(0,0)
    values = [round(at(-EXTENT+2*EXTENT*i/(GRID-1), -EXTENT+2*EXTENT*j/(GRID-1))-base,2)
              for j in range(GRID) for i in range(GRID)]
    return values,round(base,2)

def main():
    root = ET.parse(SOURCE).getroot()
    nodes={n.get('id'):((float(n.get('lon'))-LON)*X_SCALE,(LAT-float(n.get('lat')))*Y_SCALE) for n in root.findall('node')}
    buildings, roads, landmarks, trees = [], [], [], []
    road_buffers, area_buffers = {}, {}
    edge = None
    for w in root.findall('way'):
        t=tags(w)
        wid=w.get('id')
        pts=[nodes[n.get('ref')] for n in w.findall('nd') if n.get('ref') in nodes]
        if len(pts)<2 or not BOUNDS.intersects(LineString(pts)):
            continue
        closed = len(pts)>3 and pts[0]==pts[-1]
        poly = Polygon(pts).buffer(0) if closed else None
        if wid=='1076507073':
            edge=round_points(pts)
        if 'building' in t and t['building']!='no' and closed:
            for geom in polygon_parts(poly):
                if geom.area<9:continue
                name=t.get('name','')
                core=PLACE.get(wid)
                default_levels = 1 if t.get('building') in ('hut','roof','garage','shed') else 2 if geom.area<180 else 4 if geom.area<900 else 5
                levels=int(number(t.get('building:levels'), default_levels))
                h=number(t.get('height'), max(3,levels*3.5))
                evidence='osm:height' if 'height' in t else 'osm:levels' if 'building:levels' in t else 'estimate'
                kind='generic'
                c=geom.representative_point()
                if core:
                    kind, name, h, levels, evidence=core
                    landmarks.append({'id':kind,'name':name,'point':[round(c.x,2),round(c.y,2)],'note':LANDMARK_NOTES[kind],'osm':wid})
                buildings.append({'osm':wid,'kind':kind,'name':name,'p':rings(geom),'h':h,'floors':levels,'source':evidence,'center':[round(c.x,2),round(c.y,2)]})
        category=t.get('highway')
        if category and t.get('tunnel') not in ('yes','building_passage') and category not in ('construction','proposed','elevator','bus_stop'):
            path=category in ('footway','path','steps','cycleway','pedestrian','track','bridleway')
            main=category in ('primary','secondary','trunk','motorway','primary_link','secondary_link','trunk_link')
            parking=t.get('service')=='parking_aisle'
            lanes=int(number(t.get('lanes'), 2 if main else 1 if parking or category=='service' else 2))
            width=number(t.get('width'), max(1.4, lanes*3.1+(1.0 if main else 0.5)) if not path else 2.2 if category!='steps' else 1.8)
            tier='walk' if path else ('artery' if main else 'road')
            segment=LineString(pts).intersection(BOUNDS)
            pieces=[segment] if segment.geom_type=='LineString' else getattr(segment,'geoms',[])
            for piece in pieces:
                if piece.geom_type!='LineString' or piece.length<0.5:continue
                roads.append({'id':wid,'p':round_points(piece.coords),'w':round(width,2),'type':tier,'name':t.get('name',''),'lanes':lanes,'parking':parking})
                road_buffers.setdefault(tier,[]).append(piece.buffer(width/2,quad_segs=3))
        if poly is not None and not poly.is_empty:
            land='parking' if t.get('amenity')=='parking' else 'water' if t.get('natural')=='water' or t.get('landuse')=='reservoir' else 'pitch' if t.get('leisure')=='pitch' else 'forest' if t.get('natural')=='wood' or t.get('landuse')=='forest' else 'park' if t.get('landuse') in ('grass','meadow','village_green') or t.get('leisure') in ('park','garden') else ''
            if land:
                area_buffers.setdefault(land,[]).append(poly.intersection(BOUNDS))
    for n in root.findall('node'):
        t=tags(n)
        x,z=nodes[n.get('id')]
        if t.get('natural')=='tree' and BOUNDS.covers(Point(x,z)):
            trees.append([round(x,2),round(z,2)])
    merged_roads={k:[rings(p) for p in polygon_parts(unary_union(v).simplify(.12)) if p.area>1] for k,v in road_buffers.items()}
    merged_areas={k:[rings(p) for p in polygon_parts(unary_union(v).simplify(.18)) if p.area>4] for k,v in area_buffers.items()}
    heights,base=elevations()
    data={'origin':[LON,LAT],'metersPerDegree':[X_SCALE,Y_SCALE],'extent':EXTENT,'grid':GRID,'heights':heights,'elevationBase':base,'boundary':edge,'buildings':buildings,'roads':roads,'roadShapes':merged_roads,'areas':merged_areas,'trees':trees,'landmarks':landmarks}
    (ROOT/'public'/'campus.json').write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False))
    img=Image.new('RGB',(1000,850),'#273b34')
    d=ImageDraw.Draw(img)
    def draw(points):
        return [(int(x+500),int(z+425)) for x,z in points]
    d.line(draw(edge),fill='#b7f1a0',width=2)
    for key,polys in merged_areas.items():
        for p in polys:d.polygon(draw(p[0]),fill=COLORS[key])
    for road in roads:d.line(draw(road['p']),fill='#b2a99b',width=max(1,int(road['w'])))
    for b in buildings:d.polygon(draw(b['p'][0]),fill='#d6d7c7' if b['kind']!='generic' else '#7c887f')
    for l in landmarks:d.text(draw([l['point']])[0],l['id'],fill='black')
    img.save(SOURCE.parent/'gis.png')
    print(len(buildings),'buildings',len(roads),'road segments',len(trees),'mapped trees; elevation range',min(heights),max(heights))
    print(landmarks)

if __name__=='__main__':main()
