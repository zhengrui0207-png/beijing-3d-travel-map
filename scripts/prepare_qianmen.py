"""Anchors from cached OSM; architectural dimensions from published records."""
from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[1]
rows=json.loads((R/'data/urban/records.json').read_text())['records']
plans=[]
for id,osm,L,D,H in [('qianmen',25109960,95,31.45,43.65),('qianmen-arrow',439956436,62,36,35.37)]:
 r=next(x for x in rows if x['osmId']==osm);ring=r['rings'][0];edges=[(math.dist(a,b),a,b)for a,b in zip(ring,ring[1:]+ring[:1])];_,a,b=max(edges)
 angle=math.atan2(b[1]-a[1],b[0]-a[0]);angle=(angle+math.pi/2)%math.pi-math.pi/2
 cx,cy=r['center'];co,si=math.cos(angle),math.sin(angle)
 polygon=[[cx+(x*co-y*si)/100,cy+(x*si+y*co)/100]for x,y in [(-L/2,-D/2),(L/2,-D/2),(L/2,D/2),(-L/2,D/2)]]
 bounds=[min(p[0]for p in polygon),min(p[1]for p in polygon),max(p[0]for p in polygon),max(p[1]for p in polygon)]
 plans.append({'id':id,'osmId':osm,'center':r['center'],'angle':angle,'dimensions':[L,D,H],'maskPolygon':ring,'plantingPolygon':polygon,'bounds':bounds,'oldHeight':r['height']*100})
p={'assets':plans,'sources':{'gateDimensions':'https://wwj.beijing.gov.cn/bjww/wwjzzcslm/1737418/1738081/gzdt53/10856451/2020082814592768170.pdf','arrowWindows':'https://wwj.beijing.gov.cn/bjww/362760/362770/623138/index.html','heights':'https://www.beijing.gov.cn/renwen/rwzyd/gdwh/zym/202107/t20210706_2430351.html'},'limitations':['Gatehouse mapped footprint about 109.5 x 22 m conflicts with documented 95 x 31.45 m platform; retain mapped centre/angle and use published platform dimensions.','Gatehouse base 14.7 m chosen from 2020 fire-engineering review; other public descriptions cite 13.2 m. Roof spacing inferred to meet published total 43.65 m.','Arrow main roof 62 m and northern annex 42 x 12 m follow published form; base depth, window sizes, stair placement and ornaments are photo-informed approximations.','No photogrammetric or conservation-survey accuracy claimed; reference photographs are not used as texture pixels.']}
(R/'data/qianmen-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));print(plans)
