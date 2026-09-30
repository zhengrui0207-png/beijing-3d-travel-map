"""Regenerate affected urban trim tiles while retaining the full existing manifest."""
import runpy,json,hashlib,bpy,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'public/assets/urban/manifest.json';old=json.loads(path.read_text());m=runpy.run_path(str(ROOT/'scripts/blender_urban_assets.py'));m['build_shell']()
plans=json.loads((ROOT/'data/axis-courts.json').read_text());keys={f'{math.floor(p["center"][0]/10)}_{math.floor(p["center"][1]/10)}'for p in plans};ns=m['build_details'].__globals__;order=list(ns['tiles'])
for key in keys:m['build_details'](order.index(key),1)
new=ns['manifest'];updates={t['id']:t for t in new['tiles']};old['tiles']=[updates.get(t['id'],t)for t in old['tiles']];old['revision']=hashlib.sha256((ROOT/'public/assets/urban/city-shell.glb').read_bytes()+json.dumps(updates,sort_keys=True).encode()).hexdigest()[:12];path.write_text(json.dumps(old,ensure_ascii=False,separators=(',',':')))
bpy.data.libraries.write(str(ROOT/'output/urban/北京城区_建筑屋顶.blend'),{bpy.context.scene},fake_user=True)
print('Updated',list(updates),'preserved',len(old['tiles']),'tiles; revision',old['revision'])
