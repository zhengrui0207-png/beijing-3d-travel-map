"""Footprint-faithful ancillary roof mesh. Untagged elevations remain estimated.
Run with .dream-loop/urban-venv/bin/python (Shapely). No photo pixels used.
"""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import triangulate
ROOT=Path(__file__).resolve().parents[1]
NAMES={1021040713:'西侧转角附属房',1021040714:'东侧转角附属房',1021040720:'西侧北院附属房',1021040721:'东侧北院附属房'}
result=[]
for r in json.loads((ROOT/'data/urban/records.json').read_text())['records']:
 if r['osmId'] not in NAMES:continue
 cx,cy=r['center'];p=Polygon([((x-cx)*100,(y-cy)*100)for x,y in r['rings'][0]])
 x0,y0,x1,y1=p.bounds
 # Two overlapping gable wings for each concave plan. Their upper envelope makes
 # a continuous intersecting roof; the original polygon clips every roof face.
 if r['osmId']==1021040713:
  elbow=r['rings'][0][-1];ex,ey=(elbow[0]-cx)*100,(elbow[1]-cy)*100
  arms=[(x0,y0,ex,y1,'y'),(x0,y0,x1,ey,'x')]
 elif r['osmId']==1021040714:
  elbow=r['rings'][0][0];ex,ey=(elbow[0]-cx)*100,(elbow[1]-cy)*100
  arms=[(ex,y0,x1,y1,'y'),(x0,y0,x1,ey,'x')]
 else:arms=[(x0,y0,x1,y1,'y')]
 eave=4.1;slope=.72
 def roof(x,y):
  vals=[]
  for a,b,c,d,axis in arms:
   if a-.03<=x<=c+.03 and b-.03<=y<=d+.03:
    width=(c-a if axis=='y' else d-b);q=x if axis=='y'else y;mid=(a+c)/2 if axis=='y'else(b+d)/2
    t=max(0,1-abs(q-mid)/(width/2));vals.append((eave+slope*width/2*t**1.38,axis,t))
  return max(vals,default=(eave,'y',0))
 faces=[];rolls=[];spacing=.26
 # Clip cells before triangulation, so the L-shaped courtyard void stays empty.
 nx=math.ceil((x1-x0)/spacing);ny=math.ceil((y1-y0)/spacing)
 for i in range(nx):
  for j in range(ny):
   a=x0+i*spacing;b=y0+j*spacing;c=min(x1,a+spacing);d=min(y1,b+spacing);cut=p.intersection(box(a,b,c,d))
   if cut.is_empty or cut.area<1e-8:continue
   for tri in triangulate(cut):
    if not cut.covers(tri.representative_point()):continue
    pts=list(tri.exterior.coords)[:-1]
    faces.append([[x,y,roof(x,y)[0]]for x,y in pts])
   h,axis,t=roof((a+c)/2,(b+d)/2)
   line=LineString([(a,(b+d)/2),(c,(b+d)/2)])if axis=='y'else LineString([((a+c)/2,b),((a+c)/2,d)])
   segment=line.intersection(p)
   if segment.geom_type=='LineString'and segment.length>.015:
    points=list(segment.coords);rolls.append({'points':[[x,y,roof(x,y)[0]+.025]for x,y in points],'edge':t<.12})
 wall=p.buffer(-.42,join_style='mitre');wallring=list(wall.exterior.coords)[:-1]
 result.append({'record':r,'name':NAMES[r['osmId']],'roof':faces,'rolls':rolls,'walls':wallring,'heightMetresEstimated':max(v[2]for f in faces for v in f)-1.1,'eave':eave,'arms':arms,'roofArea':p.area,'footprintArea':p.area})
out=ROOT/'data/terrain/beihai-annexes.json';out.write_text(json.dumps(result,ensure_ascii=False));print(json.dumps({'buildings':len(result),'roofTriangles':sum(len(x['roof'])for x in result),'bytes':out.stat().st_size}))
