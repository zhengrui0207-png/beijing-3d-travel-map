"""Restore mapped urban land cover from the unfiltered cached OSM XML tiles.
No new roads/addresses: sidewalk widths and surface colours are illustrative.
"""
from pathlib import Path
import json,xml.etree.ElementTree as ET,collections,math
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1]
ns={'__file__':str(ROOT/'scripts/prepare_geometry.py')};src=(ROOT/'scripts/prepare_geometry.py').read_text();exec(src[:src.index('water=unary_union(waters)')],ns)
polygon,clip,xy,polys,num=map(ns.get,['polygon','clip','xy','polys','num'])
nodes={};ways={};relations={}
for path in sorted((ROOT/'data/tiles').glob('*.osm')):
 for e in ET.parse(path).getroot():
  if e.tag=='node':nodes[int(e.get('id'))]={'lon':float(e.get('lon')),'lat':float(e.get('lat'))}
  elif e.tag=='way':ways[int(e.get('id'))]=e
  elif e.tag=='relation':relations[int(e.get('id'))]=e

def tags(e):return {t.get('k'):t.get('v')for t in e.findall('tag')}
def geometry(e):
 ids=[int(n.get('ref'))for n in e.findall('nd')]
 return [nodes[i]for i in ids]if all(i in nodes for i in ids)else []
def record(e):
 t=tags(e);r={'id':int(e.get('id')),'type':e.tag,'tags':t}
 if e.tag=='way':r['geometry']=geometry(e)
 else:r['members']=[{'type':'way','ref':int(m.get('ref')),'role':m.get('role',''),'geometry':geometry(ways[int(m.get('ref'))])}for m in e.findall('member')if m.get('type')=='way'and int(m.get('ref'))in ways]
 return r

def classify(t):
 if any(k in t for k in ['building','building:part'])or t.get('location')=='underground'or t.get('tunnel')=='yes'or t.get('covered')=='yes'or str(t.get('layer','0')).startswith('-'):return None
 land=t.get('landuse');leisure=t.get('leisure');surface=t.get('surface')
 if land in ['grass','forest','meadow','flowerbed','orchard','village_green']or t.get('natural')in ['wood','scrub','grassland']or leisure in ['park','garden']:return 'green'
 if t.get('amenity')=='parking'and t.get('parking')not in ['underground','multi-storey']:return 'parking'
 if t.get('highway')=='pedestrian'and t.get('area')=='yes':return 'paved'
 if surface in ['paving_stones','cobblestone','sett','paved','concrete']:return 'paved'
 if land=='residential':return 'residential'
 if land in ['commercial','retail','governmental','civic_admin']:return 'commercial'
 if land in ['construction','brownfield','industrial','railway','garages']:return 'service'
 if t.get('amenity')in ['school','university','college','hospital']:return 'campus'
 return None
records=[record(e)for e in [*ways.values(),*relations.values()]if classify(tags(e))]
parents=collections.defaultdict(set)
for r in records:
 for m in r.get('members',[]):
  if m['role']!='inner':parents[m['ref']].add(classify(r['tags']))
groups=collections.defaultdict(list);sources=[]
for r in records:
 kind=classify(r['tags'])
 if r['type']=='way'and kind in parents[r['id']]:continue
 g=polygon(r)
 if g.is_empty or g.area<.0001:continue
 groups[kind].append(g);sources.append({'osmType':r['type'],'osmId':r['id'],'name':r['tags'].get('name',''),'kind':kind,'areaM2':round(g.area*10000,1)})
print('Mapped area sources',len(sources),dict(collections.Counter(s['kind']for s in sources)),flush=True)
water=unary_union(ns['waters']);existing_green=unary_union(ns['parks']);green=unary_union(groups['green']).union(existing_green).difference(water)
# Match the base map's carriageway widths, excluding bridge/tunnel structures.
widths={'motorway':22,'trunk':22,'primary':20,'secondary':16,'tertiary':11,'residential':7,'unclassified':6,'service':4,'pedestrian':5,'footway':2.2,'path':1.8,'cycleway':2.5,'living_street':5}
road_surfaces=[];walk_envelopes=[];walk_sources=[]
for e,line in ns['roads']:
 t=e['tags'];h=t['highway'];width=max(1.5,min(45,num(t.get('width'),widths.get(h,widths.get(h.replace('_link',''),5)*.7))))
 road=line.buffer(width/200,cap_style=2,join_style=2).intersection(clip);road_surfaces.append(road)
 if h not in ['primary','secondary','tertiary','residential','unclassified','living_street']or t.get('bridge')=='yes'or t.get('tunnel')=='yes'or t.get('sidewalk') in ['no','none']:continue
 # Fixed 1.6 m example where OSM has no sidewalk width. Do not imply routing availability.
 walk_envelopes.append(line.buffer(width/200+.016,cap_style=2,join_style=2).intersection(clip));walk_sources.append(e['id'])
