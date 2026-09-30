"""Run in live Blender via MCP. Each tile can be exported independently."""
import bpy,json,hashlib,sys,importlib.util
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('infill_detail_helpers',ROOT/'scripts/blender_urban_assets.py');U=importlib.util.module_from_spec(spec);sys.modules[spec.name]=U;spec.loader.exec_module(U)
def init():
 global scene,manifest,mats
 manifest=json.loads((ROOT/'data/urban/infill-detail/index.json').read_text())
 scene=bpy.data.scenes.get('Beijing Infill Roof Detail')or bpy.data.scenes.new('Beijing Infill Roof Detail');bpy.context.window.scene=scene
 for o in list(scene.objects):
  me=o.data;bpy.data.objects.remove(o,do_unlink=True)
  if isinstance(me,bpy.types.Mesh)and me.users==0:bpy.data.meshes.remove(me)
 mats={k:U.material('Infill trim '+k,c)for k,c in {'parapet':(.45,.45,.39),'fascia':(.21,.22,.20),'ridge':(.12,.15,.17)}.items()}
 manifest['tiles']=[{k:v for k,v in t.items()} for t in manifest['tiles']];manifest['completed']=0
 return len(manifest['tiles'])
def batch(start,count=8):
 bpy.context.window.scene=scene
 for t in manifest['tiles'][start:start+count]:
  blob=json.loads(Path(t['input']).read_text());objects=[]
  for kind,faces in blob['layers'].items():
   g={}
   for f in faces:U.add(g,kind,f)
   o=U.mesh(scene,t['id']+' '+kind,*g[kind],mats[kind],'buildings_urban_detail');o['inferredRoofDetail']=True;objects.append(o)
  bpy.context.view_layer.update()
  for o in bpy.context.view_layer.objects:o.select_set(False)
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0]
  import io_scene_gltf2
  fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB')
  path=ROOT/t['url'];bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=4,export_draco_position_quantization=18)
  t['bytes']=path.stat().st_size;t['revision']=hashlib.sha256(path.read_bytes()).hexdigest()[:12];t['triangles']=sum(len(p.vertices)-2 for o in objects for p in o.data.polygons)
  # Keep one central hutong district in the Blender source as an inspectable example.
  if t['id']!='infill--3_1':
   for o in objects:
    me=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(me)
  manifest['completed']+=1
  (ROOT/'output/urban-infill-detail/progress.json').write_text(json.dumps({'completed':manifest['completed'],'total':len(manifest['tiles']),'last':t['id']}))
 print(json.dumps({'completed':manifest['completed'],'total':len(manifest['tiles'])}))
def finish():
 assert manifest['completed']==len(manifest['tiles'])
 manifest['bytes']=sum(t['bytes']for t in manifest['tiles']);manifest['triangles']=sum(t['triangles']for t in manifest['tiles'])
 for t in manifest['tiles']:t.pop('input',None)
 (ROOT/'public/assets/urban-fill/detail/manifest.json').write_text(json.dumps(manifest,indent=2))
 bpy.data.libraries.write(str(ROOT/'output/urban-infill-detail/城区屋顶细节_中央街区.blend'),{scene},fake_user=True)
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_location=Vector((-25,15,.07));area.spaces.active.region_3d.view_distance=7;area.spaces.active.region_3d.view_rotation=Quaternion((.86,.5,.05,.025)).normalized()
 print(json.dumps({'bytes':manifest['bytes'],'triangles':manifest['triangles'],'tiles':len(manifest['tiles'])}))
