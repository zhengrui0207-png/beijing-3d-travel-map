"""Photo-informed Wumen: DPM main hall proportions; OSM geographic plan.
Not photogrammetry: tile spacing, ornaments, gallery heights and portals inferred.
"""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/wumen-detail';OUT.mkdir(exist_ok=True);PROOF=ROOT/'output/wumen-detail';PROOF.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('wumen_helpers',ROOT/'scripts/build_tiananmen_detail.py');H=importlib.util.module_from_spec(s);sys.modules[s.name]=H;s.loader.exec_module(H);T=H.T
P=json.loads((ROOT/'data/wumen-plan.json').read_text())
def roof(B,hx,hy,z,peak,cx=0,cy=0,lower=False,pyramid=False,angle=0):
 # Four continuous curved hip slopes. Lower eave is an annular skirt, no gable.
 ridge=0 if pyramid else max(0,hx-hy*.92);end=.42 if lower else 1;steps=10 if B.detail else 5;ca,sa=math.cos(angle),math.sin(angle)
 def transform(x,y,zz):return(cx+x*ca-y*sa,cy+x*sa+y*ca,zz)
 def point(side,u,t):
  xx=hx*(1-t)+ridge*t;yy=hy*(1-t);zz=z+(peak-z)*(t**1.5)+.60*abs(u)**12*(1-t)**4
  if side<2:x,y=u*xx,(-1 if side==0 else 1)*yy
  else:x,y=(-1 if side==2 else 1)*xx,u*yy
  return transform(x,y,zz)
 for side in range(4):
  n=max(4,round(2*(hx if side<2 else hy)/(.34 if B.detail else 1.1)))
  for i in range(n):
   a,b=-1+2*i/n,-1+2*(i+1)/n
   for j in range(steps):
    t,v=end*j/steps,end*(j+1)/steps;ps=[point(side,a,t),point(side,b,t),point(side,b,v),point(side,a,v)]
    # Orient every roof slope upward.
    if (Vector(ps[1])-Vector(ps[0])).cross(Vector(ps[2])-Vector(ps[0])).z<0:ps.reverse()
    B.face('roof',ps)
    q,r=point(side,(a+b)/2,t),point(side,(a+b)/2,v);B.beam('tile',(q[0],q[1],q[2]+.045),(r[0],r[1],r[2]+.045),.052 if B.detail else .065,5)
   q=point(side,(a+b)/2,0);B.cylinder('gold',.095,q[2]-.15,q[2]+.03,7,.065,(q[0],q[1]))
  for j in range(n):B.beam('gold',point(side,-1+2*j/n,0),point(side,-1+2*(j+1)/n,0),.12,6)
 # Corner ridges follow the same swept roof surface.
 for side in [0,1]:
  for u in [-1,1]:
   for j in range(steps):B.beam('gold',point(side,u,end*j/steps),point(side,u,end*(j+1)/steps),.14,7)
   if B.detail:
    for j in range(1,8):
     q=point(side,u,.035*j);B.cylinder('gold',.11,q[2]+.1,q[2]+.39,7,.065,(q[0],q[1]))
 if not lower:
  if pyramid:B.cylinder('gold',.32,peak-.03,peak+1.0,12,.08,(cx,cy))
  else:
   B.beam('gold',transform(-ridge,0,peak+.12),transform(ridge,0,peak+.12),.22,10)
   for sign in [-1,1]:
    # Curved ridge-end chiwen silhouette; not a conservation sculpt.
    pts=[transform(sign*(ridge+.1+t*.45),0,peak+.1+t*1.05)for t in [0,.25,.5,.75,1]]
    for a,b in zip(pts,pts[1:]):B.beam('gold',a,b,.24,8)
