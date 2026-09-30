"""National Art Museum: photo-informed stepped pavilion and open colonnades.
OSM plan in metres; elevations and unseen rear surfaces inferred, not surveyed.
"""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1];OUT=R/'public/assets/art-detail';OUT.mkdir(exist_ok=True);Q=R/'output/art-detail';Q.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('art_primitives',R/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(s);sys.modules[s.name]=T;s.loader.exec_module(T)
P=json.loads((R/'data/art-plan.json').read_text())
class Builder(T.Builder):
 def __init__(self,detail):super().__init__(detail);self.windows=[];self.roofs=[]

def wall(B,a,b,z0,z1,holes=()):
 dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);u=(dx/L,dy/L);n=(u[1],-u[0])
 def pt(x,z,d=0):return(a[0]+u[0]*x-n[0]*d,a[1]+u[1]*x-n[1]*d,z)
 def clear(x,z):return not any(h[0]<x<h[2]and h[1]<z<h[3]for h in holes)
 xs=sorted({0,L,*[v for h in holes for v in[h[0],h[2]]]});zs=sorted({z0,z1,*[v for h in holes for v in[h[1],h[3]]]})
 for l,r in zip(xs,xs[1:]):
  for bot,top in zip(zs,zs[1:]):
   if clear((l+r)/2,(bot+top)/2):B.face('stone',[pt(l,bot),pt(r,bot),pt(r,top),pt(l,top)])
 # Panel joints as recessed dark strips stop at real aperture boundaries.
 if B.detail:
  for z in[math.ceil(z0/.72)*.72+i*.72 for i in range(math.ceil((z1-z0)/.72))]:
   if not z0<z<z1:continue
   for l,r in zip(xs,xs[1:]):
    if clear((l+r)/2,z):B.face('joint',[pt(l,z,-.002),pt(r,z,-.002),pt(r,z+.025,-.002),pt(l,z+.025,-.002)])
  # Vertical block joints use the same aperture clipping as the horizontal seams.
  for row in range(math.ceil((z1-z0)/.72)):
   bot=max(z0,row*.72+z0);top=min(z1,bot+.72)
   for i in range(1,math.ceil(L/1.4)):
    x=i*1.4+(.7 if row%2 else 0)
    if x>=L:continue
    for lo,hi in zip(sorted({bot,top,*[z for h in holes for z in[h[1],h[3]]if bot<z<top]}),sorted({bot,top,*[z for h in holes for z in[h[1],h[3]]if bot<z<top]})[1:]):
     if clear(x,(lo+hi)/2):B.face('joint',[pt(x,lo,-.003),pt(x+.018,lo,-.003),pt(x+.018,hi,-.003),pt(x,hi,-.003)])
 for l,bot,r,top,depth in holes:
  if depth is None:continue # Opening into a connected pavilion, with no hidden backing wall.
  corners=[(l,bot),(r,bot),(r,top),(l,top)]
  for aa,bb in zip(corners,corners[1:]+corners[:1]):
   # Deep ground-floor bays form a continuous colonnade behind shallow piers.
   # Full-depth side reveals would turn each bay into a sealed alcove at corners.
   revealDepth=.60 if depth>1 and aa[0]==bb[0]else depth
   B.face('reveal',[pt(*aa),pt(*bb),pt(*bb,revealDepth),pt(*aa,revealDepth)])
  B.face('glass',[pt(*q,depth)for q in corners])
  for x in[l,r]:B.beam('frame',pt(x,bot,depth-.03),pt(x,top,depth-.03),.055,4)
  for z in[bot,top]:B.beam('frame',pt(l,z,depth-.03),pt(r,z,depth-.03),.055,4)
  count=max(2,round((r-l)/.9))
  for i in range(1,count):B.beam('frame',pt(l+(r-l)*i/count,bot,depth-.06),pt(l+(r-l)*i/count,top,depth-.06),.035,4)
  for z in[bot+(top-bot)*.28,bot+(top-bot)*.72]:B.beam('frame',pt(l,z,depth-.06),pt(r,z,depth-.06),.035,4)
  B.windows.append({'point':pt(l+(r-l)*.37,bot+(top-bot)*.46),'normal':[*n,0],'depth':depth})
 return pt

