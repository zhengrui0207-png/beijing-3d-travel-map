"""OSM-anchored imperial approach courts, photo-informed, dimensions partly inferred."""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/axis-courts';OUT.mkdir(exist_ok=True);PROOF=ROOT/'output/axis-courts';PROOF.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('axis_helpers',ROOT/'scripts/build_tiananmen_detail.py');H=importlib.util.module_from_spec(s);sys.modules[s.name]=H;s.loader.exec_module(H);T=H.T
plans=json.loads((ROOT/'data/axis-courts.json').read_text())
def longroof(B,a,b,d):
 # Continuous grey tiled roof; the roof is broken at gatehouses, not overlaid through them.
 n=max(2,math.ceil((b-a)/(.32 if B.detail else 1.0)));steps=8 if B.detail else 4;hy=d/2+.35
 for side in [-1,1]:
  for i in range(n):
   x0=a+(b-a)*i/n;x1=a+(b-a)*(i+1)/n
   for j in range(steps):
    t,u=j/steps,(j+1)/steps
    def p(x,t):return (x,side*hy*(1-t),5+3*t**1.3)
    ps=[p(x0,t),p(x1,t),p(x1,u),p(x0,u)];B.face('grayRoof',ps if side<0 else ps[::-1])
    q0,q1=p((x0+x1)/2,t),p((x0+x1)/2,u)
    B.beam('grayTile',(q0[0],q0[1],q0[2]+.04),(q1[0],q1[1],q1[2]+.04),.045,5)
  B.beam('grayRidge',(a,side*hy,5),(b,side*hy,5),.10,6)
 B.box('grayRidge',((a+b)/2,0,8.04),(b-a,.3,.14))
 for x in [a,b]:B.face('wall',[(x,-hy,5),(x,hy,5),(x,0,8)])
def gallery(B,a,b,d,side):
 if b-a<.2:return
 x=(a+b)/2;n=max(1,round((b-a)/4.1));depth=d-1.05
 B.box('stone',(x,0,.22),(b-a,d,.44));B.box('wall',(x,-side*.38,2.55),(b-a,depth,4.25))
 y=side*(d/2-.15);wy=side*(depth/2-.38+.02)
 for i in range(n+1):
  xx=a+(b-a)*i/n;B.cylinder('red',.15,.44,4.93,12 if B.detail else 8,.14,(xx,y));B.cylinder('stone',.21,.35,.57,8,.18,(xx,y))
 B.box('red',(x,y,4.76),(b-a,.30,.30));B.box('jade',(x,y,4.96),(b-a,.29,.11))
 for i in range(n):
  xx=a+(b-a)*(i+.5)/n;w=(b-a)/n-.40
  B.box('wood',(xx,wy,2.60),(w,.10,3.82))
  for j in range(5):B.box('redDark',(xx-w/2+j*w/4,wy+side*.06,2.6),(.068,.10,3.82))
  for z in [.72,1.65,4.49]:B.box('redDark',(xx,wy+side*.07,z),(w,.11,.10))
  if B.detail:
   for j in range(1,19):B.box('lattice',(xx-w/2+j*w/19,wy+side*.09,3.09),(.027,.04,2.79))
   for j in range(1,13):B.box('lattice',(xx,wy+side*.10,1.66+j*2.8/13),(w,.05,.026))
 longroof(B,a,b,d)
