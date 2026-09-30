"""Blender MCP export of conservative Overture building infill, spatially batched."""
import bpy,json,math,hashlib,sys,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/urban-fill'
spec=importlib.util.spec_from_file_location('urban_fill_helpers',ROOT/'scripts/blender_urban_assets.py');U=importlib.util.module_from_spec(spec);sys.modules[spec.name]=U;spec.loader.exec_module(U)
def build():
 blob=json.loads((ROOT/'data/urban/overture-fill-records.json').read_text());rows=blob['records']
 scene=bpy.data.scenes.get('Beijing Overture Infill')or bpy.data.scenes.new('Beijing Overture Infill');bpy.context.window.scene=scene
 for o in list(scene.objects):
  me=o.data;bpy.data.objects.remove(o,do_unlink=True)
  if isinstance(me,bpy.types.Mesh)and me.users==0:bpy.data.meshes.remove(me)
 mats={'walls':U.material('Infill light masonry',(.47,.46,.41)),'roofs':U.material('Infill grey roofs',(.17,.19,.20))}
 groups={}
 for r in rows:
  x,y=r['center'];g=groups.setdefault(f'{math.floor(x/20)}_{math.floor(y/20)}',{})
  for f in r['walls']:U.add(g,'walls',f)
  for f in r['roof']:
   a,b,c=f
   if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:f=list(reversed(f))
   U.add(g,'roofs',f)
 objects=[]
 for tile,g in groups.items():
  for kind,(verts,faces)in g.items():objects.append(U.mesh(scene,f'Infill {tile} {kind}',verts,faces,mats[kind],'buildings_urban_'+kind,uv=kind=='walls'))
 bpy.context.view_layer.update()
 for o in bpy.context.view_layer.objects:o.select_set(False)
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB')
 bpy.ops.export_scene.gltf(filepath=str(OUT/'buildings.glb'),export_format=fmt,use_selection=True,use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=10,export_draco_texcoord_quantization=12)
 revision=hashlib.sha256((OUT/'buildings.glb').read_bytes()).hexdigest()[:12]
 manifest={'url':'public/assets/urban-fill/buildings.glb','landscape':'public/assets/urban-fill/landscape.json','revision':revision,'stats':blob['stats'],'source':blob['source'],'license':'ODbL 1.0 (Overture theme); East Asian Buildings CC BY 4.0','meshes':len(objects),'bytes':(OUT/'buildings.glb').stat().st_size,'triangles':sum(len(p.vertices)-2 for o in objects for p in o.data.polygons),'groundHeight':.011}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));bpy.data.libraries.write(str(ROOT/'output/overture-fill/北京城区_影像建筑补全.blend'),{scene},fake_user=True)
 print(json.dumps(manifest,ensure_ascii=False))
 return scene
if __name__=='__main__':build()
