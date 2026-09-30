"""Photo-informed Yinding Bridge. Horizontal axis from OSM way 816148132.
Stonework, arch height, width and carvings are estimates, not measured survey data.
Reference PQ77wd, Wikimedia Commons File:Yinding Bridge.jpg, CC BY-SA 4.0.
Metres internally; map units=100m, local +Y follows the south-to-north bridge axis.
"""
import bpy,math,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/assets/yinding-detail';PROOF=ROOT/'output/yinding-detail'
spec=importlib.util.spec_from_file_location('yinding_helpers',ROOT/'scripts/build_tiantan_detail.py');T=importlib.util.module_from_spec(spec);sys.modules[spec.name]=T;spec.loader.exec_module(T)
SX=111320*math.cos(math.radians(39.915))/100;SY=1113.2
es=json.loads((ROOT/'data/osm_beijing.json').read_text())['elements'];way=next(e for e in es if e['type']=='way'and e['id']==816148132)
a,b=sorted(way['geometry'],key=lambda p:p['lat'])
p0=((a['lon']-116.415)*SX,(a['lat']-39.915)*SY);p1=((b['lon']-116.415)*SX,(b['lat']-39.915)*SY)
L=math.dist(p0,p1)*100;HALF=L/2;W=6.6;AC=-1.6;R=3.05

def deck(y):
 # Stepped approaches smoothly meet the flat-map ground at each OSM endpoint.
 t=(y-AC)/(HALF-AC if y>=AC else HALF+AC)
 return .09+2.08*max(0,1-t*t)
def arch(y):return 1.56*math.sqrt(max(0,1-((y-AC)/R)**2)) if abs(y-AC)<R else -.025
def quadblock(B,key,y0,y1,z0,z1,x,thickness):
 lo0=max(z0,arch(y0)+.24);lo1=max(z0,arch(y1)+.24);hi0=min(z1,deck(y0)-.15);hi1=min(z1,deck(y1)-.15)
 if hi0<=lo0 or hi1<=lo1:return
 xa,xb=x-thickness/2,x+thickness/2
 for pts in [[(xa,y0,lo0),(xa,y1,lo1),(xa,y1,hi1),(xa,y0,hi0)],[(xb,y1,lo1),(xb,y0,lo0),(xb,y0,hi0),(xb,y1,hi1)],[(xa,y0,hi0),(xb,y0,hi0),(xb,y1,hi1),(xa,y1,hi1)]]:B.face(key,pts)

