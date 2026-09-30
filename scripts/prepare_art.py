from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[1];r=next(r for r in json.loads((R/'data/urban/records.json').read_text())['records']if r['osmId']==131710744)
a,b=r['rings'][0][8:10];angle=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(angle),math.sin(angle);cx,cy=r['center']
local=[[(x-cx)*co*100+(y-cy)*si*100,-(x-cx)*si*100+(y-cy)*co*100]for x,y in r['rings'][0]]
p={'id':'art','osmId':r['osmId'],'center':r['center'],'angle':angle,'maskPolygon':r['rings'][0],'localFootprint':local,'height':35.0,'heightSource':'photo-inferred, not measured','sources':{'official':'https://www.namoc.cn/namoc/gaik/gk.shtml','architecture':'https://www.namoc.org/xwzx/zt/gqzt/bgpz/201305/t20130524_248636.htm','photoFront':'https://commons.wikimedia.org/wiki/File:National_Art_Museum_of_China_facade.jpg','photoWide':'https://commons.wikimedia.org/wiki/File:National_Art_Museum_of_China_(20240627).jpg'}}
(R/'data/art-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));print('angle degrees',math.degrees(angle));print([(i,[round(v,2)for v in p])for i,p in enumerate(local)])
