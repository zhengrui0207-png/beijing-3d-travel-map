"""Verify real exported-source mesh openings and silhouette, independently of recipe counts."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];report=[]
for level in['preview','detail']:
 s=bpy.data.scenes['cathedral '+level];bpy.context.window.scene=s;bpy.context.view_layer.update();vs=[];faces=[]
 for ob in s.objects:
  if ob.type!='MESH':continue
  ob.select_set(False);offset=len(vs);vs.extend([ob.matrix_world@v.co for v in ob.data.vertices]);faces.extend([tuple(offset+i for i in p.vertices)for p in ob.data.polygons])
 tree=BVHTree.FromPolygons(vs,faces,all_triangles=False);meta=json.loads((R/f'output/cathedral-detail/cathedral-{level}.json').read_text());errors=[];rays=[]
 for o in meta['openings']:
  n=Vector(o['outward']);p=Vector(o['point'])/100
  # Move off the central cross/mullion, staying inside the actual aperture.
  u=Vector((-n.y,n.x,0));p+=u*(.007 if o['kind']=='rose'else .0018)
  if o['kind']=='rose':p.z+=.005
  # Begin 80cm outside this wall, inside the 1.55m gap between neighbouring towers.
  # A 1.5m start crossed the adjacent tower's projecting cornice/pilasters.
  h=tree.ray_cast(p+n*.008,-n,.015);depth=h[3]-.008 if h[0]is not None else None
  if depth is None or not .0015<=depth<=.0051:errors.append({'kind':o['kind'],'point':list(p),'depth':depth})
  rays.append({'kind':o['kind'],'depth':depth})
 # Each separate tower must rise above the facade; the central one is tallest.
 towers=[]
 for x in[-.07,0,.07]:
  section=[v.z for v in vs if abs(v.x-x)<.004 and v.y<-.25];towers.append(max(section))
 if not(towers[1]>towers[0]and towers[1]>towers[2]and min(towers)>.24):errors.append({'towerHeights':towers})
 report.append({'level':level,'assetRevision':meta['revision'],'openingRays':len(rays),'doors':sum(o['kind']=='door'for o in meta['openings']),'towerHeights':towers,'depthRange':[min(r['depth']for r in rays if r['depth']is not None),max(r['depth']for r in rays if r['depth']is not None)],'errors':errors})
(R/'output/cathedral-detail/geometry-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
