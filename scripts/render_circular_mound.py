import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];P=json.loads((R/'data/circular-mound-plan.json').read_text());s=bpy.data.scenes.get('Circular Mound render')or bpy.data.scenes.new('Circular Mound render');bpy.context.window.scene=s
for o in list(s.objects):bpy.data.objects.remove(o,do_unlink=True)
for ob in bpy.data.scenes['Circular Mound detail'].objects:o=ob.copy();s.collection.objects.link(o)
# Include the two independent gate LODs for the standalone context render.
for g in P['gates']:
 if not g['existing']:continue
 key='mound-inner-gate'if g['kind']=='inner'else'mound-outer-gate'
 for ob in bpy.data.scenes[key+' detail'].objects:
  o=ob.copy();o.rotation_euler.z=g['angle'];o.location=((g['center'][0]-P['center'][0]),(g['center'][1]-P['center'][1]),0);s.collection.objects.link(o)
w=bpy.data.worlds.new('Mound sky');w.use_nodes=True;bg=next(n for n in w.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.75,.82,.90,1);bg.inputs['Strength'].default_value=.65;s.world=w
cam=bpy.data.cameras.new('Mound camera');ob=bpy.data.objects.new('Mound camera',cam);s.collection.objects.link(ob);ob.location=(.60,-1.0,.9);ob.rotation_euler=(Vector((0,0,.025))-ob.location).to_track_quat('-Z','Y').to_euler();cam.type=next(v.identifier for v in cam.bl_rna.properties['type'].enum_items if v.identifier=='ORTHO');cam.ortho_scale=.76;cam.clip_start=.001;s.camera=ob
light=bpy.data.lights.new('Mound sun',next(v.identifier for v in bpy.types.Light.bl_rna.properties['type'].enum_items if v.identifier=='SUN'));light.energy=2.8;light.angle=.12;o=bpy.data.objects.new('Mound sun',light);s.collection.objects.link(o);o.rotation_euler=(.4,-.5,-.5)
s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.image_settings.file_format=next(v.identifier for v in s.render.image_settings.bl_rna.properties['file_format'].enum_items if v.identifier=='PNG');s.render.filepath=str(R/'output/circular-mound/圜丘坛_Blender.png')
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=(0,0,.025);area.spaces.active.region_3d.view_distance=.95;area.spaces.active.region_3d.view_rotation=Vector((.6,-1,.9)).to_track_quat('Z','Y')
bpy.ops.render.render(write_still=True);cam.ortho_scale=2.30;s.render.filepath=str(R/'output/circular-mound/圜丘坛院落_Blender.png');bpy.ops.render.render(write_still=True);bpy.data.libraries.write(str(R/'output/circular-mound/圜丘坛_精细场景.blend'),{s},fake_user=True);print('Two renders saved')
