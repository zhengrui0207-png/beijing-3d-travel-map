import json,pathlib,struct,math
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'public/assets/metadata.json').read_text())
src=json.loads((ROOT/'data/source.json').read_text())
assert meta['stats']['buildings']==sum(meta['stats'].get(k,0) for k in ['height_tag','levels_tag','estimated_height'])
for l in meta['landmarks']:
    assert 116.345<l['lon']<116.485 and 39.865<l['lat']<39.965
    assert math.isfinite(l['x']) and math.isfinite(l['y'])
glb=ROOT/'public/assets/beijing.glb'
with glb.open('rb') as f:
    magic,version,length=struct.unpack('<4sII',f.read(12));assert magic==b'glTF' and version==2 and length==glb.stat().st_size
    size,kind=struct.unpack('<II',f.read(8));assert kind==0x4E4F534A
    model=json.loads(f.read(size))
    for a in model['accessors']:
        for prop in ['min','max']:
            assert all(math.isfinite(v) for v in a.get(prop,[]))
layer_names={n.get('extras',{}).get('layer') for n in model['nodes']}
for expected in ['roads_major','roads_local','buildings_low','water','parks','landmark_cctv','landmark_tiananmen']:
    assert expected in layer_names,(expected,layer_names)
im=Image.open(ROOT/'output/北京城市地图_8K.png');assert im.size==(7680,4320);im.verify()
assert (ROOT/'北京城市地图.blend').stat().st_size>100000
report={'status':'passed','render_resolution':[7680,4320],'glb_meshes':len(model['meshes']),'glb_bytes':glb.stat().st_size,'layers':sorted(x for x in layer_names if x),'landmark_count':len(meta['landmarks']),'stats':meta['stats'],'source':src['endpoint']}
(ROOT/'output/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(ROOT/'public/assets/render-status.json').write_text(json.dumps({'ready':True,'resolution':[7680,4320],'engine':'Cycles CPU'}))
print(json.dumps(report,ensure_ascii=False,indent=2))
