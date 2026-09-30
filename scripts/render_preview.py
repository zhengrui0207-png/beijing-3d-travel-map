import bpy,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'北京城市地图.blend'))
scene=bpy.context.scene
scene.cycles.device='CPU';scene.cycles.samples=12
scene.cycles.denoising_use_gpu=False
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_percentage=25
scene.render.filepath=str(ROOT/'output/北京城市地图_预览_修订.png')
bpy.ops.render.render(write_still=True)
print('CORRECTED_PREVIEW_DONE',flush=True)