def hall(B,cx,cy,l,d,floor,eave,bays,angle=0):
 ca,sa=math.cos(angle),math.sin(angle)
 def p(x,y,z):return(cx+x*ca-y*sa,cy+x*sa+y*ca,z)
 # Local panel boxes transform once; keep separate dark window recesses and timber frames.
 def box(key,pos,size):
  before={k:len(v[0])for k,v in B.groups.items()};B.box(key,pos,size)
  vs=B.groups[key][0]
  for i in range(before.get(key,0),len(vs)):vs[i]=p(*vs[i])
 box('redDark',(0,0,(floor+eave)/2),(l-2,d-2,eave-floor))
 for side in [-1,1]:
  for i in range(bays+1):
   x=-l/2+l*i/bays;q=p(x,side*d/2,0);B.cylinder('red',.32,floor,eave,14 if B.detail else 8,.29,(q[0],q[1]));B.cylinder('marble',.4,floor,floor+.3,10,.36,(q[0],q[1]))
   for dz,w in [(0,.7),(.24,1.1),(.48,1.55)]:box('jade',(x,side*d/2,eave-.65+dz),(w,1.1,.16))
  for i in range(bays):
   x=-l/2+(i+.5)*l/bays;w=l/bays-.52;y=side*(d/2-.92);h=eave-floor-1.15
   box('window',(x,y,floor+h/2+.25),(w,.08,h))
   for j in range(5):box('red',(x-w/2+j*w/4,y+side*.08,floor+h/2+.25),(.09,.10,h))
   for zz in [floor+.25,floor+1.4,floor+h+.25]:box('goldMuted',(x,y+side*.1,zz),(w,.07,.07))
   if B.detail:
    for j in range(1,18):box('lattice',(x-w/2+j*w/18,y+side*.12,floor+(h+1.4)/2),(.028,.04,h-1.4))
    for j in range(1,9):box('lattice',(x,y+side*.13,floor+1.4+j*(h-1.4)/9),(w,.04,.028))
  # Repeating painted fascia texture is representative, not photographed restoration art.
  y=side*(d/2+.05);ps=[p(-l/2,y,eave-.3),p(l/2,y,eave-.3),p(l/2,y,eave+.45),p(-l/2,y,eave+.45)];B.face('frieze',ps if side<0 else ps[::-1],[(0,0),(bays,0),(bays,1),(0,1)] if side<0 else [(0,1),(bays,1),(bays,0),(0,0)])
