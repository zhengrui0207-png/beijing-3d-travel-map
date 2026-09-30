import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];bpy.context.window.scene=bpy.data.scenes['Imperial Vault detail'];deps=bpy.context.evaluated_depsgraph_get();trees=[BVHTree.FromObject(o,deps)for o in bpy.context.scene.objects];checks=[]
for bay in [-1,0,1]:
 a=-math.pi/2+bay*math.tau/8;origin=Vector((.083*math.cos(a),.083*math.sin(a),.04));direction=Vector((-math.cos(a),-math.sin(a),0));hits=[t.ray_cast(origin,direction,.028)[0]for t in trees];checks.append(all(h is None for h in hits))
assert all(checks),checks
corners=[o.matrix_world@Vector(v)for o in bpy.context.scene.objects for v in o.bound_box];height=max(v.z for v in corners)-min(v.z for v in corners);assert abs(height-.195)<1e-6
letters={ch:sum(len(p.vertices)-2 for o in bpy.context.scene.objects if 'plaque '+ch in o.name for p in o.data.polygons)for ch in '皇穹宇'};assert all(n>500 for n in letters.values());assert len(set(letters.values()))==3
report={'heightMetres':height*100,'threePortalApproachesClear':checks,'plaqueTriangles':letters,'meshCount':len(trees)};(R/'output/imperial-vault/geometry-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
for o in bpy.context.scene.objects:o.select_set(False)
