"""Four ancillary buildings, on preserved OSM polygons; elevations inferred."""
import json,math

def create(P,mats,scene,field,root):
 import bpy
 from mathutils import Vector
 objs=[];entries=[]
 mats['brick']=P.mat('beihai annex grey brick',(.21,.205,.18),.92)
 mats['mortar']=P.mat('beihai annex masonry courses',(.29,.28,.25),.98)
 for spec in json.loads((root/'data/terrain/beihai-annexes.json').read_text()):
  B=P.Builder(True);r=spec['record'];cx,cy=r['center'];floor=1.1;eave=spec['eave'];pad=next(p for p in field['pads']if p['id']==r['id']);ground=.011+pad['height']
  for f in spec['roof']:B.face('yellow',f)
  for roll in spec['rolls']:
   a,b=roll['points'][0],roll['points'][-1];B.beam('green'if roll['edge']else'yellow',a,b,.052,6)
  def roof(x,y):
   heights=[]
   for a,b,c,d,axis in spec['arms']:
    if a-.03<=x<=c+.03 and b-.03<=y<=d+.03:
     width=c-a if axis=='y'else d-b;q=x if axis=='y'else y;mid=(a+c)/2 if axis=='y'else(b+d)/2
     t=max(0,1-abs(q-mid)/(width/2));heights.append(eave+.72*width/2*t**1.38)
   return max(heights,default=eave)
  ring=spec['walls'];signed=sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(ring,ring[1:]+ring[:1]));orientation=1 if signed>0 else-1
  for a,b in zip(ring,ring[1:]+ring[:1]):
   L=math.dist(a,b);u=((b[0]-a[0])/L,(b[1]-a[1])/L);n=(orientation*u[1],-orientation*u[0]);parts=max(2,math.ceil(L/.3))
   def pt(t,z,off=0):return(a[0]+u[0]*t+n[0]*off,a[1]+u[1]*t+n[1]*off,z)
   # Stone plinth and roof-height gable closure, following the concave outline.
   B.face('stone',[pt(0,floor),pt(L,floor),pt(L,floor+.35),pt(0,floor+.35)])
   for i in range(parts):
    t0,t1=L*i/parts,L*(i+1)/parts;q0,q1=pt(t0,0),pt(t1,0)
    B.face('brick',[pt(t0,floor+.35),pt(t1,floor+.35),pt(t1,roof(*q1[:2])-.08),pt(t0,roof(*q0[:2])-.08)])
   for z in [1.5,1.85,2.2,2.55,2.9,3.25,3.6]:B.beam('mortar',pt(0,z,.008),pt(L,z,.008),.009,4)
   bays=max(1,round(L/2.3));bay=L/bays
   for i in range(bays):
    middle=(i+.5)*bay;w=bay*.61;z0,z1=floor+.58,eave-.45
    B.face('shade',[pt(middle-w/2,z0,.022),pt(middle+w/2,z0,.022),pt(middle+w/2,z1,.022),pt(middle-w/2,z1,.022)])
    for t in [middle-w/2,middle+w/2]:B.beam('red',pt(t,z0,.055),pt(t,z1,.055),.07,6)
    for z in [z0,z1]:B.beam('red',pt(middle-w/2,z,.055),pt(middle+w/2,z,.055),.065,6)
    for j in range(5):
     t=middle-w*.40+j*w*.2;B.beam('gold',pt(t,z0+.16,.065),pt(t,z1-.1,.065),.017,4)
    for j in range(4):
     z=z0+.22+j*(z1-z0-.33)/3;B.beam('gold',pt(middle-w*.45,z,.065),pt(middle+w*.45,z,.065),.017,4)
  # Ridge crest follows the upper envelope, preventing hidden overlapping roofs.
  for a,b,c,d,axis in spec['arms']:
   start,end=((a+c)/2,b),((a+c)/2,d)
   if axis=='x':start,end=(a,(b+d)/2),(c,(b+d)/2)
   steps=math.ceil(math.dist(start,end)/.3)
   for j in range(steps):
    p=tuple(start[k]+(end[k]-start[k])*j/steps for k in range(2));q=tuple(start[k]+(end[k]-start[k])*(j+1)/steps for k in range(2))
    B.beam('green',(*p,roof(*p)+.1),(*q,roof(*q)+.1),.11,8)
  for key,(vs,fs,uvs)in B.groups.items():
   me=bpy.data.meshes.new(spec['name']+' '+key);me.from_pydata([(cx+x/100,cy+y/100,z/100+pad['height'])for x,y,z in vs],[],fs);me.update();me.materials.append(mats[key]);o=bpy.data.objects.new(spec['name']+' '+key,me);scene.collection.objects.link(o)
   o['layer']='buildings_urban_courtyard';o['osmId']=str(r['osmId']);o['groundHeight']=ground;o['islandLift']=True;o['templeReplacement']=True;objs.append(o)
  entries.append({'id':r['osmId'],'name':spec['name'],'rings':r['rings'],'bounds':r['bounds'],'heightMetresEstimated':spec['heightMetresEstimated'],'groundHeight':ground,'roofForm':'joined-gable'if len(r['rings'][0])>4 else'gable','role':'annex','fidelity':'Footprint from OSM; roof, height, facade layout inferred. Descriptive name, not verified historic identity.'})
 return objs,entries
