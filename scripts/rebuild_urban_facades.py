"""Only shell UV/material grouping changes; preserve existing streamed detail tiles."""
import runpy,json,hashlib,bpy
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'public/assets/urban/manifest.json';old=json.loads(p.read_text());m=runpy.run_path(str(R/'scripts/blender_urban_assets.py'));m['build_shell']();m['build_details'](0,144);new=m['build_shell'].__globals__['manifest'];new['revision']=hashlib.sha256((R/'public/assets/urban/city-shell.glb').read_bytes()).hexdigest()[:12];p.write_text(json.dumps(new,ensure_ascii=False,separators=(',',':')));bpy.data.libraries.write(str(R/'output/urban/北京城区_建筑屋顶.blend'),{bpy.context.scene},fake_user=True);(R/'output/urban-facades/audit.json').write_text(json.dumps(new['facades'],indent=2));print(new['facades'])
