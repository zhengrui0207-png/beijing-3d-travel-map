import bpy,pathlib,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'北京城市地图.blend'))
cpu='--gpu' not in sys.argv
if not cpu:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='METAL'
bpy.context.scene.cycles.device='CPU' if cpu else 'GPU'
if cpu:
    bpy.context.scene.render.threads_mode='FIXED'
    bpy.context.scene.render.threads=6
bpy.context.scene.cycles.samples=24
bpy.context.scene.cycles.denoising_use_gpu=False
for ob in bpy.context.scene.objects:
    if ob.get('layer','').startswith(('roads','paths')):ob.visible_shadow=False
if hasattr(bpy.context.scene.cycles,'use_auto_tile'):
    bpy.context.scene.cycles.use_auto_tile=True
    bpy.context.scene.cycles.tile_size=1024
bpy.context.scene.render.resolution_percentage=100
bpy.context.scene.render.filepath=str(ROOT/'output/北京城市地图_8K.png')
print('RENDER_START','CPU' if cpu else 'METAL','7680 x 4320',flush=True)
if hasattr(bpy.app.handlers,'render_stats'):
    bpy.app.handlers.render_stats.append(lambda *args:print('RENDER_PROGRESS',args,flush=True))
bpy.ops.render.render(write_still=True)
print('NATIVE_8K_RENDER_DONE',flush=True)
