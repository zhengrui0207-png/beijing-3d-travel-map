from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'public/assets/route-landmarks/manifest.json';doc=json.loads(p.read_text());s=next(s for s in doc['assets']if s['id']=='shichahai')
backup=ROOT/'output/yinding-detail/previous-manifest-entry.json'
if not backup.exists():backup.write_text(json.dumps(s,ensure_ascii=False,indent=2))
audit=json.loads((ROOT/'output/yinding-detail/detail-audit.json').read_text());a,b=audit['axis']['start'],audit['axis']['end'];length=math.dist(a,b);ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length
x,y=(a[0]+b[0])/2,(a[1]+b[1])/2;halfWidth=.0345
corners=[(x+sx*halfWidth*uy+sy*length/2*ux,y-sx*halfWidth*ux+sy*length/2*uy)for sx in [-1,1]for sy in [-1,1]]
s.update(x=x,y=y,span=length,height=audit['boundsLocalBlender'][1][2],rotation=-math.degrees(math.atan2(ux,uy)),groundHeight=.011,bounds=[min(p[0]for p in corners)-.003,min(p[1]for p in corners)-.003,max(p[0]for p in corners)+.003,max(p[1]for p in corners)+.003],methodLabel='实景参考重建',method='依据 OSM 银锭桥轴线与实景照片在 Blender 中重建单孔石拱、石块接缝、桥面铺石、望柱、镂空栏板和桥名。水平长度约 13.27 米来自 OSM 轴线；桥宽、竖向尺寸、雕花及照片不可见部分为视觉推定，并非测绘复原。',author='PQ77wd',license='CC BY-SA 4.0',licenseUrl='https://creativecommons.org/licenses/by-sa/4.0/',source='https://commons.wikimedia.org/wiki/File:Yinding_Bridge.jpg',roadReplacement={'axis':[ux,uy],'halfLength':length/2-.002,'halfWidth':.045},detailView={'label':'走近石拱与栏板','height':.024,'span':.13,'offset':[120,60,80]})
s['lods']={}
for level in ['preview','detail']:
 au=json.loads((ROOT/f'output/yinding-detail/{level}-audit.json').read_text());s['lods'][level]=f'public/assets/yinding-detail/{level}.glb?v={au["sha"]}'
p.write_text(json.dumps(doc,ensure_ascii=False,indent=2))
print(json.dumps(s,ensure_ascii=False,indent=2))
