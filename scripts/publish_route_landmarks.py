"""Publish only locally processed assets, including source attribution and billing."""
import html
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/route-landmarks'; ASSETS=ROOT/'public/assets/route-landmarks'
places={p['id']:p for p in json.loads((ROOT/'public/assets/tourism.json').read_text())['places']}
sources=json.loads((ROOT/'data/landmark-references/selected.json').read_text())
assets=[];ledger=[];cards=[]
osm={o['id']:o for o in json.loads((ROOT/'data/osm_beijing.json').read_text())['elements'] if o.get('geometry')}
anchors={'jingshan':26390235,'beihai':561193504,'yonghe':177053588,'guozijian':227782231,'bell':425993664,'drum':267371087,'shichahai':816148132,'guomao':599547918}

for row in sources:
    pid=row['id'];p=dict(places[pid])
    if pid in anchors:
        points=osm[anchors[pid]]['geometry']
        lon=sum(v['lon'] for v in points)/len(points);lat=sum(v['lat'] for v in points)/len(points)
        p['x']=(lon-116.415)*111320*math.cos(math.radians(39.915))/100
        p['y']=(lat-39.915)*111320/100
    result_path=OUT/(pid+'-result.json');report_path=OUT/(pid+'-blender.json')
    result=json.loads(result_path.read_text()) if result_path.exists() else {}
    ledger.append({'id':pid,'name':p['name'],'taskId':result.get('task_id'),'status':result.get('status','rejected' if result.get('cli_exit_code')==5 else 'pending'),'credits':result.get('credits_consumed',0)})
    if not report_path.exists():continue
    report=json.loads(report_path.read_text());low,high=report['bounds']
    margin=.14 if pid=='beihai' else .06
    subject='钟楼与沿街建筑示意' if pid=='wangfujing' else row['subject']
    methodLabel='照片参考建模' if pid=='wangfujing' else '实景照片生成'
    methodNote=('根据实景照片在 Blender 中制作钟楼与沿街建筑示意；Tripo 结果仅提取到护栏，未采用该结果。' if pid=='wangfujing' else '实景照片经 Tripo v3.1 生成网格和纹理，经 Blender 缩放、轻量化与渲染；照片不可见的部分由模型推断。')
    if pid=='shichahai':methodNote+=' 桥面游客已移除，桥面与栏杆在 Blender 中重建。'
    for level in ['preview','detail']:
        path=ASSETS/pid/(level+'.glb')
        with path.open('rb') as f:
            magic,version,length=struct.unpack('<4sII',f.read(12))
        assert magic==b'glTF' and version==2 and length==path.stat().st_size,path
    assets.append({'id':pid,'name':p['name'],'subject':subject,'methodLabel':methodLabel,'x':p['x'],'y':p['y'],
      'span':max(high[0]-low[0],high[1]-low[1]),'height':high[2]-low[2],
      'rotation':-90,'anchorOsmId':anchors.get(pid),'bounds':[p['x']+low[1]-margin,p['y']-high[0]-margin,p['x']+high[1]+margin,p['y']-low[0]+margin],
      'lods':{level:f'public/assets/route-landmarks/{pid}/{level}.glb' for level in ['preview','detail']},
      'author':row['author'],'license':row['license'],'licenseUrl':row['licenseUrl'],'source':row['page'],
      'method':methodNote})
    e=html.escape
    cards.append(f'<article><h2>{e(p["name"])} · {e(subject)}</h2><p>原图作者：{e(row["author"])}<br><a href="{e(row["page"],quote=True)}">原图与许可声明</a> · <a href="{e(row["licenseUrl"],quote=True)}">{e(row["license"])}</a></p><p>改编：{e(methodNote)} 保留原图对应的署名及共享要求。</p><a href="../../../?detail={pid}">在地图查看 3D 模型 ↗</a></article>')
manifest={'version':1,'assets':assets,'retainedExisting':['forbidden','tiananmen'],'notes':'Approximate representative buildings and street scenes, not surveyed reconstructions.'}
(ASSETS/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(ASSETS/'attributions.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>北京旅游地标模型 · 来源与署名</title><style>body{max-width:900px;margin:40px auto;padding:0 24px;font:16px/1.8 system-ui;background:#f2f4ef;color:#244237}article{background:white;padding:24px;margin:20px 0;border-radius:12px}a{color:#276b58}h1{font-size:30px}</style><h1>北京旅游地标模型 · 来源与署名</h1><p>原图及改编模型的署名与许可逐项列于下方。模型用于旅游地图中的代表性展示，不能用于建筑测绘。故宫与天安门保留现有模型和原有署名。</p>'+''.join(cards)+'</html>')
(OUT/'credits-ledger.json').write_text(json.dumps({'totalCredits':sum(x['credits'] for x in ledger),'tasks':ledger},ensure_ascii=False,indent=2))
print(json.dumps({'published':len(assets),'detailMB':round(sum((ASSETS/a['id']/'detail.glb').stat().st_size for a in assets)/1024**2,2),'previewMB':round(sum((ASSETS/a['id']/'preview.glb').stat().st_size for a in assets)/1024**2,2),'creditsRecorded':sum(x['credits'] for x in ledger)}))
