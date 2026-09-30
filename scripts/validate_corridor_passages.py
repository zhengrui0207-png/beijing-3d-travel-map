import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=json.loads((R/'data/tiantan-corridor-plan.json').read_text());bpy.context.window.scene=bpy.data.scenes['Tiantan Corridor detail'];deps=bpy.context.evaluated_depsgraph_get();trees=[BVHTree.FromObject(o,deps)for o in bpy.context.scene.objects];checks=[]
for a,b in zip(p['axis'],p['axis'][1:]):
 origin=Vector((a[0]-p['center'][0],a[1]-p['center'][1],.020));end=Vector((b[0]-p['center'][0],b[1]-p['center'][1],.020));d=end-origin;length=d.length;d.normalize();checks.append(not any(t.ray_cast(origin+d*.003,d,length-.006)[0] is not None for t in trees))
assert all(checks),checks
report={'openSegmentPassages':checks,'meshCount':len(trees),'triangles':sum(len(f.vertices)-2 for o in bpy.context.scene.objects for f in o.data.polygons)};(R/'output/tiantan-corridor/geometry-validation.json').write_text(json.dumps(report,indent=2));print(report)
for o in bpy.context.scene.objects:o.select_set(False)
