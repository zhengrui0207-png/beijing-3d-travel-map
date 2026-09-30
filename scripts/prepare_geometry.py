"""Project OSM geometry to a local metric plane; preserve footprints and holes."""
import json, math, pathlib, re, random
from collections import defaultdict, Counter
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union, polygonize
from shapely import make_valid, constrained_delaunay_triangles
from shapely.strtree import STRtree

ROOT=pathlib.Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/'data/osm_beijing.json').read_text())
SX=111320*math.cos(math.radians(39.915))/100
SY=111320/100
def xy(lon,lat): return ((lon-116.415)*SX,(lat-39.915)*SY)
W,H=.14*SX,.1*SY
clip=box(-W/2,-H/2,W/2,H/2)
def coords(gs): return [xy(p['lon'],p['lat']) for p in gs if 'lon' in p]
def polys(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    if hasattr(g,'geoms'):return [p for s in g.geoms for p in polys(s)]
    return []
def polygon(e):
    try:
        if e['type']=='way':
            c=coords(e.get('geometry',[]))
            return make_valid(Polygon(c)).intersection(clip) if len(c)>3 and c[0]==c[-1] else Polygon()
        outer=[];inner=[]
        for m in e.get('members',[]):
            c=coords(m.get('geometry',[]))
            if len(c)>1:(inner if m.get('role')=='inner' else outer).append(LineString(c))
        outer=unary_union(list(polygonize(unary_union(outer))))
        inner=unary_union(list(polygonize(unary_union(inner))))
        return make_valid(outer.difference(inner)).intersection(clip)
    except Exception:return Polygon()

layers={}
def mesh(name,material):
    if name not in layers:layers[name]={'name':name,'material':material,'vertices':[],'faces':[]}
    return layers[name]
def face(m,vs):
    i=len(m['vertices']);m['vertices'].extend([[round(c,5) for c in v] for v in vs]);m['faces'].append(list(range(i,i+len(vs))))
def surface(m,g,z):
    for p in polys(g):
        if p.area<.00001:continue
        for t in constrained_delaunay_triangles(p).geoms:
            c=list(t.exterior.coords)[:3]
            if (c[1][0]-c[0][0])*(c[2][1]-c[0][1])-(c[1][1]-c[0][1])*(c[2][0]-c[0][0])<0:c.reverse()
            face(m,[(x,y,z) for x,y in c])
def extrude(m,g,top,bottom=.075):
    for p in polys(g):
        surface(m,p,top)
        from shapely.geometry.polygon import orient
        p=orient(p,sign=1.0)
        for r in [p.exterior,*p.interiors]:
            c=list(r.coords)
            for a,b in zip(c,c[1:]):face(m,[(a[0],a[1],bottom),(b[0],b[1],bottom),(b[0],b[1],top),(a[0],a[1],top)])
def num(s,default):
    try:return float(re.search(r'[\d.]+',str(s)).group())
    except:return default

elements=raw['elements']
# Relation geometry includes its members; avoid drawing both versions.
members={m['ref'] for e in elements if e['type']=='relation' for m in e.get('members',[]) if m.get('type')=='way'}
# A building used as a hole in a pedestrian plaza is still a building.
# Suppress only outlines represented by a parent building multipolygon.
building_members={m['ref'] for e in elements if e['type']=='relation' and ('building' in e.get('tags',{}) or 'building:part' in e.get('tags',{})) for m in e.get('members',[]) if m.get('type')=='way' and m.get('role','outer')!='inner'}
parks=[];waters=[];buildings=[];roads=[]
for e in elements:
    t=e.get('tags',{})
    if 'highway' in t:
        c=coords(e.get('geometry',[]))
        if len(c)>1:
            g=LineString(c).intersection(clip)
            if not g.is_empty:roads.append((e,g))
    if 'building' in t or 'building:part' in t:
        if e['type']=='way' and e['id'] in building_members:continue
        g=polygon(e)
        if not g.is_empty:buildings.append((e,g))
    elif e['type']=='way' and e['id'] in members:continue
    elif t.get('natural')=='water' or 'water' in t:
        g=polygon(e)
        if not g.is_empty:waters.append(g)
    elif t.get('leisure') in ['park','garden','pitch'] or t.get('landuse') in ['grass','forest','recreation_ground'] or t.get('natural')=='wood':
        g=polygon(e)
        if not g.is_empty:parks.append(g)
    elif 'waterway' in t:
        c=coords(e.get('geometry',[]))
        if len(c)>1:waters.append(LineString(c).buffer(num(t.get('width'),12)/200).intersection(clip))

water=unary_union(waters); park=unary_union(parks).difference(water)
print('Parsed',len(buildings),'buildings',len(roads),'roads',flush=True)
surface(mesh('parks','park'),park,.028)
surface(mesh('water','water'),water,.045)
road_buffers=[]
widths={'motorway':22,'trunk':22,'primary':20,'secondary':16,'tertiary':11,'residential':7,'unclassified':6,'service':4,'pedestrian':5,'footway':2.2,'path':1.8,'cycleway':2.5,'living_street':5}
for e,line in roads:
    t=e['tags'];h=t['highway'];major=h in ['motorway','trunk','primary','secondary','motorway_link','trunk_link','primary_link','secondary_link']
    width=num(t.get('width'),widths.get(h,widths.get(h.replace('_link',''),5)*.7))
    width=max(1.5,min(width,45))
    g=line.buffer(width/200,cap_style=2,join_style=2).intersection(clip)
    foot=h in ['footway','path','pedestrian','cycleway','track']
    surface(mesh('paths' if foot else 'roads_major' if major else 'roads_local','path' if foot else 'road'),g,.052 if foot else .066)
    road_buffers.append(g)

landmarks=[
 {'id':'forbidden','name':'故宫','en':'THE FORBIDDEN CITY','lon':116.3972,'lat':39.9180,'height':38,'span':17,'description':'沿中轴线展开的宫殿院落。保留地图中的建筑轮廓，以简化重檐屋顶呈现紫禁城。'},
 {'id':'tiananmen','name':'天安门','en':'TIAN’ANMEN','lon':116.39747,'lat':39.90872,'height':34,'span':10,'description':'长安街与北京中轴线交汇处的城楼，以城台、门洞与重檐屋顶构成简化模型。'},
 {'id':'cctv','name':'央视大楼','en':'CCTV HEADQUARTERS','lon':116.45778,'lat':39.91517,'height':234,'span':14,'description':'倾斜双塔与空中悬挑连接形成连续环。模型突出外轮廓与斜交网格，便于从鸟瞰辨认。'},
 {'id':'tiantan','name':'天坛','en':'TEMPLE OF HEAVEN','lon':116.40657,'lat':39.88222,'height':38,'span':17,'description':'祈年殿位于天坛北部。圆形三重檐、层叠台基与大片绿地构成鲜明的城市节点。'},
 {'id':'beihai','name':'北海公园','en':'BEIHAI PARK','lon':116.3838,'lat':39.9255,'height':32,'span':17,'description':'真实水域轮廓包围琼华岛，浅蓝湖面与绿色园林在密集城市肌理中形成留白。'},
 {'id':'guomao','name':'国贸 · 中国尊','en':'BEIJING CBD','lon':116.46805,'lat':39.90285,'height':528,'span':18,'description':'以中国尊的收腰曲面体块标记 CBD 天际线，与央视大楼形成东西城市视线。'}]
landmark_osm={'tiananmen':8847697,'cctv':7820447,'tiantan':43921139,'guomao':599547918,'beihai':366464114}
for l in landmarks:
    if l['id']=='forbidden':l['lon'],l['lat']=116.3908,39.9164
    elif l['id'] in landmark_osm:
        e=next(e for e in elements if e['id']==landmark_osm[l['id']])
        c=polygon(e).centroid
        if not c.is_empty:l['lon'],l['lat']=c.x/SX+116.415,c.y/SY+39.915
        l['osm_id']=str(e['id']);l['osm_type']=e['type']
    l['x'],l['y']=xy(l['lon'],l['lat'])
custom_masks=[]
for l,r in [(landmarks[1],.75),(landmarks[2],1.55),(landmarks[3],.34),(landmarks[5],.48)]:custom_masks.append(Point(l['x'],l['y']).buffer(r))
parts_list=[g for e,g in buildings if 'building:part' in e.get('tags',{})]
parts_tree=STRtree(parts_list)
stats=Counter();building_polys=[];palace_roofs=[]
for e,g in buildings:
    t=e['tags'];cent=g.centroid
    if any(mask.contains(cent) for mask in custom_masks):continue
    if 'building:part' not in t:
        nearby=[parts_list[int(i)] for i in parts_tree.query(g,predicate='intersects')]
        if nearby and unary_union(nearby).intersection(g).area>g.area*.65:continue
    lon=cent.x/SX+116.415;lat=cent.y/SY+39.915
    palace=116.3864<lon<116.3955 and 39.9120<lat<39.9212
    historical=116.365<lon<116.435 and 39.9<lat<39.95
    kind=t.get('building','yes')
    default=7 if historical else 15
    if kind in ['apartments','residential','dormitory']:default=18
    if kind in ['commercial','office','hotel']:default=32
    if kind in ['industrial','warehouse','school','retail']:default=12
    if kind in ['garage','garages','shed','roof']:default=3.5
    if palace:
        default={'太和殿':26,'中和殿':16,'保和殿':20,'乾清宫':20,'交泰殿':17,'坤宁宫':16,'午门':20,'神武门':18}.get(t.get('name',''),8)
    if 'height' in t:height=num(t['height'],default);stats['height_tag']+=1
    elif 'building:levels' in t:height=num(t['building:levels'],default/3)*3.2;stats['levels_tag']+=1
    else:height=default;stats['estimated_height']+=1
    height=max(2,min(height,550))/100
    name='palace_buildings' if palace else 'buildings_tall' if height>.65 else 'buildings_low'
    material='palace_wall' if palace else 'building'
    extrude(mesh(name,material),g.simplify(.005,preserve_topology=True),height+.075)
    building_polys.append(g);stats['buildings']+=1
    if palace and g.area>.025:
        # Derive each low-poly roof from its actual mapped building footprint.
        rect=g.minimum_rotated_rectangle
        cs=list(rect.exterior.coords)[:4]
        a,b,c,d=cs;ab=math.dist(a,b);bc=math.dist(b,c)
        if ab<bc:a,b,c,d=b,c,d,a;ab,bc=bc,ab
        if ab>2.5 or bc>1.0:continue
        cx,cy=g.centroid.x,g.centroid.y
        cs=[(cx+(x-cx)*1.06,cy+(y-cy)*1.06) for x,y in [a,b,c,d]]
        a,b,c,d=cs;z=height+.08;rise=min(.11,bc*.38)
        r1=((a[0]+d[0])*.5+(b[0]-a[0])*.18,(a[1]+d[1])*.5+(b[1]-a[1])*.18,z+rise)
        r2=((b[0]+c[0])*.5-(b[0]-a[0])*.18,(b[1]+c[1])*.5-(b[1]-a[1])*.18,z+rise)
        m=mesh('palace_roofs','roof')
        face(m,[(*a,z),(*b,z),r2,r1]);face(m,[(*b,z),(*c,z),r2]);face(m,[(*c,z),(*d,z),r1,r2]);face(m,[(*d,z),(*a,z),r1])

# Sparse faceted tree canopies, generated only inside mapped green areas.
random.seed(26)
print('Building meshes ready',dict(stats),flush=True)
occupied_tree=STRtree(building_polys+road_buffers)
plantable=park
m=mesh('trees','tree');mt=mesh('tree_trunks','trunk')
trees=0
for p in polys(plantable):
    if p.area<.04:continue
    count=min(250,int(p.area*1.15));bounds=p.bounds
    for _ in range(count):
        x=random.uniform(bounds[0],bounds[2]);y=random.uniform(bounds[1],bounds[3])
        point=Point(x,y)
        if not p.contains(point):continue
        if len(occupied_tree.query(point.buffer(.045),predicate='intersects')):continue
        r=random.uniform(.06,.105);h=random.uniform(.11,.20)
        ring=[(x+r*math.cos(i*math.tau/6),y+r*math.sin(i*math.tau/6),.08+h*.5) for i in range(6)]
        for i in range(6):face(m,[ring[i],ring[(i+1)%6],(x,y,.08+h)])
        for i in range(6):face(m,[(x,y,.065),ring[(i+1)%6],ring[i]])
        trees+=1

stats.update({'road_segments':len(roads),'park_polygons':len(polys(park)),'water_polygons':len(polys(water)),'trees':trees})
out={'width':W,'height':H,'origin':[116.415,39.915],'units':'100 metres','layers':list(layers.values()),'landmarks':landmarks,'stats':dict(stats)}
(ROOT/'data/geometry.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
(ROOT/'public/assets').mkdir(parents=True,exist_ok=True)
(ROOT/'public/assets/metadata.json').write_text(json.dumps({k:v for k,v in out.items() if k!='layers'},ensure_ascii=False,indent=2))
print(json.dumps(stats,ensure_ascii=False));print('Meshes',len(layers),'Vertices',sum(len(m['vertices']) for m in layers.values()),flush=True)
