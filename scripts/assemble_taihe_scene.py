"""Save a separate, attributed Blender scene with the integrated authored roof."""
import bpy,json,re,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'public/assets/palace'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'故宫精细建筑.blend'))
existing={m.name:m for m in bpy.data.materials}
removed=[o for o in bpy.data.objects if (o.get('zone')=='central' and o.get('lod')=='high') or o.get('zone')=='roof-tiles-3-5']
assert len(removed)>=13, 'Expected original central body and micro chunk'
for obj in removed:bpy.data.objects.remove(obj,do_unlink=True)
for filename in ['central-high-taihe-v2.glb','roof-tiles-3-5-taihe.glb']:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(BASE/filename))
    for obj in set(bpy.data.objects)-before:
        if obj.type!='MESH':continue
        if obj.get('externalFallback')=='taihe-roof':
            bpy.data.objects.remove(obj,do_unlink=True)
            continue
        for slot in obj.material_slots:
            name=re.sub(r'\.\d{3}$','',slot.material.name)
            if name in existing:slot.material=existing[name]
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(BASE/'taihe-roof/detail.glb'))
roof=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
assert len(roof)>0
for obj in roof:
    obj['assetAuthor']='TRNKL'
    obj['license']='CC BY 4.0'
    obj['source']='https://sketchfab.com/3d-models/hall-of-supreme-harmony-c354afbc1a4f428d80a26f5904d27fe6'
    obj['layer']='landmark_taihe_roof'
bpy.ops.file.pack_all()
scene=bpy.context.scene
scene['Taihe roof attribution']=(BASE/'taihe-roof/ATTRIBUTION.md').read_text()
scene['Taihe roof alignment']=(BASE/'taihe-roof/asset.json').read_text()
text=bpy.data.texts.new('太和殿屋顶_署名与修改记录')
text.write(scene['Taihe roof attribution'])
bpy.context.preferences.filepaths.save_version=0
output=ROOT/'故宫精细建筑_太和殿屋顶版.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(output))
report={'file':str(output),'bytes':output.stat().st_size,'roofMeshes':len(roof),'meshCount':sum(o.type=='MESH' for o in bpy.data.objects),'packedImages':sum(bool(i.packed_file) for i in bpy.data.images),'fallbackMeshesRemaining':sum(o.get('externalFallback')=='taihe-roof' for o in bpy.data.objects)}
(ROOT/'.dream-loop/sketchfab/native-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('NATIVE_SCENE_READY',json.dumps(report,ensure_ascii=False),flush=True)
