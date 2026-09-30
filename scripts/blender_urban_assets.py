"""Build OSM district architecture inside the live Blender MCP session.
Shells follow footprints and tagged heights. Cornices are illustrative, not surveyed.
"""
import bpy, json, math, re, hashlib, importlib.util, sys
from pathlib import Path
from mathutils import Vector, Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from urban_facades import facade_layout,face_uv
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/assets/urban'
spec=importlib.util.spec_from_file_location('courtyard_architecture',ROOT/'scripts/courtyard_architecture.py')
courtyard=importlib.util.module_from_spec(spec);sys.modules[spec.name]=courtyard;spec.loader.exec_module(courtyard)

def material(name,color):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.86
    return m

def add(group,key,face):
    vs,fs=group.setdefault(key,([],[]));start=len(vs);vs.extend(face);fs.append(tuple(range(start,start+len(face))))

def mesh(scene,name,verts,faces,mat,layer,uv=False,face_uvs=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    if uv:
        coords=me.uv_layers.new(name='Facade')
        for poly in me.polygons:
            p0=me.vertices[poly.vertices[0]].co;p1=me.vertices[poly.vertices[1]].co
            dx,dy=p1.x-p0.x,p1.y-p0.y;length=max(math.hypot(dx,dy),1e-6)
            for li in poly.loop_indices:
                p=me.vertices[me.loops[li].vertex_index].co
                coords.data[li].uv=face_uvs[poly.index][list(poly.loop_indices).index(li)] if face_uvs else (((p.x-p0.x)*dx+(p.y-p0.y)*dy)/length/.034,(p.z-.011)/.032)
    me.materials.append(mat);o=bpy.data.objects.new(name,me);scene.collection.objects.link(o)
    o['layer']=layer;o['groundHeight']=.011;return o

def export(objects,path):
    bpy.context.view_layer.update()
    for o in bpy.context.view_layer.objects:o.select_set(False)
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    formats=[x.identifier for x in bpy.ops.export_scene.gltf.get_rna_type().properties['export_format'].enum_items]
    if not formats:
        import io_scene_gltf2
        formats=[x[0] for x in io_scene_gltf2.get_format_items(None,bpy.context)]
    binary=next(x for x in formats if x.upper()=='GLB')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format=binary,use_selection=True,use_active_scene=True,export_extras=True,export_yup=True,export_cameras=False,export_lights=False)

