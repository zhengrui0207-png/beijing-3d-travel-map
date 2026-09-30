"""Compose restored ancillary halls and the detailed prayer hall for a Blender review render."""
import bpy,sys,math
from mathutils import Vector
u=sys.modules['urban_rebuild']
s=bpy.data.scenes.get('Tiantan Courtyard Review') or bpy.data.scenes.new('Tiantan Courtyard Review')
for o in list(s.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.context.window.scene=s
for o in u.scene.objects:
 if o.get('layer')in ['buildings_urban_courtyard','buildings_urban_paving']:
  clone=o.copy();s.collection.objects.link(clone)
u.courtyard.create(s,u.records,detail=True)
for o in bpy.data.scenes['Tiantan Prayer Hall detail'].objects:
 if o.type=='MESH'and not o.name.startswith('Temple Preview'):
  clone=o.copy();s.collection.objects.link(clone);clone.location+=Vector((-7.15260097299764,-36.45607040324756,.011))
world=bpy.data.worlds.new('Courtyard soft sky');world.use_nodes=True;s.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.75,.80,.88,1);bg.inputs['Strength'].default_value=.55
light=bpy.data.lights.new('Courtyard daylight','SUN');light.energy=2.4;light.angle=.16;o=bpy.data.objects.new('Courtyard daylight',light);s.collection.objects.link(o);o.rotation_euler=(.5,-.35,-.55)
cam=bpy.data.cameras.new('Courtyard camera');cam.type='ORTHO';cam.ortho_scale=2.7;o=bpy.data.objects.new('Courtyard camera',cam);s.collection.objects.link(o);o.location=(-6.7,-40.0,3.4);o.rotation_euler=(Vector((-7.14,-36.75,.03))-o.location).to_track_quat('-Z','Y').to_euler();cam.clip_start=.001;s.camera=o
try:s.render.engine='BLENDER_EEVEE'
except TypeError:pass
s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=100
fmt=[e.identifier for e in s.render.image_settings.bl_rna.properties['file_format'].enum_items];s.render.image_settings.file_format=next(v for v in fmt if v=='PNG')
s.render.filepath=str(u.ROOT/'output/urban/天坛祈谷坛_院落重建.png')
for image in bpy.data.images:
 if image.filepath and ('tiantan-detail/frieze'in image.filepath or 'palace/marble'in image.filepath):image.pack()
bpy.data.libraries.write(str(u.ROOT/'output/urban/天坛祈谷坛_建筑群.blend'),{s},fake_user=True)
bpy.ops.render.render(write_still=True)
print(s.render.filepath)
