"""Local SRTM-derived terrain; coastline tapered to match flat-city reference.
Buildings use level pads. Terrain is a coarse visual interpretation, not a survey.
"""
import json,math,statistics
from pathlib import Path
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
import beihai_stairs as stair_builder
import beihai_platforms as platform_builder
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/beihai-terrain';OUT.mkdir(exist_ok=True)
SX=111320*math.cos(math.radians(39.915))/100;SY=1113.2
ring=json.loads((ROOT/'data/terrain/beihai-island.json').read_text());island=Polygon(ring);bounds=island.bounds
samples=json.loads((ROOT/'data/terrain/beihai-elevations.json').read_text())
def elevation(x,y):
 lo=x/SX+116.415;la=y/SY+39.915
 px=((lo+180)/360*16384-13488)*256;py=((1-math.asinh(math.tan(math.radians(la)))/math.pi)/2*16384-6207)*256
 ix,iy=int(px),int(py);fx,fy=px-ix,py-iy
 return samples[iy][ix]*(1-fx)*(1-fy)+samples[iy][ix+1]*fx*(1-fy)+samples[iy+1][ix]*(1-fx)*fy+samples[iy+1][ix+1]*fx*fy
shore=[elevation(*island.exterior.interpolate(i/100,normalized=True).coords[0])for i in range(100)]
baseline=statistics.median(shore)
def raw(x,y):
 p=Point(x,y)
 if not island.covers(p):return 0
 d=p.distance(island.boundary);f=min(1,d/.24);f=f*f*(3-2*f)
 return max(0,elevation(x,y)-baseline)*f/100
rows=json.loads((ROOT/'data/urban/records.json').read_text())['records']+json.loads((ROOT/'data/urban/overture-fill-records.json').read_text())['records']
pads=[]
for r in rows:
 if str(r['id']).split('/')[-2:-1] in [['561193504'],['1021040719']]:continue
 x,y=r['center']
 if not island.contains(Point(x,y)):continue
 g=Polygon(r['rings'][0],r['rings'][1:]);h=raw(x,y)
 pads.append({'id':r['id'],'bounds':list(g.buffer(.012).bounds),'height':h,'ring':list(g.exterior.coords),'poly':g})
# The tower and its small front shrine were removed from ordinary-building records.
es=json.loads((ROOT/'data/osm_beijing.json').read_text())['elements']
for id in [561193504,1021040719]:
 e=next(e for e in es if e['type']=='way'and e['id']==id);g=Polygon([((v['lon']-116.415)*SX,(v['lat']-39.915)*SY)for v in e['geometry']]);c=g.centroid
 pads.append({'id':str(id),'bounds':list(g.buffer(.012).bounds),'height':raw(c.x,c.y),'ring':list(g.exterior.coords),'poly':g})
def height(x,y):
 h=raw(x,y);p=Point(x,y)
 if not h:return 0
 for pad in pads:
  a,b,c,d=pad['bounds']
  if a-.03<x<c+.03 and b-.03<y<d+.03:
   distance=p.distance(pad['poly'])
   if distance<.012:return pad['height']
   if distance<.042:
    f=(distance-.012)/.03;f=f*f*(3-2*f);return pad['height']*(1-f)+h*f
 return h
