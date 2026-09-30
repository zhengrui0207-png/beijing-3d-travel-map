"""Wangfujing East Church: photo-informed exterior, mapped footprint, inferred elevations.
Metres internally. Three domed towers (not Gothic spires), west-facing front.
No reference photograph pixels used as textures; no surveyed-accuracy claim.
"""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'public/assets/cathedral-detail';OUT.mkdir(exist_ok=True);PROOF=R/'output/cathedral-detail';PROOF.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('cathedral_primitives',R/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(s);sys.modules[s.name]=T;s.loader.exec_module(T)
P=json.loads((R/'data/cathedral-plan.json').read_text());FRONT=-32.18434992039695;HALF=10.53
class Builder(T.Builder):
 def __init__(self,detail):super().__init__(detail);self.openings=[]

def arch(cx,bottom,spring,r,kind='glass'):return {'x':cx,'bottom':bottom,'spring':spring,'r':r,'kind':kind}
def circle(cx,z,r,kind='rose'):return {'x':cx,'z':z,'r':r,'kind':kind}
def limits(h,x):
 v=math.sqrt(max(0,h['r']**2-(x-h['x'])**2))
 return (h['z']-v,h['z']+v)if'z'in h else(h['bottom'],h['spring']+v)

def facade(B,a,b,z0,z1,holes=(),brick=True):
 """Cut brick surface at curved boundaries; actual inset glass/louvers and stone reveal."""
 dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);ux,uy=dx/length,dy/length;nx,ny=uy,-ux
 def pt(u,z,depth=0):return(a[0]+ux*u-nx*depth,a[1]+uy*u-ny*depth,z)
 xs={0.,length}
 for h in holes:
  n=32 if B.detail else 14
  for i in range(n+1):xs.add(h['x']+h['r']*math.cos(math.pi*i/n))
 xs=sorted(x for x in xs if -.00001<=x<=length+.00001)
 for l,r in zip(xs,xs[1:]):
  if r-l<1e-7:continue
  active=sorted([h for h in holes if abs((l+r)/2-h['x'])<h['r']],key=lambda h:limits(h,(l+r)/2)[0]);lo0=lo1=z0
  for h in active:
   b0,t0=limits(h,l);b1,t1=limits(h,r)
   if b0>lo0 or b1>lo1:B.face('brick',[pt(l,lo0),pt(r,lo1),pt(r,b1),pt(l,b0)])
   lo0,lo1=t0,t1
  if lo0<z1 or lo1<z1:B.face('brick',[pt(l,lo0),pt(r,lo1),pt(r,z1),pt(l,z1)])
 if brick and B.detail:
  # True exterior brick joints; clipped to the same curved opening silhouettes.
  bh=.22;bw=.53
  for j in range(math.ceil((z1-z0)/bh)):
   z=z0+(j+.5)*bh
   if z>=z1:continue
   for i in range(-1,math.ceil(length/bw)+1):
    l=max(0,(i+.5*(j%2))*bw+.008);r=min(length,l+bw-.016)
    if r<=l:continue
    bot=max(z0,z-bh/2+.008);top=min(z1,z+bh/2-.008)
    blocked=False
    for h in holes:
     if r<h['x']-h['r']or l>h['x']+h['r']:continue
     # Keep tiny margin rather than let brick faces seal curved cutouts.
     xx=max(h['x']-h['r'],min(h['x']+h['r'],(l+r)/2));bb,tt=limits(h,xx)
     if top>bb-.35 and bot<tt+.35:blocked=True;break
    if not blocked:B.face('brick'+str((i*17+j*43)%3),[pt(l,bot,-.007),pt(r,bot,-.007),pt(r,top,-.007),pt(l,top,-.007)])
 for h in holes:
  rad=h['r'];xc=h['x'];n=48 if B.detail else 20
  if'z'in h:points=[(xc+rad*math.cos(i*math.tau/n),h['z']+rad*math.sin(i*math.tau/n))for i in range(n)]
  else:points=[(xc-rad,h['bottom']),(xc+rad,h['bottom'])]+[(xc+rad*math.cos(i*math.pi/n),h['spring']+rad*math.sin(i*math.pi/n))for i in range(n+1)]
  depth=.48 if h['kind']=='door'else .32
  for aa,bb in zip(points,points[1:]+points[:1]):B.face('reveal',[pt(*aa),pt(*bb),pt(*bb,depth),pt(*aa,depth)])
  # Planar inset pane fan, all apertures convex.
  mid=(xc,h['z']if'z'in h else(h['bottom']+h['spring'])/2)
  for k,(aa,bb)in enumerate(zip(points,points[1:]+points[:1])):B.face('glass'+str(k*4//len(points))if h['kind']=='rose'else h['kind'],[pt(*mid,depth),pt(*aa,depth),pt(*bb,depth)])
  if'z'in h:angles=(0,math.tau);spring=h['z']
  else:angles=(0,math.pi);spring=h['spring']
  # Voussoirs are separate radiating wedges, with a recessed ring behind them.
  for i in range(n):
   t0=angles[0]+(angles[1]-angles[0])*(i+.035)/n;t1=angles[0]+(angles[1]-angles[0])*(i+.965)/n
   B.face('stone'if i%4 else'stoneLight',[pt(xc+rr*math.cos(t),spring+rr*math.sin(t),-.08)for rr,t in[(rad,t0),(rad+.22,t0),(rad+.22,t1),(rad,t1)]])
  if'z'not in h:
   for sign in[-1,1]:
    for zz in [h['bottom'],h['spring']]:B.beam('stone',pt(xc+sign*(rad+.16),zz,-.10),pt(xc+sign*(rad+.16),zz+.08,-.10),.21,4)
    B.beam('stone',pt(xc+sign*(rad+.11),h['bottom'],-.08),pt(xc+sign*(rad+.11),h['spring'],-.08),.105,4)
  if h['kind']=='louver':
   bottom=h.get('bottom',spring-rad)
   for z in [bottom+.12+k*.20 for k in range(math.ceil((spring+rad-bottom)/.20))]:
    rw=rad if z<=spring and 'z'not in h else math.sqrt(max(0,rad*rad-(z-spring)**2))
    if rw>.04:B.beam('metal',pt(xc-rw+.02,z,depth-.03),pt(xc+rw-.02,z,depth-.03),.035,4)
  if h['kind']=='glass':
   B.beam('stone',pt(xc,h['bottom'],depth-.04),pt(xc,spring+rad,depth-.04),.045,6)
   for z in [h['bottom']+.8+k*.85 for k in range(max(1,int((spring-h['bottom'])/.85)))]:B.beam('metal',pt(xc-rad,z,depth-.06),pt(xc+rad,z,depth-.06),.026,4)
  if h['kind']=='rose':
   for v in[(rad-.04,0),(0,rad-.04)]:B.beam('stoneLight',pt(xc-v[0],spring-v[1],depth-.12),pt(xc+v[0],spring+v[1],depth-.12),.115,8)
   B.beam('stoneLight',pt(xc,spring,depth-.14),pt(xc,spring,depth-.24),rad*.16,24)
  if h['kind']=='door':
   for sign in[-1,1]:
    u=xc+sign*rad*.45
    for z in[h['bottom']+.65,h['bottom']+1.8]:
     for dz in[-.45,.45]:B.beam('doorEdge',pt(u-rad*.34,z+dz,depth-.02),pt(u+rad*.34,z+dz,depth-.02),.04,4)
     for du in[-rad*.34,rad*.34]:B.beam('doorEdge',pt(u+du,z-.45,depth-.02),pt(u+du,z+.45,depth-.02),.04,4)
  B.openings.append({'point':pt(*mid),'outward':[nx,ny,0],'depth':depth,'kind':h['kind']})
 return pt

def bands(B,cx,cy,hx,hy,z,heavy=False):
 for dz,proj,h in [(-.25,.06,.14),(-.07,.14,.12),(.12,.28,.22),(.29,.34,.10)]:
  for side in[-1,1]:
   B.box('stone',(cx,cy+side*(hy+proj/2),z+dz),(2*hx+proj,proj,h));B.box('stone',(cx+side*(hx+proj/2),cy,z+dz),(proj,2*hy+proj,h))
 if heavy and B.detail:
  for side in[-1,1]:
   for i in range(math.ceil(2*hx/.28)):B.box('stoneLight',(cx-hx+(i+.5)*2*hx/math.ceil(2*hx/.28),cy+side*(hy+.07),z-.42),(.13,.18,.15))
   for i in range(math.ceil(2*hy/.28)):B.box('stoneLight',(cx+side*(hx+.07),cy-hy+(i+.5)*2*hy/math.ceil(2*hy/.28),z-.42),(.18,.13,.15))

def pilaster(B,x,y,z0,z1,w=.65):
 B.box('stone',(x,y,(z0+z1)/2),(w,.34,z1-z0))
 for dx in[-.32,0,.32]:B.box('stoneLight',(x+dx*w,y-.19,(z0+z1)/2),(w*.08,.07,z1-z0-.25))
 for z,ww,h in[(z0,w*1.5,.24),(z0+.28,w*1.25,.16),(z1-.25,w*1.20,.20),(z1,w*1.55,.23)]:B.box('stoneLight',(x,y-.03,z),(ww,.48,h))
 if B.detail:
  for sign in[-1,1]:
   last=None
   for i in range(30):
    t=i/29*math.pi*3;r=.14*(1-i/40);p=(x+sign*w*.40+r*math.cos(t),y-.29,z1-.15+r*math.sin(t))
    if last:B.beam('stoneLight',last,p,.025,4)
    last=p

def dome(B,cx,cy,z,r,h):
 n=64 if B.detail else 32;rows=20 if B.detail else 10
 for j in range(rows):
  a=j*math.pi/2/rows;b=(j+1)*math.pi/2/rows
  for i in range(n):
   t=i*math.tau/n;tt=(i+1)*math.tau/n
   B.face('dome',[(cx+r*math.cos(u)*math.cos(v),cy+r*math.cos(u)*math.sin(v),z+h*math.sin(u))for u,v in[(a,t),(a,tt),(b,tt),(b,t)]])
 for i in range(8):
  t=i*math.tau/8
  for j in range(rows):
   a=j*1.38/rows;b=(j+1)*1.38/rows
   B.beam('stone',(cx+(r+.035)*math.cos(a)*math.cos(t),cy+(r+.035)*math.cos(a)*math.sin(t),z+h*math.sin(a)),(cx+(r+.035)*math.cos(b)*math.cos(t),cy+(r+.035)*math.cos(b)*math.sin(t),z+h*math.sin(b)),.045,5)
 # Open-looking small octagonal lantern, cap and metal cross.
 zz=z+h-.04;B.cylinder('metal',.42,zz,zz+.82,8,center=(cx,cy))
 for i in range(8):
  t=i*math.tau/8;B.cylinder('stone',.06,zz,zz+.86,6,center=(cx+.46*math.cos(t),cy+.46*math.sin(t)))
 B.cylinder('stone',.56,zz+.82,zz+1.03,8,.20,(cx,cy));B.cylinder('stoneLight',.21,zz+1.03,zz+1.12,8,.12,(cx,cy));top=zz+2.25
 B.beam('metal',(cx,cy,zz+1.1),(cx,cy,top),.042,8);B.beam('metal',(cx-.38,cy,zz+1.87),(cx+.38,cy,zz+1.87),.042,8)
 return top

def tower(B,cx,cy,central=False):
 w=6.4 if central else 4.5;z0=15.6;bellTop=22 if central else 19.9;h=w/2
 pts=[(cx-h,cy-h),(cx+h,cy-h),(cx+h,cy+h),(cx-h,cy+h)]
 for a,b in zip(pts,pts[1:]+pts[:1]):
  rad=.62 if central else .47
  holes=[arch(w*f,16.1,bellTop-1.35 if central else bellTop-.94,rad,'louver')for f in[.34,.66]]
  facade(B,a,b,z0,bellTop,holes)
 bands(B,cx,cy,h,h,bellTop,True)
 B.box('stone',(cx,cy,bellTop+.12),(w,w,.24))
 for sign in[-1,1]:pilaster(B,cx+sign*(h-.28),cy-h-.13,z0+.15,bellTop-.48,.48)
 # Raised octagonal drum: central oculi; low side drums carry framed relief panels.
 dz=bellTop+.32;radius=h*.95;corners=[(cx+radius*math.cos(math.pi/8+i*math.pi/4),cy+radius*math.sin(math.pi/8+i*math.pi/4))for i in range(8)];drumH=1.75 if central else 1.15
 for a,b in zip(corners,corners[1:]+corners[:1]):
  length=math.dist(a,b);holes=[circle(length/2,dz+drumH*.50,.49,'louver')]if central else[];facade(B,a,b,dz,dz+drumH,holes,False)
  if not central:
   mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2;angle=math.atan2(b[1]-a[1],b[0]-a[0]);B.box('stone',(mx,my,dz+drumH*.48),(length*.50,.09,.60),angle)
 for zz,rr in[(dz+drumH-.05,radius+.10),(dz+drumH+.12,radius+.18)]:B.cylinder('stone',rr,zz,zz+.15,8,center=(cx,cy))
 return dome(B,cx,cy,dz+drumH+.24,radius+.10,3.23 if central else 2.72)

def pitched_roof(B,hx,ya,yb,eave,peak):
 for sign in[-1,1]:
  B.face('roof',[(sign*hx,ya,eave),(sign*hx,yb,eave),(0,yb,peak),(0,ya,peak)])
  for i in range(1,math.ceil((yb-ya)/(.30 if B.detail else 1.2))):
   y=ya+i*(.30 if B.detail else 1.2)
   if y<yb:B.beam('roofRib',(sign*hx,y,eave+.016),(0,y,peak+.016),.025,4)
  B.beam('metal',(sign*hx,ya,eave),(sign*hx,yb,eave),.10,8)
 B.beam('roofRib',(0,ya,peak),(0,yb,peak),.09,8)
 for y in[ya,yb]:B.face('brick',[(-hx,y,eave),(hx,y,eave),(0,y,peak)])

def build(B):
 # Full footprint main nave; east service/chancel volume follows mapped width changes.
 front=FRONT;end=15.6
 B.box('foundation',(0,(front+end)/2,.30),(2*HALF,end-front,.60))
 for sign in[-1,1]:
  a=(sign*HALF,front);b=(sign*HALF,end)
  if sign<0:a,b=b,a
  length=end-front;holes=[arch((i+.5)*length/8,3.0,9.6,1.07)for i in range(8)]
  facade(B,a,b,.6,13.0,holes);B.box('stone',(sign*(HALF+.08),(front+end)/2,1.05),(.23,length,.35));B.box('stone',(sign*(HALF+.12),(front+end)/2,12.7),(.3,length,.22))
  for i in range(9):
   y=front+i*length/8;B.box('stone',(sign*(HALF+.18),y,6.6),(.36,.70,12.0));B.box('stoneLight',(sign*(HALF+.23),y,12.5),(.46,.98,.42))
   if i in[0,8]:B.beam('metal',(sign*(HALF+.32),y,1.),(sign*(HALF+.32),y,12.8),.07,6)
 facade(B,(HALF,end),(-HALF,end),.6,13.0)
 pitched_roof(B,HALF+.32,front+5,end+.30,13.1,17.8)
 # Asymmetric rear mass and polygonal east end from the actual OSM ring.
 rear=P['localFootprint'][4:]+[[-4.967342371110449,end],[8.186128226414427,end]]
 area=sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(rear,rear[1:]+rear[:1]))
 if area<0:rear.reverse()
 for a,b in zip(rear,rear[1:]+rear[:1]):
  length=math.dist(a,b)
  # The attachment edge meets the nave: it is an internal wall, not an exterior window.
  attached=abs(a[1]-end)<1e-6 and abs(b[1]-end)<1e-6
  holes=[arch(length/2,2.5,6.8,.72)]if length>3 and not attached else[]
  facade(B,a,b,.15,10.,holes);B.beam('stone',(*a,9.95),(*b,9.95),.13,6)
 center=(1.5,24.5,12.1)
 for a,b in zip(rear,rear[1:]+rear[:1]):B.face('roof',[(*a,10.1),(*b,10.1),center])
 # Western two-storey three-bay facade.
 holes=[arch(HALF+x,.58,3.42,1.30 if x==0 else 1.08,'door')for x in[-7.0,0,7.0]]
 holes += [circle(HALF,10.9,1.73)]
 for sign in[-1,1]:
  for off in[-.53,.53]:holes.append(arch(HALF+sign*7.+off,8.2,11.5,.48))
 facade(B,(-HALF,front),(HALF,front),.6,15.65,holes)
 B.box('stone',(0,front+2.5,15.54),(2*HALF,5.,.22))
 facade(B,(HALF,front),(HALF,front+5),13.,15.65)
 facade(B,(-HALF,front+5),(-HALF,front),13.,15.65)
 for z in[.75,6.95,15.45]:bands(B,0,front+2.5,HALF,2.5,z,True)
 for x in[-10.,-4.25,-2.85,2.85,4.25,10.]:
  for za,zb in[(1.0,6.4),(7.5,14.85)]:pilaster(B,x,front-.13,za,zb,.46)
 # Paired window unifying arches, ornamental medallions and relief plaques.
 for sign in[-1,1]:
  xc=sign*7
  for i in range(32):
   a=i*math.pi/32;b=(i+1)*math.pi/32
   B.beam('stone',(xc+1.50*math.cos(a),front-.19,11.36+1.5*math.sin(a)),(xc+1.5*math.cos(b),front-.19,11.36+1.5*math.sin(b)),.11,6)
  for z in[4.7,10.8]:
   x=sign*3.58;B.box('stoneLight',(x,front-.30,z),(.35,.09,3.0 if z>5 else 2.7))
   if B.detail:
    for k in range(9):B.beam('stone',(x-.10,front-.37,z-1.2+k*.3),(x+.1,front-.37,z-1.05+k*.3),.025,4)
  for x,z in[(sign*1.9,13.0),(sign*1.9,8.9),(sign*8.4,5.6)]:
   B.beam('stoneLight',(x,front-.04,z),(x,front-.24,z),.24,24)
 # Shallow full-width entrance stairs, not a raised pedestal.
 for i in range(4):B.box('foundation',(0,front-.30-(3-i)*.29,(i+1)*.145/2),(21.3,.35,(i+1)*.145))
 # All three domes genuinely modelled in both LODs.
 tops=[tower(B,-7.,front+2.3),tower(B,0,front+3.2,True),tower(B,7.,front+2.3)]
 # Short balustrades visible between and outside the three tower bases.
 for xa,xb in[(-HALF,-9.25),(-4.75,-3.2),(3.2,4.75),(9.25,HALF)]:
  yy=front+.08
  B.box('stone',((xa+xb)/2,yy,15.93),(xb-xa,.32,.18))
  B.box('stoneLight',((xa+xb)/2,yy,16.82),(xb-xa,.36,.16))
  count=max(2,round((xb-xa)/.32))
  for i in range(count):
   x=xa+(i+.5)*(xb-xa)/count
   B.cylinder('stone',.075,16.0,16.23,8,.115,(x,yy))
   B.cylinder('stone',.115,16.23,16.56,8,.055,(x,yy))
   B.cylinder('stone',.055,16.56,16.75,8,.085,(x,yy))
 for x in[-10.1,10.1]:
  B.box('stone',(x,front+.10,16.94),(.48,.48,.36))
  B.cylinder('stoneLight',.23,17.12,17.36,12,.10,(x,front+.10))
 # Calibrate the inferred 30m silhouette by adjusting only above-facade elevations.
 current=max(tops)
 for vs,fs,uv in B.groups.values():
  for i,(x,y,z)in enumerate(vs):
   if z>15.6:vs[i]=(x,y,15.6+(z-15.6)*(30.-15.6)/(current-15.6))
 for o in B.openings:
  if o['point'][2]>15.6:o['point']=(*o['point'][:2],15.6+(o['point'][2]-15.6)*(30-15.6)/(current-15.6))


def export(detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get('cathedral '+level)or bpy.data.scenes.new('cathedral '+level);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=Builder(detail);build(B)
 colors={'brick':(.39,.385,.32),'brick0':(.41,.40,.34),'brick1':(.365,.365,.31),'brick2':(.425,.415,.35),'stone':(.47,.465,.39),'stoneLight':(.63,.615,.52),'foundation':(.35,.36,.325),'reveal':(.145,.15,.13),'glass':(.075,.135,.12),'glass0':(.055,.08,.07),'glass1':(.07,.085,.06),'glass2':(.065,.09,.08),'glass3':(.08,.07,.055),'door':(.045,.060,.042),'doorEdge':(.11,.13,.085),'louver':(.04,.055,.047),'metal':(.18,.205,.17),'dome':(.265,.285,.245),'roof':(.18,.21,.19),'roofRib':(.23,.255,.23)}
 mats={k:T.mat('Cathedral '+k,c,.88 if k not in['glass','metal']else .57)for k,c in colors.items()}
 for k,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new('cathedral '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mats[k]);
  if k=='dome':
   for face in me.polygons:face.use_smooth=True
  o=bpy.data.objects.new('cathedral '+k,me);scene.collection.objects.link(o)
 bpy.context.view_layer.update()
 for ob in scene.objects:ob.select_set(True)
 bpy.context.view_layer.objects.active=next(iter(scene.objects));import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');path=OUT/('cathedral-'+level+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[ob.matrix_world@Vector(v)for ob in scene.objects for v in ob.bound_box];stats={'id':'cathedral','level':level,'height':30.,'heightSource':'photo-inferred','boundsLocal':[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]],'triangles':sum(len(p.vertices)-2 for ob in scene.objects for p in ob.data.polygons),'meshes':len(scene.objects),'openings':B.openings,'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12]}
 (PROOF/('cathedral-'+level+'.json')).write_text(json.dumps(stats,ensure_ascii=False,indent=2));bpy.data.libraries.write(str(PROOF/('cathedral-'+level+'.blend')),{scene},fake_user=True);print({k:v for k,v in stats.items()if k!='openings'})
if __name__=='__main__':
 for detail in[False,True]:export(detail)
