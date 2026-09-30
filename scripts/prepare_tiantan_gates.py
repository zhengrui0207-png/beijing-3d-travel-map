import json,math
from pathlib import Path
from shapely.geometry import Polygon
R=Path(__file__).resolve().parents[1];rows=json.loads((R/'data/urban/records.json').read_text())['records'];parts=[]
for id,key,name,kind in [(43921120,'chengzhen','成贞门','hall'),(43922670,'mound-outer-gate','圜丘外壝北棂星门','outer'),(727026438,'mound-inner-gate','圜丘内壝北棂星门','inner')]:
 r=next(a for a in rows if a['osmId']==id);q=list(Polygon(r['rings'][0]).minimum_rotated_rectangle.exterior.coords)[:4];edges=[(math.dist(a,b),a,b)for a,b in zip(q,q[1:]+q[:1])];L,a,b=max(edges);angle=math.atan2(b[1]-a[1],b[0]-a[0]);angle=(angle+math.pi/2)%math.pi-math.pi/2
 parts.append({'id':key,'name':name,'kind':kind,'osmId':id,'center':r['center'],'bounds':r['bounds'],'maskPolygon':r['rings'][0],'length':L*100,'depth':min(e[0]for e in edges)*100,'angle':angle})
(R/'data/tiantan-gates-plan.json').write_text(json.dumps({'parts':parts,'note':'OSM footprints retained; architectural elevations inferred from photographs, not surveyed.'},ensure_ascii=False,indent=2));print([(p['name'],p['length'],p['depth'])for p in parts])
