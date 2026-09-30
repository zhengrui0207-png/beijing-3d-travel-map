from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'public/assets/route-landmarks/manifest.json';m=json.loads(p.read_text());f=json.loads((ROOT/'data/duanmen-footprint.json').read_text());x,y=f['center']
s={'id':'duanmen','name':'端门','subject':'端门城楼','parentPlace':'forbidden','methodLabel':'实景参考重建','x':x,'y':y,'span':1.21,'height':.35,'rotation':math.degrees(f['angle']),'anchorOsmId':f['id'],'bounds':[f['bounds'][0]-.006,f['bounds'][1]-.006,f['bounds'][2]+.006,f['bounds'][3]+.006],'groundHeight':.011,'viewOffset':[25,55,160],'detailView':{'label':'走近柱廊与瓦顶','height':.24,'span':.75,'offset':[.18,.28,1.6]},'additionalViews':{'portals':{'label':'看五个券门','height':.08,'span':.86,'offset':[.08,.16,1.6]}},'relatedModels':[{'id':'tiananmen','label':'向南看天安门'}],'author':'实景照片：そらみみ；建筑重建：本项目','license':'CC BY-SA 4.0','licenseUrl':'https://creativecommons.org/licenses/by-sa/4.0/','source':'https://commons.wikimedia.org/wiki/File:Duanmen_Gate_of_the_Forbidden_City.jpg','method':'以 OSM 轮廓和分块高度、实景照片重建城台、五券门、九开间柱廊、重檐歇山顶、瓦垄、脊饰与石栏。高度约 35 米来自 OSM，中央券门采用公开报道的 5.52 × 8.82 米；其余细部、门扇开合和色彩为推定，彩绘为生成装饰，匾额为重新排字，并非实景扫描或文物测绘。','lods':{}}
for level in ['preview','detail']:
 a=json.loads((ROOT/f'output/duanmen-detail/{level}-audit.json').read_text());s['lods'][level]=f'public/assets/duanmen-detail/{level}.glb?v={a["sha"]}'
m['assets']=[e for e in m['assets']if e['id']!='duanmen']+[s]
for e in m['assets']:
 if e['id']=='tiananmen':e['relatedModels']=[{'id':'duanmen','label':'向北看端门'}]
p.write_text(json.dumps(m,ensure_ascii=False,indent=2));print('Integrated Duanmen',s['rotation'],s['lods'])