def build(detail=True):
 level='detail'if detail else'preview';name='Yinding Bridge '+level
 scene=bpy.data.scenes.get(name)or bpy.data.scenes.new(name);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=T.Builder(detail)
 # Continuous watertight arched body; arch is offset to match the mapped water neck.
 n=128 if detail else 48
 for i in range(n):
  y0=-HALF+L*i/n;y1=-HALF+L*(i+1)/n;z0=arch(y0);z1=arch(y1);t0=deck(y0)-.10;t1=deck(y1)-.10
  for x,rev in [(-W/2,False),(W/2,True)]:
   ps=[(x,y0,z0),(x,y1,z1),(x,y1,t1),(x,y0,t0)];B.face('mortar',list(reversed(ps))if rev else ps)
  B.face('vault',[(-W/2,y0,z0),(W/2,y0,z0),(W/2,y1,z1),(-W/2,y1,z1)])
  B.face('slate',[(-W/2,y1,t1),(W/2,y1,t1),(W/2,y0,t0),(-W/2,y0,t0)])
 # Voussoir ring: actual wedge-shaped stones, with narrow radial joints.
 count=41 if detail else 21
 for side in [-1,1]:
  x=side*(W/2+.035)
  for k in range(count):
   t0=math.pi*k/count+.003;t1=math.pi*(k+1)/count-.003
   def pt(t,r,zr,xx):return(xx,AC+r*math.cos(t),zr*math.sin(t))
   pts=[pt(t0,R,1.56,x),pt(t1,R,1.56,x),pt(t1,R+.29,1.83,x),pt(t0,R+.29,1.83,x)]
   B.face('limestone'+str(k%3),pts if side<0 else list(reversed(pts)))
   if detail:
    B.face('limestone1',[pt(t0,R,1.56,x),pt(t1,R,1.56,x),pt(t1,R,1.56,x-side*.23),pt(t0,R,1.56,x-side*.23)])
  for row in range(6):
   z0=row*.39+.015;z1=z0+.365;step=.78 if detail else 1.2
   y=-HALF+(step*.5 if row%2 else 0)
   while y<HALF:
    yy=min(HALF,y+step-.014);quadblock(B,'masonry'+str((row+round(y*4))%3),y+.006,yy,z0,z1,x-side*.06,.16);y+=step
 # Individually laid slate paving follows stepped approaches; small joints remain visible.
 dy=.25 if detail else .55;ny=math.ceil(L/dy);nx=11 if detail else 6
 for j in range(ny):
  y0=-HALF+L*j/ny+.006;y1=-HALF+L*(j+1)/ny-.006;z=deck((y0+y1)/2)
  for i in range(nx):
   x=-W/2+(i+.5)*W/nx
   B.box('paver'+str((i+j*3)%4),(x,(y0+y1)/2,z-.03),(W/nx-.012,y1-y0,.08))
 # Coping, carved stone parapet panels: six lotus-topped posts on each side.
 ys=[-HALF+.45+(L-.9)*k/5 for k in range(6)]
 for side in [-1,1]:
  x=side*(W/2-.16)
  for y in ys:
   z=deck(y)
   B.box('marble',(x,y,z+.12),(.47,.48,.24))
   B.box('marble',(x,y,z+.68),(.34,.36,1.16))
   B.box('marble',(x,y,z+1.26),(.41,.43,.12))
   B.cylinder('marble',.19,z+1.32,z+1.49,16,.22,(x,y))
   B.cylinder('marble',.22,z+1.49,z+1.78,24,.235,(x,y))
   B.cylinder('marble',.235,z+1.78,z+1.84,24,.18,(x,y))
   if detail:
    for k in range(12):
     a=k*math.tau/12;B.beam('limestone0',(x+.185*math.cos(a),y+.185*math.sin(a),z+1.30),(x+.22*math.cos(a),y+.22*math.sin(a),z+1.50),.017,5)
    # Recessed rectangular panels on post faces.
    for face in [-1,1]:
     xx=x+face*.173
     for yy in [y-.115,y+.115]:B.beam('engraving',(xx,yy,z+.3),(xx,yy,z+1.07),.009,4)
     for zz in [z+.3,z+1.07]:B.beam('engraving',(xx,y-.115,zz),(xx,y+.115,zz),.009,4)
  for idx,(a,b)in enumerate(zip(ys,ys[1:])):
   a+=.20;b-=.20;segments=12 if detail else 5
   for j in range(segments):
    u=a+(b-a)*j/segments;v=a+(b-a)*(j+1)/segments;za=deck(u);zb=deck(v)
    # Lower solid slab and top handrail follow the rise of the bridge.
    for zlo,zhi,key in [(.03,.18,'marble'),(.20,.60,'marble'),(1.07,1.20,'marble')]:
     for face in [-1,1]:B.face(key,[(x+face*.10,u,za+zlo),(x+face*.10,v,zb+zlo),(x+face*.10,v,zb+zhi),(x+face*.10,u,za+zhi)])
     B.face(key,[(x-.10,u,za+zhi),(x+.10,u,za+zhi),(x+.10,v,zb+zhi),(x-.10,v,zb+zhi)])
   # Vase balusters leave real openings between solid slab and curved lintel.
   for f in [.22,.5,.78]:
    y=a+(b-a)*f;z=deck(y)
    for z0,z1,r0,r1 in [(.60,.67,.11,.12),(.67,.82,.12,.07),(.82,.91,.07,.14),(.91,1.06,.14,.09)]:B.cylinder('marble',r0,z+z0,z+z1,12,r1,(x,y))
    if detail:
     # Cloud motifs, small carved scrolls beneath the handrail on both faces.
     for face in [-1,1]:
      for sign in [-1,1]:
       last=None
       for k in range(22):
        t=k/21*math.pi*2;r=.14*(1-k/27);p=(x+face*.108,y+sign*(.10+r*math.cos(t)),z+1.015-r*.48*math.sin(t))
        if last:B.beam('limestone0',last,p,.020,5)
        last=p
   if detail:
    for face in [-1,1]:
     xx=x+face*.106
     # Carved outlines in the lower parapet; central panel remains for the name.
     for off in [.26,.54]:
      B.beam('engraving',(xx,a+.12,deck(a+.12)+off),(xx,b-.12,deck(b-.12)+off),.009,4)
     for yy in [a+.12,b-.12]:B.beam('engraving',(xx,yy,deck(yy)+.26),(xx,yy,deck(yy)+.54),.009,4)
 # Subtle synthesized stone micro-normal, no photo pixels copied.
 colors={'mortar':(.18,.19,.18),'vault':(.27,.28,.26),'slate':(.31,.32,.29),'marble':(.57,.55,.49),'engraving':(.33,.32,.29)}
 for i in range(3):colors['limestone'+str(i)]=(.49+i*.025,.48+i*.025,.43+i*.024);colors['masonry'+str(i)]=(.31+i*.027,.33+i*.027,.31+i*.027)
 for i in range(4):colors['paver'+str(i)]=(.34+i*.015,.35+i*.015,.32+i*.015)
 mats={}
 for key,color in colors.items():
  m=bpy.data.materials.new('Yinding '+key);m.use_nodes=True;m.diffuse_color=(*color,1)
  p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.89
  if key not in ['engraving','mortar']:
   tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'stone-grain-normal.png'),check_existing=True);tex.image.colorspace_settings.name='Non-Color'
   normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.24;m.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],p.inputs['Normal'])
  mats[key]=m
 for key,(verts,faces,_)in B.groups.items():
  me=bpy.data.meshes.new('Yinding '+key);me.from_pydata([(x/100,y/100,z/100)for x,y,z in verts],[],faces);me.update();me.materials.append(mats[key])
  uv=me.uv_layers.new(name='Stone grain mapping')
  for face in me.polygons:
   axis=max(range(3),key=lambda i:abs(face.normal[i]));axes=[i for i in range(3)if i!=axis]
   for li in face.loop_indices:
    v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]*100/.45,v[axes[1]]*100/.45)
  o=bpy.data.objects.new('Yinding '+key,me);scene.collection.objects.link(o)
 # Name inscription, oriented toward both parapet faces; model lettering, not a bitmap.
 if detail:
  fontpath=Path('/tmp/yinding-inscription.ttf');font=bpy.data.fonts.load(str(fontpath))if fontpath.exists()else None
  for side in [-1,1]:
   c=bpy.data.curves.new('Yinding name','FONT');c.body='銀錠橋';c.size=.0024;c.align_x='CENTER';c.extrude=.000012
   if font:c.font=font
   o=bpy.data.objects.new('Yinding name',c);scene.collection.objects.link(o);o.location=(side*(W/2-.047)/100,0,(deck(0)+.32)/100);o.rotation_euler=(math.pi/2,0,side*math.pi/2);c.materials.append(mats['engraving'])
 bpy.context.view_layer.update()
 target=next(i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if i.identifier=='MESH')
 for o in list(scene.objects):
  if o.type=='FONT':
   for q in scene.objects:q.select_set(False)
   o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target=target)
 bpy.context.view_layer.update()
 for o in scene.objects:o.select_set(True)
 bpy.context.view_layer.objects.active=next(iter(scene.objects))
 import io_scene_gltf2
 fmt=next(v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)if v[0]=='GLB')
 bpy.ops.export_scene.gltf(filepath=str(OUT/(level+'.glb')),export_format=fmt,use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12)
 corners=[o.matrix_world@Vector(v)for o in scene.objects for v in o.bound_box];mi=[min(v[i]for v in corners)for i in range(3)];ma=[max(v[i]for v in corners)for i in range(3)]
 stats={'level':level,'length':L,'width':W,'axis':{'start':p0,'end':p1},'boundsLocalBlender':[mi,ma],'triangles':sum(len(p.vertices)-2 for o in scene.objects for p in o.data.polygons),'meshes':len(scene.objects),'bytes':(OUT/(level+'.glb')).stat().st_size,'sha':hashlib.sha256((OUT/(level+'.glb')).read_bytes()).hexdigest()[:12]}
 (PROOF/(level+'-audit.json')).write_text(json.dumps(stats,indent=2));bpy.data.libraries.write(str(PROOF/('银锭桥_'+level+'.blend')),{scene},fake_user=True);print(stats)
 return scene
if __name__=='__main__':build(False);build(True)
