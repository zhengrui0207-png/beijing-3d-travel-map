import json,math
from pathlib import Path
from shapely.geometry import Polygon
ROOT=Path(__file__).resolve().parents[1];records=json.loads((ROOT/'data/urban/records.json').read_text())['records'];out=[]
for parent,base,id,name,side in [(637953173,637959186,'axis-sw','天安门至端门西朝房',-1),(637953172,637959201,'axis-se','天安门至端门东朝房',1),(638170121,638170157,'axis-nw','端门至午门西朝房',-1),(638170124,638170158,'axis-ne','端门至午门东朝房',1)]:
 parts=[r for r in records if r['parentOsmId']==parent];body=next(r for r in parts if r['osmId']==base);poly=Polygon(body['rings'][0]);rect=list(poly.minimum_rotated_rectangle.exterior.coords);p,q,r=rect[:3]
 if math.dist(p,q)<math.dist(q,r):p,q,r=rect[1:4]
 dx,dy=q[0]-p[0],q[1]-p[1]
 if dy<0:dx,dy=-dx,-dy
 a=math.atan2(dy,dx);cx,cy=poly.centroid.coords[0];ca,sa=math.cos(a),math.sin(a)
 def loc(x,y):return [(x-cx)*ca*100+(y-cy)*sa*100,-(x-cx)*sa*100+(y-cy)*ca*100]
 gates=[]
 for g in parts:
  if g['height']!=.13:continue
  ps=[loc(x,y)for x,y in g['rings'][0]];xs=[p[0]for p in ps];ys=[p[1]for p in ps]
  gates.append({'osmId':g['osmId'],'x':(min(xs)+max(xs))/2,'y':(min(ys)+max(ys))/2,'length':max(xs)-min(xs),'depth':max(ys)-min(ys),'height':13})
 bounds=[min(r['bounds'][0]for r in parts)-.01,min(r['bounds'][1]for r in parts)-.01,max(r['bounds'][2]for r in parts)+.01,max(r['bounds'][3]for r in parts)+.01]
 out.append({'id':id,'name':name,'parentOsmId':parent,'bodyOsmId':base,'center':[cx,cy],'angle':a,'length':math.dist(p,q)*100,'depth':math.dist(q,r)*100,'height':.13,'bounds':bounds,'inwardSide':side,'gates':gates,'sourceParts':[r['osmId']for r in parts]})
(ROOT/'data/axis-courts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
