"""Circular Mound: real tier dimensions, cardinal stairs, perforated marble rails and mapped enclosures."""
import bpy,math,json,sys,importlib.util,hashlib,random
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1];P=json.loads((R/'data/circular-mound-plan.json').read_text());O=R/'public/assets/circular-mound';Q=R/'output/circular-mound';O.mkdir(exist_ok=True);Q.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('mound_gate_helpers',R/'scripts/build_tiantan_gates.py');G=importlib.util.module_from_spec(s);sys.modules[s.name]=G;s.loader.exec_module(G);E=G.E;T=G.T

def polar(r,a,z):return(r*math.cos(a),r*math.sin(a),z)
def post(B,x,y,z,angle=0):
 B.box('stone',(x,y,z+.53),(.24,.24,1.06),angle);B.box('stone',(x,y,z+.08),(.35,.35,.16),angle)
 prof=[(1.02,.16),(1.10,.19),(1.25,.17),(1.35,.12),(1.42,.04)]
 for (h,r),(hh,rr)in zip(prof,prof[1:]):B.cylinder('stone',r,z+h,z+hh,16 if B.detail else 8,rr,(x,y),False)
 if B.detail:
  for side in [-1,1]:B.beam('relief',(x-.075,y+side*.125,z+.82),(x+.075,y+side*.125,z+.96),.018,5)
def panel(B,a,b,z):
 dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);ang=math.atan2(dy,dx);mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
 B.box('stone',(mx,my,z+.40),(L-.20,.13,.48),ang)
 for h in [.15,.70,1.06]:B.box('stone',(mx,my,z+h),(L,.18,.11),ang)
 # Pierced upper register and shallow inset lower panels.
 for k in range(3):
  t=(k+.5)/3;xx,yy=a[0]+dx*t,a[1]+dy*t
  B.box('stone',(xx,yy,z+.85),(.055,.14,.32),ang)
 if B.detail:
  for side in [-1,1]:
   nx,ny=-dy/L*side*.072,dx/L*side*.072;B.box('relief',(mx+nx,my+ny,z+.40),(max(.1,L-.40),.018,.25),ang)
   B.beam('stone', (mx+nx-dx*.14,my+ny-dy*.14,z+.37),(mx+nx,my+ny,z+.50),.022,5);B.beam('stone',(mx+nx,my+ny,z+.50),(mx+nx+dx*.14,my+ny+dy*.14,z+.37),.022,5)
def stairs(B,r,z0,h,angle):
 n=P['stairs']['count'];run=P['stairs']['run'];w=P['stairs']['width']
 for k in range(n):B.radial_box('stone',r+run*(1-(k+.5)/n),angle,z0+h*(k+1)/n/2,w,run/n+.004,h*(k+1)/n)
 def p(rr,l,z):return(rr*math.cos(angle)-l*math.sin(angle),rr*math.sin(angle)+l*math.cos(angle),z)
 for side in [-1,1]:
  lat=side*(w/2+.12)
  for f in [0,.5,1]:x,y,z=p(r+run*(1-f),lat,z0+h*f);post(B,x,y,z,angle)
  for j in range(4):
   f,ff=j/4,(j+1)/4;a=p(r+run*(1-f),lat,z0+h*f);b=p(r+run*(1-ff),lat,z0+h*ff)
   for zz in [.17,.72,1.08]:B.beam('stone',(a[0],a[1],a[2]+zz),(b[0],b[1],b[2]+zz),.075,4)
   B.face('stone',[(a[0],a[1],a[2]+.22),(b[0],b[1],b[2]+.22),(b[0],b[1],b[2]+.66),(a[0],a[1],a[2]+.66)])

def terrace(B):
 z0=0;stats=[]
 for idx,tier in enumerate(P['tiers']):
  r,h=tier['radius'],tier['height'];z=z0+h;seg=288 if B.detail else 144
  # Curved moulded plinth, recessed waist, upper lip and clean horizontal walking surface.
  profile=[(z0,r),(z0+.12,r+.06),(z0+.26,r+.02),(z0+.40,r-.17),(z-.40,r-.17),(z-.22,r+.08),(z-.08,r+.12),(z,r)]
  for (zz,rr),(zzz,rrr)in zip(profile,profile[1:]):B.cylinder('stone',rr,zz,zzz,seg,rrr,caps=False)
  B.cylinder('paving0',r,z-.025,z,seg)
  lo=P['tiers'][idx+1]['radius']+.04 if idx<2 else .50
  # Three sets of nine radial courses:1863/1134/405 stones; central round heart stone.
  for row,count in enumerate(tier['pavers']):
   r0=lo+(r-lo-.35)*row/9+.009;r1=lo+(r-lo-.35)*(row+1)/9-.009
   for i in range(count):
    a=i*math.tau/count+.005/r0;b=(i+1)*math.tau/count-.005/r0
    for j in range(3 if B.detail else 1):
     n=3 if B.detail else 1;aa=a+(b-a)*j/n;bb=a+(b-a)*(j+1)/n;B.face('paving'+str((i*17+row*7)%5),[polar(r0,aa,z+.003),polar(r1,aa,z+.003),polar(r1,bb,z+.003),polar(r0,bb,z+.003)])
  if idx==2:B.cylinder('heart',.49,z,z+.008,96 if B.detail else 48)
  railr=r-.34;gap=math.asin((P['stairs']['width']/2+.24)/railr)
  for side in range(4):
   a=side*math.pi/2+gap;b=(side+1)*math.pi/2-gap;count=tier['panelsPerQuarter']
   for i in range(count+1):
    th=a+(b-a)*i/count;x,y,_=polar(railr,th,z);post(B,x,y,z,th)
    if i<count:
     tt=a+(b-a)*(i+1)/count;panel(B,(x,y),polar(railr,tt,z)[:2],z)
   stairs(B,r,z0,h,side*math.pi/2)
  if B.detail:
   # Representative drain spouts and waist ornament. Not replicas of individual carvings.
   for i in range(72 if idx==2 else 108 if idx==1 else 180):
    a=(i+.5)*math.tau/(72 if idx==2 else 108 if idx==1 else 180)
    if min(abs(math.sin(a)),abs(math.cos(a)))<3/r:continue
    B.radial_box('stone',r+.11,a,z-.31,.18,.38,.13);B.radial_box('recess',r+.303,a,z-.34,.09,.006,.045)
    B.radial_box('relief',r-.163,a,z0+h*.52,.32,.02,.13)
  stats.append({'radius':r,'top':z,'stones':sum(tier['pavers']),'flights':4,'stepsPerFlight':9});z0=z
 return stats

