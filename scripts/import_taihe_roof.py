"""Align TRNKL's CC BY 4.0 Taihe upper roof without nonuniform stretching.
Run Blender --background --disable-autoexec --python scripts/import_taihe_roof.py.
Original download is untouched. Derived outputs are staged outside public/.
"""
import bpy,json,math,hashlib,os,struct,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.dream-loop/sketchfab/converted';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path.home()/'Downloads/c354afbc1a4f428d80a26f5904d27fe6.glb'
CACHE=ROOT/'.dream-loop/sketchfab/source-imported.blend'
def retain_source_credit(path):
 with open(SOURCE,'rb') as f:
  f.read(12);n,_=struct.unpack('<II',f.read(8));source_asset=json.loads(f.read(n))['asset']
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n])
 doc['asset']['extras']=dict(source_asset.get('extras',{}))
 doc['asset']['extras']['modifications']='Aligned by uniform scale and yaw; resized JPEG textures; Draco compression; preview geometry simplified.'
 body=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();body+=b' '*((-len(body))%4)
 tail=raw[20+n:];path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(body)+len(tail))+struct.pack('<II',len(body),0x4e4f534a)+body+tail)

frame=json.load(open(ROOT/'.dream-loop/sketchfab/integration-audit.json'))['upperRoofReplacementFrame']
if CACHE.exists():
 bpy.ops.wm.open_mainfile(filepath=str(CACHE))
else:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(SOURCE))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
# Obtain actual world vertices of drip tiles. Their top edge is a defensible eave contact
# datum, unlike the lower decorative animal heads included in the global bounding box.
eaves=[]
for o in objects:
 if o.name.startswith('DS_geo_lambert_DS_0') and not o.name.startswith('DS_geo_lambert_DS_00'):
  a=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',a);a=a.reshape(-1,3)
  m=np.array(o.matrix_world);eaves.append(a@m[:3,:3].T+m[:3,3])
e=np.concatenate(eaves);lo=e.min(0);hi=e.max(0)
width=hi[0]-lo[0];scale=frame['targetOuterEaveDimensionsMetres'][0]/width*.01
# Main south/north straight drip edges, not sloping corner ornament extrema.
eave_z=float(np.median(np.concatenate([a[:,2] for a in eaves[:1]])))
center=(lo+hi)/2;center[2]=eave_z
M=Matrix.Translation(Vector(frame['anchorBlenderEastNorthUp'])) @ Matrix.Rotation(frame['threeYawRadiansAboutY'],4,'Z') @ Matrix.Scale(scale,4) @ Matrix.Translation(Vector(-center))
for o in objects:
 w=o.matrix_world.copy();o.parent=None;o.matrix_world=M@w
 o['assetAuthor']='TRNKL';o['license']='CC BY 4.0';o['source']='https://sketchfab.com/3d-models/hall-of-supreme-harmony-c354afbc1a4f428d80a26f5904d27fe6'
# A texture is important when used on repeated main roof tiles; retain original nodes/UVs.
main=set()
for mat in bpy.data.materials:
 if mat.use_nodes and any(x in mat.name for x in ['lambert_W','lambert_qi_ta_wa']):
  for n in mat.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:main.add(n.image.name)
images=[i for i in bpy.data.images if i.type=='IMAGE' and i.size[0]]
originalSizes={i.name:list(i.size) for i in images}
for i in images:
 size=1024 if i.name in main else 512
 w,h=i.size;ratio=min(1,size/max(w,h));i.scale(max(1,round(w*ratio)),max(1,round(h*ratio)))
 # Remove packed original encoding so exporter sees the resized pixels.
 if i.packed_file:i.unpack(method='REMOVE')
 i.filepath_raw=str(OUT/(i.name+'.png'));i.file_format='PNG';i.save();i.pack()
print('TEXTURES_SCALED',len(images),'main',len(main),flush=True)
meta={'source':str(SOURCE),'sourceSHA256':hashlib.file_digest(open(SOURCE,'rb'),'sha256').hexdigest(),'author':'TRNKL','license':'CC BY 4.0','sourceEaveBounds':[lo.tolist(),hi.tolist()],'sourceEaveDatumZ':eave_z,'sourceEaveWidth':width,'uniformSourceToMapScale':scale,'sourceCenter':center.tolist(),'sourceToBlenderWorldMatrix':[list(r) for r in M],'targetAnchor':frame['anchorBlenderEastNorthUp'],'limitations':['Artist-created roof, not surveyed heritage data.','Uniform width fit preserves original proportions; source eave depth is narrower than prior OSM roof.','Eave datum is median of main straight drip-tile vertices; ornamental minimum is not used.'],'lods':{}}
for level in ['detail','preview']:
 if level=='preview':
  for i in images:
   w,h=i.size;i.scale(max(1,w//2),max(1,h//2));i.filepath_raw=str(OUT/(i.name+'-preview.png'));i.save();i.pack()
  for o in objects:
   bpy.context.view_layer.objects.active=o
   mod=o.modifiers.new('Preview simplification','DECIMATE');mod.ratio=.12;mod.use_collapse_triangulate=True
   bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 path=OUT/f'aligned-{level}.glb'
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=88,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_extras=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=20,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
 retain_source_credit(path)
 pts=np.array([list(o.matrix_world@Vector(c)) for o in objects for c in o.bound_box]);bmin=pts.min(0);bmax=pts.max(0)
 meta['lods'][level]={'file':path.name,'bytes':path.stat().st_size,'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),'compression':{'method':'Draco','level':6,'positionQuantization':20,'normalQuantization':12,'uvQuantization':14},'meshCount':len(objects),'blenderBounds':[bmin.tolist(),bmax.tolist()],'threeBounds':[[bmin[0],bmin[2],-bmax[1]],[bmax[0],bmax[2],-bmin[1]]],'textureRGBABytesWithMipmaps':sum(i.size[0]*i.size[1]*4*4/3 for i in images),'textures':[{'name':i.name,'originalSize':originalSizes[i.name],'size':list(i.size)} for i in images]}
 json.dump(meta,open(OUT/'metadata.json','w'),indent=2,default=float)
 print('EXPORTED',level,meta['lods'][level]['bytes'],flush=True)
# Fast source material/alignment review from a south-east bird's eye view.
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
if not scene.world:scene.world=bpy.data.worlds.new('Roof review world')
scene.world.color=(.3,.3,.3)
center=Vector(frame['anchorBlenderEastNorthUp'])+Vector((0,0,.065))
bpy.ops.object.camera_add(location=center+Vector((.45,-.8,.5)));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.78;cam.data.clip_start=.001;scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=center+Vector((-.3,-.4,.8)));lamp=bpy.context.object;lamp.data.energy=35;lamp.data.shape='DISK';lamp.data.size=.7;lamp.rotation_euler=(center-lamp.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='AgX';scene.render.film_transparent=False;scene.render.filepath=str(OUT/'aligned-review.png')
bpy.ops.render.render(write_still=True)
print('DONE',flush=True)
