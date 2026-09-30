import bpy, math, json, pathlib, sys, random
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/geometry.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for block in bpy.data.materials:bpy.data.materials.remove(block)

def mat(name,color,roughness=.75,metallic=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=roughness;bs.inputs['Metallic'].default_value=metallic
    return m
materials={
 'building':mat('Porcelain | 浅灰建筑',(.68,.71,.71)),
 'road':mat('Graphite | 深灰路网',(.18,.225,.24)),
 'path':mat('Footpaths | 园路',(.65,.70,.67)),
 'park':mat('Sage | 公园绿地',(.31,.48,.35)),
 'tree':mat('Canopy | 树冠',(.20,.38,.27)),
 'trunk':mat('Trunk',(.28,.31,.24)),
 'water':mat('Blue | 湖泊水域',(.23,.49,.61),.25,.12),
 'palace_wall':mat('Palace | 宫墙',(.57,.38,.31)),
 'roof':mat('Roof | 淡金重檐',(.67,.53,.30),.64),
 'stone':mat('Stone | 汉白玉',(.83,.85,.81)),
 'glass':mat('Silver | 地标金属',(.42,.53,.56),.32,.3),
 'grid':mat('Structure | 斜交网格',(.22,.32,.35),.5,.22),
 'blue_roof':mat('Temple | 琉璃蓝',(.16,.32,.40)),
 'terrain':mat('Terrain | 城市平原',(.77,.79,.76)),
 'edge':mat('Edge | 地图底座',(.60,.66,.65)),
 'floor':mat('Studio | 背景',(.83,.86,.86)),
}

def mesh(name,vs,fs,material,layer=None):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(materials[material]);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    ob['layer']=layer or name;return ob
for m in data['layers']:
    if not m['vertices']:continue
    ob=mesh(m['name'],m['vertices'],m['faces'],m['material'])
    if m['name'].startswith(('roads','paths')):ob.visible_shadow=False
def box(name,loc,size,material,layer='landmarks',bevel=0):
    x,y,z=loc;a,b,c=[s/2 for s in size]
    vs=[(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    ob=mesh(name,vs,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],material,layer)
    if bevel:
        mod=ob.modifiers.new('Soft edge','BEVEL');mod.width=bevel;mod.segments=3
        mod=ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return ob
def roof(name,x,y,z,w,d,r,material='roof',layer='landmarks'):
    vs=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),(x-w*.32,y,z+r),(x+w*.32,y,z+r)]
    return mesh(name,vs,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(3,2,1,0)],material,layer)
def ringbody(name,x,y,levels,material,n=32,layer='landmarks'):
    vs=[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),z) for z,r in levels for i in range(n)]
    fs=[]
    for j in range(len(levels)-1):
        for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    fs.append(tuple(range(n-1,-1,-1)));fs.append(tuple((len(levels)-1)*n+i for i in range(n)))
    return mesh(name,vs,fs,material,layer)
def beam(name,a,b,width,material='grid',layer='landmarks'):
    a,b=Vector(a),Vector(b);vec=b-a
    ob=box(name,(a+b)/2,(width,width,vec.length),material,layer)
    center=(a+b)/2
    for v in ob.data.vertices:v.co-=center
    ob.location=center;ob.rotation_euler=vec.to_track_quat('Z','Y').to_euler();return ob

W,H=data['width'],data['height']
box('atlas_plinth',(0,0,-.81),(W+.4,H+.4,1.6),'edge','base',.32)
box('city_plain',(0,0,-.115),(W,H,.23),'terrain','terrain',.12)
# Very shallow planar triangles describe Beijing's flat basin; no invented mountains.
random.seed(8)
vs=[];fs=[];NX,NY=32,30
for j in range(NY+1):
    for i in range(NX+1):vs.append((-W/2+i*W/NX,-H/2+j*H/NY,random.uniform(.001,.008)))
for j in range(NY):
    for i in range(NX):
        k=j*(NX+1)+i;fs.extend([(k,k+1,k+NX+2),(k,k+NX+2,k+NX+1)])
