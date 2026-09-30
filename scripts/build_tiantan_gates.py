"""Photo-informed Chengzhen gatehouse and inner/outer northern Lingxing gates."""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];P=json.loads((R/'data/tiantan-gates-plan.json').read_text());O=R/'public/assets/tiantan-gates';Q=R/'output/tiantan-gates';O.mkdir(exist_ok=True);Q.mkdir(exist_ok=True)
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,R/'scripts'/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
E=mod('gates_echo_helpers','build_echo_court.py');T=E.T;H=E.H

def hall(B,p):
 L,D=p['length']-1.0,p['depth']-1.25;wall=5.70;arches=[(-L*.30,1.32,2.78),(0,1.57,3.00),(L*.30,1.32,2.78)]
 ends=[-L/2]+[v for x,r,z in arches for v in [x-r,x+r]]+[L/2]
 for a,b in zip(ends[::2],ends[1::2]):
  B.box('red',((a+b)/2,0,wall/2),(b-a,D,wall));B.box('base',((a+b)/2,0,.40),(b-a+.02,D+.025,.8))
 for x,r,z in arches:
  n=40 if B.detail else 20
  for i in range(n):
   a,b=math.pi*i/n,math.pi*(i+1)/n;xa,xb=x+r*math.cos(a),x+r*math.cos(b);za,zb=z+r*math.sin(a),z+r*math.sin(b)
   for side in [-1,1]:
    y=side*D/2;ps=[(xa,y,za),(xb,y,zb),(xb,y,wall),(xa,y,wall)];B.face('red',ps if side>0 else ps[::-1])
   B.face('ochre',[(xa,-D/2,za),(xa,D/2,za),(xb,D/2,zb),(xb,-D/2,zb)])
  for side in [-1,1]:B.face('ochre',[(x+side*r,-D/2,0),(x+side*r,D/2,0),(x+side*r,D/2,z),(x+side*r,-D/2,z)])
  # Door panels folded along the tunnel sides, preserving all three through passages.
  for side in [-1,1]:
   B.box('redDark',(x+side*(r-.09),.45,1.35),(.12,r*1.45,2.7))
   if B.detail:
    for j in range(8):
     for k in range(5):B.box('metal',(x+side*(r-.17),.45-r*.60+k*r*.30,.25+j*.31),(.035,.045,.045))
 B.box('frieze',(0,0,6.02),(L+.04,D+.04,.64))
 for side in [-1,1]:
  for i in range(21):
   x=-L/2+.2+i*(L-.4)/20
   for z,w,d in [(6.38,.28,.6),(6.54,.44,.92),(6.71,.66,1.2)]:B.box('jade',(x,side*(D/2-.08),z),(w,d,.14))
   B.box('blue',(x,side*(D/2+.12),6.51),(.16,1.2,.28))
  for i in range(100 if B.detail else 32):
   x=-L/2+i*L/(99 if B.detail else 31);B.beam('redDark',(x,side*(D/2-.4),7.10),(x,side*(D/2+.70),6.96),.065,6)
 C=T.Builder(B.detail);H.roof(C,(L/2+.75)/.65,(D/2+.9)/.65,7.15/.65,10.3/.65);E.merge(B,C,scale=.65)
 # Narrow sill and two broad approaches, leaving the pedestrian route at ground level.
 for side in [-1,1]:
  B.box('stone',(0,side*(D/2+.15),.055),(L+.7,.3,.11))
  B.box('plaqueRim',(0,side*(D/2+.045),6.02),(3.65,.11,.72));B.box('plaque',(0,side*(D/2+.115),6.02),(3.42,.045,.52))
 return arches

