from pathlib import Path
import json,math,struct,itertools,urllib.parse
ROOT=Path(__file__).resolve().parents[1]
s=next(s for s in json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())['assets']if s['id']=='shichahai')
audit=json.loads((ROOT/'output/yinding-detail/detail-audit.json').read_text());a,b=audit['axis']['start'],audit['axis']['end'];length=math.dist(a,b)
assert 13<length*100<13.5
angle=math.radians(s['rotation']);axis=(-math.sin(angle),math.cos(angle))
for sign,end in [(-1,a),(1,b)]:
 mapped=[s['x']+axis[0]*length/2*sign,s['y']+axis[1]*length/2*sign]
 assert math.dist(mapped,end)<1e-9
assert s['roadReplacement']['halfLength']<length/2
assert .009<s['groundHeight']<.012
results=[]
for level,url in s['lods'].items():
 p=ROOT/urllib.parse.urlsplit(url).path;raw=p.read_bytes();magic,v,size=struct.unpack_from('<4sII',raw);assert magic==b'glTF'and size==len(raw)
 n,_=struct.unpack_from('<II',raw,12);d=json.loads(raw[20:20+n]);assert 'KHR_draco_mesh_compression'in d['extensionsRequired']
 assert all(im.get('bufferView')is not None for im in d['images'])
 assert any('normalTexture'in m for m in d['materials'])
 tris=0
 for mesh in d['meshes']:
  for prim in mesh['primitives']:
   ac=d['accessors'][prim['attributes']['POSITION']];assert all(math.isfinite(x)for x in ac['min']+ac['max']);tris+=d['accessors'][prim['indices']]['count']//3
 names=[m['name']for m in d['meshes']];assert any('vault'in name for name in names)and any('marble'in name for name in names)
 if level=='detail':assert len([name for name in names if 'name'in name])==2
 stats=json.loads((ROOT/f'output/yinding-detail/{level}-audit.json').read_text());assert tris==stats['triangles'] and len(raw)==stats['bytes']
 assert len(raw)<1_100_000
 results.append({'level':level,'triangles':tris,'bytes':len(raw),'meshes':len(d['meshes'])})
assert results[0]['triangles']<results[1]['triangles']/3
report={'horizontalEndpointErrorMetres':0,'axisLengthMetres':length*100,'rotation':s['rotation'],'assets':results,'note':'Orientation/packaging validated; vertical dimensions and carved motifs remain photo-informed estimates.'}
(ROOT/'output/yinding-detail/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
