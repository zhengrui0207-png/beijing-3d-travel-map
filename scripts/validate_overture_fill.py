"""Check footprint geometry and exported compressed model packaging independently."""
from pathlib import Path
import json,math,struct
from shapely.geometry import Polygon
ROOT=Path(__file__).resolve().parents[1]
blob=json.loads((ROOT/'data/urban/overture-fill-records.json').read_text());rows=blob['records']
assert len(rows)==blob['stats']['accepted']==76142
assert len({r['id']for r in rows})==len(rows)
minimum=math.inf;maximum=-math.inf
for r in rows:
 p=Polygon(r['rings'][0],r['rings'][1:]);assert p.is_valid and p.area>0
 assert r['heightSource']=='estimated'
 assert r['roof'] and r['walls']
 for face in r['roof']+r['walls']:
  for x,y,z in face:
   assert all(math.isfinite(v)for v in (x,y,z))
   assert -60<x<60 and -56<y<56 and .0109<=z<.6
   minimum=min(minimum,z);maximum=max(maximum,z)
 assert all(abs(v[2]-.011)<1e-7 for wall in r['walls']for v in wall[:2])
 assert all(abs(v[2]-(.011+r['height']))<1e-5 for face in r['roof']for v in face) if r['roofShape']=='unspecified-flat' else True
m=json.loads((ROOT/'public/assets/urban-fill/manifest.json').read_text());raw=(ROOT/m['url']).read_bytes()
magic,version,length=struct.unpack_from('<4sII',raw);assert magic==b'glTF'and version==2 and length==len(raw)==m['bytes']
n,kind=struct.unpack_from('<II',raw,12);d=json.loads(raw[20:20+n]);assert kind==0x4e4f534a
assert 'KHR_draco_mesh_compression'in d['extensionsRequired']
assert len(d['meshes'])==m['meshes']==72
tris=0
for mesh in d['meshes']:
 for prim in mesh['primitives']:
  a=d['accessors'][prim['attributes']['POSITION']];assert all(math.isfinite(v)for v in a['min']+a['max'])
  assert 'KHR_draco_mesh_compression'in prim['extensions']
  tris+=d['accessors'][prim['indices']]['count']//3
assert tris==m['triangles']
assert all(node['extras']['layer'].startswith('buildings_urban_')for node in d['nodes']if 'mesh'in node)
source=json.loads((ROOT/'public/assets/cartographic/landscape.json').read_text());filtered=json.loads((ROOT/'public/assets/urban-fill/landscape.json').read_text())
assert len(source['trees'])-len(filtered['trees'])==7801
report={'buildings':len(rows),'meshes':len(d['meshes']),'triangles':tris,'bytes':len(raw),'minHeight':minimum,'maxHeight':maximum,'decorativeTreesRemoved':7801,'valid':True}
(ROOT/'output/overture-fill/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
