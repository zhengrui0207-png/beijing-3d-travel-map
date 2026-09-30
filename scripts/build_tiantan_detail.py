"""Photo-informed Hall of Prayer reconstruction. Metres internally; glTF in 100 m map units.
Not a survey replica: dimensions anchored to 38.1 m height / 32.72 m lowest roof diameter.
Reference: xiquinhosilva, Wikimedia Commons, CC BY 2.0. Decorative texture is generated.
"""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/assets/tiantan-detail';OUT.mkdir(exist_ok=True)
TAU=math.tau
class Builder:
 def __init__(self,detail):self.groups={};self.detail=detail
 def face(self,mat,pts,uv=None):
  if mat=='stone':
   n=(Vector(pts[1])-Vector(pts[0])).cross(Vector(pts[2])-Vector(pts[0]));axis=max(range(3),key=lambda i:abs(n[i]));ax=[i for i in range(3)if i!=axis];uv=[(p[ax[0]]/4,p[ax[1]]/4)for p in pts]
  g=self.groups.setdefault(mat,[[],[],[]]);k=len(g[0]);g[0].extend(pts);g[1].append(tuple(range(k,k+len(pts))));g[2].append(uv or [(0,0),(1,0),(1,1),(0,1)][:len(pts)])
 def box(self,mat,c,size,angle=0):
  x,y,z=c;w,d,h=size;co,si=math.cos(angle),math.sin(angle)
  ps=[(x+dx*co-dy*si,y+dx*si+dy*co,z+dz)for dx,dy,dz in [(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),(-w/2,-d/2,h/2),(w/2,-d/2,h/2),(w/2,d/2,h/2),(-w/2,d/2,h/2)]]
  for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:self.face(mat,[ps[i]for i in ids])
 def cylinder(self,mat,r,z1,z2,n=64,r2=None,center=(0,0),caps=True,repeat=1):
  r2=r if r2 is None else r2;x,y=center
  for i in range(n):
   a=i*TAU/n;b=(i+1)*TAU/n
   p=[(x+r*math.cos(a),y+r*math.sin(a),z1),(x+r*math.cos(b),y+r*math.sin(b),z1),(x+r2*math.cos(b),y+r2*math.sin(b),z2),(x+r2*math.cos(a),y+r2*math.sin(a),z2)]
   self.face(mat,p,[(i/n*repeat,0),((i+1)/n*repeat,0),((i+1)/n*repeat,1),(i/n*repeat,1)])
   if caps:
    self.face(mat,[(x,y,z2),p[3],p[2]],[(.5,.5),(0,0),(1,0)])
    self.face(mat,[(x,y,z1),p[1],p[0]],[(.5,.5),(1,0),(0,0)])
 def ring(self,mat,r,z,width=.15,height=.15,n=128):
  self.cylinder(mat,r,z-height/2,z+height/2,n,caps=False)
  for i in range(n):
   a=i*TAU/n;b=(i+1)*TAU/n
   self.face(mat,[(rr*math.cos(t),rr*math.sin(t),z+height/2)for rr,t in [(r-width,a),(r,a),(r,b),(r-width,b)]])
 def beam(self,mat,a,b,r,n=6):
  a,b=Vector(a),Vector(b);axis=(b-a).normalized();side=axis.cross(Vector((0,0,1)))
  if side.length<.01:side=axis.cross(Vector((0,1,0)))
  side.normalize();up=axis.cross(side)
  for i in range(n):
   u=side*math.cos(i*TAU/n)+up*math.sin(i*TAU/n);v=side*math.cos((i+1)*TAU/n)+up*math.sin((i+1)*TAU/n)
   self.face(mat,[tuple(a+u*r),tuple(a+v*r),tuple(b+v*r),tuple(b+u*r)])
 def radial_box(self,mat,r,a,z,w,d,h):self.box(mat,(r*math.cos(a),r*math.sin(a),z),(d,w,h),a)

