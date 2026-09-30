"""Beijing Dacheng Hall, photograph-informed reconstruction, not a measured replica.
Nine front bays, five side bays; double hipped roof, lattice joinery and carved terrace.
The scene is isolated until visual review and footprint replacement are complete.
"""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1];O=R/'public/assets/confucius-detail';O.mkdir(exist_ok=True);Q=R/'output/confucius-detail';Q.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('confucius_primitives',R/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(s);sys.modules[s.name]=T;s.loader.exec_module(T)
P=json.loads((R/'data/confucius-plan.json').read_text())
class Builder(T.Builder):
 def __init__(self,detail):super().__init__(detail);self.openings=[];self.posts=set()

def curve(B,mat,pts,r=.06,n=6):
 for a,b in zip(pts,pts[1:]):B.beam(mat,a,b,r,n)

def roof(B,hx,hy,z0,z1,skirt=False):
 ridge=hx-hy;stop=.27 if skirt else 1.;steps=20 if B.detail else 8
 def section(t):return hx-hy*t,hy*(1-t),z0+(z1-z0)*t**1.65
 def pt(x,y,z,t):return(x,y,z+.52*(abs(x)/hx)**14*max(0,1-t*5)**2)
 for side in[-1,1]:
  for orientation in[0,1]:
   span=hx if orientation==0 else hy;n=math.ceil(2*span/(.24 if B.detail else 1.0))
   for j in range(steps):
    t,u=stop*j/steps,stop*(j+1)/steps;ax,ay,az=section(t);bx,by,bz=section(u)
    for i in range(n):
     f,g=-1+2*i/n,-1+2*(i+1)/n
     coords=[(ax*f,side*ay,az,t),(ax*g,side*ay,az,t),(bx*g,side*by,bz,u),(bx*f,side*by,bz,u)]if orientation==0 else[(side*ax,ay*f,az,t),(side*ax,ay*g,az,t),(side*bx,by*g,bz,u),(side*bx,by*f,bz,u)]
     B.face('roof',[pt(*p)for p in coords]);v=(f+g)/2
     a,b=(pt(ax*v,side*ay,az+.05,t),pt(bx*v,side*by,bz+.05,u))if orientation==0 else(pt(side*ax,ay*v,az+.05,t),pt(side*bx,by*v,bz+.05,u))
     B.beam('tile',a,b,.075,6 if B.detail else 4)
   # Visible rounded tile ends and exposed rafter tips.
   for i in range(n):
    v=-1+2*(i+.5)/n;x,y=(hx*v,side*hy)if orientation==0 else(side*hx,hy*v)
    end=pt(x,y,z0+.08,0);inside=(x,y-side*.25,z0+.08)if orientation==0 else(x-side*.25,y,z0+.08)
    B.beam('tile',inside,end,.10,8)
    if B.detail:B.box('rafter',(x,y,z0-.16),(.12,.12,.18))
  for other in[-1,1]:
   pts=[]
   for j in range(steps+1):
    t=stop*j/steps;x,y,z=section(t);pts.append(pt(side*x,other*y,z+.22,t))
   curve(B,'gold',pts,.15)
   # Nine stylized ridge beasts: symbolic silhouette only, no invented anatomical claim.
   if B.detail:
    for j in range(9):
     t=.025+j*.018;x,y,z=section(t);x,y,z=pt(side*x,other*y,z+.32,t)
     B.box('gold',(x,y,z+.09),(.18,.26,.19));B.cylinder('gold',.09,z+.14,z+.34,8,.065,(x,y));B.beam('gold',(x,y,z+.30),(x-side*.15,y-other*.10,z+.40),.075,6)
 if not skirt:
  B.box('gold',(0,0,z1+.20),(2*ridge+.45,.50,.42))
  for sign in[-1,1]:
   x=sign*ridge
   # Curled chiwen terminal follows reference silhouette; carved detail remains approximate.
   pts=[(x+sign*(.3+.55*math.sin(t*math.pi)),0,z1+.2+t*1.0)for t in[i/12 for i in range(13)]]
   curve(B,'gold',pts,.20,8);curve(B,'gold',[(x+sign*.4,0,z1+.6),(x-sign*.1,0,z1+.9),(x-sign*.35,0,z1+.65)],.13)
 for a,b in[((-hx,-hy,z0),(hx,-hy,z0)),((hx,-hy,z0),(hx,hy,z0)),((hx,hy,z0),(-hx,hy,z0)),((-hx,hy,z0),(-hx,-hy,z0))]:B.beam('wood',a,b,.16,4)

def panel(B,c,u,normal,width,z0,z1,openDoor=False):
 def pt(x,z,d=0):return(c[0]+u[0]*x+normal[0]*d,c[1]+u[1]*x+normal[1]*d,z)
 # Lattice is actual narrow geometry with an inset dark backing; doors are open voids.
 if openDoor:
  B.openings.append({'origin':pt(0,(z0+z1)/2,1),'direction':[-normal[0],-normal[1],0],'depth':1.5})
 else:
  B.face('shadow',[pt(-width/2,z0,-.12),pt(width/2,z0,-.12),pt(width/2,z1,-.12),pt(-width/2,z1,-.12)])
 for x in[-width/2,width/2]:B.beam('red',pt(x,z0),pt(x,z1),.10,4)
 for z in[z0,z1]:B.beam('gold',pt(-width/2,z,.025),pt(width/2,z,.025),.035,4)
 if not openDoor:
  low=z0+(z1-z0)*.25
  B.face('red',[pt(-width/2,z0),pt(width/2,z0),pt(width/2,low),pt(-width/2,low)])
  B.beam('gold',pt(-width/2,low,.035),pt(width/2,low,.035),.03,4)
  if B.detail:
   step=.24
   # Clipped diamond lattice, each line terminates within its own panel.
   for slope in[-1,1]:
    for k in range(-math.ceil((z1-low+width)/step),math.ceil((z1-low+width)/step)+1):
     intercept=low+k*step;candidates=[]
     for x in[-width/2,width/2]:
      z=intercept+slope*x
      if low<=z<=z1:candidates.append((x,z))
     for z in[low,z1]:
      x=(z-intercept)/slope
      if -width/2<=x<=width/2:candidates.append((x,z))
     if len(candidates)>=2:B.beam('gold',pt(*candidates[0],.02),pt(*candidates[-1],.02),.018,4)

def facade(B,a,b,bays,z0,z1,door=False):
 L=math.dist(a,b);u=((b[0]-a[0])/L,(b[1]-a[1])/L);n=(u[1],-u[0]);step=L/bays
 for i in range(bays+1):
  x,y=a[0]+u[0]*i*step,a[1]+u[1]*i*step
  B.cylinder('red',.40,z0,z1,16 if B.detail else 8,.36,(x,y));B.cylinder('stone',.49,z0-.15,z0+.22,12,.44,(x,y))
 for i in range(bays):
  c=(a[0]+u[0]*(i+.5)*step,a[1]+u[1]*(i+.5)*step)
  for j in range(4):
   w=(step-.75)/4;x=(j-1.5)*w
   center=(c[0]+u[0]*x,c[1]+u[1]*x)
   panel(B,center,u,n,w-.025,z0+.25,z1-1.65,door and i in[3,4,5]and j in[1,2])
  B.beam('jade',(c[0]-u[0]*step/2,c[1]-u[1]*step/2,z1-1.0),(c[0]+u[0]*step/2,c[1]+u[1]*step/2,z1-1.0),.47,4)
  for z in[z1-1.46,z1-.54]:B.beam('gold',(c[0]-u[0]*step/2+n[0]*.35,c[1]-u[1]*step/2+n[1]*.35,z),(c[0]+u[0]*step/2+n[0]*.35,c[1]+u[1]*step/2+n[1]*.35,z),.035,4)
 # Repeated bracket layers under the roof, not a single opaque extruded band.
 for i in range(bays*3+1):
  x,y=a[0]+u[0]*L*i/(bays*3),a[1]+u[1]*L*i/(bays*3)
  for k in range(4 if B.detail else 2):
   B.box('wood',(x+n[0]*k*.16,y+n[1]*k*.16,z1+.12+k*.20),(.42+k*.12,.42+k*.12,.16))


def railing(B,a,b,z,zEnd=None):
 zEnd=z if zEnd is None else zEnd
 L=math.dist(a,b);n=max(1,round(L/1.7));u=((b[0]-a[0])/L,(b[1]-a[1])/L);normal=(u[1],-u[0])
 def point(t,h,d=0):return(a[0]+(b[0]-a[0])*t+normal[0]*d,a[1]+(b[1]-a[1])*t+normal[1]*d,z+(zEnd-z)*t+h)
 for i in range(n+1):
  x,y,zz=point(i/n,0);key=tuple(round(v,5)for v in(x,y,zz))
  if key in B.posts:continue
  B.posts.add(key);B.box('stone',(x,y,zz+.65),(.32,.32,1.30))
  for r,lo,hi in[(.25,1.3,1.45),(.20,1.45,1.62),(.13,1.62,1.78)]:B.cylinder('stone',r,zz+lo,zz+hi,16,r*.70,(x,y))
 for zz in[.20,.95,1.24]:B.beam('stone',point(0,zz),point(1,zz),.08,4)
 for i in range(n):
  l,r=(i+.12)/n,(i+.88)/n
  # Broad stone panels rather than timber-like pickets; thin gaps above carved field.
  for d in[-.09,.09]:B.face('stone',[point(l,.24,d),point(r,.24,d),point(r,.88,d),point(l,.88,d)])
  for t in[l,r]:B.face('stone',[point(t,.24,-.09),point(t,.24,.09),point(t,.88,.09),point(t,.88,-.09)])
  B.face('stone',[point(l,.88,-.09),point(l,.88,.09),point(r,.88,.09),point(r,.88,-.09)])
  if B.detail:
   # Shallow oval floral medallions, approximation of the visible carved stone fields.
   for side in[-1,1]:
    pts=[point((l+r)/2+(r-l)*.35*math.cos(k*math.tau/24),.55+.21*math.sin(k*math.tau/24),side*.105)for k in range(25)]
    curve(B,'stoneRelief',pts,.025,5)


def platform(B,hx,hy):
 # One T-shaped top avoids overlapping coplanar terrace slabs.
 ring=[(-hx-.45,hy+.85),(-hx-.45,-hy-.85),(-11.7,-hy-.85),(-11.7,-hy-6.9),(11.7,-hy-6.9),(11.7,-hy-.85),(hx+.45,-hy-.85),(hx+.45,hy+.85)]
 for lo,hi,material in[(0,2.01,'base'),(2.01,2.23,'stone')]:
  pts=[Vector((x,y,hi))for x,y in ring]
  for tri in tessellate_polygon([pts]):B.face(material,[tuple(pts[v]if isinstance(v,int)else v)for v in tri])
  for a,b in zip(ring,ring[1:]+ring[:1]):B.face(material,[(*a,lo),(*b,lo),(*b,hi),(*a,hi)])


def upper_brackets(B,ux,uy):
 for a,b,n in[((-ux,-uy),(ux,-uy),27),((ux,-uy),(ux,uy),15),((ux,uy),(-ux,uy),27),((-ux,uy),(-ux,-uy),15)]:
  L=math.dist(a,b);u=((b[0]-a[0])/L,(b[1]-a[1])/L);normal=(u[1],-u[0])
  for i in range(n+1):
   x,y=a[0]+u[0]*L*i/n,a[1]+u[1]*L*i/n
   for k in range(3):
    z=19.28+k*.22;reach=.30+k*.18
    B.beam('wood',(x-u[0]*reach,y-u[1]*reach,z),(x+u[0]*reach,y+u[1]*reach,z),.075,4)
    B.beam('wood',(x,y,z+.06),(x+normal[0]*(.45+k*.30),y+normal[1]*(.45+k*.30),z+.06),.07,4)


def build(B):
 hx,hy=P['roofWidth']/2,P['roofDepth']/2
 # Roof extent follows the mapped outline. Height is provisional, official reported value.
 platform(B,hx,hy)
 for a,b in[((-11.6,-hy-6.8),(-4.5,-hy-6.8)),((4.5,-hy-6.8),(11.6,-hy-6.8)),((-11.6,-hy-6.8),(-11.6,-hy-.8)),((11.6,-hy-6.8),(11.6,-hy-.8))]:railing(B,a,b,2.24)
 for sign in[-1,1]:
  for i in range(14):B.box('stone',(sign*3.0,-hy-10.9+(i+.5)*.3,(i+1)*.15/2),(2.6,.31,(i+1)*.15))
  railing(B,(sign*4.5,-hy-10.9),(sign*4.5,-hy-6.8),.05,2.24)
 # Sloping imperial way between stairs. Carved dragons are deliberately deferred pending sculpting.
 B.face('stone', [(-1.55,-hy-11.,0),(1.55,-hy-11.,0),(1.55,-hy-6.8,2.2),(-1.55,-hy-6.8,2.2)])
 x,y=hx-2.0,hy-2.0
 for a,b,n,d in[((-x,-y),(x,-y),9,True),((x,-y),(x,y),5,False),((x,y),(-x,y),9,False),((-x,y),(-x,-y),5,False)]:facade(B,a,b,n,2.3,12.8,d)
 B.box('stone',(0,0,2.24),(2*x,2*y,.02))
 # Recessed interior screen creates depth behind open doors without sealing their apertures.
 B.box('shadow',(0,-y+3.0,7.0),(2*x-.8,.12,9.0))
 roof(B,hx,hy,14.0,23.0,True)
 ux,uy=hx-4.8,hy-4.8
 for a,b in[((-ux,-uy),(ux,-uy)),((ux,-uy),(ux,uy)),((ux,uy),(-ux,uy)),((-ux,uy),(-ux,-uy))]:
  B.face('jade',[(*a,15.0),(*b,15.0),(*b,19.2),(*a,19.2)])
  for z in[15.2,16.1,18.6]:B.beam('gold',(*a,z),(*b,z),.07,4)
 upper_brackets(B,ux,uy)
 roof(B,hx-1.1,hy-1.1,20.0,31.8)
 # Frieze fields with geometric floral scrolls sampled from the photographs.
 for side in[-1,1]:
  for i in range(9):
   x=(i-4)*2*ux/9;y=side*(uy+.025)
   B.box('wood',(x,y,17.0),(2*ux/9-.18,.10,1.6))
   B.box('jade',(x,y+side*.07,17.0),(2*ux/9-.35,.06,1.40))
   if B.detail:
    pts=[(x+1.15*math.cos(t),y+side*.12,17.+.40*math.sin(t))for t in[k*math.tau/32 for k in range(33)]]
    curve(B,'rafter',pts,.035,4)
    for sign in[-1,1]:
     curve(B,'rafter',[(x+sign*.15,y+side*.13,16.7),(x+sign*.65,y+side*.13,17.2),(x+sign*1.3,y+side*.13,17.)],.035,4)
 # Stone terrace side rails wrap around the building instead of stopping at the stairs.
 for a,b in[((-hx,-hy-.6),(-11.6,-hy-.6)),((11.6,-hy-.6),(hx,-hy-.6)),((-hx,-hy-.6),(-hx,hy+.6)),((hx,-hy-.6),(hx,hy+.6)),((-hx,hy+.6),(hx,hy+.6))]:railing(B,a,b,2.24)
 # Tablet positions stay tied to the facade, not the ornament-loop temporary coordinates.
 y=hy-2.0
 # Lettering is added separately in Blender; typeface is not historic calligraphy.
 B.box('blue',(0,-(hy-1.2)-.20,17.7),(1.8,.16,3.6));B.box('blue',(0,-y-.40,11.45),(5.8,.18,1.8))
 for a,b in[((-2.98,-y-.52,10.5),(2.98,-y-.52,10.5)),((-2.98,-y-.52,12.4),(2.98,-y-.52,12.4))]:B.beam('gold',a,b,.09,6)
 return B


def photo_z(z):
 """Provisional elevation ratios from photos; 33 m reported height remains unresolved."""
 knots=[(0,0),(2.3,2.3),(12.8,8.5),(14.,9.7),(15.,10.),(19.2,12.8),(20.,13.5),(31.8,21.8),(33.,23.)]
 for (a,b),(c,d) in zip(knots,knots[1:]):
  if z<=c:return b+(z-a)*(d-b)/(c-a)
 return 23.+z-33.


def lettering(B):
 # Rendered typeface glyph geometry only, not an embedded font or a calligraphy facsimile.
 path=Q/'working-font.ttf'
 if not path.exists():raise RuntimeError('Prepare local working-font.ttf with Chinese glyphs before export')
 font=bpy.data.fonts.load(str(path));hy=P['roofDepth']/2
 layouts=[(c,0,-(hy-1.2)-.30,18.8-i*1.10,1.1,1.05)for i,c in enumerate('大成殿')]
 layouts +=[(c,(i-1.5)*1.23,-(hy-2.)-.51,11.40,1.13,1.40)for i,c in enumerate('表師世萬')]
 for char,x,y,z,w,h in layouts:
  cu=bpy.data.curves.new('Dacheng glyph '+char,type='FONT');cu.body=char;cu.font=font;cu.resolution_u=5;cu.extrude=.004
  ob=bpy.data.objects.new('Dacheng glyph '+char,cu);bpy.context.scene.collection.objects.link(ob);bpy.context.view_layer.update()
  evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=evaluated.to_mesh()
  vs=[v.co.copy()for v in me.vertices];xmin=min(v.x for v in vs);xmax=max(v.x for v in vs);ymin=min(v.y for v in vs);ymax=max(v.y for v in vs)
  sx=w/(xmax-xmin);sy=h/(ymax-ymin)
  coords=[(x+(v.x-(xmin+xmax)/2)*sx,y-v.z,z+(v.y-(ymin+ymax)/2)*sy)for v in vs]
  for face in me.polygons:B.face('gold',[coords[i]for i in face.vertices])
  evaluated.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True);bpy.data.curves.remove(cu)