def wall(B,points,height):
 cx,cy=P['center'];ps=[((x-cx)*100,(y-cy)*100)for x,y in points]
 for a,b in zip(ps,ps[1:]):
  dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
  if L<.001:continue
  angle=math.atan2(dy,dx);nx,ny=-dy/L,dx/L;mid=((a[0]+b[0])/2,(a[1]+b[1])/2);h=height-.30
  B.box('red',(*mid,h/2),(L+.018,.65,h),angle);B.box('base',(*mid,.13),(L+.018,.75,.26),angle)
  for side in [-1,1]:
   B.face('blueRoof',[(a[0]+nx*.48*side,a[1]+ny*.48*side,h),(b[0]+nx*.48*side,b[1]+ny*.48*side,h),(*b,height),(*a,height)])
   if B.detail:
    n=max(1,round(L/.23))
    for i in range(n):
     t=(i+.5)/n;x,y=a[0]+dx*t,a[1]+dy*t;B.beam('blueTile',(x+nx*.48*side,y+ny*.48*side,h+.025),(x,y,height+.025),.038,5)
  B.beam('blueTile',(*a,height+.02),(*b,height+.02),.047,6)

def build(detail):
 level='detail'if detail else'preview';scene=bpy.data.scenes.get('Circular Mound '+level)or bpy.data.scenes.new('Circular Mound '+level);bpy.context.window.scene=scene
 for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
 B=T.Builder(detail);cx,cy=P['center'];poly=[Vector(((x-cx)*100,(y-cy)*100,.034))for x,y in P['court'][:-1]]
 for tri in tessellate_polygon([poly]):
  ps=[tuple(poly[v]if isinstance(v,int)else v)for v in tri];B.face('court',ps,[(x/4,y/4)for x,y,z in ps])
 for line in P['innerWall']:wall(B,line,1.89)
 for line in P['outerWall']:wall(B,line,2.75)
 for g in P['gates']:
  # Join the mapped wall endpoints to the outer stone posts, without filling any portal.
  for side in [-1,1]:
   a,b=[(g['center'][0]+side*g['length']*f*math.cos(g['angle'])/100,g['center'][1]+side*g['length']*f*math.sin(g['angle'])/100)for f in [.435,.5+(1.3/g['length']if g['kind']=='inner'else .1/g['length'])]]
   wall(B,[a,b],1.89 if g['kind']=='inner'else 2.75)
  if g['existing']:continue
  C=T.Builder(detail);G.lingxing(C,g);E.merge(B,C,((g['center'][0]-cx)*100,(g['center'][1]-cy)*100),g['angle'])
 stats=terrace(B)
 colors={'stone':(.68,.67,.62),'relief':(.58,.575,.53),'recess':(.22,.23,.22),'heart':(.34,.36,.335),'court':(.33,.335,.30),'red':(.40,.047,.029),'redDark':(.25,.028,.016),'base':(.25,.26,.23),'blueRoof':(.017,.032,.065),'blueTile':(.032,.061,.11),'metal':(.58,.37,.07)}
 for i in range(5):colors['paving'+str(i)]=(.28+i*.015,.30+i*.015,.28+i*.015)
 for k,(vs,fs,uvs)in B.groups.items():
  m=T.mat('Circular Mound '+k,colors[k],.88 if k not in ['blueRoof','blueTile']else .55)
  # Preserve map-unit scale while texture detail uses metre coordinates in the mesh UVs.
  if k in ['stone','court']:
   tex=R/('public/assets/palace/marble.png'if k=='stone'else'public/assets/palace/courtyard-stone.png');m=T.mat('Circular Mound '+k,colors[k],.88,texture=tex);next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
  me=bpy.data.meshes.new('Mound '+k);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(m);uv=me.uv_layers.new()
  for p,cs in zip(me.polygons,uvs):
   for i,co in zip(p.loop_indices,cs):uv.data[i].uv=co
  ob=bpy.data.objects.new('Mound '+k,me);scene.collection.objects.link(ob);ob.select_set(True)
 bpy.context.view_layer.update();import io_scene_gltf2;fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');imfmt=next(v.identifier for v in bpy.ops.export_scene.gltf.get_rna_type().properties['export_image_format'].enum_items if v.identifier=='JPEG');path=O/(level+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_image_format=imfmt,export_jpeg_quality=90,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20)
 st={'level':level,'meshes':len(scene.objects),'triangles':sum(len(f.vertices)-2 for ob in scene.objects for f in ob.data.polygons),'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12],'tiers':stats};(Q/(level+'.json')).write_text(json.dumps(st,indent=2));bpy.data.libraries.write(str(Q/('圜丘坛_'+level+'.blend')),{scene},fake_user=True);print(st)
if __name__=='__main__':build(False);build(True)
