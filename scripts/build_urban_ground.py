"""Blender MCP build of cached OSM land-cover polygons and inferred roadside curbs."""
import bpy,json,math,hashlib,importlib.util,sys
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/urban-ground'
spec=importlib.util.spec_from_file_location('urban_ground_helpers',ROOT/'scripts/blender_urban_assets.py');U=importlib.util.module_from_spec(spec);sys.modules[spec.name]=U;spec.loader.exec_module(U)
def build():
 blob=json.loads((ROOT/'data/urban-ground/geometry.json').read_text());scene=bpy.data.scenes.get('Beijing Urban Ground')or bpy.data.scenes.new('Beijing Urban Ground');bpy.context.window.scene=scene
 for o in list(scene.objects):
  d=o.data;bpy.data.objects.remove(o,do_unlink=True)
  if isinstance(d,bpy.types.Mesh)and d.users==0:bpy.data.meshes.remove(d)
 palette={'residential':(.36,.345,.31),'commercial':(.44,.43,.39),'campus':(.41,.395,.35),'service':(.29,.30,.29),'parking':(.17,.19,.20),'green':(.20,.35,.08),'paved':(.55,.54,.50),'sidewalk':(.56,.55,.50)}
 mats={k:U.material('Urban ground '+k,c)for k,c in palette.items()}
 for kind in ['paved','sidewalk']:
  m=mats[kind];node=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'public/assets/palace/courtyard-stone.png'),check_existing=True);tex.image.pack();m.node_tree.links.new(tex.outputs['Color'],node.inputs['Base Color'])
 groups={}
 for m in blob['meshes']:
  kind,ix,iy=m['name'].split();key=f'{kind} {math.floor(int(ix)/2)} {math.floor(int(iy)/2)}';v,f=groups.setdefault(key,([],[]));start=len(v);v.extend(m['vertices']);f.extend([[start+i for i in face]for face in m['faces']])
 objects=[]
 for key,(verts,faces)in groups.items():
  kind=key.split()[0];o=U.mesh(scene,'Ground '+key,verts,faces,mats[kind],'urban_ground_'+kind);o['sourceKind']=kind;o['groundHeight']=0;o['surfaceInferred']=kind=='sidewalk'
  if kind in ['paved','sidewalk']:
   uv=o.data.uv_layers.new(name='Stone 3 metres')
   for p in o.data.polygons:
    for li in p.loop_indices:
     v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/.03,v.y/.03)
  objects.append(o)
 bpy.context.view_layer.update()
 for o in bpy.context.view_layer.objects:o.select_set(False)
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB')
 path=OUT/'ground.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=5,export_draco_position_quantization=20,export_draco_texcoord_quantization=16)
 manifest={k:v for k,v in blob.items()if k!='meshes'};manifest.update(url='public/assets/urban-ground/ground.glb',revision=hashlib.sha256(path.read_bytes()).hexdigest()[:12],bytes=path.stat().st_size,meshes=len(objects),triangles=sum(len(p.vertices)-2 for o in objects for p in o.data.polygons))
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));bpy.data.libraries.write(str(ROOT/'output/urban-ground/北京街区地面与路缘.blend'),{scene},fake_user=True)
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=Vector((-23.35,25.4,.01));area.spaces.active.region_3d.view_distance=2;area.spaces.active.region_3d.view_rotation=Quaternion((.86,.5,.05,.025)).normalized()
 print(json.dumps({k:manifest[k]for k in ['bytes','meshes','triangles','revision']},ensure_ascii=False))
if __name__=='__main__':build()