def slab(B,ring,z,material='flatRoof'):
 points=[Vector((x,y,z))for x,y in ring]
 for tri in tessellate_polygon([points]):B.face(material,[tuple(points[p]if isinstance(p,int)else p)for p in tri])
def rect(B,x0,x1,y0,y1,z0,z1,window=True):
 ring=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
 for a,b in zip(ring,ring[1:]+ring[:1]):
  L=math.dist(a,b);n=max(1,round(L/4.7));step=L/n
  holes=[(i*step+.6,z0+.7,(i+1)*step-.6,z1-.8,.38)for i in range(n)]if window and z1-z0>2 else[];wall(B,a,b,z0,z1,holes)
 slab(B,ring,z1)

def ornament(B,a,b,z):
 L=math.dist(a,b);dx,dy=(b[0]-a[0])/L,(b[1]-a[1])/L;n=(dy,-dx);steps=max(1,round(L/1.65))
 for i in range(steps):
  x,y=a[0]+dx*(i+.5)*L/steps,a[1]+dy*(i+.5)*L/steps
  B.box('frieze',(x,y,z),(.62,.08,.45),math.atan2(dy,dx))
  for sign in[-1,1]:B.box('white',(x+dx*sign*.33,y+dy*sign*.33,z),(.06,.12,.5),math.atan2(dy,dx))
  if B.detail:
   # Geometric reconstruction of the visible circular frieze motifs, not copied photo pixels.
   for radius,material in[(.19,'gold'),(.12,'red'),(.055,'white')]:
    B.face(material,[(x+dx*radius*math.cos(k*math.tau/16)+n[0]*.065,y+dy*radius*math.cos(k*math.tau/16)+n[1]*.065,z+radius*math.sin(k*math.tau/16))for k in range(16)])


def hip(B,cx,cy,hx,hy,eave,peak,skirt=False):
 """Curved four-slope roof; skirt leaves an opening for the upper pavilion."""
 # ridge runs along the long axis; rotate narrow roofs using a local builder transform.
 swap=hy>hx
 if swap:hx,hy=hy,hx
 ridge=max(0,hx-hy);stop=.28 if skirt else 1.;steps=14 if B.detail else 6
 def point(x,y,z):return(cx-y,cy+x,z)if swap else(cx+x,cy+y,z)
 def section(t):return(hx-(hx-ridge)*t,hy*(1-t),eave+(peak-eave)*t**1.5)
 def local(x,y,z,t):return point(x,y,z+.28*(abs(x)/hx)**12*max(0,1-t*4)**2)
 for side in[-1,1]:
  n=max(12,math.ceil(2*hx/(.40 if B.detail else 1.25)))
  for j in range(steps):
   t,u=stop*j/steps,stop*(j+1)/steps;ax,ay,az=section(t);bx,by,bz=section(u)
   for i in range(n):
    f,g=-1+2*i/n,-1+2*(i+1)/n
    B.face('roof',[local(ax*f,side*ay,az,t),local(ax*g,side*ay,az,t),local(bx*g,side*by,bz,u),local(bx*f,side*by,bz,u)])
    v=(f+g)/2;B.beam('tile',local(ax*v,side*ay,az+.05,t),local(bx*v,side*by,bz+.05,u),.065,5)
  for j in range(steps):
   t,u=stop*j/steps,stop*(j+1)/steps;ax,ay,az=section(t);bx,by,bz=section(u)
   n=max(10,math.ceil(2*hy/(.45 if B.detail else 1.4)))
   for i in range(n):
    f,g=-1+2*i/n,-1+2*(i+1)/n
    B.face('roof',[local(side*ax,ay*f,az,t),local(side*ax,ay*g,az,t),local(side*bx,by*g,bz,u),local(side*bx,by*f,bz,u)])
    v=(f+g)/2;B.beam('tile',local(side*ax,ay*v,az+.05,t),local(side*bx,by*v,bz+.05,u),.063,5)
  for end in[-1,1]:
   last=None
   for j in range(steps+1):
    t=stop*j/steps;x,y,z=section(t);v=local(side*x,end*y,z+.13,t)
    if last:B.beam('ridge',last,v,.12,6)
    last=v
   # Small upturned terminal, not imperial roof beast arrays.
   B.beam('ridge',local(side*hx,end*hy,eave+.36,0),local(side*(hx+.24),end*(hy+.18),eave+.90,0),.12,6)
 if not skirt:
  B.beam('ridge',point(-ridge,0,peak+.12),point(ridge or .001,0,peak+.12),.18,8)
 # Underside fascia and cream rafter tips.
 for a,b in [((-hx,-hy),(hx,-hy)),((hx,-hy),(hx,hy)),((hx,hy),(-hx,hy)),((-hx,hy),(-hx,-hy))]:
  aa=point(*a,eave);bb=point(*b,eave);B.beam('frieze',aa,bb,.15,4)
  if B.detail:
   count=max(2,round(math.dist(a,b)/.40))
   for i in range(count):
    x=a[0]+(b[0]-a[0])*(i+.5)/count;y=a[1]+(b[1]-a[1])*(i+.5)/count
    pos=point(x,y,eave-.12);B.box('white',pos,(.15,.23,.14))
 B.roofs.append({'center':[cx,cy],'halfSize':[hy,hx]if swap else[hx,hy],'eave':eave,'peak':peak,'skirt':skirt})

