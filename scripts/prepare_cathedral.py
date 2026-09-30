from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[1];r=next(r for r in json.loads((R/'data/urban/records.json').read_text())['records']if r['osmId']==85902975)
a,b=r['rings'][0][1:3];angle=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(angle),math.sin(angle);cx,cy=r['center']
local=[[(x-cx)*co*100+(y-cy)*si*100,-(x-cx)*si*100+(y-cy)*co*100]for x,y in r['rings'][0]]
p={'id':'cathedral','osmId':85902975,'center':r['center'],'angle':angle,'maskPolygon':r['rings'][0],'localFootprint':local,'height':30.0,'heightSource':'photo-inferred, not measured','sources':{'heritage':'https://wwj.beijing.gov.cn/bjww/362771/362779/dqpqgzdwwbhdw/523538/index.html','photoFront':'https://commons.wikimedia.org/wiki/File:St_Joseph_(east_cathedral)_Wangfujing_IMG_4979.jpg','photoTowers':'https://commons.wikimedia.org/wiki/File:St._Joseph%27s_Cathedral,_Beijing_facade.JPG'}}
(R/'data/cathedral-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));print(p)
