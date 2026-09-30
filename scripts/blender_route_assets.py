"""Imported and called inside the live Blender session through Blender MCP."""
import bpy
import json
import math
import bmesh
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/route-landmarks'
ASSETS = ROOT / 'public/assets/route-landmarks'
# Approximate representative scale; these are not surveyed dimensions.
SIZES = {'jingshan':('width',32),'beihai':('height',36),'gongwang':('width',42),
 'yonghe':('height',30),'guozijian':('width',36),'wudaoying':('width',110),
 'bell':('height',46),'drum':('height',46),'yandai':('width',95),
 'shichahai':('width',32),'ditan':('width',48),'zhongshan':('width',40),
 'national':('width',310),'wangfujing':('width',90),'guomao':('height',528),'cctv':('height',234)}

def reference_wangfujing(scene):
    """Photo-informed clock-tower street vignette; not the rejected fence output."""
    groups={}
    colors={'brick':(.45,.26,.14,1),'stone':(.61,.56,.43,1),'roof':(.13,.31,.23,1),'glass':(.13,.24,.29,1),'metal':(.12,.17,.16,1),'dial':(.91,.87,.68,1),'paving':(.46,.48,.45,1)}
    def shape(key,verts,faces):
        vs,fs=groups.setdefault(key,([],[]));n=len(vs);vs.extend(verts);fs.extend([tuple(n+i for i in face) for face in faces])
    def box(key,x,y,z,w,d,h):
        shape(key,[(x+sx*w/2,y+sy*d/2,z+sz*h/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    box('paving',.06,0,.005,.6,1.05,.01)
    for x,y,w,d,h in [(-.12,-.20,.24,.46,.20),(-.13,.30,.22,.29,.17),(.25,.23,.13,.32,.15)]:
        box('stone',x,y,h/2+.01,w,d,h);box('metal',x,y,h+.014,w+.018,d+.012,.012)
        for z in [.055,.10,.145,.185]:
            if z>h-.01:continue
            box('brick',x+w/2+.001,y,z-.014,.004,d,.006)
            for j in range(max(2,round(d/.032))):
                yy=y-d/2+.022+j*.032
                if yy>y+d/2-.015:break
                box('glass',x+w/2+.003,yy,z,.004,.022,.021)
            for xx in range(max(2,round(w/.032))):
                xx=x-w/2+.022+xx*.032
                if xx>x+w/2-.012:break
                box('glass',xx,y-d/2-.002,z,.022,.004,.021)
        for j in range(max(1,int(d/.08))):
            yy=y-d/2+.04+j*.08
            box('glass',x+w/2+.003,yy,.031,.004,.065,.035)
            box('roof',x+w/2+.014,yy,.05,.03,.066,.004)
    tx,ty=-.075,.065
    box('brick',tx,ty,.175,.105,.11,.33)
    for yy in [ty-.055,ty+.055]:box('stone',tx+.057,yy,.183,.018,.014,.344)
    for xx in [tx-.049,tx+.049]:box('stone',xx,ty-.06,.183,.014,.012,.344)
    for z in [.12,.165,.21,.25]:
        for yy in [ty-.026,ty+.026]:box('glass',tx+.055,yy,z,.004,.012,.025)
        for xx in [tx-.025,tx+.025]:box('glass',xx,ty-.058,z,.012,.004,.025)
    box('stone',tx,ty,.334,.124,.129,.012)
    corners=[(tx-.057,ty-.060,.34),(tx+.057,ty-.060,.34),(tx+.057,ty+.060,.34),(tx-.057,ty+.060,.34)]
    shape('roof',corners+[(tx,ty,.465)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)])
    for axis in ['x','y']:
        verts=[]
        for j in range(64):
            a=j*math.tau/64
            verts.append((tx+.058,ty+math.cos(a)*.034,.292+math.sin(a)*.034) if axis=='x' else (tx+math.cos(a)*.034,ty-.061,.292+math.sin(a)*.034))
        shape('dial',verts,[tuple(range(64))])
        if axis=='x':
            box('metal',tx+.059,ty,.303,.002,.0025,.026);box('metal',tx+.059,ty+.01,.292,.002,.023,.003)
        else:
            box('metal',tx,ty-.062,.303,.0025,.002,.026);box('metal',tx+.01,ty-.062,.292,.023,.002,.003)
    for y in [-.38,-.17,.18,.39]:
        box('metal',.10,y,.042,.003,.003,.077);box('stone',.10,y,.083,.019,.019,.004)
    meshes=[]
    for key,(verts,faces) in groups.items():
        material=bpy.data.materials.new('Wangfujing reference '+key);material.use_nodes=True
        bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=colors[key];bsdf.inputs['Roughness'].default_value=.3 if key=='glass' else .8
        mesh=bpy.data.meshes.new('Wangfujing '+key);mesh.from_pydata(verts,[],faces);mesh.materials.append(material)
        obj=bpy.data.objects.new('Wangfujing '+key,mesh);scene.collection.objects.link(obj);meshes.append(obj)
    return meshes

def activate():
    scene = bpy.data.scenes.get('Beijing Photo Landmarks')
    if scene is None:
        scene = bpy.data.scenes.new('Beijing Photo Landmarks')
        scene.world = bpy.data.worlds.new('Landmark Studio World')
        scene.world.use_nodes = True
        background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
        background.inputs['Color'].default_value = (.74,.79,.76,1)
        background.inputs['Strength'].default_value = .45
        scene.render.resolution_x=1200; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG'
        scene.render.image_settings.color_mode='RGB'
        scene.render.film_transparent=False
        camera=bpy.data.objects.new('Landmark Studio Camera',bpy.data.cameras.new('Landmark Camera'))
        camera.data.type='ORTHO';camera.data.clip_start=.0001;camera.data.clip_end=1000
        scene.collection.objects.link(camera);scene.camera=camera
        light=bpy.data.objects.new('Landmark Studio Sun',bpy.data.lights.new('Landmark Sun','SUN'))
        light.data.energy=2.3;light.data.angle=.15;light.rotation_euler=(.45,-.55,-.45)
        scene.collection.objects.link(light)
        mesh=bpy.data.meshes.new('Studio Floor');mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[],[(0,1,2,3)])
        ground=bpy.data.objects.new('Landmark Studio Floor',mesh);scene.collection.objects.link(ground)
        material=bpy.data.materials.new('Warm neutral studio');material.use_nodes=True
        bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value=(.65,.70,.66,1);bsdf.inputs['Roughness'].default_value=.9
        mesh.materials.append(material)
    bpy.context.window.scene=scene
    return scene

def bounds(meshes):
    points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    return Vector([min(p[i] for p in points) for i in range(3)]),Vector([max(p[i] for p in points) for i in range(3)])

def clean_bridge(meshes, scene):
    # The photograph includes a crowd. Retain the generated arch masonry and
    # replace the contaminated upper deck with clean stone paving and rails.
    for obj in meshes:
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z>.136],context='VERTS')
        bm.to_mesh(obj.data);bm.free();obj.data.update()
    material=bpy.data.materials.new('Silver Ingot Bridge clean limestone');material.use_nodes=True
    bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value=(.55,.56,.51,1);bsdf.inputs['Roughness'].default_value=.86
    vertices=[];faces=[]
    def block(cx,cy,z,sx,sy,sz):
        start=len(vertices)
        vertices.extend([(cx+dx*sx/2,cy+dy*sy/2,z+dz*sz/2) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
        faces.extend([tuple(start+i for i in face) for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
    for j in range(20):
        y=-.15+(j+.5)*.3/20;top=.14+.006*math.cos(y/.15*math.pi/2)
        block(0,y,top-.007,.21,.0152,.014)
        for x in [-.099,.099]:block(x,y,top+.025,.011,.0152,.006)
        if j%2==0:
            for x in [-.099,.099]:block(x,y,top+.015,.012,.012,.03)
    data=bpy.data.meshes.new('Restored bridge paving and balustrade');data.from_pydata(vertices,[],faces);data.materials.append(material)
    obj=bpy.data.objects.new('shichahai/clean-deck',data);obj['tourism_asset']='shichahai';scene.collection.objects.link(obj);meshes.append(obj)

def prepare(pid):
    result=json.loads((OUT/(pid+'-result.json')).read_text())
    assert result.get('status')=='success', result
    dest=ASSETS/pid;dest.mkdir(exist_ok=True)
    scene=activate()
    for old in list(scene.objects):
        if old.get('tourism_asset')==pid:bpy.data.objects.remove(old,do_unlink=True)
    existing=set(bpy.data.objects)
    if pid=='wangfujing':
        meshes=reference_wangfujing(scene);imported=set(meshes)
    else:
        bpy.ops.import_scene.gltf(filepath=str(ROOT/result['model_file']))
        imported=set(bpy.data.objects)-existing
        meshes=[o for o in imported if o.type=='MESH']
    assert meshes, 'No meshes imported'
    low,high=bounds(meshes);size=high-low
    mode,metres=SIZES[pid]
    scale=metres/100/(size.z if mode=='height' else max(size.x,size.y))
    center=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    normalize=Matrix.Scale(scale,4)@Matrix.Translation(-center)
    transforms={o:normalize@o.matrix_world for o in meshes}
    for o in meshes:
        o.parent=None;o.data=o.data.copy();o.data.transform(transforms[o]);o.matrix_world=Matrix.Identity(4)
        o.name=pid+'/'+o.name;o['tourism_asset']=pid
    for o in imported:
        if o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
    if pid=='guomao':
        upper=[v.co for obj in meshes for v in obj.data.vertices if v.co.z>3.6]
        xmin=min(v.x for v in upper)-.12;xmax=max(v.x for v in upper)+.12
        ymin=min(v.y for v in upper)-.12;ymax=max(v.y for v in upper)+.12
        for obj in meshes:
            bm=bmesh.new();bm.from_mesh(obj.data)
            bmesh.ops.delete(bm,geom=[v for v in bm.verts if not(xmin<=v.co.x<=xmax and ymin<=v.co.y<=ymax)],context='VERTS')
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,1.25),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
            bm.to_mesh(obj.data);bm.free();obj.data.update()
        low,high=bounds(meshes);offset=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
        for obj in meshes:obj.data.transform(Matrix.Scale(5.28/(high.z-low.z),4)@Matrix.Translation(-offset))
    if pid=='shichahai':clean_bridge(meshes,scene)
    materials={m for o in meshes for m in o.data.materials if m}
    textures={n.image for m in materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    for image in textures:
        w,h=image.size
        if max(w,h)>2048:image.scale(round(w*2048/max(w,h)),round(h*2048/max(w,h)))
    for o in scene.objects:o.select_set(False)
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(dest/'detail.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_image_format='JPEG',export_jpeg_quality=88,export_apply=True)
    export_preview(meshes,materials,textures,dest)
    low,high=bounds(meshes)
    report={'id':pid,'bounds':[list(low),list(high)],'triangles':sum(len(o.data.loop_triangles) for o in meshes),'meshes':len(meshes),'detailBytes':(dest/'detail.glb').stat().st_size,'previewBytes':(dest/'preview.glb').stat().st_size,'scaleEstimate':{'mode':mode,'metres':metres}}
    (OUT/(pid+'-blender.json')).write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    frame(pid)
    return report

def frame(pid):
    scene=activate()
    meshes=[o for o in scene.objects if o.get('tourism_asset')==pid]
    assert meshes
    for o in scene.objects:
        if o.get('tourism_asset'):o.hide_render=o.get('tourism_asset')!=pid;o.hide_set(o.get('tourism_asset')!=pid)
    low,high=bounds(meshes);span=max(high-low);target=(low+high)/2
    cam=scene.camera;cam.location=target+Vector((3,0,1.25) if pid in ['wudaoying','yandai'] else (1.6,-2.6,1.4))*span
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=span*1.6
    floor=scene.objects['Landmark Studio Floor'];floor.scale=(span*200,span*200,1);floor.location.z=-.008
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=span*2.5
            area.spaces.active.region_3d.view_location=target
            area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
    scene.render.filepath=str(OUT/(pid+'-blender.png'))

def render(pid):
    frame(pid);bpy.ops.render.render(write_still=True)
    print('rendered',pid)

def save():
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'北京旅游地标_实景参考.blend'))

def export_preview(meshes,materials,textures,dest):
    # Keep the full-resolution source materials in the editable scene.
    texture_copies={}
    for image in textures:
        copy=image.copy();w,h=copy.size
        if max(w,h)>256:copy.scale(round(w*256/max(w,h)),round(h*256/max(w,h)))
        texture_copies[image]=copy
    for m in materials:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image in texture_copies:n.image=texture_copies[n.image]
    modifiers=[]
    total=sum(len(o.data.polygons) for o in meshes)
    for o in meshes:
        modifier=o.modifiers.new('Tourism overview LOD','DECIMATE');modifier.ratio=min(1,2400/max(total,1));modifiers.append((o,modifier))
    bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get()
    originals=[]
    for o,modifier in modifiers:
        baked=bpy.data.meshes.new_from_object(o.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
        originals.append((o,o.data,baked));o.modifiers.remove(modifier);o.data=baked
    bottom=min(o.data.vertices[i].co.z for o in meshes for poly in o.data.polygons for i in poly.vertices)
    for o in meshes:o.data.transform(Matrix.Translation((0,0,-bottom)))
    bpy.ops.export_scene.gltf(filepath=str(dest/'preview.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_image_format='JPEG',export_jpeg_quality=78,export_apply=True)
    for o,original,baked in originals:o.data=original;bpy.data.meshes.remove(baked)
    reverse={v:k for k,v in texture_copies.items()}
    for m in materials:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image in reverse:n.image=reverse[n.image]
    for image in texture_copies.values():bpy.data.images.remove(image)

def refresh_preview(pid):
    frame(pid);scene=bpy.context.scene
    meshes=[o for o in scene.objects if o.get('tourism_asset')==pid]
    for o in scene.objects:o.select_set(False)
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    materials={m for o in meshes for m in o.data.materials if m}
    textures={n.image for m in materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    export_preview(meshes,materials,textures,ASSETS/pid)
    path=OUT/(pid+'-blender.json');report=json.loads(path.read_text());report['previewBytes']=(ASSETS/pid/'preview.glb').stat().st_size;path.write_text(json.dumps(report,indent=2))
    print('preview grounded',pid)
