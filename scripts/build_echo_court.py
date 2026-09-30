"""Echo Wall court: mapped plan, documented wall dimensions, inferred architectural details."""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];P=json.loads((R/'data/echo-court-plan.json').read_text());O=R/'public/assets/echo-court';Q=R/'output/echo-court';O.mkdir(exist_ok=True);Q.mkdir(exist_ok=True)
def module(name,file):
 s=importlib.util.spec_from_file_location(name,R/'scripts'/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
T=module('echo_helpers','build_tiantan_detail.py');H=module('echo_roof','build_tiananmen_detail.py')
def merge(B,C,center=(0,0),angle=0,scale=1):
 ca,sa=math.cos(angle),math.sin(angle)
 for key,(vs,fs,uvs)in C.groups.items():
  for face,uv in zip(fs,uvs):
   points=[]
   for idx in face:
    x,y,z=vs[idx];points.append((center[0]+scale*(x*ca-y*sa),center[1]+scale*(x*sa+y*ca),scale*z))
   B.face(key,points,uv)
def roof(B,hx,hy,z,top):
 # Hipped roofs on each freestanding southern gate, with a curved eave.
 n=16 if B.detail else 8;ridge=max(.15,hx-hy)
 def p(t,side,along):
  x=(hx-(hx-ridge)*t)*along;y=side*hy*(1-t);zz=z+(top-z)*t**1.65+.16*abs(along)**12*(1-t)**6;return(x,y,zz)
 for side in [-1,1]:
  for j in range(n):
   a,b=j/n,(j+1)/n
   for i in range(36 if B.detail else 12):
    count=36 if B.detail else 12;u,v=-1+2*i/count,-1+2*(i+1)/count;ps=[p(a,side,u),p(a,side,v),p(b,side,v),p(b,side,u)];B.face('roof',ps if side<0 else ps[::-1]);B.beam('tile',p(a,side,(u+v)/2),p(b,side,(u+v)/2),.045,5)
   for sign in [-1,1]:
    ps=[p(a,-1,sign),p(a,1,sign),p(b,1,sign),p(b,-1,sign)];B.face('roof',ps if sign>0 else ps[::-1])
    B.beam('tile',p(a,side,sign),p(b,side,sign),.08,6)
 B.box('tile',(0,0,top+.10),(ridge*2,.22,.2))
 for sign in [-1,1]:
  B.box('tile',(sign*ridge,0,top+.35),(.25,.3,.5));B.beam('tile',(sign*ridge,0,top+.5),(sign*(ridge+.2),0,top+.7),.1,6)
def gate(B,width,depth):
 r=.98;spring=1.9;h=3.5
 for side in [-1,1]:B.box('brick',(side*(width/2+r)/2,0,h/2),(width/2-r,depth,h))
 n=32 if B.detail else 16
 for i in range(n):
  a,b=math.pi*i/n,math.pi*(i+1)/n;x0,x1=r*math.cos(a),r*math.cos(b);z0,z1=spring+r*math.sin(a),spring+r*math.sin(b)
  for side in [-1,1]:
   y=side*depth/2;ps=[(x0,y,z0),(x1,y,z1),(x1,y,h),(x0,y,h)];B.face('brick',ps if side>0 else ps[::-1]);rr=r+.20
   ps=[(x0,y+side*.015,z0),(x1,y+side*.015,z1),(rr*math.cos(b),y+side*.015,spring+rr*math.sin(b)),(rr*math.cos(a),y+side*.015,spring+rr*math.sin(a))];B.face('stone',ps if side>0 else ps[::-1])
  B.face('stone',[(x0,-depth/2,z0),(x0,depth/2,z0),(x1,depth/2,z1),(x1,-depth/2,z1)])
 for side in [-1,1]:
  B.box('stone',(side*(r+.1),0,spring/2),(.2,depth+.04,spring))
  # Door leaves folded against the passage sides, preserving a real through opening.
  B.box('red',(side*.92,.20,1.40),(.10,1.2,2.8))
  for j in range(6):
   for k in range(4):B.box('gold',(side*.855,-.28+k*.29,.35+j*.42),(.045,.045,.045))
 B.box('jade',(0,0,3.57),(width+.08,depth+.14,.14));B.box('frieze',(0,0,3.85),(width+.24,depth+.32,.38))
 for x in [(-width/2)+i*width/8 for i in range(9)]:
  for side in [-1,1]:
   for z,w in [(4.02,.24),(4.12,.38),(4.23,.50)]:B.box('jade',(x,side*depth/2,z),(w,.55,.1))
 roof(B,width/2+.38,depth/2+.60,4.3,5.25)
def annex(B,length,depth):
 floor=.55;top=3.75;hx=length/2;hy=depth/2
 B.box('stone',(0,0,.25),(length+.55,depth+.65,.5));B.box('brick',(0,.15,1.97),(length-.25,depth-.40,2.85))
 # Five-bay facade on the court-facing side; decorative detailing is interpretive.
 for i in range(6):
  x=-hx+.3+i*(length-.6)/5;B.cylinder('red',.13,floor,top,10,.11,(x,-hy-.02));B.cylinder('stone',.19,floor,floor+.20,8,.16,(x,-hy-.02))
 for i in range(5):
  x=-hx+.3+(i+.5)*(length-.6)/5;w=(length-.6)/5-.25;B.box('redDark',(x,-hy-.03,1.95),(w,.12,2.8));B.box('shade',(x,-hy-.105,2.25),(w-.25,.045,1.85))
  for j in range(9 if B.detail else 4):
   c=9 if B.detail else 4;B.box('red',(x-w/2+.15+j*(w-.3)/(c-1),-hy-.14,2.25),(.04,.04,1.88))
  for z in [1.3,1.75,2.2,2.65,3.15]:B.box('red',(x,-hy-.14,z),(w-.22,.05,.045))
 B.box('frieze',(0,0,3.68),(length+.12,depth+.25,.42))
 for side in [-1,1]:
  for i in range(12):
   x=-hx+.2+i*(length-.4)/11
   for z,w in [(3.90,.24),(4.02,.40),(4.14,.60)]:B.box('jade',(x,side*(hy-.15),z),(w,.65,.11))
 C=T.Builder(B.detail);H.roof(C,(hx+.55)*2,(hy+.65)*2,4.3*2,6.1*2);merge(B,C,scale=.5)
 # Broad low entry stair; count is an inferred representation.
 for i in range(4):B.box('stone',(0,-hy-.95+i*.22,(i+1)*.55/8),(length-.8,.23,(i+1)*.55/4))
def build(detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get('Echo Court '+level)or bpy.data.scenes.new('Echo Court '+level);bpy.context.window.scene=scene
 for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
 B=T.Builder(detail);cx,cy=P['center'];points=[((x-cx)*100,(y-cy)*100)for x,y in P['wall']]
 # Paved court follows the mapped wall, no rectangular slab beyond the enclosure.
 from mathutils.geometry import tessellate_polygon
 poly=[Vector((x,y,.035))for x,y in points]
 for tri in tessellate_polygon([poly]):B.face('paving',[tuple(poly[v] if isinstance(v,int) else v)for v in tri])
 if detail:
  for line in P.get('pavingJoints',[]):
   a,b=line[0],line[-1];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length*.008,dx/length*.008
   B.face('pavingJoint',[(a[0]-nx,a[1]-ny,.038),(b[0]-nx,b[1]-ny,.038),(b[0]+nx,b[1]+ny,.038),(a[0]+nx,a[1]+ny,.038)])
 for j,(a,b)in enumerate(zip(points,points[1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);nx,ny=-dy/l,dx/l;angle=math.atan2(dy,dx);mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
  B.box('brick',(*mid,1.64),(l+.025,.9,3.28),angle)
  B.box('stoneDark',(*mid,.12),(l+.035,1.02,.24),angle)
  for side in [-1,1]:
   p0=(a[0]+nx*side*.58,a[1]+ny*side*.58,3.37);p1=(b[0]+nx*side*.58,b[1]+ny*side*.58,3.37);q1=(*b,3.67);q0=(*a,3.67);B.face('roof',[p0,p1,q1,q0]if side>0 else[p0,q0,q1,p1])
   if detail:
    for t in [.15,.5,.85]:B.beam('tile',(a[0]+dx*t+nx*side*.58,a[1]+dy*t+ny*side*.58,3.4),(a[0]+dx*t,a[1]+dy*t,3.69),.034,5)
  B.beam('tile',(*a,3.67),(*b,3.67),.05,6)
  if detail:
   for z in [.4+i*.22 for i in range(13)]:
    for side in [-1,1]:B.beam('mortar',(a[0]+nx*side*.455,a[1]+ny*side*.455,z),(b[0]+nx*side*.455,b[1]+ny*side*.455,z),.008,4)
 for p in P['parts']:
  pos=((p['center'][0]-cx)*100,(p['center'][1]-cy)*100);angle=p['angle'];C=T.Builder(detail)
  if p['osmId']==43921123:
   gap=.40;w=(p['length']-2*gap)/3
   for i in [-1,0,1]:
    G=T.Builder(detail);gate(G,w,p['depth']);merge(C,G,(i*(w+gap),0))
   for side in [-1,1]:C.box('brick',(side*(w+gap)/2,0,1.4),(gap,p['depth'],2.8))
  else:
   # Turn the decorated negative-Y facade toward the centre of the enclosure.
   front=(math.sin(angle),-math.cos(angle));toward=(-pos[0],-pos[1])
   if front[0]*toward[0]+front[1]*toward[1]<0:angle+=math.pi
   annex(C,p['length'],p['depth'])
  merge(B,C,pos,angle)
 colors={'pavingJoint':(.28,.28,.26),'brick':(.28,.28,.245),'stone':(.65,.63,.56),'stoneDark':(.35,.35,.31),'paving':(.39,.385,.35),'mortar':(.21,.21,.185),'roof':(.018,.039,.085),'tile':(.035,.075,.14),'gold':(.06,.105,.15),'red':(.36,.035,.024),'redDark':(.23,.029,.016),'shade':(.023,.022,.018),'jade':(.03,.16,.11),'frieze':(.04,.13,.18)}
 for k,(vs,fs,uvs)in B.groups.items():
  tex=R/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else None;mat=T.mat('Echo court '+k,colors[k],.55 if k in ['roof','tile']else .85,0,texture=tex)
  if tex:next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
  me=bpy.data.meshes.new('Echo court '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mat);uv=me.uv_layers.new()
  for poly,coords in zip(me.polygons,uvs):
   for i,co in zip(poly.loop_indices,coords):uv.data[i].uv=co
  ob=bpy.data.objects.new('Echo court '+k,me);scene.collection.objects.link(ob);ob.select_set(True)
 bpy.context.view_layer.update();import io_scene_gltf2;fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');imfmt=next(v.identifier for v in bpy.ops.export_scene.gltf.get_rna_type().properties['export_image_format'].enum_items if v.identifier=='JPEG');path=O/(level+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_image_format=imfmt,export_jpeg_quality=90,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20)
 corners=[ob.matrix_world@Vector(v)for ob in scene.objects for v in ob.bound_box];stats={'level':level,'meshes':len(scene.objects),'triangles':sum(len(p.vertices)-2 for ob in scene.objects for p in ob.data.polygons),'bounds':[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]],'sourceIds':[43921113,43921117,43921122,43921123],'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12]};(Q/(level+'.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(Q/('回音壁院落_'+level+'.blend')),{scene},fake_user=True);print(stats)
if __name__=='__main__':build(False);build(True)
