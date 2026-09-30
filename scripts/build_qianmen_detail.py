"""Photo-informed Zhengyangmen pair. Metres internally, map units = 100 m.
Anchors OSM; documented dimensions in data/qianmen-plan.json. Not a survey model.
"""
import bpy,math,json,sys,importlib.util,hashlib,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'public/assets/qianmen-detail';OUT.mkdir(exist_ok=True);PROOF=R/'output/qianmen-detail';PROOF.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('qianmen_helpers',R/'scripts/build_tiananmen_detail.py');H=importlib.util.module_from_spec(s);sys.modules[s.name]=H;s.loader.exec_module(H);T=H.T
P=json.loads((R/'data/qianmen-plan.json').read_text())

class Builder(T.Builder):
 def __init__(self,detail):super().__init__(detail);self.windows=[];self.portals=[]

def wall(B,a,b,z0,z1,holes=(),brick=True):
 """Brick face with true rectangular cutouts, reveals and recessed shutters."""
 dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);ux,uy=dx/length,dy/length;nx,ny=uy,-ux
 def pt(u,z,depth=0):return(a[0]+ux*u-nx*depth,a[1]+uy*u-ny*depth,z)
 def clear(x,z):return not any(l<x<r and bot<z<top for l,bot,r,top in holes)
 xs=sorted({0,length,*[v for h in holes for v in [max(0,h[0]),min(length,h[2])]]});zs=sorted({z0,z1,*[v for h in holes for v in [max(z0,h[1]),min(z1,h[3])]]})
 for l,r in zip(xs,xs[1:]):
  for bot,top in zip(zs,zs[1:]):
   if r>l and top>bot and clear((l+r)/2,(bot+top)/2):B.face('mortar',[pt(l,bot),pt(r,bot),pt(r,top),pt(l,top)])
 if brick and B.detail:
  bh=.19;bw=.63
  for j in range(math.ceil((z1-z0)/bh)):
   bot=z0+j*bh+.007;top=min(z1,bot+bh-.014)
   for i in range(-1,math.ceil(length/bw)+1):
    l=max(.006,(i+(j%2)*.5)*bw+.006);r=min(length-.006,(i+(j%2)*.5+1)*bw-.006)
    if l>=r or bot>=top:continue
    xx=sorted({l,r,*[q for h in holes for q in (h[0],h[2]) if l<q<r]});zz=sorted({bot,top,*[q for h in holes for q in (h[1],h[3]) if bot<q<top]})
    key='brick'+str((i*71+j*29)%4)
    for x,x1 in zip(xx,xx[1:]):
     for z,z2 in zip(zz,zz[1:]):
      if clear((x+x1)/2,(z+z2)/2):B.face(key,[pt(x,z,-.012),pt(x1,z,-.012),pt(x1,z2,-.012),pt(x,z2,-.012)])
 for l,bot,r,top in holes:
  q=[(l,bot),(r,bot),(r,top),(l,top)]
  for aa,bb in zip(q,q[1:]+q[:1]):B.face('reveal',[pt(*aa),pt(*aa,.70),pt(*bb,.70),pt(*bb)])
  B.face('window',[pt(l,bot,.72),pt(r,bot,.72),pt(r,top,.72),pt(l,top,.72)])
  B.beam('redDark',pt(l-.08,top+.06,-.05),pt(r+.08,top+.06,-.05),.08,6)
  B.windows.append({'center':pt((l+r)/2,(bot+top)/2),'outward':[nx,ny,0],'width':r-l,'height':top-bot,'recess':.72})
 return pt

