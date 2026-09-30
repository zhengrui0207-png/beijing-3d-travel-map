"""Ray checks against actual Blender meshes, not the model recipe alone."""
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(__file__).resolve().parents[1];report=[]
for id in['qianmen','qianmen-arrow']:
 for level in['preview','detail']:
  s=bpy.data.scenes[id+' '+level];bpy.context.window.scene=s;bpy.context.view_layer.update();vs=[];faces=[]
  for ob in s.objects:
   if ob.type!='MESH':continue
   offset=len(vs);vs.extend([ob.matrix_world@v.co for v in ob.data.vertices]);faces.extend([tuple(offset+i for i in p.vertices)for p in ob.data.polygons])
  tree=BVHTree.FromPolygons(vs,faces,all_triangles=False);meta=json.loads((R/f'output/qianmen-detail/{id}-{level}.json').read_text());errors=[];count=0
  for x in[-.015,0,.015]:
   for z in[.01,.025,.045]:
    p=Vector((x,-.25,z));h=tree.ray_cast(p,Vector((0,1,0)),.5)
    if h[0]is not None:errors.append({'type':'blocked portal','x':x,'z':z,'hit':list(h[0])})
    count+=1
  for x in[-.06,.06]:
   h=tree.ray_cast(Vector((x,-.3,.04)),Vector((0,1,0)),.6)
   if h[0]is None:errors.append({'type':'missing platform wall','x':x})
  for w in meta['windowRecesses']:
   n=Vector(w['outward']);p=Vector(w['center'])/100+n*.02;hit=tree.ray_cast(p,-n,.04)
   if hit[0]is None or abs(hit[3]-(.02+w['recess']/100))>.0003:errors.append({'type':'incorrect window depth','center':w['center'],'distance':hit[3]})
  stairHits=[]
  for sign in[-1,1]:
   x,y,expected=(sign*.355,.168,.0755)if id=='qianmen'else(sign*.19,.19,.064)
   hit=tree.ray_cast(Vector((x,y,.4)),Vector((0,0,-1)),.5);stairHits.append(list(hit[0])if hit[0]is not None else None)
   if hit[0]is None or abs(hit[0].z-expected)>.005:errors.append({'type':'buried or missing stairs','x':x,'y':y,'hit':stairHits[-1]})
  roof=max(v.z for v in vs)
  if abs(roof-meta['height']/100)>1e-5:errors.append({'type':'incorrect total height','actual':roof})
  report.append({'id':id,'level':level,'throughPortalRays':count,'solidFlankRays':2,'windowRays':len(meta['windowRecesses']),'errors':errors,'heightMetres':roof*100,'stairRays':stairHits,'assetRevision':meta['revision']})
(R/'output/qianmen-detail/geometry-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
