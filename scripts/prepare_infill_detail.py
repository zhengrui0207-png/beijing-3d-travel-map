"""Inferred construction trim on existing Overture footprints, not surveyed detail.
Flat parapets use polygon differences so courtyards and concave corners stay open.
"""
from pathlib import Path
import json,math,collections
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
ROOT=Path(__file__).resolve().parents[1]

def polys(g):
 if g.geom_type=='Polygon':return [g]
 return [p for s in getattr(g,'geoms',[]) for p in polys(s)]

def add(out,kind,f):out.setdefault(kind,[]).append(f)
def prism(out,kind,a,b,width,depth):
 dx,dy=b[0]-a[0],b[1]-a[1];n=math.hypot(dx,dy)
 if n<.001:return
 nx,ny=-dy/n*width/2,dx/n*width/2
 v=[(p[0]+s*nx,p[1]+s*ny,p[2]+z) for z in [-depth/2,depth/2] for p,s in [(a,-1),(b,-1),(b,1),(a,1)]]
 for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:add(out,kind,[v[i] for i in ids])

def detail(r):
 out={};top=max(p[2] for tri in r['roof'] for p in tri)
 if r['roofShape']=='inferred-gabled':
  for w in r['walls']:
   a,b=w[3],w[2]
   prism(out,'fascia',[a[0],a[1],a[2]-.0006],[b[0],b[1],b[2]-.0006],.0024,.0014)
  edges=set()
  for tri in r['roof']:
   for a,b in zip(tri,tri[1:]+tri[:1]):
    if abs(a[2]-top)<.00002 and abs(b[2]-top)<.00002:
     key=tuple(sorted((tuple(a),tuple(b))))
     if key not in edges:
      edges.add(key);prism(out,'ridge',[a[0],a[1],a[2]+.0007],[b[0],b[1],b[2]+.0007],.002,.002)
 else:
  p=Polygon(r['rings'][0],r['rings'][1:]);inside=p.buffer(-.002,join_style=2)
  if inside.is_empty:return out
  band=p.difference(inside);z0=top+.00002;z1=top+.0045
  for poly in polys(band):
   for tri in constrained_delaunay_triangles(poly).geoms:
    pts=list(tri.exterior.coords)[:3]
    if (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])<0:pts.reverse()
    add(out,'parapet',[(x,y,z1) for x,y in pts])
   poly=orient(poly,sign=1)
   for ring in [poly.exterior,*poly.interiors]:
    pts=list(ring.coords)[:-1]
    for a,b in zip(pts,pts[1:]+pts[:1]):add(out,'parapet',[(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)])
 return out

if __name__=='__main__':
 rows=json.loads((ROOT/'data/urban/overture-fill-records.json').read_text())['records'];tiles={};counts=collections.Counter()
 for r in rows:
  x,y=r['center'];key=f'{math.floor(x/10)}_{math.floor(y/10)}';t=tiles.setdefault(key,{'id':'infill-'+key,'bounds':[1e9,1e9,-1e9,-1e9],'height':0,'buildings':0,'layers':{}})
  g=detail(r)
  if not g:continue
  t['buildings']+=1;t['height']=max(t['height'],r['height']+.006)
  a,b,c,d=r['bounds'];q=t['bounds'];t['bounds']=[min(q[0],a-.002),min(q[1],b-.002),max(q[2],c+.002),max(q[3],d+.002)]
  for kind,faces in g.items():t['layers'].setdefault(kind,[]).extend(faces);counts[kind+'Triangles']+=sum(len(f)-2 for f in faces)
  counts[r['roofShape']]+=1
 specs=[]
 for key,t in tiles.items():
  if not t['buildings']:continue
  path=ROOT/f'data/urban/infill-detail/{key}.json';path.write_text(json.dumps(t,separators=(',',':')));specs.append({k:v for k,v in t.items()if k!='layers'}|{'input':str(path),'url':f'public/assets/urban-fill/detail/{key}.glb','minPpu':300})
 manifest={'source':'Overture Maps 2026-09-23.1 / East Asian Buildings; derived from the attributed infill footprints', 'attribution':'public/assets/urban-fill/ATTRIBUTION.html', 'tiles':specs,'stats':dict(counts),'method':'Illustrative roof construction: 20 cm thick / 45 cm high flat parapets, 24 cm fascia and 20 cm ridge trim. Footprints retained; these details are estimates, not field measurements.'}
 (ROOT/'data/urban/infill-detail/index.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'tiles':len(specs),'stats':dict(counts)}),flush=True)
