import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];s=bpy.data.scenes.get('Echo Court overview')or bpy.data.scenes.new('Echo Court overview');bpy.context.window.scene=s
for o in list(s.objects):bpy.data.objects.remove(o,do_unlink=True)
plan=json.loads((ROOT/'data/echo-court-plan.json').read_text());vault=json.loads((ROOT/'data/imperial-vault-plan.json').read_text())
for name in ['Echo Court detail','Imperial Vault detail']:
 for ob in bpy.data.scenes[name].objects:
  o=ob.copy();s.collection.objects.link(o)
  if name=='Imperial Vault detail':o.location.x+=vault['center'][0]-plan['center'][0];o.location.y+=vault['center'][1]-plan['center'][1]
world=bpy.data.worlds.new('Echo Court overview sky');world.use_nodes=True;n=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');n.inputs['Color'].default_value=(.75,.81,.9,1);n.inputs['Strength'].default_value=.65;s.world=world
c=bpy.data.cameras.new('Echo Court overview camera');o=bpy.data.objects.new('Echo Court overview camera',c);s.collection.objects.link(o);o.location=(.30,-.95,.78);o.rotation_euler=(Vector((0,0,.04))-o.location).to_track_quat('-Z','Y').to_euler();c.type=next(i.identifier for i in c.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO');c.ortho_scale=.9;c.clip_start=.001;s.camera=o
ld=bpy.data.lights.new('Echo Court overview sun',next(i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items if i.identifier=='SUN'));ld.energy=2.5;ld.angle=.13;o=bpy.data.objects.new('Echo Court overview sun',ld);s.collection.objects.link(o);o.rotation_euler=(.4,-.5,-.5)
s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.image_settings.file_format=next(i.identifier for i in s.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG');s.render.filepath=str(ROOT/'output/echo-court/回音壁院落_Blender.png')
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=(0,0,.04);area.spaces.active.region_3d.view_distance=1.2;area.spaces.active.region_3d.view_rotation=Vector((1,-1,2)).to_track_quat('Z','Y')
bpy.data.libraries.write(str(ROOT/'output/echo-court/回音壁院落_精细场景.blend'),{s},fake_user=True);bpy.ops.render.render(write_still=True);print('Rendered imperial vault')