# Real stair axes keep their counts, while vertical dimensions remain estimated.
building_height=height
terraces=platform_builder.prepare(es,pads,SX,SY)
terracemask=unary_union([t['_poly']for t in terraces])
def terrace_height(x,y):return platform_builder.grade(x,y,building_height(x,y),terraces)
stairs=stair_builder.prepare(es,SX,SY,terrace_height)
stairmask=unary_union([s['_poly']for s in stairs])
def height(x,y):return stair_builder.grade(x,y,terrace_height(x,y),stairs)
stair_meshes,stair_specs=stair_builder.mesh(stairs)
platform_meshes,court_spec,courtmask=platform_builder.mesh(terraces,stairs,building_height,rows)
# Real OSM path/road polygons are draped over the same sampled surface.
ns={'__file__':str(ROOT/'scripts/prepare_geometry.py')};s=(ROOT/'scripts/prepare_geometry.py').read_text();exec(s[:s.index('water=unary_union(waters)')],ns)
widths={'motorway':22,'trunk':22,'primary':20,'secondary':16,'tertiary':11,'residential':7,'unclassified':6,'service':4,'pedestrian':5,'footway':2.2,'path':1.8,'cycleway':2.5,'living_street':5};surfaces=[]
for e,g in ns['roads']:
 if not g.intersects(island) or e['id']in stair_builder.IDS:continue
 h=e['tags'].get('highway');width=ns['num'](e['tags'].get('width'),widths.get(h,5));key='paths'if h in ['footway','path','pedestrian','steps','cycleway']else'roads_local'
 surfaces.append((key,g.buffer(width/200,cap_style=2,join_style=2).intersection(island).difference(stairmask).difference(terracemask).difference(courtmask)))
paths={key:unary_union([p for k,p in surfaces if k==key])for key in ['paths','roads_local']}
step=.04;x0,y0,x1,y1=bounds;nx=math.ceil((x1-x0)/step)+1;ny=math.ceil((y1-y0)/step)+1
grid=[[height(x0+i*step,y0+j*step)for i in range(nx)]for j in range(ny)]
meshes={'terrain':[],'paths':[],'roads_local':[]}
def triangles(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return list(constrained_delaunay_triangles(g).geoms)
 return [t for p in getattr(g,'geoms',[])for t in triangles(p)]
for j in range(ny-1):
 for i in range(nx-1):
  cell=box(x0+i*step,y0+j*step,x0+(i+1)*step,y0+(j+1)*step).intersection(island).difference(courtmask)
  if cell.is_empty:continue
  surfaces=[('terrain',cell.difference(stairmask).difference(terracemask),None),('terrain',cell.intersection(stairmask),None),('terrain',cell.intersection(terraces[0]['_poly']).difference(stairmask),terraces[0]['heightOffset']),('terrain',cell.intersection(terraces[1]['_poly']).difference(terraces[0]['_poly']).difference(stairmask),terraces[1]['heightOffset']),*[(k,p.intersection(cell),None)for k,p in paths.items()]]
  for key,geom,flat in surfaces:
   for t in triangles(geom):
    verts=[[x,y,.0105+(height(x,y)if flat is None else flat)+(.002 if key!='terrain'else 0)]for x,y in list(t.exterior.coords)[:3]];meshes[key].append(verts)
meshes.update(stair_meshes)
meshes.update(platform_meshes)
for p in pads:p.pop('poly')
manifest={'origin':[x0,y0],'step':step,'grid':grid,'ring':ring,'bounds':bounds,'pads':pads,'stairs':stair_specs,'terraces':[{k:v for k,v in t.items()if not k.startswith('_')}for t in terraces],'courtyard':court_spec,'baselineElevationMetres':baseline,'source':'Mapzen Terrain Tiles (AWS) / SRTM courtesy of USGS','resolutionNote':'Underlying SRTM resolution is approximately 30m; 4m output tessellation is interpolation, not new survey precision. Shoreline regraded to the flat-city datum; building pads flattened.','towerGroundHeight':.011+next(p['height']for p in pads if p['id']=='561193504')}
(OUT/'heightfield.json').write_text(json.dumps(manifest,separators=(',',':')))
(ROOT/'data/terrain/beihai-meshes.json').write_text(json.dumps(meshes,separators=(',',':')))
print({'bounds':bounds,'pads':len(pads),'triangles':{k:len(v)for k,v in meshes.items()},'baseline':baseline,'towerGroundHeight':manifest['towerGroundHeight'],'maxHeight':max(map(max,grid))})