def mat(name,color,rough=.8,metal=0,texture=None):
 m=bpy.data.materials.get('Tiantan '+name) or bpy.data.materials.new('Tiantan '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if texture and texture.exists():
  node=next((n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'),None)or m.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(texture),check_existing=True);m.node_tree.links.new(node.outputs['Color'],p.inputs['Base Color'])
 return m

def stairs(B,r,z0,h,angle,width=5.0,run=4.6):
 n=12 if B.detail else 7
 for k in range(n):
  rr=r+run*(1-(k+.5)/n)
  B.radial_box('stone',rr,angle,z0+h*(k+.5)/n/2,width,run/n+.015,h*(k+.5)/n)
 # Sloped side coping and vertical handrail posts follow the ascent.
 for side in [-1,1]:
  def point(rr,z):return (rr*math.cos(angle)-side*(width/2+.45)*math.sin(angle),rr*math.sin(angle)+side*(width/2+.45)*math.cos(angle),z)
  B.beam('stone',point(r+run,z0+1.05),point(r,z0+h+1.05),.10,6)
  B.beam('stone',point(r+run,z0+.37),point(r,z0+h+.37),.075,4)
  for k in range(5):
   f=k/4;rr=r+run*(1-f);x,y,z=point(rr,z0+h*f)
   B.box('stone',(x,y,z+.52),(.26,.26,1.04));B.cylinder('stone',.17,z+1.04,z+1.20,8,.08,(x,y))

def terrace(B):
 for level,(r,z) in enumerate([(43.5,2.1),(37.0,4.2),(30.5,6.3)]):
  B.cylinder('stone',r,(level)*2.1,z,192 if B.detail else 96)
  B.ring('stoneLight',r+.14,z-.05,.5,.22)
  B.ring('stoneShade',r+.04,level*2.1+.16,.12,.22)
  # Circular stone paving joints represented by narrow pale courses.
  for rr in [r-1.4,r-3.0]:B.ring('stoneShade',rr,z+.012,.018,.018)
  count=round(TAU*(r-.5)/2.2)
  def gap(a):return abs(math.sin(a*4))<min(.62,4*3.3/r)
  for i in range(count):
   a=i*TAU/count;b=(i+1)*TAU/count
   if gap(a)or gap(b):continue
   x,y=(r-.45)*math.cos(a),(r-.45)*math.sin(a)
   B.box('stoneLight',(x,y,z+.66),(.29,.29,1.32),a)
   B.cylinder('stoneLight',.20,z+1.29,z+1.48,8,.10,(x,y))
   # Perforated balustrades, with stone rather than an opaque fence.
   for zz in [.27,.91,1.16]:
    B.beam('stoneLight',((r-.45)*math.cos(a),(r-.45)*math.sin(a),z+zz),((r-.45)*math.cos(b),(r-.45)*math.sin(b),z+zz),.065,4)
   for f in [.25,.5,.75]:
    t=a+(b-a)*f;B.radial_box('stoneLight',r-.45,t,z+.60,.10,.13,.62)
   if B.detail:
    for rr in [r-.35]:B.radial_box('stoneShade',rr,(a+b)/2,z+.44,.45,.1,.10)
  for j in range(8):stairs(B,r,level*2.1,2.1,j*TAU/8)

def curved_roof(B,outer,inner,z0,z1,count):
 rings=18 if B.detail else 12;segments=192 if B.detail else 96
 def profile(t):return z0+(z1-z0)*t**1.75+.20*math.exp(-t*28)
 for j in range(rings):
  t=j/rings;tt=(j+1)/rings;ra=outer+(inner-outer)*t;rb=outer+(inner-outer)*tt
  for i in range(segments):
   a=i*TAU/segments;b=(i+1)*TAU/segments
   B.face('roof',[(ra*math.cos(a),ra*math.sin(a),profile(t)),(ra*math.cos(b),ra*math.sin(b),profile(t)),(rb*math.cos(b),rb*math.sin(b),profile(tt)),(rb*math.cos(a),rb*math.sin(a),profile(tt))])
 B.ring('roofEdge',outer+.035,z0+.05,.27,.26,segments)
 B.ring('red',outer-.08,z0-.18,.34,.12,segments)
 B.ring('jade',outer-.22,z0-.31,.35,.09,segments)
 B.cylinder('shade',outer-.18,z0-.10,z0+.01,segments,r2=inner,caps=False)
 # Round roll tiles follow the entire roof curve. Preview keeps every fourth row.
 n=count if B.detail else count//4
 for i in range(n):
  a=i*TAU/n
  for j in range(rings):
   t=j/rings;tt=(j+1)/rings;ra=outer+(inner-outer)*t;rb=outer+(inner-outer)*tt
   # Half-round tile cross section; full profile is explicit geometry.
   cross=5 if B.detail else 3
   for k in range(cross):
    th=k*math.pi/cross;th2=(k+1)*math.pi/cross
    def v(r,zz,theta):
     w=.080*math.cos(theta);return(r*math.cos(a)-w*math.sin(a),r*math.sin(a)+w*math.cos(a),zz+.078*math.sin(theta)+.023)
    B.face('tile', [v(ra,profile(t),th),v(rb,profile(tt),th),v(rb,profile(tt),th2),v(ra,profile(t),th2)])
  if B.detail:
   # Eave tile ends with a small pale central relief.
   c=(outer*math.cos(a),outer*math.sin(a),z0+.12)
   B.radial_box('tile',outer+.025,a,z0+.12,.13,.14,.13)
   if i%2==0:B.radial_box('goldMuted',outer+.105,a,z0+.12,.033,.015,.033)

def bracket_ring(B,r,z,count):
 for i in range(count):
  a=i*TAU/count
  for k in range(3):
   B.radial_box('jade'if k%2 else'azure',r+.16*k,a,z+.16*k,.20+.15*k,.48+.16*k,.115)
  if B.detail:
   B.radial_box('goldMuted',r+.48,a,z+.35,.07,.05,.18)
   for side in [-1,1]:B.radial_box('blue',r+.21,a+side*.018,z+.31,.32,.4,.10)

def drums(B):
 # Main hall walls, 12 outer structural bays and four doors/panels per bay.
 r=12.05
 B.cylinder('red',r,6.32,10.48,144 if B.detail else 96)
 B.cylinder('frieze',r+.03,10.50,11.87,144 if B.detail else 96,repeat=12)
 B.cylinder('frieze',r+.03,12.0,13.45,144 if B.detail else 96,repeat=12)
 for z in [6.47,10.46,11.91,12.0,13.37]:B.ring('goldMuted',r+.09,z,.12,.085)
 for i in range(12):
  a=(i-.5)*TAU/12
  x,y=r*math.cos(a),r*math.sin(a)
  B.cylinder('red',.32,6.35,13.55,12,.25,(x,y))
  B.cylinder('stoneLight',.40,6.31,6.67,12,.33,(x,y))
  for k in range(4):
   t=a+(k+.5)*TAU/48
   # South central portal is slightly open; other bays retain lattice doors.
   opening=i==9 and k in [1,2]
   B.radial_box('shade'if opening else'redDark',r+.09,t,8.42,1.32,.14,3.86)
   for side in [-1,1]:B.radial_box('goldMuted',r+.18,t+side*.054,8.42,.045,.06,3.92)
   for zz in [6.49,8.11,10.37]:B.radial_box('goldMuted',r+.18,t,zz,1.38,.07,.085)
   if not opening:
    divisions=7 if B.detail else 3
    for q in range(1,divisions):B.radial_box('woodGold',r+.19,t+(q/divisions-.5)*.098,9.24,.022,.045,2.18)
    for q in range(1,10 if B.detail else 5):B.radial_box('woodGold',r+.2,t,8.11+q*(2.26/(10 if B.detail else 5)),1.23,.045,.022)
   B.radial_box('woodGold',r+.18,t,7.29,.96,.045,1.02)
   B.radial_box('red',r+.21,t,7.29,.77,.05,.83)
 # Inner 12 pillars and four dragon-well pillars, total 28 structural columns.
 for i in range(12):
  a=(i+.5)*TAU/12;B.cylinder('red',.30,6.35,24.5,12,.25,(6.6*math.cos(a),6.6*math.sin(a)))
 for a in [math.pi/4,math.pi*3/4,math.pi*5/4,math.pi*7/4]:B.cylinder('red',.60,6.35,25.55,16,.52,(3.7*math.cos(a),3.7*math.sin(a)))
 for r,z1,z2 in [(10.35,17.5,20.75),(7.5,23.8,26.90)]:
  B.cylinder('blue',r,z1,z2,128)
  B.cylinder('frieze',r+.025,z1+.25,z2-.30,128,repeat=12)
  for z in [z1+.12,z1+.32,z2-.27,z2-.10]:B.ring('goldMuted',r+.08,z,.11,.075)
  for i in range(48):B.radial_box('jade',r+.06,i*TAU/48,(z1+z2)/2,.095,.09,z2-z1-.4)
 bracket_ring(B,12.02,12.88,96 if B.detail else 48)
 bracket_ring(B,10.30,20.08,80 if B.detail else 40)
 bracket_ring(B,7.48,26.15,64 if B.detail else 32)
 # Gold finial with convex bud silhouette, not a sphere on a stick.
 profile=[(35.40,.85),(35.66,.84),(35.86,.64),(36.0,.56),(36.15,.47),(36.30,.45),(36.46,.56),(36.80,.79),(37.25,.91),(37.64,.83),(37.94,.57),(38.10,.02)]
 for (z,r),(zz,rr)in zip(profile,profile[1:]):B.cylinder('gold',r,z,zz,48,rr,caps=False)
 B.ring('gold',.95,35.45,.35,.15)
 # Plaque hangs from the upper south eave; vertical gold characters are added below.
 B.box('gold',(.0,-10.1,25.45),(1.65,.24,3.55))
 B.box('plaque',(.0,-10.25,25.45),(1.42,.12,3.26))
 for z in [23.95,26.95]:B.box('goldMuted',(0,-10.34,z),(1.38,.055,.065))

def write_scene(detail):
 name='Tiantan Prayer Hall '+('detail'if detail else'preview')
 scene=bpy.data.scenes.get(name)or bpy.data.scenes.new(name);bpy.context.window.scene=scene
 for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 B=Builder(detail);terrace(B);drums(B)
 curved_roof(B,16.36,10.32,13.75,17.80,400)
 curved_roof(B,13.85,7.48,21.05,24.03,336)
 curved_roof(B,10.65,.85,27.22,35.45,256)
 materials={
  'stone':mat('white marble',(.52,.49,.43),.88,texture=ROOT/'public/assets/palace/marble.png'),'stoneLight':mat('carved marble',(.65,.62,.55),.82),
  'stoneShade':mat('paving joints',(.36,.35,.31),.94),'roof':mat('blue glazed tiles',(.016,.032,.065),.52),
  'tile':mat('tile rolls',(.025,.045,.089),.49),'roofEdge':mat('eave edge',(.012,.027,.063),.36),
  'red':mat('vermilion pillars',(.33,.024,.018),.72),'redDark':mat('lacquer doors',(.12,.012,.011),.83),
  'gold':mat('gilded finial',(.68,.42,.06),.28,.75),'goldMuted':mat('painted gold',(.55,.35,.09),.58,.18),
  'woodGold':mat('window lattice',(.34,.20,.054),.77),'jade':mat('green brackets',(.035,.17,.13),.7),
  'blue':mat('painted blue',(.017,.073,.16),.75),'azure':mat('blue brackets',(.034,.12,.24),.68),
  'shade':mat('recess',(.016,.014,.017),.95),'plaque':mat('plaque blue',(.013,.026,.090),.72),
  'frieze':mat('painted frieze',(.03,.1,.2),.77,texture=OUT/'frieze.png')}
 objs=[]
 for key,(verts,faces,uvs)in B.groups.items():
  me=bpy.data.meshes.new('Tiantan '+key);me.from_pydata([(x/100,y/100,z/100)for x,y,z in verts],[],faces);me.update()
  uv=me.uv_layers.new(name='Architectural mapping')
  for poly,coords in zip(me.polygons,uvs):
   for li,xy in zip(poly.loop_indices,coords):uv.data[li].uv=xy
   # Small roof facets retain their tile shape; round silhouettes use dense rings.
  me.materials.append(materials[key]);o=bpy.data.objects.new('Tiantan '+key,me);scene.collection.objects.link(o);objs.append(o)
 # Actual Chinese plaque lettering as curves, converted to mesh for portable glTF.
 fontpath='/System/Library/Fonts/Supplemental/Songti.ttc'
 font=bpy.data.fonts.load(fontpath) if Path(fontpath).exists() else None
 for i,ch in enumerate('祈年殿'):
  c=bpy.data.curves.new('Plaque '+ch,'FONT');c.body=ch;c.size=.007;c.extrude=.00012
  if font:c.font=font
  o=bpy.data.objects.new('Plaque '+ch,c);scene.collection.objects.link(o);o.location=(-.0034,-.1035,.263-i*.0102);o.rotation_euler=(math.pi/2,0,0);c.materials.append(materials['gold']);objs.append(o)
 bpy.context.view_layer.update()
 for o in scene.objects:o.select_set(False)
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0]
 enum=[i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items]
 for o in objs:
  if o.type=='FONT':
   for other in scene.objects:other.select_set(False)
   o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target=next(v for v in enum if v=='MESH'))
 bpy.context.view_layer.update()
 for o in scene.objects:o.select_set(True)
 import io_scene_gltf2
 formats=[v[0]for v in io_scene_gltf2.get_format_items(None,bpy.context)]
 level='detail'if detail else'preview'
 image_formats=[i.identifier for i in bpy.ops.export_scene.gltf.get_rna_type().properties['export_image_format'].enum_items]
 image_format=next(v for v in image_formats if v=='JPEG')
 bpy.ops.export_scene.gltf(filepath=str(OUT/(level+'.glb')),export_format=next(v for v in formats if v=='GLB'),use_selection=True,use_active_scene=True,export_image_format=image_format,export_jpeg_quality=90,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=18,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
 bpy.data.libraries.write(str(ROOT/'output/tiantan-detail'/('祈年殿_'+level+'.blend')),{scene},fake_user=True)
 stats={'level':level,'meshes':len(scene.objects),'vertices':sum(len(o.data.vertices)for o in scene.objects if o.type=='MESH'),'triangles':sum(len(p.vertices)-2 for o in scene.objects if o.type=='MESH'for p in o.data.polygons),'heightMetres':38.1,'roofDiameterMetres':32.72,'fileBytes':(OUT/(level+'.glb')).stat().st_size}
 (ROOT/'output/tiantan-detail'/(level+'-audit.json')).write_text(json.dumps(stats,indent=2));print(stats)
 return scene

if __name__=='__main__':
 write_scene(False);write_scene(True)
