import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'北京城市地图.blend'))
scene=bpy.context.scene
scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.denoising_use_gpu=False
scene.render.threads_mode='AUTO'
scene.cycles.use_auto_tile=True;scene.cycles.tile_size=1024
scene.render.resolution_x=7680;scene.render.resolution_y=4320;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'output/北京城市地图_8K.png')
for ob in scene.objects:
    if ob.get('layer','').startswith(('roads','paths')):ob.visible_shadow=False
scene['Render engine']='Cycles CPU, 24 samples, adaptive sampling, OpenImageDenoise, native 7680 × 4320'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'北京城市地图.blend'))
print('FINAL_SCENE_SAVED',flush=True)
