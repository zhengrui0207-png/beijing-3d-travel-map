"""Place the museum LODs on the OSM footprint, retaining inferred-elevation disclosure."""
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=json.loads((R/'data/art-plan.json').read_text());x,y=p['center'];co,si=math.cos(p['angle']),math.sin(p['angle'])
audit=json.loads((R/'output/art-detail/geometry-validation.json').read_text())
assert len(audit)==2 and all(not a['errors'] for a in audit)
s={'id':'art','name':'中国美术馆','subject':'层叠黄瓦阁楼、柱廊与石材立面','methodLabel':'资料与实景参考重建','x':x,'y':y,'rotation':math.degrees(p['angle']),'sourceOsmIds':[p['osmId']],'maskPolygon':p['maskPolygon'],'span':1.65,'height':.35,'groundHeight':.012,'viewOffset':[70,75,160],'author':'参考摄影：Jackiejackie123123、CNHowey；重建：本项目','license':'CC BY-SA 4.0','licenseUrl':'https://creativecommons.org/licenses/by-sa/4.0/','source':'public/assets/art-detail/ATTRIBUTION.html','method':'建筑平面来自 OSM；参考中国美术馆官方资料和实景照片重建黄瓦阁楼、柱廊、凹入窗洞与石材拼缝。35米高度、背面及装饰尺寸为推定，非测绘模型。','lods':{}}
for level in ['preview','detail']:
 a=json.loads((R/f'output/art-detail/art-{level}.json').read_text());assert next(v for v in audit if v['level']==level)['revision']==a['revision'];s['lods'][level]=f'public/assets/art-detail/art-{level}.glb?v={a["revision"]}'
lo,hi=a['boundsLocal'];poly=[[x+xx*co-yy*si,y+xx*si+yy*co]for xx,yy in[(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]]
s['plantingPolygon']=poly;s['bounds']=[min(v[0]for v in poly),min(v[1]for v in poly),max(v[0]for v in poly),max(v[1]for v in poly)]
s['detailView']={'label':'走近中央阁楼','x':x+.22*si,'y':y-.22*co,'height':.20,'span':.68,'offset':[.25,.18,1]}
s['additionalViews']={'roof':{'label':'俯瞰层叠瓦顶','x':x,'y':y,'height':.17,'span':1.60,'offset':[.65,1.25,.8]}}
f=R/'public/assets/route-landmarks/manifest.json';m=json.loads(f.read_text());m['assets']=[v for v in m['assets']if v['id']!='art']+[s];f.write_text(json.dumps(m,ensure_ascii=False,indent=2))
f=R/'index.html';t=f.read_text();note='<h3>中国美术馆</h3><p>按 OSM 平面与实景资料重建层叠瓦顶、柱廊和凹入窗洞；高度、背面和装饰尺寸为推定。<a href="public/assets/art-detail/ATTRIBUTION.html" target="_blank" rel="noreferrer">来源与精度说明</a>。</p>'
if note not in t:t=t.replace('<h3>关于三维地图</h3>',note+'<h3>关于三维地图</h3>')
f.write_text(t);print('Integrated art:',len(m['assets']),'landmark assets')