def gate(B,g,side):
 x,y=g['x'],g['y'];l,d=g['length'],g['depth'];w=l/2;dep=d/2+.7
 B.box('stone',(x,y,.22),(l,d+1,.44))
 # Three bays, centre opening goes through the building. Side wings have timber doors.
 openw=min(4.3,l*.26)
 for sign in [-1,1]:
  start=x+sign*openw/2;end=x+sign*w
  B.box('wall',((start+end)/2,y,4.1),(abs(end-start),d,7.5))
 B.box('redDark',(x,y,7.85),(l,d,.75))
 for xx in [x-w+.25,x-openw/2-.15,x+openw/2+.15,x+w-.25]:
  for sign in [-1,1]:
   yy=y+sign*(d/2+.14);B.cylinder('red',.25,.45,8.68,14 if B.detail else 8,.22,(xx,yy))
   for dz,sz in [(0,.65),(.23,.95),(.46,1.3)]:B.box('jade',(xx,yy,8.1+dz),(sz,.65+dz,.16))
 for side2 in [-1,1]:
  yy=y+side2*(d/2+.04)
  for sign in [-1,1]:
   xx=x+sign*(w+openw/2)/2;ww=w-openw/2-.45
   B.box('wood',(xx,yy,3.9),(ww,.1,6.8))
   if B.detail:
    for k in range(9):
     for j in range(9):B.beam('gold',(xx-ww*.43+k*ww*.86/8,yy+side2*.07,.9+j*.71),(xx-ww*.43+k*ww*.86/8,yy+side2*.13,.9+j*.71),.035,6)
  for z in [8.0,8.65]:B.box('blue',(x,yy,z),(l,.16,.38));B.box('goldMuted',(x,yy+side2*.10,z+.16),(l,.04,.04))
 # One curved xieshan roof rather than generic stacked triangular roof parts.
 H.roof(B,w+1.3,dep+1,9.1,11.0,False,x,y)

def build(spec,detail):
 level='detail' if detail else 'preview';name=spec['id']+' '+level;scene=bpy.data.scenes.get(name) or bpy.data.scenes.new(name);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=T.Builder(detail);length,depth=spec['length'],spec['depth'];gates=sorted(spec['gates'],key=lambda g:g['x']);a=-length/2
 for g in gates:
  left=g['x']-g['length']/2;gallery(B,a,left,depth,spec['inwardSide']);gate(B,g,spec['inwardSide']);a=g['x']+g['length']/2
 gallery(B,a,length/2,depth,spec['inwardSide'])
 colors={'stone':(.36,.34,.29),'wall':(.39,.07,.049),'red':(.38,.035,.024),'redDark':(.24,.028,.02),'wood':(.056,.026,.020),'lattice':(.20,.049,.028),'grayRoof':(.20,.23,.22),'grayTile':(.25,.275,.25),'grayRidge':(.17,.19,.18),'jade':(.025,.12,.075),'blue':(.018,.065,.10),'roof':(.62,.30,.06),'tile':(.72,.39,.095),'gold':(.61,.33,.055),'goldMuted':(.47,.31,.10)}
 mats={key:T.mat('Axis courts '+key,c,.61 if key in ['roof','tile','gold']else .86)for key,c in colors.items()}
 for key,(vs,fs,uvs) in B.groups.items():
  me=bpy.data.meshes.new(spec['id']+' '+key);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update();me.materials.append(mats[key]);o=bpy.data.objects.new(spec['id']+' '+key,me);scene.collection.objects.link(o)
 for o in scene.objects:o.select_set(True)
 bpy.context.view_layer.objects.active=next(iter(scene.objects));bpy.context.view_layer.update()
 import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB');path=OUT/(spec['id']+'-'+level+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[o.matrix_world@Vector(v) for o in scene.objects for v in o.bound_box];bounds=[[min(v[i]for v in corners)for i in range(3)],[max(v[i]for v in corners)for i in range(3)]]
 audit={'id':spec['id'],'level':level,'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'meshes':len(scene.objects),'bounds':bounds,'bytes':path.stat().st_size,'revision':hashlib.sha256(path.read_bytes()).hexdigest()[:12],'gateCount':len(gates)};(PROOF/(spec['id']+'-'+level+'.json')).write_text(json.dumps(audit,indent=2));print(audit)
 bpy.data.libraries.write(str(PROOF/(spec['id']+'-'+level+'.blend')),{scene},fake_user=True)
if __name__=='__main__':
 for spec in plans:
  for detail in [False,True]:build(spec,detail)