def build(B):
 ring=P['localFootprint'];area=sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(ring,ring[1:]+ring[:1]));ring=ring if area>0 else ring[::-1]
 # Full mapped outline, with real deep ground colonnade bays rather than painted rectangles.
 for a,b in zip(ring,ring[1:]+ring[:1]):
  L=math.dist(a,b);n=max(1,round(L/5.0));step=L/n
  holes=[]
  if step>2:
   for i in range(n):
    holes.extend([(i*step+.70,1.3,(i+1)*step-.70,8.4,2.5),(i*step+.65,10.9,(i+1)*step-.65,14.5,.40)])
  # The entrance and pavilion cover the centre of the south wall.
  if abs(a[1]+26.65)<.05 and abs(b[1]+26.65)<.05:
   holes=[h for h in holes if abs(a[0]+h[0])>17 and abs(a[0]+h[2])>17]
   holes.append((-5.8-a[0],1.3,5.8-a[0],8.4,.5))
   holes.append((-16.4-a[0],10.5,16.4-a[0],15.6,None))
  pt=wall(B,a,b,.15,15.6,holes)
  for z in[1.15,9.9,15.6]:B.beam('white',pt(0,z,-.04),pt(L,z,-.04),.13,4)
 slab(B,ring,15.6)
 # Raised central gallery bar. Top-storey open balcony with deeper rear glazing.
 x0,x1,y0,y1=-61.23,53.92,-26.65,26.55
 upper=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
 for a,b in zip(upper,upper[1:]+upper[:1]):
  L=math.dist(a,b);n=max(2,round(L/4.8));st=L/n
  holes=[(i*st+.4,16.25,(i+1)*st-.4,20.5,1.7)for i in range(n)]
  if a[1]==y0 and b[1]==y0:
   holes=[h for h in holes if abs(a[0]+h[0])>17 and abs(a[0]+h[2])>17]
   holes.append((-16.4-a[0],15.6,16.4-a[0],21.2,None))
  pt=wall(B,a,b,15.6,21.2,holes);ornament(B,a,b,20.95)
  # Thin horizontal balcony rails do not fill the openings.
  for z in[16.,16.35]:B.beam('white',pt(0,z,-.18),pt(L,z,-.18),.06,6)
 slab(B,upper,21.2)
 # Four roof strips surround the mostly flat gallery roof.
 hip(B,-39.,-19.7,23.3,8.1,21.3,23.4);hip(B,35.5,-19.7,19.5,8.1,21.3,23.4)
 hip(B,-56.5,0,5.8,20.2,21.3,23.2);hip(B,49.2,0,5.8,20.2,21.3,23.2)
 hip(B,-2.8,21.2,53.8,6.3,21.3,23.3)
 # Central pavilion's nested terraces have broad lower windows and a smaller upper lantern.
 rect(B,-16.4,16.4,-25.95,-2.5,21.2,23.1,False)
 for za,zb in[(10.5,15.6),(15.6,23.1)]:
  holes=[(i*6.56+.5,za+.7,(i+1)*6.56-.5,zb-.7,.38)for i in range(5)]
  wall(B,(-16.4,-26.7),(16.4,-26.7),za,zb,holes)
 for rb,pk,hx,hy in[(23.15,25.8,18.1,13.8),(25.15,27.6,17.5,13.1),(27.1,29.2,16.8,12.4)]:
  hip(B,0,-14.6,hx,hy,rb,pk,True)
  rect(B,-hx+2.,hx-2.,-14.6-hy+2.,-14.6+hy-2.,rb,rb+(.65 if rb>27 else 1.9),False)
 rect(B,-11.9,11.9,-24.1,-5.1,27.4,31.25)
 hip(B,0,-14.6,13.4,10.6,31.3,33.7,True)
 rect(B,-10.5,10.5,-22.8,-6.4,31.5,32.2,False)
 hip(B,0,-14.6,12.1,9.5,32.25,34.4)
 B.cylinder('ridge',.23,34.45,35.0,10,.12,(0,-14.6))
 # Entry portico: open between four piers, glazed main door at the back.
 for x in[-14.,-6.1,6.1,14.]:
  B.box('stone',(x,-31.5,5.55),(1.4,1.6,8.7));B.box('white',(x,-31.5,1.4),(1.7,1.9,.4))
 B.box('stone',(0,-31.5,10.0),(29.4,1.6,1.1));B.box('stone',(0,-27.8,10.25),(29.4,8.9,.55));ornament(B,(-14.7,-32.33),(14.7,-32.33),9.85)
 hip(B,0,-28.0,16.1,5.8,10.55,13.25)
 # Ground colonnade roof continues to the two projecting front wings.
 hip(B,-26.,-27.7,9.9,3.5,9.5,10.8);hip(B,27.,-27.7,10.9,3.5,9.5,10.8)
 for cx,hx in[(-51.9,18.),(53.7,17.1)]:hip(B,cx,-43.4 if cx<0 else-41.9,hx,3.0,9.5,10.8)
 for i in range(8):B.box('stone',(0,-36.2+(i+.5)*.50,(i+1)*.15/2),(34.,.51,(i+1)*.15))
 # Open stone balustrades at the entry stairs.
 for x in[-17.5,17.5]:
  for y in[-35.9,-34.5,-33.1]:B.box('white',(x,y,.85),(.35,.35,1.7))
  for z in[1.4,1.7]:B.beam('white',(x,-36.0,z),(x,-32.7,z),.065,6)
 # Representative frieze medallions; no claim of reproducing historic calligraphy.
 B.box('white',(0,-32.36,9.55),(8.8,.16,1.6))
 return B