def platform(B,L,D,h,front=(3.,3.29),back=(3.54,5.95)):
 # Single central through-vault. Front/back opening profiles intentionally differ.
 for side,(r,spring) in [(-1,front),(1,back)]:
  y=side*D/2
  # Face strips above the arch + solid flanks. No full cube across the tunnel.
  for l,rr in [(-L/2,-r),(r,L/2)]:
   a=(l,y)if side<0 else(rr,y);b=(rr,y)if side<0 else(l,y);wall(B,a,b,0,h)
  n=64 if B.detail else 24
  for i in range(n):
   a,b=math.pi*i/n,math.pi*(i+1)/n;x0,x1=r*math.cos(a),r*math.cos(b);z0,z1=spring+r*math.sin(a),spring+r*math.sin(b)
   q=[(x0,y,z0),(x1,y,z1),(x1,y,h),(x0,y,h)];B.face('brick1',q if side>0 else q[::-1])
   Rr=r+.34;q=[(x0,y+side*.025,z0),(x1,y+side*.025,z1),(Rr*math.cos(b),y+side*.025,spring+Rr*math.sin(b)),(Rr*math.cos(a),y+side*.025,spring+Rr*math.sin(a))];B.face('stone',q if side>0 else q[::-1])
  for sign in [-1,1]:B.box('stone',(sign*(r+.16),y+side*.025,spring/2),(.32,.08,spring))
  if B.detail:
   for j in range(math.ceil(h/.19)):
    bot=j*.19+.007;top=min(h,bot+.176)
    for i in range(-math.ceil(r/.63)-1,math.ceil(r/.63)+1):
     l=max(-r,(i+(j%2)*.5)*.63+.006);rr=min(r,(i+(j%2)*.5+1)*.63-.006)
     if l>=rr:continue
     arch=max(spring+math.sqrt(max(0,r*r-x*x))for x in[l,(l+rr)/2,rr])
     if bot<arch+.015:continue
     q=[(l,y+side*.014,bot),(rr,y+side*.014,bot),(rr,y+side*.014,top),(l,y+side*.014,top)]
     B.face('brick'+str((i*71+j*29)%4),q if side<0 else q[::-1])
 # Intrados is a loft between the two documented arch profiles.
 n=64 if B.detail else 24
 for i in range(n):
  aa,bb=math.pi*i/n,math.pi*(i+1)/n
  def q(side,t):r,spring=front if side<0 else back;return(r*math.cos(t),side*D/2,spring+r*math.sin(t))
  B.face('reveal',[q(-1,aa),q(1,aa),q(1,bb),q(-1,bb)])
 for side in [-1,1]:
  B.face('reveal',[(side*front[0],-D/2,0),(side*back[0],D/2,0),(side*back[0],D/2,back[1]),(side*front[0],-D/2,front[1])])
 wall(B,(L/2,-D/2),(L/2,D/2),0,h);wall(B,(-L/2,D/2),(-L/2,-D/2),0,h)
 B.box('deck',(0,0,h+.10),(L,D,.20));B.box('stone',(0,0,.018),(min(front[0],back[0])*2,D,.036))
 # Stone footing only along solid exterior flanks, never seals the doorway.
 for side in [-1,1]:
  rr=(front if side<0 else back)[0]
  for sign in [-1,1]:B.box('stone',(sign*(L/2+rr)/2,side*(D/2+.04),.38),(L/2-rr,.16,.76))
 # Castle platform narrows towards its crown. Keep arch widths fixed while
 # battering the outer flanks and both front/rear brick faces.
 for vs,fs,uvs in B.groups.values():
  for i,(x,y,z)in enumerate(vs):
   f=max(0,min(1,z/h));xx=math.copysign(6+(abs(x)-6)*(1-.018*f),x)if abs(x)>6 else x
   vs[i]=(xx,y*(1-.05*f),z)
 B.portals.append({'front':front,'back':back,'depth':D})

def glazed_roof(B,hx,hy,rb,peak,lower=False,cx=0,cy=0):
 H.roof(B,hx,hy,rb,peak,lower,cx,cy)
 # Green glazed eave bands, distinct from the grey field of cylindrical tiles.
 for side in[-1,1]:
  for row in range(3):
   off=row*.14
   last=None
   for i in range(65):
    x=-hx+i*2*hx/64;z=rb+.12+.38*(abs(x)/hx)**14+off*.10;p=(cx+x,cy+side*(hy-off),z)
    if last:B.beam('gold',last,p,.085,6)
    last=p


def band(B,hx,hy,z,cy=0,height=1.1):
 for side in [-1,1]:
  y=cy+side*hy;q=[(-hx,y,z),(hx,y,z),(hx,y,z+height),(-hx,y,z+height)];B.face('frieze',q if side<0 else q[::-1],[(0,0),(7,0),(7,1),(0,1)]if side<0 else[(0,1),(7,1),(7,0),(0,0)])
  x=side*hx;q=[(x,cy-hy,z),(x,cy+hy,z),(x,cy+hy,z+height),(x,cy-hy,z+height)];B.face('frieze',q if side>0 else q[::-1],[(0,0),(3,0),(3,1),(0,1)])

def wood_rail(B,a,b,z):
 B.beam('red',(*a,z+.9),(*b,z+.9),.065,6);B.beam('red',(*a,z+.3),(*b,z+.3),.065,6)
 for i in range(math.ceil(math.dist(a,b)/.7)+1):
  f=i/max(1,math.ceil(math.dist(a,b)/.7));x=a[0]+(b[0]-a[0])*f;y=a[1]+(b[1]-a[1])*f;B.box('red',(x,y,z+.56),(.065,.065,1.0))

