"""Independent spatial invariants over every inferred sidewalk top triangle."""
from pathlib import Path
import json,numpy as np
from shapely.geometry import Polygon,Point
from shapely.strtree import STRtree
from shapely import points,union_all
ROOT=Path(__file__).resolve().parents[1]
b=json.loads((ROOT/'data/urban-ground/geometry.json').read_text());footprints=[]
for filename in ['records.json','overture-fill-records.json']:
 footprints.extend(Polygon(r['rings'][0],r['rings'][1:]) for r in json.loads((ROOT/'data/urban'/filename).read_text())['records'])
# Original cached map's water triangles are independent of the new surface script.
old=json.loads((ROOT/'data/geometry.json').read_text());water=[];roads=[]
for m in old['layers']:
 if m['name']not in ['water','roads_major','roads_local','paths']:continue
 target=water if m['name']=='water'else roads
 for f in m['faces']:target.append(Polygon([m['vertices'][i][:2]for i in f]))
centres=[];top_area=0;all_area={}
for m in b['meshes']:
 area=0
 for f in m['faces']:
  if len(f)!=3:continue
  a,c,d=[m['vertices'][i]for i in f];area+=abs((c[0]-a[0])*(d[1]-a[1])-(d[0]-a[0])*(c[1]-a[1]))/2
  if m['kind']=='sidewalk':centres.append([(a[0]+c[0]+d[0])/3,(a[1]+c[1]+d[1])/3]);assert all(abs(p[2]-.0112)<1e-10 for p in [a,c,d])
 all_area[m['kind']]=all_area.get(m['kind'],0)+area*10000
p=points(np.asarray(centres));counts={}
for name,geoms in [('buildings',footprints),('water',water),('roads',roads)]:
 hits=STRtree(geoms).query(p,predicate='within');counts[name]=len(hits[0])
 if len(hits[0]):
  union=union_all(geoms);depths=[float(p[int(i)].distance(union.boundary))for i in set(hits[0])];print('Overlap depths in metres',name,sorted(v*100 for v in depths),flush=True)
 assert not len(hits[0]),(name,len(hits[0]))
for kind,value in all_area.items():assert abs(value-b['stats'][kind+'M2'])<145,(kind,value,b['stats'][kind+'M2'])
report={'sidewalkTopTrianglesChecked':len(centres),'centroidsInsideExcludedFeatures':counts,'areaM2':{k:round(v,1)for k,v in all_area.items()}}
(ROOT/'output/urban-ground/spatial-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
