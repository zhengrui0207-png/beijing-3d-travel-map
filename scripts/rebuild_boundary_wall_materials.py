"""Rebuild only the OSM shell after separating boundary walls from facades.
Preserve every existing LOD tile and the saved per-tile source metadata.
"""
import runpy,json,hashlib,bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'public/assets/urban/manifest.json';old=json.loads(p.read_text())
m=runpy.run_path(str(ROOT/'scripts/blender_urban_assets.py'))
m['build_shell']()
old['revision']=hashlib.sha256((ROOT/'public/assets/urban/city-shell.glb').read_bytes()).hexdigest()[:12]
old['boundaryWallMaterialCorrection']={'count':16,'source':'OSM building=wall; solid walls instead of generic window facade','heightUnchanged':True}
p.write_text(json.dumps(old,ensure_ascii=False,separators=(',',':')))
s=bpy.context.scene;bpy.data.libraries.write(str(ROOT/'output/urban/北京城区_建筑屋顶.blend'),{s},fake_user=True)
print('Preserved',len(old['tiles']),'detail tiles. New shell revision',old['revision'])
