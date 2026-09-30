import bpy,math
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=bpy.data.scenes['Beihai Stupa detail'];bpy.context.window.scene=s
for o in list(s.objects):
 if o.name.startswith('Beihai Preview '):bpy.data.objects.remove(o,do_unlink=True)
world=bpy.data.worlds.new('Beihai Preview daylight');world.use_nodes=True
p=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');p.inputs['Color'].default_value=(.70,.79,.90,1);p.inputs['Strength'].default_value=.45;s.world=world
cam=bpy.data.cameras.new('Beihai Preview camera');o=bpy.data.objects.new('Beihai Preview camera',cam);s.collection.objects.link(o)
o.location=(.8,-.75,.50);o.rotation_euler=(Vector((0,0,.17))-o.location).to_track_quat('-Z','Y').to_euler()
cam.type=next(i.identifier for i in cam.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO');cam.ortho_scale=.48;cam.clip_start=.001;s.camera=o
light_types=[i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items]
ld=bpy.data.lights.new('Beihai Preview sunlight',next(v for v in light_types if v=='SUN'));ld.energy=2.8;ld.angle=.16;ld.color=(1,.94,.82)
l=bpy.data.objects.new('Beihai Preview sunlight',ld);s.collection.objects.link(l);l.rotation_euler=(.55,-.5,-.65)
me=bpy.data.meshes.new('Beihai Preview floor');me.from_pydata([(-2,-2,-.002),(2,-2,-.002),(2,2,-.002),(-2,2,-.002)],[],[(0,1,2,3)]);me.update()
m=bpy.data.materials.new('Beihai Preview neutral');m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.57,.61,.59,1);p.inputs['Roughness'].default_value=.85;me.materials.append(m)
o=bpy.data.objects.new('Beihai Preview floor',me);s.collection.objects.link(o)
s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.render.image_settings.file_format=next(i.identifier for i in s.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG')
s.render.filepath=str(ROOT/'output/beihai-detail/北海白塔_Blender精细渲染.png')
for image in bpy.data.images:
 if image.filepath and ('tiantan-detail/frieze'in image.filepath or 'palace/marble'in image.filepath):image.pack()
for o in s.objects:o.select_set(False)
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  sp=area.spaces.active;sp.region_3d.view_location=(0,0,.17);sp.region_3d.view_distance=.60;sp.region_3d.view_rotation=Vector((1,-1,.5)).to_track_quat('Z','Y')
bpy.data.libraries.write(str(ROOT/'output/beihai-detail/北海白塔_精细场景.blend'),{s},fake_user=True)
bpy.ops.render.render(write_still=True)
print('Temple rendered',s.render.filepath)
