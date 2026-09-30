"""Retain existing photo-derived lower stupa and rebuild the damaged spire.
Official reference: Beijing Tourism / attraction120900:35.9m high,13 rings,16 bells.
Unrecorded ornament dimensions estimated. Existing CC BY-SA3.0 reference retained.
"""
import bpy,bmesh,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/beihai-detail';PROOF=ROOT/'output/beihai-detail'
spec=importlib.util.spec_from_file_location('beihai_helpers',ROOT/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(spec);sys.modules[spec.name]=T;spec.loader.exec_module(T)
def build(detail):
 level='detail'if detail else'preview';s=bpy.data.scenes.get('Beihai Stupa '+level)or bpy.data.scenes.new('Beihai Stupa '+level);bpy.context.window.scene=s
 for o in list(s.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/f'public/assets/route-landmarks/beihai/{level}.glb'));bpy.context.view_layer.update()
 for o in list(s.objects):
  if o.type!='MESH':continue
  o.data.transform(o.matrix_world);o.matrix_world.identity()
  # Centre on the tower axis, rather than on the combined tower/shrine bounding box.
  for v in o.data.vertices:v.co.x=(v.co.x+.0255)*.892;v.co.y=(v.co.y-.002)*.892;v.co.z*=35.9/36
  bm=bmesh.new();bm.from_mesh(o.data)
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,.222),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
  bm.to_mesh(o.data);bm.free();o.data.update();o.name='Beihai photo referenced lower stupa'
 B=T.Builder(detail);N=128 if detail else 64
 # New geometry is made in metres with the same local axis as the imported body.
 B.cylinder('white',2.12,21.9,22.4,N,2.05)
 B.ring('white',2.17,22.05,.24,.12,N)
 for i in range(13):
  z=22.4+i*.69;r=2.09-i*.043
  B.cylinder('white',r,z,z+.65,N,r-.04)
  B.ring('rim',r+.07,z+.04,.12,.095,N)
  if detail:
   # Fine masonry courses, subordinate to the thirteen principal rings.
   for zz in [.24,.45]:B.ring('plasterJoint',r-.01,z+zz,.018,.012,N)
 # Canopy, two bronze/gilded discs with physically modeled ribs and hanging bells.
 B.cylinder('bronze',1.72,31.40,31.72,N,2.30)
 B.ring('goldEdge',2.32,31.69,.18,.12,N)
 B.cylinder('bronze',2.30,31.74,32.25,N,1.40)
 B.cylinder('bronze',1.40,32.25,32.47,N,1.05)
 B.cylinder('bronze',1.05,32.47,32.62,N,1.54)
 B.ring('goldEdge',1.55,32.62,.10,.09,N)
 B.cylinder('bronze',1.54,32.66,33.0,N,.68)
 for i in range(16):
  a=i*math.tau/16;x,y=2.05*math.cos(a),2.05*math.sin(a)
  B.beam('bronze',(x,y,31.55),(x,y,30.94),.023,6)
  B.cylinder('bell',.11,30.77,30.96,6,.07,(x,y));B.cylinder('bell',.17,30.63,30.77,6,.11,(x,y))
  B.beam('bronze',(x,y,30.63),(x,y,30.27),.012,5)
  B.box('bronze',(x,y,30.31),(.24,.028,.055),a);B.box('bronze',(x,y,30.31),(.028,.24,.055),a)
  if detail:
   for t in range(9):
    u=t/8;v=(t+1)/8
    if v>1:break
    ra=2.30-(2.30-1.40)*u;rb=2.30-(2.30-1.40)*v
    B.beam('goldEdge',(ra*math.cos(a),ra*math.sin(a),31.74+.51*u),(rb*math.cos(a),rb*math.sin(a),31.74+.51*v),.018,5)
 for i in range(4):
  a=i*math.pi/2+math.pi/4
  B.beam('bronze',(2.10*math.cos(a),2.10*math.sin(a),31.55),(1.71*math.cos(a),1.71*math.sin(a),28.55),.04,8)
 # Lotus moulding, sun-and-moon finial. Silhouette reaches the documented total height.
 B.box('gold',(0,0,33.13),(.81,.81,.25))
 B.cylinder('gold',.39,33.25,33.43,32,.22)
 for i in range(12):
  a=i*math.tau/12;B.beam('gold',(.32*math.cos(a),.32*math.sin(a),33.3),(.40*math.cos(a),.40*math.sin(a),33.5),.07,8)
 # Crescent lies in the frontal YZ plane (original photo asset faces +X).
 for j in range(40):
  a=math.pi+math.pi*j/40;b=math.pi+math.pi*(j+1)/40
  B.beam('gold',(0,.58*math.cos(a),34.05+.46*math.sin(a)),(0,.58*math.cos(b),34.05+.46*math.sin(b)),.085,8)
 B.cylinder('gold',.12,33.4,34.12,24)
 def sphere(center,r,n=32):
  x,y,z=center
  for j in range(16):
   a=-math.pi/2+j*math.pi/16;b=-math.pi/2+(j+1)*math.pi/16
   for i in range(n):
    u=i*math.tau/n;v=(i+1)*math.tau/n
    B.face('gold',[(x+r*math.cos(t)*math.cos(p),y+r*math.cos(t)*math.sin(p),z+r*math.sin(t))for t,p in [(a,u),(a,v),(b,v),(b,u)]])
 sphere((0,0,34.12),.28)
 B.cylinder('gold',.16,34.35,34.49,24,.24)
 # Flame/heart profile revolved; side tongues retained as separate carved tips.
 profile=[(34.49,.12),(34.63,.28),(34.88,.32),(35.15,.22),(35.43,.16),(35.69,.06),(35.9,0)]
 for (z,r),(zz,rr)in zip(profile,profile[1:]):B.cylinder('gold',r,z,zz,48,rr,caps=False)
 for side in [-1,1]:
  B.beam('gold',(0,side*.21,34.68),(0,side*.42,35.10),.06,8)
  B.beam('gold',(0,side*.42,35.10),(0,side*.30,35.42),.035,8)
 colors={'white':(.73,.72,.67),'rim':(.67,.66,.61),'plasterJoint':(.57,.56,.52),'bronze':(.085,.095,.082),'goldEdge':(.33,.25,.08),'gold':(.64,.39,.08),'bell':(.29,.25,.14)}
 for key,(verts,faces,_)in B.groups.items():
  me=bpy.data.meshes.new('Beihai '+key);me.from_pydata([(x/100,y/100,z/100)for x,y,z in verts],[],faces);me.update()
  if key in ['white','rim','gold']:
   bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0000001);bm.to_mesh(me);bm.free()
   for poly in me.polygons:poly.use_smooth=True
  m=bpy.data.materials.new('Beihai '+key);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*colors[key],1);p.inputs['Roughness'].default_value=.84 if key in ['white','rim','plasterJoint']else .43;p.inputs['Metallic'].default_value=.7 if key in ['bronze','gold','goldEdge','bell']else 0;me.materials.append(m)
  o=bpy.data.objects.new('Beihai '+key,me);s.collection.objects.link(o)
 bpy.context.view_layer.update()
 for o in s.objects:o.select_set(True)
 bpy.context.view_layer.objects.active=next(o for o in s.objects if o.type=='MESH')
 import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB')
 bpy.ops.export_scene.gltf(filepath=str(OUT/(level+'.glb')),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=19,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
 for o in s.objects:
  for m in getattr(o.data,'materials',[]):
   for node in m.node_tree.nodes:
    if node.type=='TEX_IMAGE'and node.image:node.image.pack()
 bpy.data.libraries.write(str(PROOF/('北海白塔_'+level+'.blend')),{s},fake_user=True)
 stats={'level':level,'rings':13,'bells':16,'heightMetres':35.9,'meshes':len(s.objects),'triangles':sum(len(p.vertices)-2 for o in s.objects for p in o.data.polygons),'bytes':(OUT/(level+'.glb')).stat().st_size,'sha':hashlib.sha256((OUT/(level+'.glb')).read_bytes()).hexdigest()[:12]};(PROOF/(level+'-audit.json')).write_text(json.dumps(stats,indent=2));print(stats)
 return s
if __name__=='__main__':build(False);build(True)
