"""Run inside Blender: actual mesh ray tests, independent of model metadata."""
import bpy,json
from mathutils import Vector
from pathlib import Path
s=bpy.data.scenes['Duanmen detail'];bpy.context.window.scene=s;dg=bpy.context.evaluated_depsgraph_get()
def cast(x,z):
 r=s.ray_cast(dg,Vector((x,-1,z)),Vector((0,1,0)),distance=2)
 return {'hit':r[0],'object':r[4].name if r[0] else None,'point':list(r[1]) if r[0] else None}
r={'centerPassage':cast(0,.04),'centerUpperOpening':cast(0,.087),'aboveArch':cast(0,.09),'betweenPortals':cast(.065,.04),'sideRecessedDoor':cast(.135,.04)}
assert not r['centerPassage']['hit'] and not r['centerUpperOpening']['hit'],r
assert r['aboveArch']['hit'] and r['betweenPortals']['hit'],r
assert r['sideRecessedDoor']['hit'] and 'door' in r['sideRecessedDoor']['object'],r
(Path(__file__).resolve().parents[1]/'output/duanmen-detail/portal-ray-check.json').write_text(json.dumps(r,indent=2));print(r)
