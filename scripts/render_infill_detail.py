"""Neutral construction study of one geographic district; not photo-real reconstruction."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
D=sys.modules['infill_roof_detail'];U=D.U;s=D.scene;bpy.context.window.scene=s
for o in list(s.objects):
 if o.name.startswith('Infill Study '):bpy.data.objects.remove(o,do_unlink=True)
g={}
for r in json.loads((ROOT/'data/urban/overture-fill-records.json').read_text())['records']:
 if not(-30<=r['center'][0]<-20 and 10<=r['center'][1]<20):continue
 for f in r['walls']:U.add(g,'walls',f)
 for f in r['roof']:
  a,b,c=f
  if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:f=list(reversed(f))
  U.add(g,'roofs',f)
for k,c in {'walls':(.58,.57,.52),'roofs':(.13,.16,.17)}.items():U.mesh(s,'Infill Study '+k,*g[k],U.material('Infill Study '+k,c),'buildings_urban_'+k)
world=bpy.data.worlds.new('Infill Study daylight');world.use_nodes=True;back=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');back.inputs['Color'].default_value=(.70,.79,.9,1);back.inputs['Strength'].default_value=.5;s.world=world
cam=bpy.data.cameras.new('Infill Study camera');o=bpy.data.objects.new('Infill Study camera',cam);s.collection.objects.link(o);target=Vector((-23.35,16.4,.05));o.location=target+Vector((1,-1.6,1.55));o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();cam.type=next(i.identifier for i in cam.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO');cam.ortho_scale=1.4;cam.clip_start=.001;s.camera=o
ld=bpy.data.lights.new('Infill Study sunlight',next(i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items if i.identifier=='SUN'));ld.energy=2.7;ld.angle=.12;l=bpy.data.objects.new('Infill Study sunlight',ld);s.collection.objects.link(l);l.rotation_euler=(.6,-.45,-.6)
U.mesh(s,'Infill Study floor',[(-30,10,.008),(-20,10,.008),(-20,20,.008),(-30,20,.008)],[(0,1,2,3)],U.material('Infill Study ground',(.4,.44,.38)),'terrain')
s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format=next(i.identifier for i in s.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG');s.render.filepath=str(ROOT/'output/urban-infill-detail/城区屋顶构造_Blender.png')
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=target;area.spaces.active.region_3d.view_distance=1.5
bpy.data.libraries.write(str(ROOT/'output/urban-infill-detail/城区屋顶细节_中央街区.blend'),{s},fake_user=True)
bpy.ops.render.render(write_still=True)
print(s.render.filepath)
