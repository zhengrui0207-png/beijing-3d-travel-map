"""Photo-informed Tiananmen, local metres; map units = 100 m.
OSM footprint / 34.7 m documented height; other dimensions inferred.
Portrait texture: Daniel Case, CC BY-SA 3.0. Decorative frieze is generated.
"""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/assets/tiananmen-detail';OUT.mkdir(exist_ok=True)
PROOF=ROOT/'output/tiananmen-detail';PROOF.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('tiananmen_helpers',ROOT/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(spec);sys.modules[spec.name]=T;spec.loader.exec_module(T)
plan=json.loads((ROOT/'data/tiananmen-footprint.json').read_text());p,q,r=plan['rect'][:3]
L=math.dist(p,q)*100;D=math.dist(q,r)*100

def roof(B,hx,hy,rb,peak,lower=False,cx=0,cy=0):
 join=.38;ridge=hx-hy*.52;steps=18 if B.detail else 9
 # Upper gabled roof and lower hipped eave skirt have distinct silhouettes.
 def section(t):return(hx-(hx-ridge)*min(t/join,1),hy*(1-t),rb+(peak-rb)*t**1.55)
 def pt(x,y,z,t):return(cx+x,cy+y,z+.38*max(0,abs(x)/hx)**14*max(0,1-t/join)**3)
 end=.46 if lower else 1
 n=max(24,round(2*hx/(.25 if B.detail else .75)))
 for sign in [-1,1]:
  for j in range(steps):
   t,u=end*j/steps,end*(j+1)/steps;ax,ay,az=section(t);bx,by,bz=section(u)
   for i in range(n):
    f,g=-1+2*i/n,-1+2*(i+1)/n
    ps=[pt(ax*f,sign*ay,az,t),pt(ax*g,sign*ay,az,t),pt(bx*g,sign*by,bz,u),pt(bx*f,sign*by,bz,u)]
    B.face('roof',ps if sign<0 else ps[::-1])
    f=(f+g)/2;B.beam('tile',pt(ax*f,sign*ay,az+.07,t),pt(bx*f,sign*by,bz+.07,u),.078,6 if B.detail else 4)
   # Slightly thick eaves do not become a flat heavy shelf.
  for i in range(n):
   x=-hx+(i+.5)*2*hx/n
   B.beam('tile',pt(x,sign*hy,rb+.08,0),pt(x,sign*(hy+.13),rb-.08,0),.12,8)
  for j in range(8 if B.detail else 4):
   count=8 if B.detail else 4;t,u=min(join,end)*j/count,min(join,end)*(j+1)/count
   ax,ay,az=section(t);bx,by,bz=section(u)
   ps=[pt(sign*ax,-ay,az,t),pt(sign*ax,ay,az,t),pt(sign*bx,by,bz,u),pt(sign*bx,-by,bz,u)]
   B.face('roof',ps if sign>0 else ps[::-1])
   for i in range(60 if B.detail else 20):
    f=-1+2*(i+.5)/(60 if B.detail else 20)
    B.beam('tile',pt(sign*ax,f*ay,az+.08,t),pt(sign*bx,f*by,bz+.08,u),.075,6)
  # Two upturned corner ridges, with individually modeled miniature ridge beasts.
  for side in [-1,1]:
   last=None
   for j in range(21):
    t=min(join,end)*j/20;x,y,z=section(t);v=pt(sign*x,side*y,z+.15,t)
    if last:B.beam('gold',last,v,.17,8)
    last=v
   if B.detail:
    for k in range(9):
     t=.045+k*.024;x,y,z=section(t);x=cx+sign*x;y=cy+side*y
     z+=.28+.38*(abs(x-cx)/hx)**14*max(0,1-t/join)**3
     B.box('gold',(x,y,z+.07),(.27,.34,.14))
     B.cylinder('gold',.12,z+.10,z+.42,7,.16,(x,y))
     B.beam('gold',(x,y,z+.35),(x+sign*.08,y+side*.16,z+.57),.12,7)
     B.beam('gold',(x-sign*.1,y-side*.1,z+.27),(x-sign*.23,y-side*.23,z+.52),.055,6)
  if not lower:
   _,yy,zz=section(join);x=cx+sign*ridge
   ps=[(x,cy-yy,zz),(x,cy+yy,zz),(x,cy,peak)];B.face('redDark',ps if sign>0 else ps[::-1])
   for side in [-1,1]:
    for j in range(15):
     t,u=j/15,(j+1)/15
     B.beam('gold',(x,cy+side*yy*(1-t),zz+(peak-zz)*t**1.55+.12),(x,cy+side*yy*(1-u),zz+(peak-zz)*u**1.55+.12),.16,8)
 if not lower:
  B.box('roof',(cx,cy,peak+.19),(2*ridge,.44,.38))
  # Chiwen silhouette with curled tail and a snout embracing the ridge.
  for sign in [-1,1]:
   x=cx+sign*ridge
   for z,w,d,off in [(0,.75,.67,0),(.4,.65,.58,.04),(.8,.57,.52,.12),(1.2,.42,.44,.16)]:
    B.box('gold',(x+sign*off,cy,peak+.38+z),(w,d,.44))
   last=None
   for j in range(18):
    a=j/17*math.pi*1.5;v=(x+sign*(.32+.38*math.sin(a)),cy,peak+1.45+.40*math.cos(a))
    if last:B.beam('gold',last,v,.12,8)
    last=v
   B.beam('gold',(x-sign*.12,cy,peak+.65),(x-sign*.65,cy,peak+.55),.19,8)

def railing(B,a,b,z):
 length=math.dist(a,b);n=math.ceil(length/2.5)
 for i in range(n+1):
  f=i/n;x=a[0]+f*(b[0]-a[0]);y=a[1]+f*(b[1]-a[1])
  B.box('marble',(x,y,z+.63),(.26,.26,1.26));B.cylinder('marble',.20,z+1.23,z+1.48,10,.10,(x,y))
 for zz,rr in [(.18,.08),(.85,.065),(1.07,.08)]:B.beam('marble',(*a,z+zz),(*b,z+zz),rr,6)
 for i in range(n*4):
  f=(i+.5)/(n*4);x=a[0]+f*(b[0]-a[0]);y=a[1]+f*(b[1]-a[1]);B.box('marble',(x,y,z+.52),(.075,.075,.64))

def build(detail=True):
 level='detail'if detail else'preview';name='Tiananmen '+level
 scene=bpy.data.scenes.get(name)or bpy.data.scenes.new(name);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=T.Builder(detail);H=11.5
 # Five full-depth portals: the mass above each arch uses strips, never a blocking cube.
 arches=[(-25.8,2.1,2.9),(-13.8,2.35,3.25),(0,2.9,3.45),(13.8,2.35,3.25),(25.8,2.1,2.9)]
 ends=[-L/2]+[v for x,r,s in arches for v in [x-r,x+r]]+[L/2]
 for a,b in zip(ends[::2],ends[1::2]):
  B.box('wall',((a+b)/2,0,H/2),(b-a,D,H))
  B.box('marble',((a+b)/2,0,.73),(b-a+.01,D+.09,1.46))
 for x,r,spring in arches:
  n=48 if detail else 20
  for i in range(n):
   a=math.pi*i/n;b=math.pi*(i+1)/n
   x0=x+r*math.cos(a);x1=x+r*math.cos(b);z0=spring+r*math.sin(a);z1=spring+r*math.sin(b)
   for side in [-1,1]:
    yy=side*D/2;ps=[(x0,yy,z0),(x1,yy,z1),(x1,yy,H),(x0,yy,H)];B.face('wall',ps if side>0 else ps[::-1])
    # Recessed grey stone arch ring and mortar grooves.
    R=r+.28;ps=[(x+r*math.cos(a),yy+side*.018,spring+r*math.sin(a)),(x+r*math.cos(b),yy+side*.018,spring+r*math.sin(b)),(x+R*math.cos(b),yy+side*.018,spring+R*math.sin(b)),(x+R*math.cos(a),yy+side*.018,spring+R*math.sin(a))];B.face('archStone',ps if side>0 else ps[::-1])
   B.face('vault',[(x0,-D/2,z0),(x0,D/2,z0),(x1,D/2,z1),(x1,-D/2,z1)])
  for sign in [-1,1]:
   B.face('vault',[(x+sign*r,-D/2,0),(x+sign*r,D/2,0),(x+sign*r,D/2,spring),(x+sign*r,-D/2,spring)])
  # Historic doors are recessed at the northern end, leaving the southern arch visible.
  B.box('door',(x,D/2-1.2,2.8),(r*2-.15,.20,5.6))
  for k in range(8):
   xx=x-r+.25+k*(2*r-.5)/7;B.box('redDark',(xx,D/2-1.32,2.8),(.035,.025,5.3))
   if detail:
    for j in range(9):B.beam('gold',(xx,D/2-1.34,.42+j*.54),(xx,D/2-1.39,.42+j*.54),.05,8)
 B.box('marble',(0,0,H+.10),(L+.24,D+.22,.20))
 # Stone coping above red castle wall; deck remains clear around the gallery.
 for side in [-1,1]:
  B.box('marble',(0,side*(D/2+.05),H-.20),(L+.30,.25,.38))
  railing(B,(-L/2+.3,side*(D/2-.4)),(L/2-.3,side*(D/2-.4)),H+.20)
  railing(B,(side*(L/2-.4),-D/2+.3),(side*(L/2-.4),D/2-.3),H+.20)
 # Main nine-bay hall, with ten columns on each long face and six on each short face.
 floor=H+.22;top=19.9;hx=30.8;hy=10.0
 B.box('redDark',(0,0,(floor+top)/2),(57.6,15.0,top-floor))
 for i in range(10):
  x=-hx+2*hx*i/9
  for j in range(6):
   y=-hy+2*hy*j/5
   B.cylinder('red',.40,floor,top,16 if detail else 10,.34,(x,y))
   B.cylinder('marble',.53,floor,floor+.38,12,.44,(x,y))
   if j in [0,5]or i in [0,9]:
    for dz,w in [(0,1.1),(.24,1.55),(.49,2.0)]:B.box('jade'if dz else'blue',(x,y,top-.55+dz),(w,1.2+dz,.18))
 for side in [-1,1]:
  y=side*7.54
  for i in range(9):
   x=-28.8+(i+.5)*57.6/9;w=5.78;z0=floor+.33;z1=18.95
   B.box('window',(x,y,(z0+z1)/2),(w,.07,z1-z0))
   for j in range(5):
    xx=x-w/2+j*w/4;B.box('goldMuted',(xx,y+side*.06,(z0+z1)/2),(.11,.1,z1-z0))
   for z in [z0,z0+1.6,z1]:B.box('jade',(x,y+side*.07,z),(w,.12,.13))
   if detail:
    for j in range(1,24):B.box('jade',(x-w/2+j*w/24,y+side*.07,(z0+1.6+z1)/2),(.025,.05,z1-z0-1.6))
    for j in range(1,12):B.box('jade',(x,y+side*.08,z0+1.6+j*(z1-z0-1.6)/12),(w,.05,.025))
  for z in [19.0,20.0,23.3,24.2]:
   xx=31 if z<22 else 27.8;yy=side*(10.3 if z<22 else 8.025)
   ps=[(-xx,yy,z), (xx,yy,z),(xx,yy,z+.72),(-xx,yy,z+.72)]
   B.face('frieze',ps if side<0 else ps[::-1],[(0,0),(9,0),(9,1),(0,1)]if side<0 else[(0,1),(9,1),(9,0),(0,0)])
 B.box('jade',(0,0,24.5),(56.2,16.0,3.4))
 roof(B,34.9,13.2,21.0,29.2,True)
 roof(B,31.1,10.25,26.0,32.6)
 # Two small terrace guard halls; their dimensions are inferred from front photographs.
 for side in [-1,1]:
  B.box('redDark',(side*43.5,1.0,13.35),(12,8,4.2))
  roof(B,6.9,4.8,15.5,18.0,False,side*43.5,1.0)
 # Portrait is UV-mapped from the architectural part of the attributed photo.
 yy=-D/2-.06
 B.box('goldMuted',(0,yy,8.05),(5.08,.18,6.92))
 B.face('photo',[(-2.4,yy-.105,4.73),(2.4,yy-.105,4.73),(2.4,yy-.105,11.38),(-2.4,yy-.105,11.38)],[(586/1280,1-354/511),(623/1280,1-354/511),(623/1280,1-301/511),(586/1280,1-301/511)])
 for side in [-1,1]:
  B.box('marble',(side*25.0,yy,8.26),(30.1,.17,3.25))
  B.box('banner',(side*25.0,yy-.10,8.26),(29.6,.08,2.84))
 # Circular national emblem, photo UVs isolate the architectural ornament.
 ey=-8.065;ez=24.3;er=.91
 for i in range(40):
  a=math.tau*i/40;b=math.tau*(i+1)/40
  points=[(0,ey,ez),(er*math.cos(a),ey,ez+er*math.sin(a)),(er*math.cos(b),ey,ez+er*math.sin(b))]
  def eu(t):return((597+9.1*math.cos(t))/1280,1-(202-9.1*math.sin(t))/511)
  B.face('photo',points,[(597/1280,1-202/511),eu(a),eu(b)])
 # Restrained cloth flags, static geometry: no people or foreground photo objects.
 for side in [-1,1]:
  for i in range(4):
   x=side*(38+i*5.9);y=-D/2+2;z=H+.22
   B.cylinder('pole',.055,z,z+7.5,8,center=(x,y))
   for j in range(10):
    a=j/10;b=(j+1)/10
    def v(t,h):return(x+2.5*t,y+.27*math.sin(t*math.tau),z+7.1-1.8*h-.42*t)
    B.face('flag',[v(a,1),v(b,1),v(b,0),v(a,0)])
 colors={'wall':(.39,.075,.055),'marble':(.69,.66,.57),'archStone':(.19,.19,.14),'vault':(.12,.11,.085),'door':(.075,.10,.075),'red':(.34,.025,.012),'redDark':(.16,.027,.016),'roof':(.61,.29,.045),'tile':(.71,.37,.075),'gold':(.55,.27,.025),'goldMuted':(.54,.34,.10),'jade':(.025,.15,.09),'blue':(.015,.06,.105),'window':(.026,.043,.024),'frieze':(.06,.13,.08),'photo':(1,1,1),'banner':(.59,.015,.008),'flag':(.67,.012,.005),'pole':(.43,.45,.41),'letter':(.92,.90,.79)}
 mats={}
 for key,c in colors.items():
  texture=ROOT/'data/landmark-references/tiananmen-0.jpg'if key=='photo'else ROOT/'public/assets/tiantan-detail/frieze.png'if key=='frieze'else None
  mats[key]=T.mat('Tiananmen '+key,c,.55 if key in ['roof','tile','gold']else .86,texture=texture)
  if key in ['photo','frieze']:
   node=next(n for n in mats[key].node_tree.nodes if n.type=='TEX_IMAGE');node.image.pack()
 for key,(verts,faces,uvs)in B.groups.items():
  me=bpy.data.meshes.new('Tiananmen '+key);me.from_pydata([(x/100,y/100,z/100)for x,y,z in verts],[],faces);me.update();me.materials.append(mats[key]);uv=me.uv_layers.new(name='Architectural materials')
  for poly,coords in zip(me.polygons,uvs):
   for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
  o=bpy.data.objects.new('Tiananmen '+key,me);scene.collection.objects.link(o)
 # Plain modern glyphs for the two banners; no claim of exact historical calligraphy.
 fontpath=ROOT/'data/tiananmen-banner.ttf';font=bpy.data.fonts.load(str(fontpath))if fontpath.exists()else None
 for x,body in [(-25,'中华人民共和国万岁'),(25,'世界人民大团结万岁')]:
  c=bpy.data.curves.new('Tiananmen banner text','FONT');c.body=body;c.align_x='CENTER';c.size=.0205;c.extrude=.00002
  if font:c.font=font
  o=bpy.data.objects.new('Tiananmen banner text',c);scene.collection.objects.link(o);o.location=(x/100,(yy-.16)/100,7.54/100);o.rotation_euler=(math.pi/2,0,0);c.materials.append(mats['letter'])
 bpy.context.view_layer.update()
 target=next(i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if i.identifier=='MESH')
 for o in list(scene.objects):
  if o.type=='FONT':
   for q in scene.objects:q.select_set(False)
   o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target=target)
 # Documented overall height, uniformly calibrate vertical axis only (unmeasured details).
 corners=[o.matrix_world@Vector(v)for o in scene.objects for v in o.bound_box];maxz=max(v.z for v in corners);factor=.347/maxz
 for o in scene.objects:
  o.location.z*=factor
  for v in o.data.vertices:v.co.z*=factor
 bpy.context.view_layer.update()
 for o in scene.objects:o.select_set(True)
 bpy.context.view_layer.objects.active=next(iter(scene.objects))
 import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB')
 bpy.ops.export_scene.gltf(filepath=str(OUT/(level+'.glb')),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[o.matrix_world@Vector(v)for o in scene.objects for v in o.bound_box];mi=[min(v[i]for v in corners)for i in range(3)];ma=[max(v[i]for v in corners)for i in range(3)]
 stats={'level':level,'footprintMetres':[L,D],'heightMetres':34.7,'portals':5,'columnGrid':[10,6],'frontBays':9,'boundsLocalBlender':[mi,ma],'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'meshes':len(scene.objects),'bytes':(OUT/(level+'.glb')).stat().st_size,'sha':hashlib.sha256((OUT/(level+'.glb')).read_bytes()).hexdigest()[:12]}
 (PROOF/(level+'-audit.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(PROOF/('天安门_'+level+'.blend')),{scene},fake_user=True);print(stats)
 return scene
if __name__=='__main__':build(False);build(True)