def build_shell():
    global scene,records,tiles,mats,shell_objects,manifest,raw_tags
    blob=json.loads((ROOT/'data/urban/records.json').read_text());records=blob['records']
    scene=bpy.data.scenes.get('Beijing Urban Architecture') or bpy.data.scenes.new('Beijing Urban Architecture');bpy.context.window.scene=scene
    for obj in list(scene.objects):
        if str(obj.get('layer','')).startswith('buildings_urban'):
            data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
            if data.users==0:bpy.data.meshes.remove(data)
    scene.world=bpy.data.worlds.new('Urban Daylight');scene.world.use_nodes=True
    next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Color'].default_value=(.7,.8,1,1)
    mats={k:material('Urban '+k,c)for k,c in {'walls':(.63,.62,.56),'boundary_red':(.39,.075,.055),'boundary_gray':(.25,.25,.22),'heritage':(.34,.18,.12),'gray':(.16,.19,.20),'red':(.29,.13,.08),'blue':(.09,.22,.26),'green':(.12,.24,.18),'trim':(.62,.61,.53)}.items()}
    tiles={};shell_objects=[]
    for r in records:
        x,y=r['center'];key=f'{math.floor(x/10)}_{math.floor(y/10)}';tiles.setdefault(key,[]).append(r)
    # Cluster the always-visible shells in 2 km groups for frustum culling.
    groups={};facade_uvs={};profiles={};profile_counts={};floor_sources={}
    raw_tags={e['id']:e.get('tags',{})for e in json.loads((ROOT/'data/osm_beijing.json').read_text())['elements']}
    for r in records:
        if r['osmId'] in courtyard.IDS:continue
        x,y=r['center'];key=f'{math.floor(x/20)}_{math.floor(y/20)}';g=groups.setdefault(key,{})
        finish=r.get('wallFinish',{});wallkind='heritage' if finish.get('solid',r.get('heritage')) else 'walls'
        raw=finish.get('color','').lower();aliases={'firebrick':'b22222','indianred':'cd5c5c','grey':'808080','lightgrey':'d3d3d3','white':'ffffff','lightcoral':'f08080'};raw=aliases.get(raw,raw.lstrip('#'))
        if re.fullmatch('[0-9a-f]{6}',raw):
            wallkind=('solid_'if finish.get('solid')else'facade_')+raw
            if wallkind not in mats:
                rgb=[int(raw[i:i+2],16)/255 for i in [0,2,4]];linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb];mats[wallkind]=material('Urban '+wallkind,linear)
        textured=wallkind=='walls' or wallkind.startswith('facade_')
        if textured:
            layout=facade_layout(r,raw_tags.get(r['osmId'],{}));basekind=wallkind;wallkind+='__'+layout['style'];profiles[wallkind]=layout['style'];mats[wallkind]=mats[basekind]
            profile_counts[layout['style']]=profile_counts.get(layout['style'],0)+1;floor_sources[layout['floorSource']]=floor_sources.get(layout['floorSource'],0)+1
        for face in r['walls']:
            add(g,wallkind,face)
            if textured:facade_uvs.setdefault((key,wallkind),[]).append(face_uv(face,r,layout))
        for face in r.get('bottom',[]):
            add(g,wallkind,face)
            if textured:facade_uvs.setdefault((key,wallkind),[]).append([(0,0)]*len(face))
        color=r['roofColor'].lower()
        if color=='grey':color='gray'
        aliases={'lightgrey':'b3b3b3','orange':'d79135','white':'c5c3b8','black':'353b40'}
        raw=aliases.get(color,color.lstrip('#'))
        if re.fullmatch('[0-9a-f]{6}',raw):
            color='roof_'+raw
            if color not in mats:
                rgb=[int(raw[i:i+2],16)/255 for i in [0,2,4]]
                linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
                mats[color]=material('Urban '+color,linear)
        if color not in mats:color='gray'
        for face in r['roof']:
            a,b,c=face
            if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:face=list(reversed(face))
            add(g,color,face)
    for key,g in groups.items():
        for kind,(vs,fs)in g.items():
            layer='buildings_urban_walls'if kind.startswith('walls__')else'buildings_urban_tagged_facade'if kind.startswith('facade_')else'buildings_urban_heritage'if kind=='heritage'or kind.startswith('solid_')else'buildings_urban_roofs'
            obj=mesh(scene,f'Urban {key} {kind}',vs,fs,mats[kind],layer,kind in profiles,facade_uvs.get((key,kind)))
            if kind in profiles:obj['facadeProfile']=profiles[kind]
            shell_objects.append(obj)
    shell_objects+=courtyard.create(scene,records)
    for paving in blob.get('courtyardPaving',[]):
        g={}
        for tri in paving['triangles']:
            a,b,c=tri
            if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:tri=list(reversed(tri))
            add(g,'paving',[(x,y,.0108)for x,y in tri])
        obj=mesh(scene,'Urban courtyard paving',*g['paving'],courtyard.P.mat('courtyard paving',(.55,.53,.48),.98,texture=ROOT/'public/assets/palace/marble.png'),'buildings_urban_paving')
        uv=obj.data.uv_layers.new(name='Paving')
        for poly in obj.data.polygons:
            for li in poly.loop_indices:
                co=obj.data.vertices[obj.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x/.04,co.y/.04)
        shell_objects.append(obj)
    export(shell_objects,OUT/'city-shell.glb')
    manifest={'shell':'public/assets/urban/city-shell.glb','stats':blob['stats'],'source':blob['source'],'floor':.011,'tiles':[]}
    manifest['boundaryWallMaterialCorrection']={'count':16,'source':'OSM building=wall; solid walls instead of generic window facade','heightUnchanged':True}
    manifest['facades']={'profiles':profile_counts,'floorSources':floor_sources,'method':'OSM building classes and explicit storey counts; facade bays and fenestration are illustrative. Unknown buildings keep generic style.'}
    manifest['reconstructions']=[{'osmId':r['osmId'],'name':r['name'],'bounds':r['bounds'],'method':'OSM footprint + photo-informed architectural form; heights, ornaments and painted texture inferred','source':'https://www.tiantanpark.cn/scenic_spot_list_g7yU_96/detail/1182.html'} for r in records if r['osmId'] in courtyard.IDS]
    manifest['pavedCourtyards']=[{'osmId':p['osmId'],'bounds':p['bounds']}for p in blob.get('courtyardPaving',[])]
    print(json.dumps({'shellObjects':len(shell_objects),'buildings':len(records),'tiles':len(tiles),'bytes':(OUT/'city-shell.glb').stat().st_size}))

