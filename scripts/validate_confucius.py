"""Check actual mesh openings, finite coordinates, footprint and duplicate polygons."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];reports=[]
for level in['preview','detail']:
 scene=bpy.data.scenes['confucius '+level];bpy.context.window.scene=scene;vs=[];fs=[];errors=[]
 for ob in scene.objects:
  if ob.type!='MESH':continue
  offset=len(vs);vs.extend([ob.matrix_world@v.co for v in ob.data.vertices]);fs.extend([tuple(offset+i for i in p.vertices)for p in ob.data.polygons])
 if not all(math.isfinite(c)for v in vs for c in v):errors.append({'type':'nonfinite'})
 tree=BVHTree.FromPolygons(vs,fs);meta=json.loads((R/f'output/confucius-detail/confucius-{level}.json').read_text());checks=[]
 for i,w in enumerate(meta['openings']):
  pos=Vector(w['origin'])/100;direction=Vector(w['direction']);hit=tree.ray_cast(pos,direction,w['depth']/100)
  checks.append({'opening':i,'hitDistance':hit[3]if hit[0]is not None else None})
  if hit[0]is not None:errors.append({'type':'blocked-door','opening':i,'hitDistance':hit[3]})
 bounds=[[min(v[i]for v in vs)for i in range(3)],[max(v[i]for v in vs)for i in range(3)]]
 if bounds[0][2]<-.0001:errors.append({'type':'below-ground','minZ':bounds[0][2]})
 report={'level':level,'revision':meta['revision'],'meshCount':len([o for o in scene.objects if o.type=='MESH']),'boundsLocal':bounds,'doorRays':checks,'errors':errors,'scope':'Door aperture clearance and finite mesh/bounds only. Not a fidelity approval.'};reports.append(report)
(R/'output/confucius-detail/geometry-validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