roads=unary_union(road_surfaces)
# Use the actual rendered road triangles as a second exclusion, not only the
# reconstructed centre-line widths, which can differ from the rendered mesh.
base_geometry=json.loads((ROOT/'data/geometry.json').read_text())
rendered_roads=[]
for layer in base_geometry['layers']:
 if layer['name']in ['roads_major','roads_local','paths']:
  rendered_roads.extend(Polygon([layer['vertices'][i][:2]for i in face])for face in layer['faces'])
roads=roads.union(unary_union(rendered_roads))
del base_geometry,rendered_roads
# Keep precise palace/landmark paving and island relief as the authoritative surfaces.
protected=[box(*s['bounds']).buffer(.005)for s in json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())['assets']]
protected += [box(*xy(116.3864,39.9120),*xy(116.3955,39.9212))]
field=json.loads((ROOT/'public/assets/beihai-terrain/heightfield.json').read_text());protected.append(Polygon(field['ring']))
protected=unary_union(protected)
blocked=water.union(protected)
cover={};occupied=blocked.union(green).union(roads)
for kind in ['paved','parking','campus','commercial','residential','service']:
 area=unary_union(groups[kind]).difference(occupied);cover[kind]=area;occupied=occupied.union(area)
cover['green']=unary_union(groups['green']).difference(existing_green.union(blocked).union(roads))
# Sidewalk bands never cover known buildings, water, mapped greens, or carriageways.
walk=unary_union(walk_envelopes).difference(roads.union(blocked).union(green))
footprints=[]
for name in ['records.json','overture-fill-records.json']:
 footprints += [Polygon(r['rings'][0],r['rings'][1:])for r in json.loads((ROOT/'data/urban'/name).read_text())['records']]
ftree=STRtree(footprints)
# Triangulate and subtract buildings per 1 km cell to bound memory.
meshes=[];stats=collections.Counter();sidewalk_total=0
minx,miny,maxx,maxy=clip.bounds
for ix in range(math.floor(minx/10),math.ceil(maxx/10)):
 for iy in range(math.floor(miny/10),math.ceil(maxy/10)):
  cell=box(ix*10,iy*10,(ix+1)*10,(iy+1)*10).intersection(clip)
  for kind,g in cover.items():
   piece=g.intersection(cell)
   if piece.is_empty:continue
   verts=[];faces=[];z=.00825 if kind!='green'else .0084
   for p in polys(piece):
    for tri in constrained_delaunay_triangles(p).geoms:
     pts=list(tri.exterior.coords)[:3]
     if (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])<0:pts.reverse()
     i=len(verts);verts.extend((x,y,z)for x,y in pts);faces.append([i,i+1,i+2])
   if faces:meshes.append({'name':f'{kind} {ix} {iy}','kind':kind,'vertices':verts,'faces':faces});stats[kind+'M2']+=round(piece.area*10000)
  piece=walk.intersection(cell)
  if piece.is_empty:continue
  near=[footprints[int(i)].buffer(.0003)for i in ftree.query(piece,predicate='intersects')]
  if near:piece=piece.difference(unary_union(near))
  verts=[];faces=[]
  for p in polys(piece):
   if p.area<.000002:continue
   for tri in constrained_delaunay_triangles(p).geoms:
    pts=list(tri.exterior.coords)[:3]
    if (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])<0:pts.reverse()
    i=len(verts);verts.extend((x,y,.0112)for x,y in pts);faces.append([i,i+1,i+2])
   from shapely.geometry.polygon import orient
   p=orient(p,sign=1)
   for ring in [p.exterior,*p.interiors]:
    pts=list(ring.coords)[:-1]
    for a,b in zip(pts,pts[1:]+pts[:1]):
     i=len(verts);verts.extend([(a[0],a[1],.0098),(b[0],b[1],.0098),(b[0],b[1],.0112),(a[0],a[1],.0112)]);faces.append([i,i+1,i+2,i+3])
  if faces:meshes.append({'name':f'sidewalk {ix} {iy}','kind':'sidewalk','vertices':verts,'faces':faces});stats['sidewalkM2']+=round(piece.area*10000)
 print('Column',ix,'meshes',len(meshes),flush=True)
result={'meshes':meshes,'sources':sources,'stats':dict(stats),'sidewalkRoadIds':walk_sources,'source':'Cached official OSM XML map tiles, same snapshot as existing city; © OpenStreetMap contributors / ODbL 1.0','method':'Mapped land-use polygons and explicit paved/parking areas. Colours and surface patterns are illustrative. Sidewalks are inferred 1.6 m bands beside selected road classes, not verified accessible pedestrian routes.'}
(ROOT/'data/urban-ground/geometry.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
print(json.dumps({'meshes':len(meshes),'triangles':sum(sum(len(f)-2 for f in m['faces'])for m in meshes),'stats':dict(stats)}),flush=True)
