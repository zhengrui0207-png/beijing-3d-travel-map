import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
for id in['qianmen','qianmen-arrow']:
 s=bpy.data.scenes.get(id+' render')or bpy.data.scenes.new(id+' render');bpy.context.window.scene=s
 for ob in list(s.objects):bpy.data.objects.remove(ob,do_unlink=True)
 for ob in bpy.data.scenes[id+' detail'].objects:o=ob.copy();s.collection.objects.link(o)
 w=bpy.data.worlds.new(id+' sky');w.use_nodes=True;bg=next(n for n in w.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.76,.83,.92,1);bg.inputs['Strength'].default_value=.8;s.world=w
 cam=bpy.data.cameras.new(id+' camera');ob=bpy.data.objects.new(id+' camera',cam);s.collection.objects.link(ob);ob.location=(.85,-1.4,.82);ob.rotation_euler=(Vector((0,0,.20))-ob.location).to_track_quat('-Z','Y').to_euler();cam.type=next(v.identifier for v in cam.bl_rna.properties['type'].enum_items if v.identifier=='ORTHO');cam.ortho_scale=1.10 if id=='qianmen'else .84;cam.clip_start=.001;s.camera=ob
 light=bpy.data.lights.new(id+' sun',next(v.identifier for v in bpy.types.Light.bl_rna.properties['type'].enum_items if v.identifier=='SUN'));light.energy=2.6;light.angle=.14;o=bpy.data.objects.new(id+' sun',light);s.collection.objects.link(o);o.rotation_euler=(.4,-.5,-.5)
 s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.image_settings.file_format=next(v.identifier for v in s.render.image_settings.bl_rna.properties['file_format'].enum_items if v.identifier=='PNG');s.render.filepath=str(R/'output/qianmen-detail'/ (id+'_Blender.png'))
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=(0,0,.20);area.spaces.active.region_3d.view_distance=1.1;area.spaces.active.region_3d.view_rotation=Vector((.85,-1.4,.82)).to_track_quat('Z','Y')
 bpy.ops.render.render(write_still=True)
 bpy.data.libraries.write(str(R/'output/qianmen-detail'/(id+'_渲染场景.blend')),{s},fake_user=True)
 print('Rendered',id)
