import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];s=bpy.data.scenes.get('Axis courts overview')or bpy.data.scenes.new('Axis courts overview');bpy.context.window.scene=s
for o in list(s.objects):bpy.data.objects.remove(o,do_unlink=True)
for p in json.loads((ROOT/'data/axis-courts.json').read_text()):
 for ob in bpy.data.scenes[p['id']+' detail'].objects:
  o=ob.copy();s.collection.objects.link(o);o.location=(p['center'][0]+20.44,p['center'][1]+6,0);o.rotation_euler.z=p['angle']
world=bpy.data.worlds.new('Axis courts sky');world.use_nodes=True;n=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');n.inputs['Color'].default_value=(.75,.81,.9,1);n.inputs['Strength'].default_value=.65;s.world=world
c=bpy.data.cameras.new('Axis courts camera');o=bpy.data.objects.new('Axis courts camera',c);s.collection.objects.link(o);o.location=(3,-5,7);o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();c.type=next(i.identifier for i in c.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO');c.ortho_scale=5.4;c.clip_start=.001;s.camera=o
ld=bpy.data.lights.new('Axis courts sun',next(i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items if i.identifier=='SUN'));ld.energy=2.5;ld.angle=.13;o=bpy.data.objects.new('Axis courts sun',ld);s.collection.objects.link(o);o.rotation_euler=(.4,-.5,-.5)
s.render.resolution_x=1400;s.render.resolution_y=1600;s.render.resolution_percentage=100;s.render.image_settings.file_format=next(i.identifier for i in s.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG');s.render.filepath=str(ROOT/'output/axis-courts/朝房建筑群_Blender.png')
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=(0,0,0);area.spaces.active.region_3d.view_distance=5;area.spaces.active.region_3d.view_rotation=Vector((1,-1,2)).to_track_quat('Z','Y')
bpy.data.libraries.write(str(ROOT/'output/axis-courts/中轴朝房_精细场景.blend'),{s},fake_user=True);bpy.ops.render.render(write_still=True);print('Rendered axis courts')