def build(detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get('Wumen '+level)or bpy.data.scenes.new('Wumen '+level);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=T.Builder(detail)
 for part in P['platform']:
  for tri in part['triangles']:B.face('deck',[(x,y,12)for x,y in tri])
  for a,b in zip(part['ring'],part['ring'][1:]):
   B.face('wall',[(a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],12),(a[0],a[1],12)])
   B.beam('stone',(a[0],a[1],.22),(b[0],b[1],.22),.24,4)
 # Actual openings through platform: recessed round vault with squared south entry.
 for x,r,spring,y0,y1 in P['portals']:
  n=36 if detail else 16
  for i in range(n):
   a,b=math.pi*i/n,math.pi*(i+1)/n;x0,x1=x+r*math.cos(a),x+r*math.cos(b);z0,z1=spring+r*math.sin(a),spring+r*math.sin(b)
   B.face('vault',[(x0,y0,z0),(x1,y0,z1),(x1,y1,z1),(x0,y1,z0)])
   for y in ([y1]if abs(x)>40 else[y0,y1]):B.face('wall',[(x0,y,z0),(x1,y,z1),(x1,y,12),(x0,y,12)])
  B.box('deck',(x,(y0+y1)/2,11.9),(2*r,y1-y0,.2))
  if abs(x)>40:B.box('wall',((x+math.copysign(37,x))/2,-20,9.8),(abs(x)-37,4,4.4))
  for sign in [-1,1]:B.box('door',(x+sign*(r-.12),y1-2,spring/2),(.15,3.8,spring))
 # Marble balustrades outline the three-sided courtyard wall.
 for a,b in [((-40,-14.7),(40,-14.7)),((-40,-14.7),(-40,-88)),((40,-14.7),(40,-88)),((-61,-88),(-61,7)),((61,-88),(61,7)),((-61,11),(61,11))]:H.railing(B,a,b,12)
 # Main nine-bay, five-deep 60.05 x 25m hall. Crown calibrated to 35.6m.
 hall(B,0,0,60.05,25,12.3,21.8,9)
 B.box('jade',(0,0,26.0),(57.0,21.8,3.9))
 for side in [-1,1]:
  y=side*10.94;ps=[(-28.5,y,25.6),(28.5,y,25.6),(28.5,y,26.8),(-28.5,y,26.8)];B.face('frieze',ps if side<0 else ps[::-1],[(0,0),(9,0),(9,1),(0,1)] if side<0 else [(0,1),(9,1),(9,0),(0,0)])
 roof(B,33.5,16.0,22.1,30.3,lower=True)
 roof(B,30.6,12.8,27.1,34.45)
 # Blue plaque visible between the eaves.
 B.box('gold',(0,-11.13,26.2),(1.75,.15,2.4));B.box('blue',(0,-11.24,26.2),(1.58,.12,2.23))
 # East/west 13-bay wing galleries retain observed OSM axes.
 for key in ['638156484','638156495']:
  p=P['parts'][key];x,y=p['center'];l=p['w'];d=p['d'];hall(B,x,y,l,d,12.2,17.5,13,math.pi/2);roof(B,l/2+1,d/2+1,18,21,cx=x,cy=y,angle=math.pi/2)
 # Four separate double pyramidal-roof corner towers.
 for key in ['638156655','638156665','638156677','638156830']:
  p=P['parts'][key];x,y=p['center'];l,d=p['w'],p['d'];hall(B,x,y,l,d,12.2,19.0,3);B.box('jade',(x,y,22.6),(l-1,d-1,4))
  roof(B,l/2+2.1,d/2+2.1,19.6,27,cx=x,cy=y,lower=True,pyramid=True)
  roof(B,l/2+.9,d/2+.9,24.2,29.7,cx=x,cy=y,pyramid=True)
 # Three-bay connecting bell/drum pavilions on each side of the hall.
 for side in [-1,1]:hall(B,side*39.8,0,15.5,10,12.2,16.5,3);roof(B,8.7,6,17,20,cx=side*39.8)
 colors={'wall':(.45,.085,.050),'deck':(.33,.32,.27),'stone':(.28,.28,.24),'vault':(.13,.10,.08),'door':(.18,.02,.016),'marble':(.77,.75,.67),'red':(.39,.029,.019),'redDark':(.15,.024,.020),'window':(.047,.031,.023),'lattice':(.40,.21,.074),'jade':(.028,.14,.09),'blue':(.018,.048,.12),'roof':(.65,.32,.058),'tile':(.73,.40,.083),'gold':(.67,.38,.057),'goldMuted':(.49,.29,.072),'frieze':(.09,.15,.13)}
 mats={}
 for k,c in colors.items():
  tex=ROOT/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else None;mats[k]=T.mat('Wumen '+k,c,.63 if k in ['roof','tile','gold']else .87,texture=tex)
  if tex:next(n for n in mats[k].node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
 for k,(vs,fs,uvs) in B.groups.items():
  me=bpy.data.meshes.new('Wumen '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mats[k]);uv=me.uv_layers.new(name='Architectural materials')
  for p,coords in zip(me.polygons,uvs):
   for i,co in zip(p.loop_indices,coords):uv.data[i].uv=co
  o=bpy.data.objects.new('Wumen '+k,me);scene.collection.objects.link(o)
 c=bpy.data.curves.new('Wumen plaque','FONT');c.body='午\n門';c.align_x='CENTER';c.size=.009;c.space_line=.94;c.extrude=.00001;c.font=bpy.data.fonts.load(str(ROOT/'data/wumen-plaque.ttf'));o=bpy.data.objects.new('Wumen plaque',c);scene.collection.objects.link(o);o.location=(0,-.1132,.269);o.rotation_euler=(math.pi/2,0,0);c.materials.append(mats['gold'])
 for q in scene.objects:q.select_set(False)
 o.select_set(True);bpy.context.view_layer.objects.active=o;target=next(i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if i.identifier=='MESH');bpy.ops.object.convert(target=target)
 for o in scene.objects:o.select_set(True)
 bpy.context.view_layer.update();import io_scene_gltf2;fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');path=OUT/(level+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[o.matrix_world@Vector(v)for o in scene.objects for v in o.bound_box];stats={'level':level,'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'bytes':path.stat().st_size,'bounds':[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]],'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12],'platformHeight':12,'mainHallDimensions':[60.05,25],'roofType':'double-eaved hipped','cornerPavilions':4,'galleryBays':13,'portalCount':5}
 (PROOF/(level+'.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(PROOF/('午门_'+level+'.blend')),{scene},fake_user=True);print(stats)
if __name__=='__main__':build(False);build(True)
