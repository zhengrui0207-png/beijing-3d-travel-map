import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];reports=[]
for level in ['preview','detail']:
 scene=bpy.data.scenes['art '+level];bpy.context.window.scene=scene;vs=[];fs=[]
 for ob in scene.objects:
  if ob.type!='MESH':continue
  ob.select_set(False);offset=len(vs);vs.extend([ob.matrix_world@v.co for v in ob.data.vertices]);fs.extend([tuple(offset+i for i in p.vertices)for p in ob.data.polygons])
 tree=BVHTree.FromPolygons(vs,fs);meta=json.loads((R/f'output/art-detail/art-{level}.json').read_text());errors=[];rays=[]
 for i,w in enumerate(meta['windows']):
  p=Vector(w['point'])/100;n=Vector(w['normal']);h=tree.ray_cast(p+n*.006,-n,.04);depth=h[3]-.006 if h[0]is not None else None
  expected=w['depth']/100
  if depth is None or abs(depth-expected)>.0015:errors.append({'window':i,'point':list(p),'depth':depth,'expected':expected})
  rays.append(depth)
 reports.append({'level':level,'revision':meta['revision'],'windowRays':len(rays),'errors':errors})
(R/'output/art-detail/geometry-validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