def gallery(B,z0,z1,upper=False):
 hx,hy=20.5,10.5
 B.box('redDark',(0,0,(z0+z1)/2),(36.7,16.5,z1-z0))
 for i in range(8):
  for j in range(4):
   if i not in [0,7]and j not in[0,3]:continue
   x=-hx+i*2*hx/7;y=-hy+j*2*hy/3;B.cylinder('red',.37,z0,z1,16 if B.detail else 10,.33,(x,y));B.cylinder('stone',.44,z0,z0+.3,12,.40,(x,y))
   for dz,w in [(0,.80),(.23,1.2),(.46,1.65)]:B.box('jade'if dz else'blue',(x,y,z1-.7+dz),(w,w*.72,.18))
 for side in [-1,1]:
  y=side*8.27
  for i in range(7):
   x=(i-3)*36.7/7;w=4.65;lo=z0+.25;hi=z1-.8
   if not upper and i not in[1,3,5]:continue
   B.box('window'if upper else'red',(x,y,(lo+hi)/2),(w,.08,hi-lo))
   for j in range(5):B.box('red',(x-w/2+j*w/4,y+side*.07,(lo+hi)/2),(.09,.09,hi-lo))
   for z in[lo,lo+1.2,hi]:B.box('red',(x,y+side*.08,z),(w,.10,.11))
   if upper and B.detail:
    # Diamond lattice built as clipped slanted struts over recessed dark glazing.
    low=lo+1.2;high=hi
    for sign in[-1,1]:
     for k in range(-18,19):
      c=k*.36;points=[]
      for xx in[-w/2,w/2]:
       zz=low+c+sign*xx
       if low<=zz<=high:points.append((x+xx,y+side*.11,zz))
      for zz in[low,high]:
       xx=(zz-low-c)/sign
       if -w/2<=xx<=w/2:points.append((x+xx,y+side*.11,zz))
      if len(points)>=2 and math.dist(points[0],points[1])>.03:B.beam('red',points[0],points[1],.024,4)
  if upper:wood_rail(B,(-20.6,side*10.6),(20.6,side*10.6),z0)
 if upper:
  for side in[-1,1]:wood_rail(B,(side*20.6,-10.6),(side*20.6,10.6),z0)
 band(B,20.55,10.55,z1-1.5)

def gatehouse(B):
 platform(B,95,31.45,14.7)
 for side in[-1,1]:
  spans=[(-47.5,47.5)]if side<0 else[(-47.5,-26.5),(-23.5,23.5),(26.5,47.5)]
  for a,b in spans:
   B.box('brick2',((a+b)/2,side*15.4,15.4),(b-a,.55,1.2));B.box('stone',((a+b)/2,side*15.4,16.03),(b-a,.66,.14))
  B.box('brick2',(side*47.15,0,15.4),(.55,31.45,1.2))
 # Main seven-by-three-bay timber pavilion with three separate dripping eaves.
 gallery(B,14.93,21.8);glazed_roof(B,23.5,13.,22.0,29.,True)
 B.box('deck',(0,0,24.16),(42.1,21.7,.24));gallery(B,24.3,29.7,True);glazed_roof(B,22.9,12.6,29.9,35.8,True)
 B.box('jade',(0,0,33.5),(38,17.2,3.0));band(B,19.1,8.7,32.15,height=2.2);glazed_roof(B,21.8,11.3,34.65,41.68)
 # Paired north-side ramps run onto the castle platform; inferred from photographs.
 for side in[-1,1]:
  x0=side*46;x1=side*25;y=16.8;w=3.3
  for k in range(60):
   f=(k+.5)/60;x=x0+(x1-x0)*f;h=.15+14.55*f
   B.box('brick2',(x,y,h/2),(abs(x1-x0)/60+.02,w,h))
  B.beam('stone',(x0,y+w/2,1),(x1,y+w/2,15.8),.19,6)
  B.box('deck',(x1,15.8,14.8),(3.,3.8,.20))
 # Red frame around the southern hanging name tablet; glyphs added after meshing.
 B.box('letter',(0,-8.78,32.65),(1.48,.14,2.34));B.box('blue',(0,-8.88,32.65),(1.32,.08,2.18))
 return 43.65

def window_hood(B,point,width):
 # Concentric curved plaster cornice above the first two rows of arrow windows.
 x,y,z=point;r=width/2+.17
 for dr in[0,.14,.28]:
  last=None
  for j in range(25):
   a=j*math.pi/24;p=(x+(r+dr)*math.cos(a),y,z+(r+dr)*math.sin(a))
   if last:B.beam('marble',last,p,.065,6)
   last=p

