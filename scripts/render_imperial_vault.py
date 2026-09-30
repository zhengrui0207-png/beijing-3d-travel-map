import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];s=bpy.data.scenes.get('Imperial Vault overview')or bpy.data.scenes.new('Imperial Vault overview');bpy.context.window.scene=s
for o in list(s.objects):bpy.data.objects.remove(o,do_unlink=True)
for ob in bpy.data.scenes['Imperial Vault detail'].objects:
 o=ob.copy();s.collection.objects.link(o)
world=bpy.data.worlds.new('Imperial Vault overview sky');world.use_nodes=True;n=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');n.inputs['Color'].default_value=(.75,.81,.9,1);n.inputs['Strength'].default_value=.65;s.world=world
c=bpy.data.cameras.new('Imperial Vault overview camera');o=bpy.data.objects.new('Imperial Vault overview camera',c);s.collection.objects.link(o);o.location=(.20,-.6,.28);o.rotation_euler=(Vector((0,0,.08))-o.location).to_track_quat('-Z','Y').to_euler();c.type=next(i.identifier for i in c.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO');c.ortho_scale=.38;c.clip_start=.001;s.camera=o
ld=bpy.data.lights.new('Imperial Vault overview sun',next(i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items if i.identifier=='SUN'));ld.energy=2.5;ld.angle=.13;o=bpy.data.objects.new('Imperial Vault overview sun',ld);s.collection.objects.link(o);o.rotation_euler=(.4,-.5,-.5)
s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.image_settings.file_format=next(i.identifier for i in s.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG');s.render.filepath=str(ROOT/'output/imperial-vault/皇穹宇_Blender.png')
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=(0,0,.08);area.spaces.active.region_3d.view_distance=.55;area.spaces.active.region_3d.view_rotation=Vector((1,-1,2)).to_track_quat('Z','Y')
bpy.data.libraries.write(str(ROOT/'output/imperial-vault/皇穹宇_精细场景.blend'),{s},fake_user=True);bpy.ops.render.render(write_still=True);print('Rendered imperial vault')
