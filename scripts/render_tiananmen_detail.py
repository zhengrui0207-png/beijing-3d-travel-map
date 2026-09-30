import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];s=bpy.data.scenes['Tiananmen detail'];bpy.context.window.scene=s
for o in list(s.objects):
 if o.name.startswith('Tiananmen Preview'):bpy.data.objects.remove(o,do_unlink=True)
world=bpy.data.worlds.new('Tiananmen Preview sky');world.use_nodes=True;p=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');p.inputs['Color'].default_value=(.75,.81,.90,1);p.inputs['Strength'].default_value=.7;s.world=world
cam=bpy.data.cameras.new('Tiananmen Preview camera');o=bpy.data.objects.new('Tiananmen Preview camera',cam);s.collection.objects.link(o);o.location=(.5,-1.6,.7);o.rotation_euler=(Vector((0,0,.17))-o.location).to_track_quat('-Z','Y').to_euler();cam.type=next(i.identifier for i in cam.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO');cam.ortho_scale=1.45;cam.clip_start=.0001;s.camera=o
ld=bpy.data.lights.new('Tiananmen Preview sun',next(i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items if i.identifier=='SUN'));ld.energy=2.5;ld.angle=.13;l=bpy.data.objects.new('Tiananmen Preview sun',ld);s.collection.objects.link(l);l.rotation_euler=(.4,-.5,-.5)
s.render.resolution_x=1500;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.render.image_settings.file_format=next(i.identifier for i in s.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG');s.render.filepath=str(ROOT/'output/tiananmen-detail/天安门_Blender精细渲染.png')
for o in s.objects:o.select_set(False)
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  sp=area.spaces.active;sp.region_3d.view_location=(0,0,.17);sp.region_3d.view_distance=1.5;sp.region_3d.view_rotation=Vector((1,-1,.7)).to_track_quat('Z','Y')
bpy.data.libraries.write(str(ROOT/'output/tiananmen-detail/天安门_精细场景.blend'),{s},fake_user=True)
bpy.ops.render.render(write_still=True)
print('Rendered',s.render.filepath)
