"""Integrate the principal Dacheng Hall with explicit reconstruction limitations."""
import json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=json.loads((R/'data/confucius-plan.json').read_text());audit=json.loads((R/'output/confucius-detail/geometry-validation.json').read_text());x,y=p['center'];co,si=math.cos(p['angle']),math.sin(p['angle'])
assert len(audit)==2 and all(not a['errors']for a in audit)
s={'id':'confucius','name':'孔庙·大成殿','subject':'重檐黄瓦、九开间格扇与石台基','methodLabel':'实景参考重建','x':x,'y':y,'rotation':math.degrees(p['angle']),'sourceOsmIds':[p['osmId']],'maskPolygon':p['maskPolygon'],'span':.72,'height':audit[1]['boundsLocal'][1][2],'groundHeight':.012,'viewOffset':[40,45,110],'author':'实景参考：호고호（CC0）；重建：本项目','license':'MIT；地理轮廓 ODbL','licenseUrl':'https://opendatacommons.org/licenses/odbl/','source':'public/assets/confucius-detail/ATTRIBUTION.html','method':'根据 OSM 建筑轮廓和实景照片重建大成殿。当前高度约23米为照片比例推定，与公开资料33米尚未统一；匾额为字体重绘，雕饰简化，非测绘复刻。目前精细模型覆盖主殿。','lods':{}}
for level in['preview','detail']:
 a=json.loads((R/f'output/confucius-detail/confucius-{level}.json').read_text());v=next(v for v in audit if v['level']==level);path=R/f'public/assets/confucius-detail/confucius-{level}.glb';assert v['revision']==a['revision']==hashlib.sha256(path.read_bytes()).hexdigest()[:12];s['lods'][level]=f'public/assets/confucius-detail/confucius-{level}.glb?v={a["revision"]}'
lo,hi=v['boundsLocal'];poly=[[x+xx*co-yy*si,y+xx*si+yy*co]for xx,yy in[(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]]
s['plantingPolygon']=poly;s['bounds']=[min(v[0]for v in poly),min(v[1]for v in poly),max(v[0]for v in poly),max(v[1]for v in poly)]
s['detailView']={'label':'走近大成殿','x':x+.16*si,'y':y-.16*co,'height':.10,'span':.39,'offset':[.25,.18,1]}
s['additionalViews']={'roof':{'label':'俯瞰重檐瓦顶','x':x,'y':y,'height':.12,'span':.72,'offset':[.65,1.25,.8]}}
f=R/'public/assets/route-landmarks/manifest.json';m=json.loads(f.read_text());m['assets']=[v for v in m['assets']if v['id']!='confucius']+[s];f.write_text(json.dumps(m,ensure_ascii=False,indent=2));print('Integrated principal hall',s['id'],'total assets',len(m['assets']))
