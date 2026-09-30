"""Photo-informed 72-bay corridor; mapped axis retained, inferred roof/column details."""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'public/assets/tiantan-corridor';O.mkdir(exist_ok=True);Q=R/'output/tiantan-corridor';Q.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('corridor_helpers',R/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(s);sys.modules[s.name]=T;s.loader.exec_module(T)
P=json.loads((R/'data/tiantan-corridor-plan.json').read_text());axis=[Vector(((x-P['center'][0])*100,(y-P['center'][1])*100,0))for x,y in P['axis']];directions=[(b-a).normalized()for a,b in zip(axis,axis[1:])];normals=[Vector((-d.y,d.x,0))for d in directions];miters=[normals[0]]+[(a+b)/(1+a.dot(b))for a,b in zip(normals,normals[1:])]+[normals[-1]]
def build(detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get('Tiantan Corridor '+level)or bpy.data.scenes.new('Tiantan Corridor '+level);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=T.Builder(detail)
 for seg,(a,b,bays) in enumerate(zip(axis,axis[1:],P['bayCounts'])):
  L=(b-a).length
  def p(u,y,z):
   m=normals[seg].copy();edge=min(.15,4/L)
   if u<edge:m=miters[seg].lerp(normals[seg],u/edge)
   elif u>1-edge:m=normals[seg].lerp(miters[seg+1],(u-1+edge)/edge)
   v=a.lerp(b,u)+m*y;return(v.x,v.y,z)
  def strip(key,y0,y1,z0,z1):
   B.face(key,[p(0,y0,z0),p(1,y0,z0),p(1,y1,z1),p(0,y1,z1)])
  strip('stone',-2.5,2.5,.18,.18)
  for side in [-1,1]:
   strip('stone',side*2.5,side*2.5,0,.18)
   B.beam('red',p(0,side*2.2,3.2),p(1,side*2.2,3.2),.14,8)
   # Grey-blue representative painted fascia, kept separate from the open bays.
   B.face('frieze',[p(0,side*2.23,3.04),p(1,side*2.23,3.04),p(1,side*2.23,3.50),p(0,side*2.23,3.50)],[(0,0),(bays,0),(bays,1),(0,1)])
   for i in range(bays+(seg==3)):
    u=i/bays;q=p(u,side*2.2,0);B.cylinder('red',.155,.23,3.48,12 if detail else 8,.14,q[:2]);B.cylinder('stone',.22,.18,.40,8,.19,q[:2])
    B.beam('beam',p(u,-2.25,3.30),p(u,2.25,3.30),.12,6)
   # Sitting benches and short balusters, interrupted at the two end entrances.
   strip('red',side*2.18-.20,side*2.18+.20,.72,.72)
   B.beam('red',p(.012,side*2.18,.72),p(.988,side*2.18,.72),.105,6)
   B.beam('blue',p(.012,side*2.18,.26),p(.988,side*2.18,.26),.075,6)
   for i in range(bays*4):
    u=(i+.5)/(bays*4);q=p(u,side*2.18,0);B.cylinder('blue',.039,.26,.70,5,.039,q[:2])
  # Photo shows a plain rear wall along the main run; ends remain walk-through.
  if seg==2:
   B.face('plaster',[p(0,2.17,.2),p(1,2.17,.2),p(1,2.17,3.20),p(0,2.17,3.20)])
  # Continuous mitered gable sweep: real open volume below, no solid building box.
  n=round(L/(.30 if detail else .95));steps=8 if detail else 4
  def roof(u,t,side):return p(u,side*2.9*(1-t),3.52+1.50*t**1.4)
  for side in [-1,1]:
   for i in range(n):
    u,v=i/n,(i+1)/n
    for j in range(steps):
     t,w=j/steps,(j+1)/steps;pts=[roof(u,t,side),roof(v,t,side),roof(v,w,side),roof(u,w,side)]
     if (Vector(pts[1])-Vector(pts[0])).cross(Vector(pts[2])-Vector(pts[0])).z<0:pts.reverse()
     B.face('roof',pts)
     aa=Vector(roof((u+v)/2,t,side));bb=Vector(roof((u+v)/2,w,side));aa.z+=.045;bb.z+=.045;B.beam('tile'+str((i+seg)%3),aa,bb,.064,6 if detail else 5)
    q=roof((u+v)/2,0,side);B.beam('tile0',(q[0],q[1],q[2]-.03),(q[0],q[1],q[2]+.10),.078,6)
   B.beam('edge',roof(0,0,side),roof(1,0,side),.10,8)
   if detail:
    for i in range(round(L/.5)):
     u=(i+.5)/round(L/.5);B.beam('beam',p(u,side*2.75,3.38),p(u,0,4.87),.055,6)
  B.beam('ridge',p(0,0,5.06),p(1,0,5.06),.135,8)
  for u in ([0]if seg==0 else[1]if seg==3 else[]):
   B.face('red',[p(u,-2.7,3.52),p(u,2.7,3.52),p(u,0,4.96)])
 colors={'stone':(.42,.41,.35),'red':(.40,.036,.022),'beam':(.22,.075,.035),'blue':(.045,.12,.15),'plaster':(.77,.74,.65),'roof':(.075,.22,.12),'tile0':(.16,.36,.19),'tile1':(.23,.40,.21),'tile2':(.12,.30,.17),'edge':(.09,.24,.16),'ridge':(.046,.12,.086),'frieze':(.07,.12,.15)}
 for k,(vs,fs,uvs) in B.groups.items():
  tex=R/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else None;mat=T.mat('Corridor '+k,colors[k],.65 if k.startswith('tile')else .85,texture=tex)
  if tex:next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
  mat.use_backface_culling=False;me=bpy.data.meshes.new('Corridor '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mat);uv=me.uv_layers.new()
  for poly,coords in zip(me.polygons,uvs):
   for i,co in zip(poly.loop_indices,coords):uv.data[i].uv=co
  o=bpy.data.objects.new('Corridor '+k,me);scene.collection.objects.link(o)
 for o in scene.objects:o.select_set(True)
 bpy.context.view_layer.update();import io_scene_gltf2;fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');path=O/(level+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20)
 stats={'level':level,'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12],'bays':sum(P['bayCounts']),'mappedLengthMetres':P['mappedLengthMetres'],'heightMetres':5.195,'method':'photo-informed; inferred roof heights, bay positions, rear wall and decorative details'};(Q/(level+'.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(Q/('天坛七十二长廊_'+level+'.blend')),{scene},fake_user=True);print(stats)
if __name__=='__main__':build(False);build(True)
