"""Duanmen: photo-informed reconstruction, not a surveyed conservation model.
Plan and vertical extents: OSM 25097188 and its building parts. 5 portals;
central opening 5.52 x 8.82 m per CCTV (2015-09-03). Other details inferred.
Reference photograph: そらみみ, CC BY-SA 4.0, 2016-08-26. No photo pixels used.
"""
import bpy, math, json, sys, importlib.util, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/assets/duanmen-detail'; OUT.mkdir(exist_ok=True)
PROOF=ROOT/'output/duanmen-detail'; PROOF.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('duanmen_helpers',ROOT/'scripts/build_tiananmen_detail.py'); H=importlib.util.module_from_spec(s);sys.modules[s.name]=H;s.loader.exec_module(H)
T=H.T
plan=json.loads((ROOT/'data/duanmen-footprint.json').read_text());L,D=plan['dimensions']
CX,CY=-3.35,1.025
ARCHES=[(-25,1.69,4.65),(-13,2.215,5.08),(0,2.76,6.06),(13,2.215,5.08),(25,1.69,4.65)]

def build(detail=True):
 level='detail' if detail else 'preview';name='Duanmen '+level
 scene=bpy.data.scenes.get(name) or bpy.data.scenes.new(name);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=T.Builder(detail);platform=13.0
 ends=[-L/2]+[v for x,r,z in ARCHES for v in [x-r,x+r]]+[L/2]
 for a,b in zip(ends[::2],ends[1::2]):
  B.box('wall',((a+b)/2,0,platform/2),(b-a,D,platform))
  B.box('stone',((a+b)/2,0,.45),(b-a,D+.02,.9))
 for x,r,spring in ARCHES:
  n=48 if detail else 20
  for i in range(n):
   a,b=math.pi*i/n,math.pi*(i+1)/n
   x0,x1=x+r*math.cos(a),x+r*math.cos(b);z0,z1=spring+r*math.sin(a),spring+r*math.sin(b)
   for side in [-1,1]:
    y=side*D/2;ps=[(x0,y,z0),(x1,y,z1),(x1,y,platform),(x0,y,platform)];B.face('wall',ps if side>0 else ps[::-1])
    R=r+.30;ps=[(x+r*math.cos(a),y+side*.02,spring+r*math.sin(a)),(x+r*math.cos(b),y+side*.02,spring+r*math.sin(b)),(x+R*math.cos(b),y+side*.02,spring+R*math.sin(b)),(x+R*math.cos(a),y+side*.02,spring+R*math.sin(a))];B.face('stone',ps if side>0 else ps[::-1])
   B.face('vault',[(x0,-D/2,z0),(x0,D/2,z0),(x1,D/2,z1),(x1,-D/2,z1)])
  for sign in [-1,1]:
   B.face('vault',[(x+sign*r,-D/2,0),(x+sign*r,D/2,0),(x+sign*r,D/2,spring),(x+sign*r,-D/2,spring)])
   for side in [-1,1]:B.box('stone',(x+sign*(r+.15),side*(D/2+.025),spring/2),(.3,.08,spring))
  # Leave the central passage genuinely open. Side doors stand recessed within vaults.
  for sign in [-1,1]:
   yy=D/2-1.5;doorh=spring+.25
   if x==0:
    # Open leaves, parallel to passage walls; no plane blocks the central void.
    xx=x+sign*(r-.10);B.box('door',(xx,yy-r/2,doorh/2),(.16,r-.12,doorh))
   else:
    xx=x+sign*r/2;B.box('door',(xx,yy,doorh/2),(r-.10,.16,doorh))
   if detail:
    for i in range(9):
     for j in range(9):
      u=.14+(r-.38)*i/8;zz=.25+(doorh-.5)*j/8
      if x==0:B.beam('gold',(xx-sign*.09,yy-u,zz),(xx-sign*.14,yy-u,zz),.044,7)
      else:B.beam('gold',(x+sign*u,yy-.09,zz),(x+sign*u,yy-.14,zz),.044,7)
  # Stone portal thresholds retain the open silhouette.
  B.box('stone',(x,0,.035),(2*r,D,.07))
 B.box('deck',(0,0,platform+.10),(L+.12,D+.12,.20))
 for side in [-1,1]:
  B.box('marble',(0,side*(D/2+.04),platform-.12),(L+.2,.24,.36))
  H.railing(B,(-L/2+.35,side*(D/2-.4)),(L/2-.35,side*(D/2-.4)),platform+.2)
  H.railing(B,(side*(L/2-.4),-D/2+.35),(side*(L/2-.4),D/2-.35),platform+.2)
 floor=13.23;top=20.8;hx=27.34;hy=13
 B.box('redDark',(CX,CY,(floor+top)/2),(50.6,21.7,top-floor))
 for i in range(10):
  x=CX-hx+2*hx*i/9
  for j in range(6):
   y=CY-hy+2*hy*j/5
   B.cylinder('red',.46,floor,top,18 if detail else 10,.40,(x,y));B.cylinder('marble',.56,floor,floor+.32,12,.48,(x,y))
   if j in [0,5] or i in [0,9]:
    for dz,w in [(0,.95),(.25,1.45),(.50,1.95)]:
     B.box('blue' if dz==0 else 'jade',(x,y,top-.60+dz),(w,1.1+dz,.17))
    if detail:
     for sign in [-1,1]:B.beam('goldMuted',(x+sign*.15,y,top-.50),(x+sign*.88,y,top-.12),.07,6)
 for side in [-1,1]:
  y=CY+side*10.90
  for i in range(9):
   x=CX-25.3+(i+.5)*50.6/9;w=5.1;z0=floor+.25;z1=19.7
   B.box('window',(x,y,(z0+z1)/2),(w,.09,z1-z0))
   # Four panels in each of the nine bays, dark red lattice above solid aprons.
   for j in range(5):B.box('red',(x-w/2+j*w/4,y+side*.07,(z0+z1)/2),(.095,.12,z1-z0))
   for z in [z0,z0+1.5,z1]:B.box('red',(x,y+side*.08,z),(w,.12,.13))
   if detail:
    for j in range(1,25):B.box('redDark',(x-w/2+j*w/25,y+side*.08,(z0+1.5+z1)/2),(.036,.05,z1-z0-1.5))
    for j in range(1,13):B.box('redDark',(x,y+side*.09,z0+1.5+j*(z1-z0-1.5)/13),(w,.05,.034))
  for z,xx,yy in [(20.0,27.5,13.05),(24.7,25.92,11.56),(26.0,25.92,11.56)]:
   y=CY+side*yy;ps=[(CX-xx,y,z),(CX+xx,y,z),(CX+xx,y,z+.68),(CX-xx,y,z+.68)]
   B.face('frieze',ps if side<0 else ps[::-1],[(0,0),(9,0),(9,1),(0,1)] if side<0 else [(0,1),(9,1),(9,0),(0,0)])
 B.box('jade',(CX,CY,25.2),(51.9,23.1,3.6))
 H.roof(B,32.37,18.035,21,29,True,CX,CY)
 H.roof(B,27.34,13,27,32.9,False,CX,CY)
 # Photo shows a small blue/gold name plaque between the roofs.
 B.box('gold',(CX,CY-11.69,25.85),(1.5,.16,1.85))
 B.box('blue',(CX,CY-11.79,25.85),(1.33,.10,1.68))
 colors={'wall':(.42,.085,.062),'stone':(.25,.24,.21),'vault':(.15,.12,.10),'deck':(.43,.40,.33),'marble':(.76,.73,.65),'red':(.36,.038,.025),'redDark':(.15,.027,.024),'door':(.21,.025,.019),'window':(.047,.035,.033),'jade':(.025,.13,.085),'blue':(.014,.047,.115),'roof':(.62,.30,.06),'tile':(.72,.39,.095),'gold':(.64,.37,.065),'goldMuted':(.45,.30,.10),'frieze':(.09,.15,.13),'letter':(.88,.64,.21)}
 mats={}
 for key,c in colors.items():
  texture=ROOT/'public/assets/tiantan-detail/frieze.png' if key=='frieze' else None
  mats[key]=T.mat('Duanmen '+key,c,.59 if key in ['roof','tile','gold'] else .87,texture=texture)
  if texture:next(n for n in mats[key].node_tree.nodes if n.type=='TEX_IMAGE').image.pack()
 for key,(verts,faces,uvs) in B.groups.items():
  me=bpy.data.meshes.new('Duanmen '+key);me.from_pydata([(x/100,y/100,z/100)for x,y,z in verts],[],faces);me.update();me.materials.append(mats[key]);uv=me.uv_layers.new(name='Architectural materials')
  for p,coords in zip(me.polygons,uvs):
   for li,co in zip(p.loop_indices,coords):uv.data[li].uv=co
  o=bpy.data.objects.new('Duanmen '+key,me);scene.collection.objects.link(o)
 fontpath=ROOT/'data/duanmen-plaque.ttf';font=bpy.data.fonts.load(str(fontpath)) if fontpath.exists() else None
 # Plaque glyphs are legible modern typesetting, not a claim of historic calligraphy.
 c=bpy.data.curves.new('Duanmen plaque','FONT');c.body='端\n門';c.align_x='CENTER';c.size=.0066;c.space_line=.92;c.extrude=.000015
 if font:c.font=font
 o=bpy.data.objects.new('Duanmen plaque',c);scene.collection.objects.link(o);o.location=(CX/100,(CY-11.85)/100,.2615);o.rotation_euler=(math.pi/2,0,0);c.materials.append(mats['letter'])
 for q in scene.objects:q.select_set(False)
 o.select_set(True);bpy.context.view_layer.objects.active=o
 target=next(i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if i.identifier=='MESH');bpy.ops.object.convert(target=target)
 bpy.context.view_layer.update()
 # Only roof ornaments are calibrated to the OSM total 35 m: never distort arch dimensions.
 maxz=max((o.matrix_world@Vector(v)).z for o in scene.objects for v in o.bound_box)
 if maxz>.35:
  for o in scene.objects:
   for v in o.data.vertices:
    if v.co.z>.27:v.co.z=.27+(v.co.z-.27)*(.35-.27)/(maxz-.27)
 bpy.context.view_layer.update()
 for o in scene.objects:o.select_set(True)
 bpy.context.view_layer.objects.active=next(iter(scene.objects))
 import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB')
 bpy.ops.export_scene.gltf(filepath=str(OUT/(level+'.glb')),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[o.matrix_world@Vector(v) for o in scene.objects for v in o.bound_box];mi=[min(v[i]for v in corners)for i in range(3)];ma=[max(v[i]for v in corners)for i in range(3)]
 stats={'level':level,'footprintMetres':[L,D],'heightMetres':35,'heightSource':'OSM, not surveyed','portals':5,'centerOpeningMetres':[5.52,8.82],'columnGrid':[10,6],'frontBays':9,'bodyOffsetMetres':[CX,CY],'boundsLocalBlender':[mi,ma],'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'meshes':len(scene.objects),'bytes':(OUT/(level+'.glb')).stat().st_size,'sha':hashlib.sha256((OUT/(level+'.glb')).read_bytes()).hexdigest()[:12]}
 (PROOF/(level+'-audit.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(PROOF/('端门_'+level+'.blend')),{scene},fake_user=True);print(stats)
 return scene
if __name__=='__main__':build(False);build(True)
