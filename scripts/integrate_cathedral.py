"""Publish the photo-informed East Church at its mapped west-facing anchor."""
import json,math,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=json.loads((R/'data/cathedral-plan.json').read_text());x,y=p['center'];co,si=math.cos(p['angle']),math.sin(p['angle'])
audit=json.loads((R/'output/cathedral-detail/geometry-validation.json').read_text())
assert len(audit)==2 and all(not a['errors'] for a in audit), 'Fix geometry before publishing'
s={'id':'cathedral','name':'王府井天主堂','subject':'三座圆顶钟塔与西向拱门立面','methodLabel':'资料与实景参考重建','x':x,'y':y,'rotation':p['angle'],'sourceOsmIds':[p['osmId']],'maskPolygon':p['maskPolygon'],'span':.82,'height':.30,'groundHeight':.012,'viewOffset':[-150,95,65],'author':'参考摄影：Bjoertvedt、BrokenSphere；建筑重建：本项目','license':'CC BY-SA 4.0','licenseUrl':'https://creativecommons.org/licenses/by-sa/4.0/','source':'public/assets/cathedral-detail/ATTRIBUTION.html','method':'按 OSM 轮廓与公开实景照片重建；坐东朝西，三座圆顶钟塔。30米总高、侧墙窗距及装饰尺寸为推定，非测绘或摄影测量。','lods':{}}
for level in ['preview','detail']:
 a=json.loads((R/f'output/cathedral-detail/cathedral-{level}.json').read_text());assert next(r for r in audit if r['level']==level)['assetRevision']==a['revision'];s['lods'][level]=f'public/assets/cathedral-detail/cathedral-{level}.glb?v={a["revision"]}'
s['rotation']=math.degrees(p['angle']) # RouteLandmarks manifest stores degrees; modelling plan uses radians.
lo,hi=a['boundsLocal'];polygon=[[x+xx*co-yy*si,y+xx*si+yy*co]for xx,yy in[(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]]
s['plantingPolygon']=polygon;s['bounds']=[min(q[0]for q in polygon),min(q[1]for q in polygon),max(q[0]for q in polygon),max(q[1]for q in polygon)]
s['detailView']={'label':'走近钟塔与拱窗','x':x+.31*si,'y':y-.31*co,'height':.15,'span':.38,'offset':[-1,.18,.20]}
s['additionalViews']={'side':{'label':'查看侧墙与屋顶','x':x,'y':y,'height':.12,'span':.78,'offset':[-.6,.55,1.]}}
f=R/'public/assets/route-landmarks/manifest.json';m=json.loads(f.read_text());m['assets']=[v for v in m['assets']if v['id']!='cathedral']+[s];f.write_text(json.dumps(m,ensure_ascii=False,indent=2))
f=R/'index.html';t=f.read_text();t=re.sub(r'app\.js\?v=[^"\s]+','app.js?v=20260930-cathedral1',t)
note='<h3>王府井天主堂</h3><p>按地图轮廓与实景参考重建三座圆顶钟塔、西向拱门立面与侧墙；高度和细部尺寸为推定。<a href="public/assets/cathedral-detail/ATTRIBUTION.html" target="_blank" rel="noreferrer">来源与精度说明</a>。</p>'
if note not in t:t=t.replace('<h3>关于三维地图</h3>',note+'<h3>关于三维地图</h3>')
f.write_text(t)
print('Integrated cathedral;',len(m['assets']),'models')
