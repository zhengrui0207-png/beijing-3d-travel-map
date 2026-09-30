"""Imperial Vault, photo-informed exterior on its original OSM anchor, metres internally."""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'public/assets/imperial-vault';Q=R/'output/imperial-vault';P=json.loads((R/'data/imperial-vault-plan.json').read_text())
s=importlib.util.spec_from_file_location('vault_helpers',R/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(s);sys.modules[s.name]=T;s.loader.exec_module(T)
TAU=math.tau

def build(detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get('Imperial Vault '+level)or bpy.data.scenes.new('Imperial Vault '+level);bpy.context.window.scene=scene
 for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
 B=T.Builder(detail);N=160 if detail else 80
 # Single profiled marble base, carved panel inset strip and ring of posts.
 for r,z0,z1 in [(10.1,0,.25),(9.8,.25,.55),(9.6,.55,1.85),(9.85,1.85,2.08),(10.05,2.08,2.2)]:B.cylinder('stone',r,z0,z1,N)
 B.ring('stoneShade',9.62,.75,.15,.06,N);B.ring('stoneLight',9.88,2.08,.2,.13,N)
 for i in range(48):
  a=i*TAU/48;b=(i+1)*TAU/48
  if any(abs(math.atan2(math.sin(t-c),math.cos(t-c)))<(.37 if c==-math.pi/2 else .24) for t in [a,b] for c in [-math.pi/2,0,math.pi]):continue
  x,y=9.55*math.cos(a),9.55*math.sin(a);B.box('stoneLight',(x,y,2.9),(.27,.27,1.4),a);B.cylinder('stoneLight',.17,3.5,3.65,10,.08,(x,y))
  for z in [2.42,3.15,3.42]:B.beam('stoneLight',(x,y,z),(9.55*math.cos(b),9.55*math.sin(b),z),.075,4)
  for j in range(1,4):
   t=a+(b-a)*j/4;B.radial_box('stoneLight',9.55,t,2.8,.12,.15,.62)
  if detail:
   t=(a+b)/2;B.radial_box('stoneShade',9.63,t,1.2,.75,.025,.65)
 # South imperial ramp with fourteen steps on either side (Beijing Cultural Heritage Bureau).
 for side in [-1,1]:
  for i in range(14):B.box('stone',(side*2.20,-13.65+(i+.5)*4.15/14,(i+1)*2.2/28),(2.20,4.15/14+.01,(i+1)*2.2/14))
  a=(side*3.48,-13.65,0);b=(side*3.48,-9.5,2.2)
  for dz,r in [(.45,.09),(1.10,.13)]:B.beam('stoneLight',(a[0],a[1],a[2]+dz),(b[0],b[1],b[2]+dz),r,6)
  for i in range(7):
   u=i/6;x=side*3.48;y=-13.65+4.15*u;z=2.2*u;B.box('stoneLight',(x,y,z+.60),(.26,.26,1.2));B.cylinder('stoneLight',.18,z+1.2,z+1.38,10,.08,(x,y))
 B.face('stone',[(-1.05,-13.65,.16),(1.05,-13.65,.16),(1.05,-9.5,2.25),(-1.05,-9.5,2.25)])
 for side in [-1,1]:B.beam('stoneLight',(side*1.08,-13.65,.2),(side*1.08,-9.5,2.3),.11,6)
 if detail:
  # Shallow scrolling relief on the imperial ramp, representative only.
  for i in range(50):
   t=i/49;tt=(i+1)/49;x=.60*math.sin(t*math.pi*6);xx=.60*math.sin(tt*math.pi*6)
   B.beam('stoneLight',(x,-13.4+3.5*t,.32+1.76*t),(xx,-13.4+3.5*tt,.32+1.76*tt),.047,6)
 # East and west fourteen-step flights, without the south-only imperial ramp.
 for side in [-1,1]:
  for i in range(14):B.box('stone',(side*(13.65-(i+.5)*3.55/14),0,(i+1)*2.2/28),(3.55/14+.01,3.8,(i+1)*2.2/14))
  for edge in [-1,1]:
   for dz,r in [(.45,.09),(1.10,.13)]:B.beam('stoneLight',(side*13.65,edge*2.05,dz),(side*10.1,edge*2.05,2.2+dz),r,6)
   for i in range(7):
    u=i/6;x=side*(13.65-3.55*u);y=edge*2.05;z=2.2*u;B.box('stoneLight',(x,y,z+.6),(.26,.26,1.2));B.cylinder('stoneLight',.18,z+1.2,z+1.38,10,.08,(x,y))
 # Round walls with three southern bays openable; north/east/west are grey brick.
 for i in range(N):
  a=i*TAU/N;b=(i+1)*TAU/N;mid=(a+b)/2;front=math.sin(mid)<-.35
  if not front:B.face('brick',[(7.8*math.cos(a),7.8*math.sin(a),2.2),(7.8*math.cos(b),7.8*math.sin(b),2.2),(7.8*math.cos(b),7.8*math.sin(b),6.40),(7.8*math.cos(a),7.8*math.sin(a),6.40)])
 B.cylinder('frieze',7.82,6.4,7.65,N,repeat=8,caps=False)
 for z in [6.42,6.9,7.62]:B.ring('goldMuted',7.85,z,.09,.065,N)
 for i in range(8):
  a=-math.pi/2+(i-.5)*TAU/8;x,y=7.8*math.cos(a),7.8*math.sin(a);B.cylinder('red',.25,2.2,7.70,14 if detail else 8,.22,(x,y));B.cylinder('stoneLight',.32,2.2,2.47,10,.28,(x,y))
  # Inner support ring and cross beams visible through the portals.
  x,y=4.9*math.cos(a),4.9*math.sin(a);B.cylinder('red',.24,2.2,8.4,10,.21,(x,y))
 # 3 southern bays, five narrow panels each; middle panel remains a real opening.
 for bay in [-1,0,1]:
  center=-math.pi/2+bay*TAU/8
  for j in [-2,-1,0,1,2]:
   a=center+j*.132;w=.91
   if j==0:
    B.radial_box('redDark',7.8,a,5.93,w,.14,.88)
   else:
    B.radial_box('redDark',7.8,a,4.2,w,.17,4.0)
    B.radial_box('shade',7.91,a,4.75,w*.82,.04,2.25)
    for side in [-1,1]:B.radial_box('goldMuted',7.95,a+side*w*.46/7.8,4.23,.06,.06,3.95)
    for z in [2.32,3.45,5.93,6.15]:B.radial_box('goldMuted',7.96,a,z,w,.07,.065)
    B.radial_box('goldMuted',7.95,a,2.90,.66,.04,.77);B.radial_box('red',8.0,a,2.90,.57,.03,.67)
    count=9 if detail else 4
    # Diamond lattice in a local tangent plane, clipped to each glazed window rectangle.
    tangent=Vector((-math.sin(a),math.cos(a),0));radial=Vector((math.cos(a),math.sin(a),0));base=radial*7.98
    for sign in [-1,1]:
     for k in range(-count,count+1):
      intercept=k*2.25/count;pts=[]
      for xx in [-w*.39,w*.39]:
       zz=4.75+intercept+sign*xx*2
       if 3.63<=zz<=5.87:pts.append(base+tangent*xx+Vector((0,0,zz)))
      for zz in [3.63,5.87]:
       xx=(zz-4.75-intercept)/(sign*2)
       if abs(xx)<=w*.39:pts.append(base+tangent*xx+Vector((0,0,zz)))
      if len(pts)>=2:B.beam('woodGold',pts[0],pts[1],.024 if detail else .035,5)
 T.bracket_ring(B,7.77,7.60,64 if detail else 32)
 # Under-eave rafters fan out; single sharply curved roof, not three-tier prayer hall.
 for i in range(192 if detail else 64):
  a=i*TAU/(192 if detail else 64);B.beam('azure',(7.4*math.cos(a),7.4*math.sin(a),8.4),(9.47*math.cos(a),9.47*math.sin(a),8.18),.045,6)
 T.curved_roof(B,9.6,.53,8.6,17.72,288)
 profile=[(17.72,.53),(17.90,.63),(18.06,.48),(18.23,.39),(18.37,.51),(18.6,.66),(18.91,.73),(19.20,.59),(19.42,.31),(19.5,0.005)]
 for (z,r),(zz,rr)in zip(profile,profile[1:]):B.cylinder('gold',r,z,zz,48 if detail else 24,rr,caps=False)
 # South plaque hangs below the eave, with correctly named gold lettering.
 B.box('gold',(0,-8.65,7.51),(1.57,.16,1.78));B.box('plaque',(0,-8.77,7.51),(1.37,.1,1.59))
 colors={'stone':(.56,.53,.46),'stoneLight':(.69,.66,.57),'stoneShade':(.43,.41,.36),'roof':(.016,.032,.065),'tile':(.030,.053,.096),'roofEdge':(.015,.032,.061),'red':(.35,.033,.023),'redDark':(.22,.031,.019),'gold':(.72,.48,.09),'goldMuted':(.55,.34,.085),'woodGold':(.39,.22,.065),'jade':(.023,.15,.08),'blue':(.02,.08,.15),'azure':(.03,.13,.20),'shade':(.021,.017,.015),'plaque':(.016,.032,.12),'frieze':(.025,.1,.17),'brick':(.23,.23,.21)}
 mats={}
 for k in B.groups:
  tex=R/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else R/'public/assets/palace/marble.png'if k=='stone'else None;mats[k]=T.mat('Imperial Vault '+k,colors[k],.5 if k in ['roof','tile']else .82,.65 if k=='gold'else 0,texture=tex)
  if tex:next(n for n in mats[k].node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
 for k,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new('Imperial Vault '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mats[k]);uv=me.uv_layers.new()
  for poly,coords in zip(me.polygons,uvs):
   for i,co in zip(poly.loop_indices,coords):uv.data[i].uv=co
  o=bpy.data.objects.new('Imperial Vault '+k,me);scene.collection.objects.link(o)
 font=bpy.data.fonts.load(str(R/'data/imperial-vault-plaque.ttf'))
 for i,ch in enumerate('皇穹宇'):
  c=bpy.data.curves.new('Vault plaque '+ch,'FONT');c.body=ch;c.size=.004;c.extrude=.00001;c.align_x='CENTER';c.font=font;o=bpy.data.objects.new('Vault plaque '+ch,c);scene.collection.objects.link(o);o.location=(0,-.08846,.0793-i*.0050);o.rotation_euler=(math.pi/2,0,0);c.materials.append(mats['gold'])
  for ob in scene.objects:ob.select_set(False)
  o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target=next(v.identifier for v in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if v.identifier=='MESH'))
 for ob in scene.objects:ob.select_set(True)
 bpy.context.view_layer.update();import io_scene_gltf2;fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');imfmt=next(v.identifier for v in bpy.ops.export_scene.gltf.get_rna_type().properties['export_image_format'].enum_items if v.identifier=='JPEG');path=O/(level+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_image_format=imfmt,export_jpeg_quality=90,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20)
 corners=[o.matrix_world@Vector(v)for o in scene.objects for v in o.bound_box];stats={'level':level,'meshes':len(scene.objects),'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'bounds':[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]],'heightMetres':19.5,'bodyDiameterMetres':15.6,'roofTiers':1,'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12]};(Q/(level+'.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(Q/('皇穹宇_'+level+'.blend')),{scene},fake_user=True);print(stats)
if __name__=='__main__':build(False);build(True)
