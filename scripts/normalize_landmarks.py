import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'北京城市地图.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('layer')!='studio']
for ob in objects:
    if ob.get('layer','').startswith(('building','palace','landmark')):ob.scale.z/=2.6
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/beijing.glb'),export_format='GLB',export_extras=True,export_yup=True,export_apply=True,use_selection=True)
for ob in objects:
    if ob.get('layer','').startswith(('building','palace','landmark')):ob.scale.z=2.6
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'北京城市地图.blend'))
print('NORMALIZED_LANDMARK_TRANSFORMS',flush=True)
