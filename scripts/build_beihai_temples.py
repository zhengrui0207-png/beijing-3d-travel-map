"""Five Yong'an Temple halls on OSM footprints. Photo-informed, not survey geometry.
Official visual reference: https://s.visitbeijing.com.cn/gallery/22851 (photos 4/5).
No official photograph pixels used; decorative frieze is existing generated material.
"""
import bpy,json,math,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/assets/beihai-temples';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('beihai_temple_helpers',ROOT/'scripts/courtyard_architecture.py');C=importlib.util.module_from_spec(spec);sys.modules[spec.name]=C;spec.loader.exec_module(C);P=C.P
SPECS={561193502:('法轮殿',5,9.0,'hip'),478118169:('正觉殿',3,6.9,'gable'),478118172:('普安殿',5,8.8,'hip'),478118170:('圣果殿',3,6.2,'gable'),478118171:('宗镜殿',3,6.2,'gable')}
records=[r for r in json.loads((ROOT/'data/urban/records.json').read_text())['records']if r['osmId']in SPECS]
field=json.loads((ROOT/'public/assets/beihai-terrain/heightfield.json').read_text())
scene=bpy.data.scenes.get('Beihai Yong an Temples')or bpy.data.scenes.new('Beihai Yong an Temples');bpy.context.window.scene=scene
for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
colors={'stone':(.46,.44,.37),'red':(.32,.024,.015),'wall':(.30,.045,.031),'yellow':(.65,.34,.035),'green':(.025,.18,.095),'purple':(.06,.035,.095),'blue':(.012,.06,.16),'gold':(.46,.27,.045),'shade':(.016,.013,.012),'frieze':(.03,.10,.17)}
mats={k:P.mat('beihai hall '+k,v,.5 if k in ['yellow','green','purple']else .83,texture=ROOT/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else None)for k,v in colors.items()}
objs=[];entries=[]
for r in records:
 name,bays,H,roofkind=SPECS[r['osmId']];B=P.Builder(True);L,D,ang=C.dimensions(r)
 while ang>math.pi/2:ang-=math.pi
 while ang<-math.pi/2:ang+=math.pi
 hx,hy=L/2,D/2;floor=1.1;plinth=.65;walltop=H*.62;rb=walltop+.25;peak=H+floor
 bx,by=hx-.62,hy-.9
 B.box('stone',(0,0,floor+plinth/2),(L-.15,D-.15,plinth))
 B.box('wall',(0,0,(floor+plinth+walltop)/2),(bx*2,by*2,walltop-floor-plinth))
 for sign in [-1,1]:
  for j in range(5):B.box('stone',(0,sign*(hy+.10+j*.26),floor+plinth*(5-j)/10),(min(4,L*.35),.28,plinth*(5-j)/5))
  for i in range(bays+1):
   x=-bx+2*bx*i/bays;B.cylinder('red',.16,floor+plinth,walltop,12,center=(x,sign*(hy-.42)))
   B.cylinder('stone',.20,floor+plinth,floor+plinth+.18,12,center=(x,sign*(hy-.42)))
   for level in range(3):
    B.box('green'if level%2 else'blue',(x,sign*(hy-.42),walltop-.5+level*.21),(.3+level*.23,.46+level*.14,.16))
  # Recessed dark door interiors with distinct red frames and open lattice above.
  for i in range(bays):
   x=-bx+2*bx*(i+.5)/bays;w=2*bx/bays*.76;z0=floor+plinth+.07;z1=walltop-.75;y=sign*(by+.018)
   B.box('shade',(x,y,(z0+z1)/2),(w,.04,z1-z0))
   for sx in [-1,1]:B.box('red',(x+sx*w*.47,y+sign*.045,(z0+z1)/2),(w*.13,.09,z1-z0))
   B.box('red',(x,y+sign*.05,z1),(w,.12,.16));B.box('red',(x,y+sign*.05,z0+.15),(w,.1,.27))
   # Lattice panel either side of the central passage, with visible geometry.
   if i!=bays//2:
    for j in range(6):B.box('gold',(x-w*.37+j*w*.74/5,y+sign*.07,(z0+z1)/2+.3),(.026,.035,max(.1,z1-z0-.85)))
    for j in range(5):B.box('gold',(x,y+sign*.08,z0+.73+j*(z1-z0-.82)/4),(w*.78,.04,.035))
  y=sign*(hy-.40);pts=[(-bx,y,walltop-.65),(bx,y,walltop-.65),(bx,y,walltop+.12),(-bx,y,walltop+.12)]
  if sign>0:pts.reverse()
  B.face('frieze',pts,[(0,0),(bays,0),(bays,1),(0,1)])
 def prof(t):return rb+(peak-rb)*t**1.65+.1*math.exp(-t*24)
 def point(side,f,t):
  if side==0:p=(-hx+L*f,-hy)
  elif side==1:p=(hx,-hy+D*f)
  elif side==2:p=(hx-L*f,hy)
  else:p=(-hx,hy-D*f)
  end=(max(-hx+hy,min(hx-hy,p[0])),0)if roofkind=='hip'else(p[0],0)
  return(p[0]+(end[0]-p[0])*t,p[1]*(1-t),prof(t)+.22*abs(2*f-1)**10*(1-t)**3)
 sides=range(4)if roofkind=='hip'else[0,2]
 for side in sides:
  n=max(12,round((L if side%2==0 else D)/.25));steps=14
  for i in range(n):
   for j in range(steps):
    f,g=i/n,(i+1)/n;t,u=j/steps,(j+1)/steps
    # Simplified polychrome ceramic pattern; exact historic tile layout not claimed.
    band=(i//3+j//3)%7;key='green'if j<2 else'purple'if band==0 else'yellow'
    B.face(key,[point(side,f,t),point(side,g,t),point(side,g,u),point(side,f,u)])
    a=point(side,(i+.5)/n,t);b=point(side,(i+.5)/n,u)
    B.beam(key,tuple(a[k]+(.028 if k==2 else 0)for k in range(3)),tuple(b[k]+(.028 if k==2 else 0)for k in range(3)),.065,6)
  for i in range(n):
   p=point(side,(i+.5)/n,0);B.beam('green',p,(p[0],p[1],p[2]-.13),.11,8)
 if roofkind=='gable':
  for x in [-hx+.08,hx-.08]:
   B.face('wall',[(x,-hy,rb),(x,hy,rb),(x,0,peak)])
 ridge=hx-hy if roofkind=='hip'else hx
 B.box('yellow',(0,0,peak+.2),(max(.3,2*ridge),.25,.38))
 # Curved green crest over the yellow ridge, no exact dragon sculpture claim.
 for sign in [-1,1]:
  for j in range(16):
   x1=sign*ridge*j/16;x2=sign*ridge*(j+1)/16
   B.beam('green',(x1,-.14,peak+.34+.09*math.sin(j*.8)),(x2,-.14,peak+.34+.09*math.sin((j+1)*.8)),.05,6)
  B.beam('green',(sign*ridge,0,peak+.3),(sign*(ridge+.2),0,peak+.83),.13,8)
 if roofkind=='hip':
  B.cylinder('yellow',.22,peak+.4,peak+.7,12,.14);B.cylinder('blue',.13,peak+.7,peak+1,10,.06)
 # Project into actual map orientation, then use the level terrain pad.
 C.project(B,r,ang);pad=next(p for p in field['pads']if p['id']==r['id']);ground=floor/100+pad['height']
 for key,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new(name+' '+key);me.from_pydata([(x/100,y/100,z/100+pad['height'])for x,y,z in vs],[],fs);me.update();uv=me.uv_layers.new(name='Temple detail')
  for poly,coords in zip(me.polygons,uvs):
   for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
  me.materials.append(mats[key]);o=bpy.data.objects.new(name+' '+key,me);scene.collection.objects.link(o);o['layer']='buildings_urban_courtyard';o['osmId']=str(r['osmId']);o['groundHeight']=ground;o['islandLift']=True;o['templeReplacement']=True;objs.append(o)
 entries.append({'id':r['osmId'],'name':name,'rings':r['rings'],'bounds':r['bounds'],'heightMetresEstimated':H,'groundHeight':ground,'roofForm':roofkind,'bays':bays})
annexspec=importlib.util.spec_from_file_location('beihai_annexes',ROOT/'scripts/beihai_annex_architecture.py');annex=importlib.util.module_from_spec(annexspec);annexspec.loader.exec_module(annex)
annex_objects,annex_entries=annex.create(P,mats,scene,field,ROOT);objs.extend(annex_objects);entries.extend(annex_entries)
yuespec=importlib.util.spec_from_file_location('beihai_yuexin',ROOT/'scripts/beihai_yuexin_architecture.py');yue=importlib.util.module_from_spec(yuespec);yuespec.loader.exec_module(yue)
yue_objects,yue_entries=yue.create(P,C,scene,field,ROOT);objs.extend(yue_objects);entries.extend(yue_entries)
qingspec=importlib.util.spec_from_file_location('beihai_qingxiao',ROOT/'scripts/beihai_qingxiao_architecture.py');qing=importlib.util.module_from_spec(qingspec);qingspec.loader.exec_module(qing)
qing_objects,qing_entries=qing.create(P,C,scene,field,ROOT);objs.extend(qing_objects);entries.extend(qing_entries)
bpy.context.view_layer.update()
for o in scene.objects:o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
import io_scene_gltf2
fmt=next(x[0]for x in io_scene_gltf2.get_format_items(None,bpy.context)if x[0]=='GLB')
bpy.ops.export_scene.gltf(filepath=str(OUT/'temples.glb'),export_format=fmt,use_selection=True,use_active_scene=True,export_extras=True,export_image_format=next(i.identifier for i in bpy.ops.export_scene.gltf.get_rna_type().properties['export_image_format'].enum_items if i.identifier=='JPEG'),export_jpeg_quality=88,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
bpy.data.libraries.write(str(ROOT/'output/beihai-temples/永安寺_殿堂与附属房.blend'),{scene},fake_user=True)
raw=(OUT/'temples.glb').read_bytes();manifest={'url':'public/assets/beihai-temples/temples.glb','revision':hashlib.sha256(raw).hexdigest()[:12],'buildings':entries,'bytes':len(raw),'triangles':sum(len(p.vertices)-2 for o in objs for p in o.data.polygons),'source':'OSM footprints; Beijing Tourism / Beijing Park Management official reference photographs and architectural descriptions. Heights, tile motifs and unseen elevations inferred.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in manifest.items()if k!='buildings'},ensure_ascii=False))
