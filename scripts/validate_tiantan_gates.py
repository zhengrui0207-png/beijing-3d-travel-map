import bpy,json,math
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[1];plan=json.loads((R/'data/tiantan-gates-plan.json').read_text());result=[]
for p in plan['parts']:
 for level in ['preview','detail']:
  s=bpy.data.scenes[p['id']+' '+level];bpy.context.window.scene=s;bpy.context.view_layer.update();assert all(math.isfinite(v)for o in s.objects for pt in o.data.vertices for v in pt.co)
  L=p['length']-1 if p['kind']=='hall'else p['length'];xs=[-L*.30,0,L*.30]if p['kind']=='hall'else[-L*.34,0,L*.34];d=(p['depth']-1.25)/2+.1 if p['kind']=='hall'else 2;clear=[]
  for x in xs:clear.append(not s.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector(((x+.20)/100,-d/100,.012)),Vector((0,1,0)),distance=2*d/100)[0])
  expected=[True,False,True]if p['kind']=='outer'else[True,True,True];assert clear==expected,(p['id'],level,clear)
  glyphs={o.name:sum(len(f.vertices)-2 for f in o.data.polygons)for o in s.objects if o.name.startswith('成贞门牌匾')}
  assert all(n>100 for n in glyphs.values()),glyphs
  result.append({'id':p['id'],'level':level,'passages':clear,'glyphTriangles':glyphs,'finite':True})
(R/'output/tiantan-gates/geometry-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