mesh('low_poly_plain',vs,fs,'terrain','terrain')

lm={l['id']:l for l in data['landmarks']}
# Tian'anmen, a stylized gate with five true open arch bays.
l=lm['tiananmen'];x,y=l['x'],l['y'];ly='landmark_tiananmen'
box('Gate terrace',(x,y,.10),(1.0,.47,.09),'stone',ly)
for a,b in [(-.48,-.37),(-.29,-.23),(-.15,-.07),(.07,.15),(.23,.29),(.37,.48)]:box('Gate pier',(x+(a+b)/2,y,.17),(b-a,.36,.18),'palace_wall',ly)
box('Gate lintel',(x,y,.273),(.96,.36,.065),'palace_wall',ly)
box('Upper hall',(x,y,.326),(.66,.25,.10),'palace_wall',ly)
roof('First eaves',x,y,.335,.86,.38,.062,layer=ly)
box('Upper gallery',(x,y,.389),(.58,.20,.057),'palace_wall',ly)
roof('Upper eaves',x,y,.419,.74,.32,.074,layer=ly)
for i in range(11):
    xx=x-.29+i*.058
    box('Gallery column',(xx,y-.137,.326),(.012,.012,.08),'stone',ly)

# CCTV: inclined towers, elbow-shaped cantilever and diagonal facade structure.
l=lm['cctv'];x,y=l['x'],l['y'];ly='landmark_cctv'
box('CCTV podium',(x,y,.115),(1.92,1.56,.15),'stone',ly,.02)
def slant(name,base,top,w,d,z):
    a,b=base;c,e=top
    vs=[(x+a+dx*w/2,y+b+dy*d/2,.15) for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]]+[(x+c+dx*w/2,y+e+dy*d/2,z) for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    mesh(name,vs,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'glass',ly)
    for side in range(4):
        p0,p1,p2,p3=[Vector(vs[k]) for k in [side,(side+1)%4,4+(side+1)%4,4+side]]
        for row in range(10):
            for col in range(3):
                def p(u,v):return p0.lerp(p1,u).lerp(p3.lerp(p2,u),v)
                aa=p(col/3,row/10);bb=p((col+1)/3,(row+1)/10)
                cc=p((col+1)/3,row/10);dd=p(col/3,(row+1)/10)
                beam('CCTV diagonal',aa,bb,.009,'grid',ly);beam('CCTV diagonal',cc,dd,.009,'grid',ly)
    return vs
slant('CCTV west tower',(-.63,-.46),(-.30,-.19),.49,.56,2.49)
slant('CCTV east tower',(.57,.45),(.28,.13),.52,.56,2.23)
box('CCTV overhang',(x+.04,y-.19,2.28),(1.17,.56,.42),'glass',ly)
box('CCTV elbow',(x+.38,y+.055,2.105),(.52,.62,.25),'glass',ly)
for i in range(10):
    xx=x-.52+i*.113
    beam('Overhang diagonal',(xx,y-.477,2.075),(xx+.113,y-.477,2.485),.012,'grid',ly)

# Hall of Prayer for Good Harvests: three circular blue eaves and marble podiums.
l=lm['tiantan'];x,y=l['x'],l['y'];ly='landmark_tiantan'
for z,r in [(.06,.47),(.10,.39),(.14,.31)]:ringbody('Marble terrace',x,y,[(z,r),(z+.035,r)],'stone',48,ly)
ringbody('Prayer hall',x,y,[(.175,.17),(.37,.17)],'palace_wall',32,ly)
for z,r in [(.25,.245),(.33,.207),(.415,.165)]:ringbody('Blue glazed eave',x,y,[(z,r),(z+.027,r*.96),(z+.087,r*.39)],'blue_roof',48,ly)
ringbody('Golden finial',x,y,[(.50,.021),(.535,.025),(.55,0)],'roof',16,ly)

# China Zun silhouette, based on a concave taper; individual facade strips.
l=lm['guomao'];x,y=l['x'],l['y'];ly='landmark_guomao'
levels=[(.08,.36),(.6,.34),(1.8,.27),(2.8,.255),(3.8,.29),(4.8,.35),(5.36,.39)]
vs=[]
for z,r in levels:
    for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:vs.append((x+dx*r,y+dy*r,z))
fs=[]
for j in range(len(levels)-1):
    for i in range(4):fs.append((j*4+i,j*4+(i+1)%4,(j+1)*4+(i+1)%4,(j+1)*4+i))
fs.append((24,25,26,27));mesh('China Zun',vs,fs,'glass',ly)
for side in range(4):
    for c in range(9):
        for j in range(len(levels)-1):
            aa=Vector(vs[j*4+side]).lerp(Vector(vs[j*4+(side+1)%4]),c/8)
            bb=Vector(vs[(j+1)*4+side]).lerp(Vector(vs[(j+1)*4+(side+1)%4]),c/8)
            beam('Zun fins',aa,bb,.008,'stone',ly)

# Beihai white stupa.
x=(116.38315-116.415)*111320*math.cos(math.radians(39.915))/100;y=(39.9246-39.915)*111320/100;ly='landmark_beihai'
ringbody('White dagoba',x,y,[(.08,.13),(.13,.13),(.18,.09),(.26,.11),(.34,.07),(.46,.025),(.49,0)],'stone',24,ly)

# Merge authored pieces by landmark and material, keeping layers independently editable.
groups={}
for ob in list(bpy.context.scene.objects):
    if ob.type=='MESH' and ob.get('layer','').startswith('landmark_'):
        groups.setdefault((ob['layer'],ob.data.materials[0].name),[]).append(ob)
for (layer,material),obs in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.object.join();ob=bpy.context.object;ob.name=layer+'_'+material.split(' | ')[0];ob['layer']=layer
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

# Export unexaggerated metric geometry; apply the same 2.6× vertical emphasis for rendering.
out=ROOT/'public/assets/beijing.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_extras=True,export_yup=True,export_apply=True)
for ob in bpy.context.scene.objects:
    layer=ob.get('layer','')
    if layer.startswith(('building','palace','landmark')):ob.scale.z=2.6

box('studio_floor',(0,0,-2.05),(2000,2000,.4),'floor','studio')
world=bpy.data.worlds.new('Soft daylight');bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.77,.84,.91,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.48
def area(name,location,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(-65,-35,110),160000,75,(1,.96,.88))
d=bpy.data.lights.new('Daylight sun','SUN');d.energy=2.3;d.angle=math.radians(12)
o=bpy.data.objects.new('Daylight sun',d);bpy.context.collection.objects.link(o);o.rotation_euler=(math.radians(26),math.radians(-28),math.radians(-28))
camd=bpy.data.cameras.new('Atlas orthographic');cam=bpy.data.objects.new('Atlas orthographic',camd);bpy.context.collection.objects.link(cam)
cam.location=(100,-146,146);target=Vector((0,0,1.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=217;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.denoising_use_gpu=False;scene.cycles.adaptive_threshold=.04;scene.cycles.max_bounces=5
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='CPU'
except Exception as e:print('GPU fallback:',e)
scene.render.resolution_x=7680;scene.render.resolution_y=4320;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.3
scene.render.filepath=str(ROOT/'output/北京城市地图_8K.png')
(ROOT/'output').mkdir(exist_ok=True)
scene['Data attribution']='© OpenStreetMap contributors, ODbL 1.0';scene['Geometry notes']='Real OSM roads/footprints; missing heights estimated; stylized landmarks; vertical scale 2.6; flat terrain, not surveyed DEM.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'北京城市地图.blend'))
scene.render.resolution_percentage=25;scene.cycles.samples=16;scene.render.filepath=str(ROOT/'output/北京城市地图_预览.png')
bpy.ops.render.render(write_still=True)
print('BUILD_AND_PREVIEW_DONE',flush=True)