def ornament(B,x,z,side):
 # Carved cloud silhouette, extruded through the white-stone lintel plane.
 outline=[(0,0),(.23,.08),(.50,.06),(.69,.20),(.72,.39),(.59,.60),(.33,.76),(.10,.82),(-.07,.69),(-.16,.49),(-.12,.28)]
 anchors=outline;outline=[]
 for i,p1 in enumerate(anchors):
  p0,p2,p3=anchors[(i-1)%len(anchors)],anchors[(i+1)%len(anchors)],anchors[(i+2)%len(anchors)]
  for k in range(6 if B.detail else 3):
   t=k/(6 if B.detail else 3);outline.append(tuple(.5*(2*p1[j]+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t*t+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t*t*t)for j in range(2)))
 for front in [-1,1]:
  pts=[(x+side*a,front*.20,z+b)for a,b in outline]
  for i in range(1,len(pts)-1):B.face('stone',[pts[0],pts[i],pts[i+1]]if front<0 else[pts[0],pts[i+1],pts[i]])
 for a,b in zip(outline,outline[1:]+outline[:1]):B.face('stone',[(x+side*a[0],-.20,z+a[1]),(x+side*b[0],-.20,z+b[1]),(x+side*b[0],.20,z+b[1]),(x+side*a[0],.20,z+a[1])])
 if B.detail:
  for front in [-1,1]:
   last=None
   for i in range(32):
    t=i/31*math.pi*3.5;r=.25*(1-i/38);pt=(x+side*(.25+r*math.cos(t)),front*.213,z+.40+r*math.sin(t))
    if last:B.beam('relief',last,pt,.025,5)
    last=pt

def lingxing(B,p):
 L=p['length'];pitch=L*.34;centers=[-pitch,0,pitch];w=L*.155
 for i,x in enumerate(centers):
  h=4.35 if i==1 else 3.62
  for side in [-1,1]:
   xx=x+side*w/2
   for z,sx,sy,hh in [(.14,.72,.9,.28),(.38,.56,.7,.22),(h/2,.42,.48,h-.6),(h-.25,.49,.55,.16),(h+.13,.42,.48,.43)]:B.box('stone',(xx,0,z),(sx,sy,hh))
   # Lotus/bud cap, built as a curved stone profile rather than a cube.
   prof=[(h+.34,.20),(h+.44,.24),(h+.65,.26),(h+.80,.18),(h+.98,.065),(h+1.04,.015)]
   for (z,r),(zz,rr)in zip(prof,prof[1:]):B.cylinder('stone',r,z,zz,64 if B.detail else 24,rr,(xx,0),caps=False)
   for front in [-1,1]:
    B.box('relief',(xx,front*.248,h-.50),(.31,.02,.22))
    if B.detail:
     for j in range(7):
      a=j*math.tau/7;B.beam('relief',(xx+.12*math.cos(a),front*.265,h-.51+.08*math.sin(a)),(xx+.03*math.cos(a),front*.265,h-.43),.018,5)
   ornament(B,xx,h-.65,side)
   ornament(B,xx,h-.85,-side)
  for z,hh,depth in [(h-1.48,.18,.62),(h-1.14,.48,.39),(h-.80,.22,.47)]:B.box('stone',(x,0,z),(w+.66,depth,hh))
  for front in [-1,1]:
   B.box('recess',(x,front*.206,h-1.14),(w-.13,.015,.27))
   if B.detail:
    for k in range(8):
     xx=x-w*.42+k*w*.12;B.box('relief',(xx,front*.219,h-1.14),(.055,.018,.20))
  if p['kind']=='outer':
   # Closed central ceremonial leaves; side leaves open against their posts.
   doorheight=h-1.60
   if i==1:
    for side in [-1,1]:
     xx=x+side*w*.25;dw=w*.5-.02;B.box('redDark',(xx,.12,doorheight/2+.12),(dw,.15,doorheight))
     for z in [.3,.8,doorheight-.2]:B.box('metal',(xx,.025,z),(dw-.13,.026,.025))
     for k in range(6):B.box('metal',(xx-dw*.4+k*dw*.16,.02,1.05),(.025,.035,.035))
     B.beam('red',(xx-dw*.4,.02,.95),(xx+dw*.4,.02,doorheight-.45),.035,4)
   else:
    for side in [-1,1]:B.box('redDark',(x+side*(w/2-.12),.65,doorheight/2+.12),(.12,w*.47,doorheight))
 for a,b in zip(centers,centers[1:]):
  x0,x1=a+w/2+.23,b-w/2-.23;B.box('red',((x0+x1)/2,0,.62),(x1-x0,.50,1.18));B.box('base',((x0+x1)/2,0,.12),(x1-x0,.59,.24))
  for side in [-1,1]:B.face('blueRoof',[(x0,side*.40,1.22),(x1,side*.40,1.22),(x1,0,1.52),(x0,0,1.52)])
  B.beam('blueTile',(x0,0,1.53),(x1,0,1.53),.065,6)
  for k in range(max(8,round((x1-x0)/(.16 if B.detail else .5)))):
   count=max(8,round((x1-x0)/(.16 if B.detail else .5)));xx=x0+(k+.5)*(x1-x0)/count
   for side in [-1,1]:B.beam('blueTile',(xx,side*.40,1.24),(xx,0,1.54),.045,6)
 return centers,w

