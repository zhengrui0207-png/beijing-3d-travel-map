import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];P=json.loads((R/'data/circular-mound-plan.json').read_text());out=[]
for level in ['preview','detail']:
 s=bpy.data.scenes['Circular Mound '+level];bpy.context.window.scene=s;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();finite=all(math.isfinite(v)for o in s.objects for p in o.data.vertices for v in p.co);assert finite
 heights=[];z=0
 for t in P['tiers']:
  for j in range(4):
   a=j*math.pi/2
   for k in range(9):
    rr=t['radius']+P['stairs']['run']*(1-(k+.5)/9);hit=s.ray_cast(deps,Vector((rr*math.cos(a)/100,rr*math.sin(a)/100,.15)),Vector((0,0,-1)));expected=z+t['height']*(k+1)/9
    assert hit[0]and abs(hit[1].z*100-expected)<.003,(level,j,k,hit[1].z*100,expected)
    heights.append(round(hit[1].z*100,5))
  z+=t['height']
 center=s.ray_cast(deps,Vector((0,0,.15)),Vector((0,0,-1)));assert abs(center[1].z*100-5.178)<.002
 passages=[]
 for g in P['gates']:
  if g['existing']:continue
  ca,sa=math.cos(g['angle']),math.sin(g['angle']);cx=(g['center'][0]-P['center'][0]);cy=(g['center'][1]-P['center'][1]);clear=[]
  for sign in [-1,0,1]:
   x=(sign*g['length']*.34+.2)/100;y=-.022;o=Vector((cx+x*ca-y*sa,cy+x*sa+y*ca,.012));d=Vector((-sa,ca,0));clear.append(not s.ray_cast(deps,o,d,distance=.044)[0])
  expected=[True,True,True]if g['kind']=='inner'else[True,False,True];assert clear==expected,(g['osmId'],clear);passages.append({'osmId':g['osmId'],'clear':clear})
 out.append({'level':level,'finite':finite,'stairSamples':len(heights),'stairHeights':heights,'heartStoneTop':round(center[1].z*100,4),'passages':passages})
(R/'output/circular-mound/geometry-validation.json').write_text(json.dumps(out,indent=2));print('Validated',len(out)*108,'step surfaces and',len(out)*18,'gate passages')
