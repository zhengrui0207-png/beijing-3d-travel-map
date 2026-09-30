import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];p=json.loads((R/'data/echo-court-plan.json').read_text());results={}
for name in ['Echo Court preview','Echo Court detail','Imperial Vault detail']:
 s=bpy.data.scenes[name];bpy.context.window.scene=s;bpy.context.view_layer.update()
 assert all(math.isfinite(v)for o in s.objects if o.type=='MESH'for pt in o.data.vertices for v in pt.co)
 results[name]={'meshes':len(s.objects),'triangles':sum(len(f.vertices)-2 for o in s.objects if o.type=='MESH'for f in o.data.polygons)}
 if name.startswith('Echo Court'):
  g=next(a for a in p['parts']if a['osmId']==43921123);angle=g['angle'];ca,sa=math.cos(angle),math.sin(angle);pos=[(g['center'][i]-p['center'][i])*100 for i in range(2)];w=(g['length']-.8)/3;clear=[]
  for n in [-1,0,1]:
   xx=n*(w+.4);yy=-g['depth']/2-.05;origin=Vector(((pos[0]+ca*xx-sa*yy)/100,(pos[1]+sa*xx+ca*yy)/100,.015));direction=Vector((-sa,ca,0));hit=s.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,direction,distance=(g['depth']+.1)/100)[0];clear.append(not hit)
  assert all(clear),clear;results[name]['gatePassagesClear']=clear
 else:
  o=next(o for o in s.objects if o.type=='MESH'and o.name.startswith('Imperial Vault stone.')or o.name=='Imperial Vault stone');elevations={}
  for side in ['south','east','west']:
   levels=[]
   for i in range(14):
    r=13.65-(i+.5)*(4.15 if side=='south'else 3.55)/14;x,y=(2.2,-r)if side=='south'else(r*(1 if side=='east'else-1),0)
    hit,pt,normal,index=o.ray_cast(Vector((x/100,y/100,.10)),Vector((0,0,-1)))
    assert hit;h=pt.z*100;expected=(i+1)*2.2/14;assert abs(h-expected)<.002,(side,i,h,expected);levels.append(round(h,4))
   elevations[side]=levels
  results[name]['fourteenStepElevations']=elevations
(R/'output/echo-court/geometry-validation.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
