"""Verify route coverage and the actual exported binary assets."""
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())
tours=json.loads((ROOT/'public/assets/tourism.json').read_text())['tours']
required={pid for tour in tours for pid in tour['stops']}
covered={a['id'] for a in manifest['assets']}|set(manifest['retainedExisting'])
assert required<=covered,required-covered
for asset in manifest['assets']:
    assert asset['source'] and asset['author'] and asset['license']
    for level,url in asset['lods'].items():
        path=ROOT/url;content=path.read_bytes()
        magic,version,length=struct.unpack_from('<4sII',content)
        assert magic==b'glTF' and version==2 and length==len(content),path
        size=struct.unpack_from('<I',content,12)[0];gltf=json.loads(content[20:20+size])
        assert not any(node.get('name')=='Cube' for node in gltf['nodes']),path
        assert all('uri' not in image for image in gltf.get('images',[])),path
        primitives=[p for mesh in gltf['meshes'] for p in mesh['primitives']]
        triangles=sum(gltf['accessors'][p['indices']]['count']//3 for p in primitives)
        assert triangles<(12000 if level=='preview' else 65000),(path,triangles)
        positions=[gltf['accessors'][p['attributes']['POSITION']] for p in primitives]
        bottom=min(p['min'][1] for p in positions);top=max(p['max'][1] for p in positions)
        assert abs(bottom)<.001,(path,'model does not sit on ground',bottom)
        if level=='detail':assert math.isclose(top,asset['height'],abs_tol=.001),(path,top,asset['height'])
print(f"PASS: {len(required)} route places covered; {len(manifest['assets'])*2} GLBs verified for geometry, scale, grounding, size budgets and attribution.")
