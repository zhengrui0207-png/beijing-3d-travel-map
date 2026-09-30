import json,math
from pathlib import Path
from shapely.geometry import Polygon,box,LineString
from shapely.geometry.polygon import orient
from shapely.ops import triangulate
R=Path(__file__).resolve().parents[1];rs=json.loads((R/'data/palace-layout.json').read_text())['records'];rs=[r for r in rs if r.get('owner')=='午门'];main=next(r for r in rs if r['id']==638156994);cx,cy=main['center'];a=math.atan2(-main['u'][1],-main['u'][0]);ca,sa=math.cos(a),math.sin(a)
def loc(p):
 x,y=(p[0]-cx)*100,(p[1]-cy)*100;return [x*ca+y*sa,-x*sa+y*ca]
sx=111320*math.cos(math.radians(39.915))/100;sy=111320/100
raw=json.loads((R/'data/osm_beijing.json').read_text());p=next(e for e in raw['elements']if e['id']==638156366)
poly=Polygon([loc(((q['lon']-116.415)*sx,(q['lat']-39.915)*sy))for q in p['geometry']])
# Straight and concealed flanking passages; portal dimensions inferred from photographs.
portals=[[-17.8,2.2,4.1],[0,2.7,4.5],[17.8,2.2,4.1],[-43.1,1.85,3.7],[43.1,1.85,3.7]]
portals=[v+[poly.intersection(LineString([(v[0],-150),(v[0],50)])).bounds[1],poly.intersection(LineString([(v[0],-150),(v[0],50)])).bounds[3]]for v in portals]
for v in portals:
 x,r,s,y0,y1=v
 if abs(x)>40:v[3]=-22
 poly=poly.difference(box(x-r,-22,x+r,24))
 if abs(x)>40:poly=poly.difference(box(min(x,math.copysign(37,x)),-22,max(x,math.copysign(37,x)),-18))
polys=list(poly.geoms)if hasattr(poly,'geoms')else[poly]
polys=[orient(p,1)for p in polys]
base=[{'ring':list(p.exterior.coords),'triangles':[list(t.exterior.coords)[:3]for t in triangulate(p)if p.covers(t)]}for p in polys]
out={'center':[cx,cy],'angle':a,'platform':base,'portals':portals,'sourceParts':[r['id']for r in rs],'parts':{str(r['id']):{'center':loc(r['center']),'w':r['w']*100,'d':r['d']*100,'boundary':[loc(q)for q in r['boundary']]}for r in rs},'bounds':[min(q[0]for r in rs for q in r['boundary'])-.025,min(q[1]for r in rs for q in r['boundary'])-.025,max(q[0]for r in rs for q in r['boundary'])+.025,max(q[1]for r in rs for q in r['boundary'])+.025]}
(R/'data/wumen-plan.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(out['bounds'])