def arrow(B):
 platform(B,62,36,12.5,(3.25,3.75),(3.25,3.75))
 # T-shaped masonry, with four rows facing the southern approach.
 rows=[(13.8,15.45),(17.7,19.35),(21.6,23.25)];xs=[(i-6)*3.75 for i in range(13)]
 for lo,hi,z0,z1,hx,front,back in [(0,3,12.7,25.7,26.5,-16,4),(3,4,27.15,30.7,25.,-14.8,3.5)]:
  zs=rows if lo==0 else[(28.,29.65)]
  holes=[(x+hx-.78,z,x+hx+.78,t)for z,t in zs for x in xs]
  wall(B,(-hx,front),(hx,front),z0,z1,holes)
  for side in[-1,1]:
   a=(side*hx,front)if side>0 else(side*hx,back);b=(side*hx,back)if side>0 else(side*hx,front)
   d=back-front;holes=[((k+.5)*d/4-.78,z,(k+.5)*d/4+.78,t)for z,t in zs for k in range(4)];wall(B,a,b,z0,z1,holes)
  # North shoulders flank the central projecting annex.
  for a,b in[((hx,back),(21,back)),((-21,back),(-hx,back))]:wall(B,a,b,z0,z1)
 # Annex side openings: five per side, four added in 1915 and one older upper opening.
 for side in[-1,1]:
  a=(side*21,4)if side>0 else(side*21,16);b=(side*21,16)if side>0 else(side*21,4)
  holes=[(u-.65,z,u+.65,z+1.55)for u,z in [(3.,14.0),(9.,14.0),(3.,18.),(9.,18.)]];wall(B,a,b,12.7,25.7,holes)
 # North glazing described in 1928 records; actual glass is recessed in the wall.
 wall(B,(21,16),(-21,16),12.7,25.7,[(19.4,21.0,22.6,23.16)])
 for side in[-1,1]:
  a=(side*19,3.5)if side>0 else(side*19,15.9);b=(side*19,15.9)if side>0 else(side*19,3.5)
  wall(B,a,b,27.15,30.7,[(5.55,28.,6.85,29.55)])
 wall(B,(19,15.9),(-19,15.9),27.15,30.7)
 band(B,26.55,10,24.3,-6);band(B,25.05,9.15,29.55,-5.65)
 glazed_roof(B,30.7,11.2,25.9,31.5,True,0,-6);glazed_roof(B,28.6,10.3,30.8,33.40,False,0,-5.65)
 # Northern roof projection uses a lower parallel ridge, with valleys overlapped
 # inside the main roof. Outer parts remain visible as the photo's rear eaves.
 glazed_roof(B,22.,7.1,25.9,31.5,True,0,9.5);glazed_roof(B,20.,7.,30.8,32.85,False,0,8.8)
 band(B,21,6,24.3,10)
 # White 1915 balustrades: front, sides and northern terrace.
 for a,b in[((-30.3,-17.4),(30.3,-17.4)),((30.3,-17.4),(30.3,17.4)),((30.3,17.4),(11.5,17.4)),((8.5,17.4),(-8.5,17.4)),((-11.5,17.4),(-30.3,17.4)),((-30.3,17.4),(-30.3,-17.4))]:H.railing(B,a,b,12.72)
 # Front curved window hoods connect into continuous horizontal strings.
 for z in[15.45,19.35]:
  B.box('marble',(0,-16.16,z+.04),(48.8,.25,.14))
  for x in xs:window_hood(B,(x,-16.22,z+.06),1.56)
 # East/west hoods rotate with their facades.
 for sign in[-1,1]:
  C=Builder(B.detail)
  for z in[15.45,19.35]:
   for k in range(4):window_hood(C,(-7.5+k*5,0,z+.06),1.56)
  ang=sign*math.pi/2;co,si=math.cos(ang),math.sin(ang)
  for mat,(vs,fs,uvs)in C.groups.items():
   for face,uv in zip(fs,uvs):B.face(mat,[(sign*26.7+x*co-y*si,-6+x*si+y*co,z)for x,y,z in[vs[i]for i in face]],uv)
 # 1915 western-style semicircular canopy relief on each side of the base.
 for side in[-1,1]:
  x=side*30.6;cy=0.;z=10.8;rad=5.0
  for j in range(40):
   a=math.pi+j*math.pi/40;b=math.pi+(j+1)*math.pi/40
   q=[(x,cy,z),(x,cy+rad*math.cos(a),z+rad*.58*math.sin(a)),(x,cy+rad*math.cos(b),z+rad*.58*math.sin(b))]
   B.face('marble',q if side>0 else q[::-1])
  for j in range(1,10):
   a=math.pi+j*math.pi/10;B.beam('stone',(x+side*.018,cy,z),(x+side*.018,cy+rad*math.cos(a),z+rad*.58*math.sin(a)),.026,5)
 # Corbels beneath the added front terrace: separate shaped brackets.
 for i in range(19):
  x=-28.5+i*3.1667
  for k in range(4):B.box('marble',(x,-17.4+k*.16,12.30-k*.20),(.30+.14*k,.40+.1*k,.26))
 # Northern twin access stairs; tread/flight positions are inferred, not measured.
 for sign in[-1,1]:
  for k in range(48):
   f=(k+.5)/48;x=sign*(28-18*f);h=12.5*f;B.box('stone',(x,19.,h/2),(18/48+.012,2.,h))
  B.beam('marble',(sign*28,19.85,1.),(sign*10,19.85,13.6),.09,8)
  B.box('stone',(sign*10,18.3,12.52),(3.,3.4,.16))
 return 35.37

