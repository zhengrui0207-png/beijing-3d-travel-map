import bpy,json,sys,importlib.util,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/beihai-terrain'
spec=importlib.util.spec_from_file_location('beihai_terrain_helpers',ROOT/'scripts/blender_urban_assets.py');U=importlib.util.module_from_spec(spec);sys.modules[spec.name]=U;spec.loader.exec_module(U)
scene=bpy.data.scenes.get('Beihai Island Terrain')or bpy.data.scenes.new('Beihai Island Terrain');bpy.context.window.scene=scene
for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
blob=json.loads((ROOT/'data/terrain/beihai-meshes.json').read_text());objs=[]
for key,faces in blob.items():
 if not faces:continue
 group={}
 for f in faces:
  a,b,c=f[:3]
  if not key.startswith(('steps_','platform_walls')) and (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:f=list(reversed(f))
  U.add(group,key,f)
 verts,fs=group[key];color=(.24,.34,.11)if key=='terrain'else(.56,.52,.39)if key=='paths'else(.19,.23,.23)
 if key.startswith('steps_'):color={'steps_treads':(.43,.42,.37),'steps_risers':(.29,.28,.25),'steps_edges':(.38,.37,.33),'steps_rails':(.055,.065,.057)}[key]
 if key.startswith('platform_'):color={'platform_stone':(.48,.47,.42),'platform_joints':(.25,.25,.23),'platform_walls':(.30,.29,.26)}[key]
 o=U.mesh(scene,'Beihai '+key,verts,fs,U.material('Beihai '+key,color),'terrain_beihai'if key=='terrain'else 'architecture_beihai_'+key if key.startswith(('steps_','platform_'))else key)
 if key=='platform_stone':
  o.data.materials.clear();o.data.materials.append(U.courtyard.P.mat('Beihai worn stone slabs',(.48,.47,.42),.96,texture=ROOT/'public/assets/palace/marble.png'))
  uv=o.data.uv_layers.new(name='Stone paving')
  for poly in o.data.polygons:
   for li in poly.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x/.025,co.y/.025)
 if key=='terrain':
  # Weld the tessellation so normals interpolate across cell boundaries.
  import bmesh
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(o.data);bm.free()
  for p in o.data.polygons:p.use_smooth=True
 objs.append(o)
U.export(objs,OUT/'terrain.glb');bpy.data.libraries.write(str(ROOT/'output/beihai-detail/琼华岛_高程地形.blend'),{scene},fake_user=True)
print('Exported terrain',len(objs),(OUT/'terrain.glb').stat().st_size)

field=json.loads((OUT/'heightfield.json').read_text());field['meshRevision']=hashlib.sha256((OUT/'terrain.glb').read_bytes()).hexdigest()[:12];(OUT/'heightfield.json').write_text(json.dumps(field,separators=(',',':')))
