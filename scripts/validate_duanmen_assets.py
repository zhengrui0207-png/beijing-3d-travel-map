"""Verify temple export metadata against model scale and LOD contracts.
Browser QA separately decodes compressed geometry, checks rendered appearance and unloads it.
"""
from pathlib import Path
import struct,json,math,urllib.parse,itertools
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())
spec=next(s for s in manifest['assets']if s['id']=='duanmen')
result=[]
def transform(point,node):
 if 'matrix' in node:
  m=node['matrix'];p=(*point,1)
  return [sum(m[j*4+i]*p[j] for j in range(4)) for i in range(3)]
 v=[p*s for p,s in zip(point,node.get('scale',[1,1,1]))]
 x,y,z,w=node.get('rotation',[0,0,0,1]);q=[x,y,z]
 norm=math.sqrt(x*x+y*y+z*z+w*w);q=[a/norm for a in q];w/=norm
 def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
 uv=cross(q,v);uuv=cross(q,uv)
 return [v[i]+2*(w*uv[i]+uuv[i])+node.get('translation',[0,0,0])[i] for i in range(3)]
for level,url in spec['lods'].items():
 p=ROOT/urllib.parse.urlsplit(url).path
 raw=p.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw);assert magic==b'glTF'and version==2 and length==len(raw)
 n,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n]);assert kind==0x4e4f534a
 assert 'KHR_draco_mesh_compression'in doc['extensionsRequired']
 assert len(doc['meshes'])==(16 if level=='preview' else 17)
 assert not doc.get('cameras')
 assert all('Duanmen Preview'not in node.get('name','')for node in doc['nodes'])
 minv=[math.inf]*3;maxv=[-math.inf]*3;triangles=0
 parents={child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
 for ni,node in enumerate(doc['nodes']):
  if 'mesh' not in node:continue
  mesh=doc['meshes'][node['mesh']]
  for prim in mesh['primitives']:
   a=doc['accessors'][prim['attributes']['POSITION']]
   assert all(math.isfinite(v)for v in a['min']+a['max'])
   for corner in itertools.product(*zip(a['min'],a['max'])):
    p=corner;ancestor=ni
    while ancestor is not None:
     p=transform(p,doc['nodes'][ancestor]);ancestor=parents.get(ancestor)
    for i in range(3):minv[i]=min(minv[i],p[i]);maxv[i]=max(maxv[i],p[i])
   triangles+=doc['accessors'][prim['indices']]['count']//3
 assert abs(minv[1])<1e-7 and abs(maxv[1]-.35)<.002
 assert 1.17<maxv[0]-minv[0]<1.19
 assert abs(minv[0]+maxv[0])<1e-5 and abs(minv[2]+maxv[2])<.001
 assert all(im.get('bufferView')is not None for im in doc['images'])
 assert len(doc['images'])==1
 assert len(raw)<9_000_000
 result.append({'level':level,'bytes':len(raw),'triangles':triangles,'bounds':[minv,maxv],'embeddedTextures':len(doc['images']),'draco':True})
assert result[0]['triangles']<result[1]['triangles']/2
# Mapped shells / trim must not poke through the new platform.
records=json.loads((ROOT/'data/urban/records.json').read_text())['records'];a,b,c,d=spec['bounds']
intersections=[r['id']for r in records if r['bounds'][0]<c and r['bounds'][2]>a and r['bounds'][1]<d and r['bounds'][3]>b]
from shapely.geometry import Polygon
footprint=Polygon(json.loads((ROOT/'data/duanmen-footprint.json').read_text())['rings'][0])
real_intersections=[r['id']for r in records if r['id']in intersections and footprint.intersection(Polygon(r['rings'][0],r['rings'][1:])).area>1e-8]
assert len(real_intersections)==12,real_intersections
assert all(r['parentOsmId']==25097188 for r in records if r['id'] in real_intersections)
report={'assets':result,'sourcePartsReplacedByMask':real_intersections,'adjacentBoundaryWalls':[i for i in intersections if i not in real_intersections],'note':'Scale and packaging validated; photographic accuracy remains a separate visual assessment.'}
(ROOT/'output/duanmen-detail/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
