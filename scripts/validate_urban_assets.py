"""Check delivered GLBs: bounds, UVs, finite coordinates, district coverage."""
import json,struct,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def glb(path):
    b=path.read_bytes();assert b[:4]==b'glTF';n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);return j,b[28+n:]
def positions(j,b,a):
    acc=j['accessors'][a];v=j['bufferViews'][acc['bufferView']];base=v.get('byteOffset',0)+acc.get('byteOffset',0);stride=v.get('byteStride',12)
    return [struct.unpack_from('<fff',b,base+i*stride)for i in range(acc['count'])]
m=json.loads((ROOT/'public/assets/urban/manifest.json').read_text());r=json.loads((ROOT/'data/urban/records.json').read_text())['records']
assert len(r)==m['stats']['buildings'] and len(r)>=25039
assert len({x['id']for x in r})==len(r)
assert sum(x['roofShape']!='flat'for x in r)==m['stats']['pitchedRoofs']
# Regression: inner buildings of a pedestrian plaza must not disappear.
assert {43921111,43921133,43921137,43921140}.issubset({x['osmId']for x in r})
pitch_open=0
for row in r:
    assert math.isclose(row['top']-row['height'],.011,abs_tol=1e-8)
    for face in row['roof']+row['walls']:
        assert all(math.isfinite(q)for p in face for q in p)
    if row['roofShape']=='gabled':
        # Roof ridge ends must be capped by the wall, not an open triangle.
        assert max(p[2]for f in row['walls']for p in f)>=row['eaves']
files=[m['shell']]+[t['url']for t in m['tiles']];mesh_count=0;vertex_count=0
for url in files:
    j,b=glb(ROOT/url)
    assert all(n.get('extras',{}).get('layer','').startswith('buildings_urban')for n in j['nodes'] if 'mesh'in n)
    for mesh in j['meshes']:
        for p in mesh['primitives']:
            xyz=positions(j,b,p['attributes']['POSITION']);vertex_count+=len(xyz);mesh_count+=1
            assert all(math.isfinite(v)for point in xyz for v in point)
            assert all(-62<x<62 and .005<y<6 and -58<z<58 for x,y,z in xyz),(url,'bad bounds')
            if url==m['shell'] and 'walls'in mesh['name']:assert 'TEXCOORD_0'in p['attributes']
assert len(m['tiles'])==144 and all(t['bytes']>0 for t in m['tiles'])
result={'buildings':len(r),'pitchedRoofs':m['stats']['pitchedRoofs'],'photoInferredRoofs':sum(x['roofSource']=='photoInferred' for x in r),'districts':144,'meshes':mesh_count,'vertices':vertex_count,'assetBytes':sum((ROOT/x).stat().st_size for x in files),'checks':['all finite coordinates','ground-aligned heights','preserved OSM footprint ids including inner buildings of pedestrian plazas','wall UVs for facade alignment','district assets and bounds','no foreign scene objects']}
(ROOT/'output/urban/asset-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