def export(id,detail=True):
 level='detail'if detail else'preview';name=id+' '+level
 scene=bpy.data.scenes.get(name)or bpy.data.scenes.new(name);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=Builder(detail);height=gatehouse(B)if id=='qianmen'else arrow(B)
 colors={'mortar':(.16,.17,.145),'brick0':(.235,.25,.21),'brick1':(.27,.28,.24),'brick2':(.30,.305,.26),'brick3':(.245,.265,.24),'reveal':(.12,.135,.12),'stone':(.38,.385,.33),'deck':(.35,.35,.30),'marble':(.77,.75,.65),'window':(.038,.045,.036),'red':(.36,.045,.024),'redDark':(.16,.035,.023),'jade':(.030,.15,.080),'blue':(.017,.07,.14),'roof':(.15,.19,.16),'tile':(.215,.245,.19),'gold':(.032,.20,.090),'frieze':(.1,.17,.13),'letter':(.78,.55,.17)}
 mats={}
 for k,c in colors.items():
  texture=R/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else None
  mats[k]=T.mat('Qianmen '+k,c,.6 if k in['roof','tile','gold']else .89,texture=texture)
  if texture:next(n for n in mats[k].node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
 for k,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new(id+' '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mats[k]);uv=me.uv_layers.new(name='Facade')
  for poly,coords in zip(me.polygons,uvs):
   for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
  o=bpy.data.objects.new(id+' '+k,me);scene.collection.objects.link(o)
 if id=='qianmen':
  c=bpy.data.curves.new('Zhengyangmen plaque','FONT');c.body='正\n陽\n門';c.align_x='CENTER';c.size=.0060;c.space_line=1.08;c.extrude=.000015
  font=R/'data/qianmen-plaque.ttf'
  if font.exists():c.font=bpy.data.fonts.load(str(font))
  o=bpy.data.objects.new('Zhengyangmen plaque',c);scene.collection.objects.link(o);o.location=(0,-.0894,.3320);o.rotation_euler=(math.pi/2,0,0);c.materials.append(mats['letter'])
  for ob in scene.objects:ob.select_set(False)
  o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target=next(v.identifier for v in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if v.identifier=='MESH'))
 bpy.context.view_layer.update();maxz=max((ob.matrix_world@Vector(v)).z for ob in scene.objects for v in ob.bound_box)
 # Only ridge ornaments are calibrated to the published overall height.
 cutoff=.3465 if id=='qianmen'else .308
 for ob in scene.objects:
  for v in ob.data.vertices:
   if v.co.z>cutoff:v.co.z=cutoff+(v.co.z-cutoff)*(height/100-cutoff)/(maxz-cutoff)
 bpy.context.view_layer.update()
 for ob in scene.objects:ob.select_set(True)
 bpy.context.view_layer.objects.active=next(iter(scene.objects));import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');path=OUT/(id+'-'+level+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[ob.matrix_world@Vector(v)for ob in scene.objects for v in ob.bound_box];stats={'id':id,'level':level,'height':height,'boundsLocal':[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]],'triangles':sum(len(p.vertices)-2 for ob in scene.objects for p in ob.data.polygons),'meshes':len(scene.objects),'windowRecesses':B.windows,'portals':B.portals,'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12]}
 (PROOF/(id+'-'+level+'.json')).write_text(json.dumps(stats,ensure_ascii=False,indent=2));bpy.data.libraries.write(str(PROOF/(id+'-'+level+'.blend')),{scene},fake_user=True);print({k:v for k,v in stats.items()if k not in['windowRecesses','portals']});return scene

if __name__=='__main__':
 for id in['qianmen','qianmen-arrow']:
  for detail in[False,True]:export(id,detail)