def beam(g,a,b,z1,z2,width,depth):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    if length<.005:return
    nx,ny=-dy/length*width/2,dx/length*width/2
    v=[(a[0]-nx,a[1]-ny,z1-depth/2),(b[0]-nx,b[1]-ny,z2-depth/2),(b[0]+nx,b[1]+ny,z2-depth/2),(a[0]+nx,a[1]+ny,z1-depth/2),(a[0]-nx,a[1]-ny,z1+depth/2),(b[0]-nx,b[1]-ny,z2+depth/2),(b[0]+nx,b[1]+ny,z2+depth/2),(a[0]+nx,a[1]+ny,z1+depth/2)]
    for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:add(g,'trim',[v[i]for i in ids])

def build_details(start=0,count=20):
    specs=json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())['assets']
    masks=[s['bounds']for s in specs if not (s.get('maskPolygon') or s.get('maskPolygons'))]
    polygon_ids={id for s in specs if s.get('maskPolygon') or s.get('maskPolygons') for id in s.get('sourceOsmIds',([s['osmId']] if s.get('osmId') else []))}
    masks.append([-28.1,-13.9,-25.5,-12.0]) # NCPA dome
    for key in list(tiles)[start:start+count]:
        batch=tiles[key];g={};bounds=[1e9,1e9,-1e9,-1e9];included=0
        for r in batch:
            x0,y0,x1,y1=r['bounds']
            if r['osmId'] in polygon_ids:continue
            if any(x1>b[0]and x0<b[2]and y1>b[1]and y0<b[3]for b in masks):continue
            included+=1;bounds=[min(bounds[0],x0),min(bounds[1],y0),max(bounds[2],x1),max(bounds[3],y1)]
            if r['osmId'] in courtyard.IDS or r.get('wallFinish',{}).get('solid'):continue
            for wall in r['walls']:
                a,b=wall[-1],wall[-2]
                # A real silhouette with a shallow parapet / eave profile.
                beam(g,a,b,a[2]+.001,b[2]+.001,.0035,.003)
                # Limited floor bands for modern blocks, not invented rooftop props.
                if r['roofShape']=='flat'and r['height']>.1:
                    layout=facade_layout(r,raw_tags.get(r['osmId'],{}))
                    for level in range(2,min(24,layout['floors']),2):
                        z=.011+r.get('minHeight',0)+level*layout['floorHeight']
                        if .011+r.get('minHeight',0)<z<r['eaves']-.025:beam(g,a,b,z,z,.002,.0015)
        objects=courtyard.create(scene,batch,detail=True)
        if g:objects.append(mesh(scene,'Urban detail '+key, *g['trim'],mats['trim'],'buildings_urban_detail'))
        if not objects:continue
        export(objects,OUT/f'detail-{key}.glb')
        manifest['tiles'].append({'id':key,'url':f'public/assets/urban/detail-{key}.glb','bounds':bounds,'height':max(r['height']for r in batch),'buildings':included,'bytes':(OUT/f'detail-{key}.glb').stat().st_size})
        for o in objects:
            data=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(data)
    manifest['revision']=hashlib.sha256((ROOT/'scripts/blender_urban_assets.py').read_bytes()+(ROOT/'scripts/courtyard_architecture.py').read_bytes()+(ROOT/'scripts/urban_facades.py').read_bytes()+(ROOT/'data/urban/records.json').read_bytes()).hexdigest()[:12]
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')))
    print(json.dumps({'detailsExported':len(manifest['tiles']),'detailBytes':sum(t['bytes']for t in manifest['tiles'])}))

def save():
    # Preserve the complete existing landmark scenes in this new copy.
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output/urban/北京城区_建筑屋顶.blend'))
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_location=Vector((-14,10,.1))
            area.spaces.active.region_3d.view_distance=9
            area.spaces.active.region_3d.view_rotation=Quaternion((.86,.5,.05,.025)).normalized()
    print('Saved urban scene and preserved previous landmark scenes')