def build(p,detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get(p['id']+' '+level)or bpy.data.scenes.new(p['id']+' '+level);bpy.context.window.scene=scene
 for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
 B=T.Builder(detail);hall(B,p)if p['kind']=='hall'else lingxing(B,p)
 colors={'red':(.42,.045,.027),'redDark':(.27,.031,.02),'base':(.22,.23,.20),'ochre':(.48,.35,.13),'frieze':(.03,.12,.15),'jade':(.028,.15,.11),'blue':(.02,.07,.17),'roof':(.033,.095,.054),'tile':(.07,.16,.085),'gold':(.10,.19,.095),'stone':(.66,.63,.54),'relief':(.72,.69,.60),'recess':(.48,.46,.40),'blueRoof':(.018,.034,.065),'blueTile':(.033,.06,.105),'metal':(.62,.40,.075),'plaque':(.16,.14,.105),'plaqueRim':(.37,.045,.023)}
 mats={}
 for k,(vs,fs,uvs)in B.groups.items():
  tex=R/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else R/'public/assets/palace/marble.png'if k=='stone'else None;m=T.mat(p['id']+' '+k,colors[k],.55 if k in ['roof','tile']else .83,.55 if k=='metal'else 0,texture=tex);mats[k]=m
  if tex:next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
  me=bpy.data.meshes.new(p['id']+' '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(m);uv=me.uv_layers.new()
  for poly,coords in zip(me.polygons,uvs):
   for idx,co in zip(poly.loop_indices,coords):uv.data[idx].uv=co
  ob=bpy.data.objects.new(p['id']+' '+k,me);scene.collection.objects.link(ob)
 if p['kind']=='hall':
  if 'metal' not in mats:mats['metal']=T.mat(p['id']+' metal',colors['metal'],.5,.55)
  font=bpy.data.fonts.load(str(R/'data/chengzhen-plaque-traditional.ttf'))
  for side in [-1,1]:
   for i,ch in enumerate('門貞成'):
    c=bpy.data.curves.new('成贞门牌匾 '+ch,'FONT');c.body=ch;c.font=font;c.size=.0041;c.extrude=.000008;c.align_x='CENTER';o=bpy.data.objects.new('成贞门牌匾 '+ch,c);scene.collection.objects.link(o);o.location=((i-1)*.008*(-side),side*((p['depth']-1.25)/2+.15)/100,.0588);o.rotation_euler=(math.pi/2,0,math.pi if side==1 else 0);c.materials.append(mats['metal'])
    for ob in scene.objects:ob.select_set(False)
    o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target=next(v.identifier for v in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if v.identifier=='MESH'))
 for ob in scene.objects:ob.select_set(True)
 bpy.context.view_layer.update();import io_scene_gltf2;fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');imfmt=next(v.identifier for v in bpy.ops.export_scene.gltf.get_rna_type().properties['export_image_format'].enum_items if v.identifier=='JPEG');path=O/(p['id']+'-'+level+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_image_format=imfmt,export_jpeg_quality=90,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20)
 corners=[ob.matrix_world@Vector(v)for ob in scene.objects for v in ob.bound_box];stats={'id':p['id'],'level':level,'meshes':len(scene.objects),'triangles':sum(len(f.vertices)-2 for ob in scene.objects for f in ob.data.polygons),'bounds':[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]],'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12]};(Q/(p['id']+'-'+level+'.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(Q/(p['name']+'_'+level+'.blend')),{scene},fake_user=True);print(stats)
if __name__=='__main__':
 for p in P['parts']:
  for detail in [False,True]:build(p,detail)