def export(detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get('art '+level)or bpy.data.scenes.new('art '+level);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=build(Builder(detail));colors={'stone':(.70,.66,.55),'white':(.80,.77,.66),'joint':(.39,.375,.33),'reveal':(.43,.43,.37),'flatRoof':(.37,.39,.35),'glass':(.025,.036,.041),'frame':(.20,.185,.135),'roof':(.40,.125,.018),'tile':(.65,.24,.035),'ridge':(.61,.20,.025),'gold':(.65,.40,.10),'red':(.33,.055,.024),'frieze':(.095,.29,.23)}
 mats={k:T.mat('Art Museum '+k,c,.78 if k not in['glass','tile','roof']else .45)for k,c in colors.items()}
 for k,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new('art '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mats[k]);o=bpy.data.objects.new('art '+k,me);scene.collection.objects.link(o);o.select_set(True)
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=next(iter(scene.objects));import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');path=OUT/('art-'+level+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[ob.matrix_world@Vector(v)for ob in scene.objects for v in ob.bound_box];meta={'id':'art','level':level,'heightSource':P['heightSource'],'boundsLocal':[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]],'windows':B.windows,'roofs':B.roofs,'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'meshes':len(scene.objects),'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12]}
 (Q/('art-'+level+'.json')).write_text(json.dumps(meta,indent=2));bpy.data.libraries.write(str(Q/('art-'+level+'.blend')),{scene},fake_user=True);print({k:v for k,v in meta.items()if k not in['windows','roofs']})
if __name__=='__main__':
 for d in[False,True]:export(d)
