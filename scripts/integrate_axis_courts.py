import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'public/assets/route-landmarks/manifest.json';m=json.loads(path.read_text());plans=json.loads((ROOT/'data/axis-courts.json').read_text())
for p in plans:
 s={'id':p['id'],'name':p['name'],'subject':'灰瓦朝房与琉璃瓦门楼','parentPlace':'forbidden','methodLabel':'实景参考重建','x':p['center'][0],'y':p['center'][1],'rotation':math.degrees(p['angle']),'bounds':p['bounds'],'span':p['length']/100+.04,'height':.13,'groundHeight':.011,'viewOffset':[85,80,130],'sourceParts':p['sourceParts'],'anchorOsmId':p['parentOsmId'],'author':'照片参考：Gagaboys；建筑重建：本项目','license':'CC BY-SA 3.0','licenseUrl':'https://creativecommons.org/licenses/by-sa/3.0/','source':'https://commons.wikimedia.org/wiki/File:午门俯瞰.jpg','method':'沿 OSM 朝房轮廓与门楼位置，在 Blender 中重建连续灰瓦屋面、红柱、木格门窗及黄色琉璃瓦门楼；高度采用 OSM，柱距、瓦片、窗格和脊饰推定。实景参考 Gagaboys 俯瞰照片及北京中轴线遗产保护中心建筑资料；未使用照片像素作贴图。','relatedModels':[{'id':'duanmen','label':'查看端门城楼'}],'lods':{}}
 g=p['gates'][-1];ca,sa=math.cos(p['angle']),math.sin(p['angle']);gx=p['center'][0]+(g['x']*ca-g['y']*sa)/100;gy=p['center'][1]+(g['x']*sa+g['y']*ca)/100
 s['detailView']={'label':'走近朝房与门楼','x':gx,'y':gy,'height':.055,'span':.48,'offset':[1 if p['inwardSide']<0 else -1,.45,.15]}
 for level in ['preview','detail']:
  a=json.loads((ROOT/f'output/axis-courts/{p["id"]}-{level}.json').read_text());s['lods'][level]=f'public/assets/axis-courts/{p["id"]}-{level}.glb?v={a["revision"]}'
 m['assets']=[v for v in m['assets']if v['id']!=s['id']]+[s]
for s in m['assets']:
 if s['id']=='duanmen':
  s['relatedModels']=[v for v in s.get('relatedModels',[]) if v['id']!='axis-nw']+[{'id':'axis-nw','label':'查看朝房细节'}]
  s['contextView']={'label':'中轴朝房建筑群','x':-20.44,'y':-6.0,'height':.08,'span':4.7,'offset':[15,165,110]}
path.write_text(json.dumps(m,ensure_ascii=False,indent=2))
p=ROOT/'index.html';t=p.read_text().replace('20260930-duanmen1','20260930-axis-courts1');needle='<h3>关于三维地图</h3>';note='<h3>中轴朝房 · 建筑群重建</h3><p>天安门、端门、午门之间的四排东西朝房及六座门楼，按 OSM 位置与实景参考补充连续灰瓦、红柱和木格门窗。柱距、彩绘与脊饰为推定；保留原有地理轮廓和高度来源。<a href="public/assets/axis-courts/ATTRIBUTION.html" target="_blank" rel="noreferrer">查看来源与精度说明</a>。</p>'
if note not in t:t=t.replace(needle,note+needle)
p.write_text(t)
