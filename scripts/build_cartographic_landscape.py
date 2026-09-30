"""Decorative planting constrained to cached OSM green areas and road verges.
Not surveyed tree locations. No new geographic features or road connections.
"""
import json, math, random, pathlib, collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
g=json.loads((ROOT/'data/geometry.json').read_text()); random.seed(930)
layers={x['name']:x for x in g['layers']}; cell=.8; grid=collections.defaultdict(list)
def triangles(layer, roofs=False):
    v=layer['vertices']
    for f in layer['faces']:
        if roofs and (len(f)!=3 or max(v[i][2] for i in f)-min(v[i][2] for i in f)>.001):continue
        for i in range(1,len(f)-1):yield [v[f[0]][:2],v[f[i]][:2],v[f[i+1]][:2]]
def inside(x,y,t):
    signs=[(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]) for a,b in zip(t,t[1:]+t[:1])]
    return min(signs)>=-1e-7 or max(signs)<=1e-7
def key(x,y):return math.floor(x/cell),math.floor(y/cell)
for name in ['buildings_low','buildings_tall','palace_buildings','water','roads_major','roads_local','paths']:
    for t in triangles(layers[name],name.startswith(('buildings','palace'))):
        x0,y0=key(min(p[0] for p in t),min(p[1] for p in t));x1,y1=key(max(p[0] for p in t),max(p[1] for p in t))
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):grid[x,y].append(t)
manifest=json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())
masks=[a['bounds'] for a in manifest['assets']]
pm=json.loads((ROOT/'public/assets/palace/manifest.json').read_text());masks.append(pm['replacementBounds'])
plants=[]; used=set()
def add(x,y,kind=0):
    if abs(x)>59 or abs(y)>55:return
    if any(a-.08<x<c+.08 and b-.08<y<d+.08 for a,b,c,d in masks):return
    k=round(x/.16),round(y/.16)
    if k in used or any(inside(x,y,t) for t in grid[key(x,y)]):return
    used.add(k);plants.append([round(x,4),round(y,4),round(random.uniform(.115,.185),3),round(random.uniform(.23,.38),3),random.randrange(8)])
for t in triangles(layers['parks']):
    a,b,c=t; area=abs((b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1]))/2
    count=int(area*12+random.random())
    for _ in range(count):
        u=math.sqrt(random.random());v=random.random();add((1-u)*a[0]+u*(1-v)*b[0]+u*v*c[0],(1-u)*a[1]+u*(1-v)*b[1]+u*v*c[1])
raw=json.loads((ROOT/'data/osm_beijing.json').read_text());sx=1113.2*math.cos(math.radians(39.915));sy=1113.2
marks=[];widths={'trunk':22,'primary':20,'secondary':16,'tertiary':11,'residential':7}
for e in raw['elements']:
    tag=e.get('tags',{});kind=tag.get('highway');geo=e.get('geometry',[])
    if kind not in widths or len(geo)<2 or tag.get('tunnel')=='yes':continue
    pts=[((p['lon']-116.415)*sx,(p['lat']-39.915)*sy) for p in geo]
    width=widths[kind]/100
    try:width=float(tag.get('width',width*100))/100
    except:pass
    width=min(.45,max(.04,width))
    for a,b in zip(pts,pts[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<.03:continue
        nx,ny=-dy/length,dx/length
        for i in range(int(length/.3)):
            f=(i+.5)*.3/length;x,y=a[0]+dx*f,a[1]+dy*f
            for sign in [-1,1]:add(x+nx*(width/2+.13)*sign,y+ny*(width/2+.13)*sign,1)
        if kind in ['trunk','primary','secondary','tertiary']:
            for i in range(int(length/.15)):
                f=(i+.5)*.15/length;x,y=a[0]+dx*f,a[1]+dy*f
                if abs(x)<59 and abs(y)<55:marks.append([round(x,4),round(y,4),round(math.atan2(dy,dx),5),.06])
result={'trees':plants,'roadMarks':marks,'notes':'Illustrative planting within mapped green areas / verges; approximate road center dashes, not lane survey. © OpenStreetMap contributors.'}
(ROOT/'public/assets/cartographic/landscape.json').write_text(json.dumps(result,separators=(',',':')))
print('trees',len(plants),'road marks',len(marks))