def export(detail):
 level='detail'if detail else'preview';name='confucius '+level;scene=bpy.data.scenes.get(name)or bpy.data.scenes.new(name);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=build(Builder(detail));lettering(B);colors={'roof':(.48,.19,.038),'tile':(.68,.32,.06),'gold':(.43,.30,.12),'wood':(.105,.07,.035),'rafter':(.37,.36,.20),'red':(.38,.07,.037),'jade':(.13,.20,.15),'stone':(.65,.63,.55),'stoneRelief':(.54,.53,.47),'base':(.35,.34,.30),'shadow':(.035,.025,.017),'blue':(.022,.065,.24)}
 for k,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new(name+' '+k);me.from_pydata([(x/100,y/100,photo_z(z)/100)for x,y,z in vs],[],fs);me.update();me.materials.append(T.mat('Dacheng '+k,colors[k],.53 if k in['roof','tile']else .82));o=bpy.data.objects.new(name+' '+k,me);scene.collection.objects.link(o);o.select_set(True)
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=next(iter(scene.objects));import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');path=O/('confucius-'+level+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20)
 meta={'id':'confucius','level':level,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12],'bytes':path.stat().st_size,'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'heightSource':'photo-proportion estimate ~23 m; reported 33 m not reconciled, not survey verified','openings':[{**v,'origin':[v['origin'][0],v['origin'][1],photo_z(v['origin'][2])]}for v in B.openings],'status':'Photo-informed reconstruction; height, bracket proportion and carvings require further review; tablets use rendered typeface, not facsimile'}
 (Q/('confucius-'+level+'.json')).write_text(json.dumps(meta,indent=2));bpy.data.libraries.write(str(Q/('confucius-'+level+'.blend')),{scene},fake_user=True);print({k:v for k,v in meta.items()if k!='openings'})
if __name__=='__main__':
 for d in[False,True]:export(d)
