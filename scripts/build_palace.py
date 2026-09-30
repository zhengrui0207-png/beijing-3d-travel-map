"""Build a georeferenced, artist-authored Forbidden City asset with 2 streamed LODs.
OSM building/roof-part outlines anchor the scene; decorative architectural details
and surface reconstruction are illustrative, not a survey or conservation record.
Run with Blender CLI --background --python scripts/build_palace.py.
"""
import sys, pathlib, json, math, os, random, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'public/assets/palace'; OUT.mkdir(parents=True,exist_ok=True)
LAYOUT=ROOT/'data/palace-layout.json'
SX=111320*math.cos(math.radians(39.915))/100; SY=111320/100
BBOX=[116.3864,39.9114,116.3955,39.9212]
def xy(lon,lat):return ((lon-116.415)*SX,(lat-39.915)*SY)
def num(v,default=0):
 try:return float(str(v).split()[0])
 except:return default

def prepare():
 from shapely.geometry import Polygon,LineString,box,Point
 from shapely import make_valid, constrained_delaunay_triangles
 from shapely.ops import unary_union
 from shapely.strtree import STRtree
 from shapely.geometry.polygon import orient
 from shapely.affinity import affine_transform
 raw=json.loads((ROOT/'data/osm_beijing.json').read_text())['elements']
 bounds=[*xy(BBOX[0],BBOX[1]),*xy(BBOX[2],BBOX[3])]; clip=box(*bounds)
 splitN=xy(116.39,39.9180)[1];splitS=xy(116.39,39.9142)[1]
 splitW=xy(116.3899,39.91)[0];splitE=xy(116.39175,39.91)[0]
 zones={'south':[bounds[0],bounds[1],bounds[2],splitS], 'central':[splitW,splitS,splitE,splitN], 'north-west':[bounds[0],splitN,splitW,bounds[3]], 'north-central':[splitW,splitN,splitE,bounds[3]], 'north-east':[splitE,splitN,bounds[2],bounds[3]],'west':[bounds[0],splitS,splitW,splitN], 'east':[splitE,splitS,bounds[2],splitN]}
 def polys(g):
  if g.is_empty:return []
  if g.geom_type=='Polygon':return [g]
  return [p for a in getattr(g,'geoms',[]) for p in polys(a)]
 def poly(e):
  if e['type']=='way':
   g=e.get('geometry',[])
   return make_valid(Polygon([xy(p['lon'],p['lat']) for p in g])) if len(g)>3 and g[0]==g[-1] else Polygon()
  from shapely.ops import polygonize
  outer=[];inner=[]
  for m in e.get('members',[]):
   g=m.get('geometry',[])
   if len(g)>1:(inner if m.get('role')=='inner' else outer).append(LineString([xy(p['lon'],p['lat']) for p in g]))
  return unary_union(list(polygonize(outer))).difference(unary_union(list(polygonize(inner))))
 def triangles(p):
  result=[]
  for t in constrained_delaunay_triangles(p).geoms:
   c=list(t.exterior.coords)[:3];a,b,d=c
   if (b[0]-a[0])*(d[1]-a[1])-(b[1]-a[1])*(d[0]-a[0])<0:c.reverse()
   result.append(c)
  return result
 def shape(p):
  p=orient(p,sign=1.0);cs=list(p.minimum_rotated_rectangle.exterior.coords)[:4]
  a,b,c,d=cs;w=math.dist(a,b);dep=math.dist(b,c)
  if w<dep:a,b,c,d=b,c,d,a;w,dep=dep,w
  ux=(b[0]-a[0])/w;uy=(b[1]-a[1])/w;ct=p.minimum_rotated_rectangle.centroid
  return {'center':[ct.x,ct.y],'w':w,'d':dep,'u':[ux,uy],'boundary':list(p.exterior.coords)[:-1],'triangles':triangles(p),'area':p.area}
 # Stone courses follow the actual palace axis, about 1.37 degrees from north.
 pu,pv=.99971264,.02397148
 def paving_panels(p):
  local=affine_transform(p,[pu,pv,-pv,pu,0,0]);left,bottom,right,top=local.bounds;panels=[]
  for row in range(math.floor(bottom/.012),math.ceil(top/.012)):
   offset=.009*(row%2)
   for col in range(math.floor((left-offset)/.018),math.ceil((right-offset)/.018)):
    a=col*.018+offset;b=row*.012
    cell=local.intersection(box(a+.00010,b+.00010,a+.01790,b+.01190))
    for q in polys(cell):
     if q.area<.0000005:continue
     world=affine_transform(q,[pu,-pv,pv,pu,0,0]);panels.extend(triangles(world))
  return panels
 entries=[];greens=[];water=[];waterlines=[];paths=[];bridges=[];water_sources=[];path_sources=[]
 member_ids={m['ref'] for e in raw if e['type']=='relation' for m in e.get('members',[]) if m.get('type')=='way'}
 for e in raw:
  t=e.get('tags',{})
  # Linear rivers and paths are independent of area relations. Culverts remain
  # underground, and a polyline must never accidentally become a filled polygon.
  if e['type']=='way' and len(e.get('geometry',[]))>1:
   line=LineString([xy(p['lon'],p['lat']) for p in e['geometry']])
   if line.intersects(clip) and t.get('tunnel') not in ['yes','culvert'] and num(t.get('layer'))>=0:
    if t.get('waterway') in ['river','canal','stream','drain'] and t.get('covered')!='yes':
     width=num(t.get('width'),4 if t['waterway'] in ['drain','stream'] else 8)
     waterlines.append((e['id'],line.intersection(clip),width/200))
    if t.get('highway') in ['footway','pedestrian','path','steps','service','cycleway']:
     width=num(t.get('width'),4.5 if t['highway']=='service' else 2)
     paths.append(line.buffer(width/200,cap_style=2).intersection(clip));path_sources.append(e['id'])
     if t.get('bridge')=='yes' or t.get('name')=='断虹桥':
      bridges.append({'id':e['id'],'line':list(line.coords),'width':num(t.get('width'),5.8 if e['id']==41439020 else 3.8 if t.get('name')=='内金水桥' else 3)/100,'humpback':t.get('bridge:structure')=='humpback','zone':None})
  if not any(k in t for k in ['building','building:part','leisure','natural','landuse']):continue
  if e['type']=='way' and e['id'] in member_ids:continue
  try:g=poly(e)
  except:continue
  if g.is_empty or not g.intersects(clip):continue
  if 'building' in t or 'building:part' in t:
   if not clip.contains(g.centroid):continue
   for p in polys(g):
    if p.area>.000008:entries.append((e,p))
  elif t.get('natural')=='water' or 'water' in t:water.extend(polys(g.intersection(clip)));water_sources.append(e['id'])
  elif t.get('leisure') in ['garden','park'] or t.get('natural') in ['wood','tree_row'] or t.get('landuse') in ['grass','forest']:greens.extend(polys(g.intersection(clip)))
 parts=[p for e,p in entries if 'building:part'in e['tags']];tree=STRtree(parts)
 named=[(e,p) for e,p in entries if e['tags'].get('name') and 'building:part' not in e['tags']]
 def zone_for(p):
  x,y=p.centroid.x,p.centroid.y
  return 'south' if y<splitS else ('north-west' if x<splitW else 'north-east' if x>splitE else 'north-central') if y>splitN else 'west' if x<splitW else 'east' if x>splitE else 'central'
 records=[];occupancy=[]
 for e,p in entries:
  t=e['tags'];ispart='building:part'in t
  if not ispart:
   sub=[parts[int(i)] for i in tree.query(p,predicate='intersects')]
   if sub and unary_union(sub).intersection(p).area>p.area*.65:continue
  rec=shape(p);rec.update(id=e['id'],tags=t,zone=zone_for(p))
  owner=t.get('name','')
  if ispart:
   for ne,np in named:
    if np.contains(p.centroid):owner=ne['tags']['name'];break
  rec['owner']=owner;rec['hero']=owner in ['太和殿','中和殿','保和殿','太和门','乾清宫','交泰殿','坤宁宫','午门','神武门']
  if (t.get('building:material')=='stone' or t.get('roof:material')=='stone') and t.get('roof:shape')!='skillion' and p.area>.012:
   rec['pavingPanels']=paving_panels(p)
  records.append(rec);occupancy.append(p)
 # Three Great Halls: terrace parts extend well beyond each hall's own footprint.
 terrace_groups={};stair_polys=[]
 for rec in records:
  t=rec['tags'];cx,cy=rec['center'];stone=t.get('building:material')=='stone' or t.get('roof:material')=='stone'
  rec['terraceSet']=stone and -21.28<cx<-20.05 and .12<cy<2.80 and num(t.get('height')) in [3,6,9]
  if rec['terraceSet']:
   pp=Polygon(rec['boundary'])
   if t.get('roof:shape')=='skillion':stair_polys.append(pp)
   else:terrace_groups.setdefault(num(t.get('height')),[]).append(pp)
 stair_mask=unary_union(stair_polys).buffer(.006)
 terraces=[]
 for level,ps in terrace_groups.items():
  combined=unary_union(ps)
  line=combined.boundary.difference(stair_mask)
  for seg in ([line] if line.geom_type=='LineString' else line.geoms):
   cs=list(seg.coords)
   for a,b in zip(cs,cs[1:]):
    if math.dist(a,b)>.012:terraces.append({'a':list(a),'b':list(b),'z':level/100+.011,'zone':'central'})
 water=unary_union(water)
 # Mapped bank outlines take precedence. Buffer only uncovered open channel
 # centre-lines, so an estimated width never widens the surveyed OSM outline.
 polygon_water=water
 for source,line,radius in waterlines:
  missing=line.difference(polygon_water.buffer(.03))
  if not missing.is_empty:water=water.union(missing.buffer(radius,cap_style=2,join_style=2));water_sources.append(source)
 water=water.intersection(clip)
 bridges=[b for b in bridges if water.intersects(LineString(b['line']))]
 for b in bridges:b['zone']=zone_for(LineString(b['line']))
 mapped_paths=unary_union(paths);green=unary_union(greens).difference(water).difference(mapped_paths)
 occupied=unary_union(occupancy).buffer(.045)
 # Plant only mapped gardens. Retain OSM path gaps, leave clear lawns, and
 # concentrate mature crowns towards walls and water rather than a uniform grid.
 random.seed(8813);trees=[]
 planting=green.difference(occupied).difference(mapped_paths.buffer(.024))
 for p in polys(planting):
  for _ in range(min(3200,int(p.area*90))):
   x=random.uniform(p.bounds[0],p.bounds[2]);y=random.uniform(p.bounds[1],p.bounds[3]);pt=Point(x,y)
   if not p.contains(pt):continue
   edge=min(pt.distance(occupied),pt.distance(water));density=.52+.35*math.exp(-edge/.22)
   if random.random()>density:continue
   if all((x-t[0])**2+(y-t[1])**2>.0058 for t in trees):
    trees.append([x,y,random.uniform(.077,.128),random.uniform(.135,.22)])
 # Banks use exactly the exterior/interior water boundaries; clipping into
 # zones must not produce artificial walls across the river at zone seams.
 banks=water.buffer(.0045,join_style=2).difference(water).intersection(clip)
 boundary=water.boundary.intersection(clip.buffer(-.00001))
 def lines(g):
  if g.is_empty:return []
  if g.geom_type=='LineString':return [g]
  return [p for a in getattr(g,'geoms',[]) for p in lines(a)]
 zone_surfaces={}
 # Broad, axial paving fields describe coherent courts. They are surface
 # appearance zones, not additional roads or invented architectural boundaries.
 def axis_box(left,bottom,right,top):return affine_transform(box(left,bottom,right,top),[pu,-pv,pv,pu,0,0])
 axis_center=-20.65043*pu+.99698*pv
 paving_fields=[('Courtyard_Axis',axis_box(axis_center-.13,-5,axis_center+.13,8)),('Courtyard_Cool',axis_box(axis_center+.13,-5,axis_center+1.3,8)),('Courtyard_Warm',axis_box(axis_center-1.3,-5,axis_center-.13,8))]
 for zone,b in zones.items():
  area=box(*b);zone_surfaces[zone]={'ground':triangles(area.difference(water)), 'green':[tri for p in polys(green.intersection(area)) for tri in triangles(p)],'water':[tri for p in polys(water.intersection(area)) for tri in triangles(p)],'bankTops':[tri for p in polys(banks.intersection(area)) for tri in triangles(p)],'bankLines':[list(seg.coords) for seg in lines(boundary.intersection(area))],'trees':[t for t in trees if area.covers(Point(t[0],t[1]))]}
  zone_surfaces[zone]['pavingFields']=[{'material':name,'triangles':[tri for p in polys(field.intersection(area).difference(water)) for tri in triangles(p)]}for name,field in paving_fields]
  zone_surfaces[zone]['ground']=[tri for p in polys(area.difference(water).difference(unary_union([field for name,field in paving_fields]))) for tri in triangles(p)]
 canopy=unary_union([Point(t[0],t[1]).buffer(t[2]*.68+.01) for t in trees]).intersection(green)
 landscape={'treeCount':len(trees),'mappedGreenAreaM2':round(green.area*10000),'canopyFootprintM2':round(canopy.area*10000),'waterSourceIds':sorted(set(water_sources)),'pathSourceCount':len(path_sources),'bridgeSourceIds':[b['id'] for b in bridges],'estimatedChannelWidthMetres':4,'notes':'Water polygons, open waterway centre-lines and bridge positions are cached OSM; unmapped channel/bridge widths, bank masonry and planting are illustrative. Culverts are excluded. Planting preserves mapped path gaps.'}
 LAYOUT.write_text(json.dumps({'bounds':bounds,'zones':zones,'records':records,'surfaces':zone_surfaces,'terraces':terraces,'landscape':landscape,'bridges':bridges},ensure_ascii=False))
 print('PREPARED',len(records),'parts,',len(trees),'trees',flush=True)

if '--prepare' in sys.argv:
 prepare();sys.exit(0)
import bpy
from mathutils import Vector
subprocess.run([str(ROOT.parent/'.venv-beijing/bin/python'),str(pathlib.Path(__file__)),'--prepare'],check=True)
data=json.loads(LAYOUT.read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
COLORS={
 'Roof_Glazed_Ochre':((.69,.40,.105),.47), 'Roof_Ridge_Highlight':((.82,.53,.16),.46),
 'Vermilion':((.37,.073,.035),.81), 'Painted_Timber':((.045,.17,.135),.70),
 'Painted_Azure':((.036,.17,.235),.63), 'Limestone':((.62,.61,.52),.91),
 'Courtyard_Stone':((.275,.30,.285),.94), 'Timber_Shadow':((.073,.04,.024),.9),
 'Terrace_Paving':((.44,.465,.445),.94), 'Courtyard_Axis':((.405,.425,.405),.92),
 'Courtyard_Cool':((.315,.34,.345),.96), 'Courtyard_Warm':((.365,.35,.32),.95),
 'Bronze_Gold':((.29,.23,.10),.45), 'Garden_Green':((.14,.22,.105),1),
 'Foliage_Leaves':((.24,.36,.17),.93), 'Water_Jade':((.09,.17,.20),.32)}
MATERIALS={}
for name,(col,rough) in COLORS.items():
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough
 m.diffuse_color=(*col,1);m['uv_units']='metres';m['appearance']='artist-authored reconstruction';MATERIALS[name]=m

class Batch:
 def __init__(self):self.parts={};self.tiles_only=False;self.emitting_tiles=False
 def face(self,mat,points,smooth=False,uvs=None):
  if len(points)<3 or (self.tiles_only and not self.emitting_tiles):return
  vs,fs,ss,us=self.parts.setdefault(mat,([],[],[],[]));start=len(vs);vs.extend(points);fs.append(tuple(range(start,start+len(points))));ss.append(smooth)
  if uvs is None:
   a,b,c=map(Vector,points[:3]);n=(b-a).cross(c-a);axis=max(range(3),key=lambda i:abs(n[i]));others=[i for i in range(3) if i!=axis];uvs=[(p[others[0]]*100,p[others[1]]*100) for p in points]
  us.extend(uvs)
 def box(self,mat,c,w,d,h,u=(1,0),bevel=0):
  x,y,z=c;ux,uy=u;v=(-uy,ux)
  pts=[(x+ux*dx*w/2+v[0]*dy*d/2,y+uy*dx*w/2+v[1]*dy*d/2,z+dz*h/2) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  for ids in [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]:self.face(mat,[pts[i] for i in ids])
 def paving(self,mat,points):
  self.face(mat,points,False,[((x*.99971264+y*.02397148)*100,(-x*.02397148+y*.99971264)*100)for x,y,z in points])
 def tube(self,mat,path,r,sides=5):
  if len(path)<2:return
  rings=[]
  for i,p in enumerate(path):
   a=Vector(path[max(0,i-1)]);b=Vector(path[min(len(path)-1,i+1)]);t=(b-a).normalized();q=t.cross(Vector((0,0,1)))
   if q.length<.01:q=Vector((1,0,0))
   q.normalize();s=t.cross(q).normalized();rings.append([tuple(Vector(p)+r*(math.cos(k*math.tau/sides)*q+math.sin(k*math.tau/sides)*s)) for k in range(sides)])
  for a,b in zip(rings,rings[1:]):
   for j in range(sides):self.face(mat,[a[j],a[(j+1)%sides],b[(j+1)%sides],b[j]],True)
 def tile_roll(self,path,r=.0011,segments=6):
  # Only the exposed semicylinder is needed. Its circular section, closed ends
  # and continuous arc-length UV remove square tubes, open holes and face seams.
  if len(path)<2:return
  rings=[];distances=[0]
  for i,p in enumerate(path):
   if i:distances.append(distances[-1]+math.dist(path[i-1],p))
   tangent=(Vector(path[min(i+1,len(path)-1)])-Vector(path[max(0,i-1)])).normalized()
   side=Vector((-tangent.y,tangent.x,0)).normalized();normal=tangent.cross(side).normalized()
   rings.append([tuple(Vector(p)+side*(math.cos(k*math.pi/segments)*r)+normal*(math.sin(k*math.pi/segments)*r))for k in range(segments+1)])
  for i,(a,b) in enumerate(zip(rings,rings[1:])):
   for j in range(segments):
    self.face('Roof_Glazed_Ochre',[a[j],a[j+1],b[j+1],b[j]],True,[(j*math.pi*r/segments*100,distances[i]*100),((j+1)*math.pi*r/segments*100,distances[i]*100),((j+1)*math.pi*r/segments*100,distances[i+1]*100),(j*math.pi*r/segments*100,distances[i+1]*100)])
  self.face('Roof_Glazed_Ochre',list(reversed(rings[0])),False,[(j/segments,0)for j in reversed(range(segments+1))])
  self.face('Roof_Glazed_Ochre',rings[-1],False,[(j/segments,1)for j in range(segments+1)])
 def lathe(self,mat,x,y,levels,n=8):
  rings=[[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),z) for i in range(n)] for z,r in levels]
  for a,b in zip(rings,rings[1:]):
   for j in range(n):self.face(mat,[a[j],a[(j+1)%n],b[(j+1)%n],b[j]],True)
  self.face(mat,list(reversed(rings[0])));self.face(mat,rings[-1])
 def create(self,zone,lod):
  obs=[]
  for name,(vs,fs,ss,us) in self.parts.items():
   if not vs:continue
   # Weld shared positions before calculating smooth normals and GLB indices.
   unique=[];mapped={};indices=[]
   for v in vs:
    key=tuple(round(c,7) for c in v)
    if key not in mapped:mapped[key]=len(unique);unique.append(v)
    indices.append(mapped[key])
   fs=[tuple(indices[i] for i in f) for f in fs]
   me=bpy.data.meshes.new(zone+'_'+lod+'_'+name);me.from_pydata(unique,[],fs);me.update();me.materials.append(MATERIALS[name]);uv=me.uv_layers.new(name='UVMap')
   uv.data.foreach_set('uv',[c for pair in us for c in pair])
   for p,s in zip(me.polygons,ss):p.use_smooth=s
   me.validate(verbose=False,clean_customdata=False);me.update()
   ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob);ob['zone']=zone;ob['lod']=lod;ob['layer']='palace_detail';ob['uvUnits']='metres';obs.append(ob)
  return obs

def subdiv_tri(tri,maxedge,depth=0):
 a,b,c=tri
 if depth>5 or max(math.dist(a,b),math.dist(b,c),math.dist(c,a))<maxedge:return [tri]
 ab=((a[0]+b[0])/2,(a[1]+b[1])/2);bc=((b[0]+c[0])/2,(b[1]+c[1])/2);ca=((c[0]+a[0])/2,(c[1]+a[1])/2)
 return [t for sub in [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)] for t in subdiv_tri(sub,maxedge,depth+1)]
def curved_tri(tri,height,tolerance,depth=0):
 a,b,c=tri;edges=[(a,b,c),(b,c,a),(c,a,b)];errors=[]
 for p,q,_ in edges:
  m=((p[0]+q[0])/2,(p[1]+q[1])/2);errors.append(abs(height(*m)-(height(*p)+height(*q))/2))
 index=max(range(3),key=lambda i:errors[i])
 if depth>=11 or errors[index]<tolerance:return [tri]
 p,q,r=edges[index];m=((p[0]+q[0])/2,(p[1]+q[1])/2)
 return curved_tri((p,m,r),height,tolerance,depth+1)+curved_tri((m,q,r),height,tolerance,depth+1)

def inside(x,y,poly):
 odd=False;j=len(poly)-1
 for i in range(len(poly)):
  a,b=poly[i],poly[j]
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:odd=not odd
  j=i
 return odd

def build_roof(B,r,eave,rise,shape,hi):
 x,y=r['center'];w,d=r['w'],r['d'];ux,uy=r['u'];vx,vy=-uy,ux;hero=r['hero'];boundary=r['boundary'];t=r['tags'];ridge=max(0,w*.5-d*.5)
 if shape=='pyramidal':ridge=0
 def local(a,b):return ((a-x)*ux+(b-y)*uy,(a-x)*vx+(b-y)*vy)
 direction=math.radians(num(t.get('roof:direction'),180));ds=(math.sin(direction),math.cos(direction));dots=[p[0]*ds[0]+p[1]*ds[1] for p in boundary];lo,high=min(dots),max(dots)
 def profile(t):
  t=max(0,min(1,t));return (1-t)**1.23+.018*t**12
 def height(a,b):
  px,py=local(a,b)
  if shape=='skillion':rr=(a*ds[0]+b*ds[1]-lo)/max(.00001,high-lo)
  elif shape=='gabled':rr=abs(py)/max(.002,d/2)
  else:rr=max(abs(py)/max(.002,d/2),max(0,abs(px)-ridge)/max(.002,w*.5-ridge))
  corner=(abs(px)/max(.002,w/2))**10*(abs(py)/max(.002,d/2))**10 if shape not in ['skillion','gabled'] else 0
  return eave+rise*profile(rr)+(0.003 if hero else 0.0015)*corner
 def emit_roof(local_points):
  ps=[]
  for px,py in local_points:
   a=x+ux*px+vx*py;b=y+uy*px+vy*py;p=(a,b,height(a,b))
   if not ps or math.dist(p,ps[-1])>1e-8:ps.append(p)
  if len(ps)>2 and math.dist(ps[0],ps[-1])<1e-8:ps.pop()
  if len(ps)<3:return
  signed=sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(ps,ps[1:]+ps[:1]))
  if signed<0:ps.reverse()
  B.face('Roof_Glazed_Ochre',ps,True,[(local(a,b)[0]*100,local(a,b)[1]*100) for a,b,z in ps])
 rectangular=r['area']/max(.00001,w*d)>.92
 if rectangular and shape in ['hipped','pyramidal','gabled']:
  slopes=28 if hi and hero else 10 if hi else 8 if hero else 4
  along=12 if hi and hero else 4
  for sign in [-1,1]:
   for j in range(slopes):
    t0=1-(1-j/slopes)**2;t1=1-(1-(j+1)/slopes)**2
    for k in range(along):
     a=-1+2*k/along;b=-1+2*(k+1)/along
     ex0=w/2 if shape=='gabled' else ridge+(w/2-ridge)*t0;ex1=w/2 if shape=='gabled' else ridge+(w/2-ridge)*t1
     emit_roof([(a*ex0,sign*d/2*t0),(b*ex0,sign*d/2*t0),(b*ex1,sign*d/2*t1),(a*ex1,sign*d/2*t1)])
  if shape!='gabled':
   for sign in [-1,1]:
    for j in range(slopes):
     t0=1-(1-j/slopes)**2;t1=1-(1-(j+1)/slopes)**2
     for k in range(along):
      a=-1+2*k/along;b=-1+2*(k+1)/along
      emit_roof([(sign*(ridge+(w/2-ridge)*t0),a*d/2*t0),(sign*(ridge+(w/2-ridge)*t1),a*d/2*t1),(sign*(ridge+(w/2-ridge)*t1),b*d/2*t1),(sign*(ridge+(w/2-ridge)*t0),b*d/2*t0)])
 else:
  tolerance=.00012 if hi and hero else .0003 if hi else .0018
  for tri in r['triangles']:
   for sub in curved_tri(tri,height,tolerance):B.face('Roof_Glazed_Ochre',[(a,b,height(a,b)) for a,b in sub],True,[(local(a,b)[0]*100,local(a,b)[1]*100) for a,b in sub])
 # Fascia follows every source outline; edges are sculpted along the curved skin.
 for a,b in zip(boundary,boundary[1:]+boundary[:1]):
  n=max(1,int(math.dist(a,b)/.07)) if hi else (3 if hero else 1);path=[(a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n,0) for j in range(n+1)];path=[(px,py,height(px,py)-.002) for px,py,pz in path]
  B.tube('Roof_Ridge_Highlight',path,.0018 if not hero else .0025,5)
  if hero and min(p[2] for p in path)<eave+rise*.25:
   # Exposed eaves have a ceramic edge above the deep painted fascia. These
   # continuous strips thicken the existing roof without changing its footprint.
   for pa,pb in zip(path,path[1:]):
    if (pa[2]+pb[2])/2>eave+rise*.32:continue
    for mat,low,high in [('Roof_Glazed_Ochre',-.002,.002),('Painted_Timber',-.008,-.002),('Painted_Azure',-.0064,-.0046)]:
     B.face(mat,[(pa[0],pa[1],pa[2]+low),(pb[0],pb[1],pb[2]+low),(pb[0],pb[1],pb[2]+high),(pa[0],pa[1],pa[2]+high)])
   if hi:
    count=max(2,int(math.dist(a,b)/.012))
    for k in range(count):
     f=(k+.5)/count;px=a[0]+(b[0]-a[0])*f;py=a[1]+(b[1]-a[1])*f;zz=height(px,py)
     if zz>eave+rise*.20:continue
     inward=Vector((x-px,y-py,0)).normalized()*.007
     B.tube('Painted_Timber',[(px,py,zz-.004),(px+inward.x,py+inward.y,zz-.009)],.00085,5)
 # Roof tile rolls follow each slope and meet a continuous capped hip.
 B.emitting_tiles=True
 def local_path(points,radius=.0010):
  path=[]
  for px,py in points:
   xx=x+ux*px+vx*py;yy=y+uy*px+vy*py;path.append((xx,yy,height(xx,yy)+.00045))
  if len(path)>1:B.tile_roll(path,radius,6 if hero else 5)
 if hi and w*d>.0002 and B.tiles_only:
  step=.005 if hero else .004
  if rectangular and shape in ['hipped','pyramidal','gabled']:
   nrows=min(900,max(2,math.ceil(w/step)));ribsegments=12 if hero else 5
   for k in range(1,nrows):
    px=-w/2+w*k/nrows;tstart=0 if shape=='gabled' else max(0,(abs(px)-ridge)/max(.002,w/2-ridge))
    for sign in [-1,1]:local_path([(px,sign*d/2*(tstart+(1-tstart)*(1-(1-j/ribsegments)**2))) for j in range(ribsegments+1)])
   if shape!='gabled':
    nrows=min(900,max(2,math.ceil(d/step)))
    for k in range(1,nrows):
     py=-d/2+d*k/nrows;tstart=abs(py)/(d/2)
     for sign in [-1,1]:
      local_path([(sign*(ridge+(w/2-ridge)*(tstart+(1-tstart)*(1-(1-j/ribsegments)**2))),py) for j in range(ribsegments+1)])
  else:
   if shape=='skillion':cx,cy=-ds[1],ds[0];across=[p[0]*cx+p[1]*cy for p in boundary];amin,amax=min(across),max(across);smin,smax=lo,high
   else:cx,cy=ux,uy;ds=(vx,vy);across=[p[0]*cx+p[1]*cy for p in boundary];amin,amax=min(across),max(across);along=[p[0]*ds[0]+p[1]*ds[1] for p in boundary];smin,smax=min(along),max(along)
   count=min(900,max(2,math.ceil((amax-amin)/step)))
   for k in range(1,count):
    aa=amin+(amax-amin)*k/count;cuts=[]
    for pa,pb in zip(boundary,boundary[1:]+boundary[:1]):
     qa=pa[0]*cx+pa[1]*cy;qb=pb[0]*cx+pb[1]*cy
     if (qa<=aa<qb) or (qb<=aa<qa):
      f=(aa-qa)/(qb-qa);px=pa[0]+(pb[0]-pa[0])*f;py=pa[1]+(pb[1]-pa[1])*f;cuts.append(px*ds[0]+py*ds[1])
    cuts.sort()
    for lo_s,hi_s in zip(cuts[::2],cuts[1::2]):
     n=max(4,min(16,math.ceil((hi_s-lo_s)/.025)));path=[]
     for j in range(n+1):
      ss=lo_s+(hi_s-lo_s)*(1-(1-j/n)**2);px=cx*aa+ds[0]*ss;py=cy*aa+ds[1]*ss;path.append((px,py,height(px,py)+.00045))
     B.tile_roll(path,.0010 if hero else .0011,6 if hero else 5)
 B.emitting_tiles=False
 if rectangular and shape in ['hipped','pyramidal']:
  for sx in [-1,1]:
   for sy in [-1,1]:
    path=[]
    hip_segments=16 if hi else 3
    for j in range(hip_segments+1):
     tt=j/hip_segments;px=sx*(ridge+(w/2-ridge)*tt);py=sy*d/2*tt;xx=x+ux*px+vx*py;yy=y+uy*px+vy*py;path.append((xx,yy,height(xx,yy)+.002))
    B.tube('Roof_Ridge_Highlight',path,.0024 if hero else .0015,6 if hi else 3)
 if shape not in ['skillion','flat'] and w>.055:
  # Main ridge and upturned chiwen ends, with layered scale silhouettes.
  rr=w*.43 if shape=='gabled' else ridge
  segments=14 if hi else 3
  path=[(x+ux*s,y+uy*s,eave+rise+.0015+.004*(abs(s)/max(.00001,rr))**8) for s in [(-rr+2*rr*i/segments) for i in range(segments+1)]]
  B.tube('Roof_Ridge_Highlight',path,.003 if hero else .0019,6)
  if hi and hero:
   for sign in [-1,1]:
    px=x+sign*ux*rr;py=y+sign*uy*rr;z=eave+rise
    # Curled dragon-tail ridge ornaments: smoothly changing cross section, not box ornaments.
    curve=[(px+sign*ux*a,py+sign*uy*a,z+b) for a,b in [(0,0),(.007,.006),(.010,.018),(.007,.027),(-.001,.030),(-.004,.024)]]
    B.tube('Roof_Ridge_Highlight',curve,.0035,7)
    for j in range(4):B.tube('Roof_Ridge_Highlight',[(px+sign*ux*.009,py+sign*uy*.009,z+.011+j*.004),(px+sign*ux*(.015-j*.001),py+sign*uy*(.015-j*.001),z+.014+j*.004)],.0014,5)
 return height

def railing(B,a,b,z,hi,open_center=False):
 length=math.dist(a,b)
 if length<.008:return
 n=max(1,int(length/(.019 if hi else .029)));dx=(b[0]-a[0])/n;dy=(b[1]-a[1])/n;ux=(b[0]-a[0])/length;uy=(b[1]-a[1])/length
 for i in range(n+1):
  x=a[0]+dx*i;y=a[1]+dy*i
  B.lathe('Limestone',x,y,[(z,.0028),(z+.0022,.0018),(z+.010,.0017),(z+.0107,.0025),(z+.0124,.0027),(z+.0151,.0006)],6 if hi else 4)
 for i in range(n):
  aa=(a[0]+dx*i,a[1]+dy*i,z+.0102);bb=(aa[0]+dx,aa[1]+dy,z+.0102);cc=((aa[0]+bb[0])/2,(aa[1]+bb[1])/2);width=math.hypot(dx,dy)
  B.box('Limestone',(cc[0],cc[1],z+.0052),max(.003,width-.003),.0016,.0058,(ux,uy))
  B.tube('Limestone',[aa,bb],.0015,6 if hi else 4)
  B.tube('Limestone',[(aa[0],aa[1],z+.0016),(bb[0],bb[1],z+.0016)],.0014,4)
  if hi:
   # A shallow ribbon relief keeps carved cloud motifs without subpixel tubes.
   for side in [-1,1]:
    c=(cc[0]-uy*side*.00105,cc[1]+ux*side*.00105)
    for sign in [-1,1]:
     path=[]
     for k in range(7):
      theta=math.pi*.35+math.pi*1.8*k/6;rr=.0016*(1-k/10);h=sign*(width*.19+math.cos(theta)*rr);v=math.sin(theta)*rr
      path.append((h,v))
     for pa,pb in zip(path,path[1:]):
      points=[]
      for hh,vv in [(pa[0],pa[1]-.0003),(pb[0],pb[1]-.0003),(pb[0],pb[1]+.0003),(pa[0],pa[1]+.0003)]:points.append((c[0]+ux*hh,c[1]+uy*hh,z+.0054+vv))
      B.face('Limestone',points)
    # Central lozenge projects 3cm from the stone panel.
    center=(c[0]-uy*side*.0003,c[1]+ux*side*.0003,z+.0053)
    corners=[(c[0]+ux*hh,c[1]+uy*hh,z+.0053+vv) for hh,vv in [(0,.0025),(.003,0),(0,-.0025),(-.003,0)]]
    for j in range(4):B.face('Limestone',[corners[j],corners[(j+1)%4],center])


def facade(B,r,bottom,top,hi):
 x,y=r['center'];w,d=r['w'],r['d'];ux,uy=r['u'];vx,vy=-uy,ux;hero=r['hero'];h=top-bottom
 # Local interface adjustment: keep Taihe columns and beams fixed while seating
 # the illustrative upper brackets below TRNKL's independently curved roof.
 bracket_drop=.0023 if r['id']==638449353 else 0
 if h<.018 or d<.025 or w<.04:return
 bays=11 if r['id']==638449346 else max(3,min(21,int(w/(.055 if hero else .045))));spacing=w/(bays if hero else bays+1);rad=.006 if hero else .003
 for side in [-1,1]:
  for i in (range(bays+1) if hero else range(1,bays+1)):
   xx=-w/2+spacing*i;px=x+ux*xx+vx*side*d*.50;py=y+uy*xx+vy*side*d*.50
   B.lathe('Vermilion',px,py,[(bottom,rad*1.14),(bottom+.003,rad*1.14),(bottom+.007,rad*.86),(top-.004,rad*.73),(top,rad*.86)],10 if hi else 6)
   B.lathe('Limestone',px,py,[(bottom-.004,rad*1.45),(bottom+.001,rad*1.45),(bottom+.004,rad*1.1)],8 if hi else 5)
   if hi:
    # Dougong brackets: three nested cantilever blocks under the eave.
    for j in range(3):
     B.box('Painted_Timber',(px+vx*side*.002*j,py+vy*side*.002*j,top-.004+j*.004-bracket_drop),.012+j*.007,.008+j*.005,.0035,(ux,uy))
    B.box('Painted_Azure',(px,py,top-.009),spacing*.70,.003,.006,(ux,uy))
  # Deep shadow panels behind the detached red colonnade keep the timber legible.
  z=bottom+h*.52;pyoff=side*d*.37
  B.box('Timber_Shadow',(x+vx*pyoff,y+vy*pyoff,z),w*.92,.002,h*.71,(ux,uy))
  for j in range(bays):
   xx=-w*.46+w*.92*(j+.5)/bays;px=x+ux*xx+vx*(pyoff+side*.002);py=y+uy*xx+vy*(pyoff+side*.002)
   B.box('Vermilion',(px,py,bottom+h*.29),w*.86/bays,.002,h*.19,(ux,uy))
   if hi:
    for k in range(4):
     x2=xx+(k-1.5)*w*.75/bays/4;B.box('Painted_Timber',(x+ux*x2+vx*(pyoff+side*.002),y+uy*x2+vy*(pyoff+side*.002),bottom+h*.66),.001,.002,h*.35,(ux,uy))
    for k in range(3):B.box('Painted_Timber',(px,py,bottom+h*(.51+k*.13)),w*.84/bays,.002,.001,(ux,uy))
  B.box('Painted_Timber',(x+vx*side*d*.5,y+vy*side*d*.5,top-.005),w,.008,.012,(ux,uy))
  B.box('Painted_Azure',(x+vx*side*d*.508,y+vy*side*d*.508,top-.006),w,.001,.004,(ux,uy))
 # Hero halls have a continuous gallery around the short ends as well. The
 # existing source footprint fixes its outer column line and upper beam course.
 if hero:
  sidebays=5 if r['id']==638449346 else max(2,round(d/.066));ds=d/sidebays
  for side in [-1,1]:
   for i in range(1,sidebays):
    yy=-d/2+ds*i;px=x+ux*side*w/2+vx*yy;py=y+uy*side*w/2+vy*yy
    B.lathe('Vermilion',px,py,[(bottom,rad*1.14),(bottom+.007,rad*.86),(top-.004,rad*.73),(top,rad*.86)],10 if hi else 6)
    B.lathe('Limestone',px,py,[(bottom-.004,rad*1.45),(bottom+.001,rad*1.45),(bottom+.004,rad*1.1)],8 if hi else 5)
    if hi:
     for j in range(3):B.box('Painted_Timber',(px+ux*side*.002*j,py+uy*side*.002*j,top-.004+j*.004-bracket_drop),.012+j*.007,.008+j*.005,.0035,(vx,vy))
   B.box('Painted_Timber',(x+ux*side*w/2,y+uy*side*w/2,top-.005),d,.008,.012,(vx,vy))
   B.box('Painted_Azure',(x+ux*side*(w/2+.004),y+uy*side*(w/2+.004),top-.006),d,.001,.004,(vx,vy))


def solid(B,r,bottom,top,mat,hi):
 if top-bottom<.0002:return
 if mat=='Limestone' and r.get('pavingPanels'):
  # The mapped slab elevation stays exact. Recessed mortar makes joints without
  # raising the architectural platform or applying a noisy global displacement.
  for tri in r['triangles']:B.paving('Courtyard_Stone',[(a,b,top-.00015)for a,b in tri])
  for tri in r['pavingPanels']:B.paving('Terrace_Paving',[(a,b,top)for a,b in tri])
 else:
  for tri in r['triangles']:B.face(mat,[(a,b,top) for a,b in tri])
 poly=r['boundary']
 for a,b in zip(poly,poly[1:]+poly[:1]):B.face(mat,[(a[0],a[1],bottom),(b[0],b[1],bottom),(b[0],b[1],top),(a[0],a[1],top)])
 if mat=='Limestone' and r['hero'] and not r.get('terraceSet') and r['area']>.04 and top>.021:
  for a,b in zip(poly,poly[1:]+poly[:1]):
   if math.dist(a,b)>.11:railing(B,a,b,top+.001,hi,False)

def part_elevations(r):
 t=r['tags'];wall=t.get('building')=='wall';stone=t.get('building:material')=='stone' or t.get('roof:material')=='stone'
 height=num(t.get('height'),7 if wall else 10 if 'building:part'in t else 8)
 minimum=num(t.get('min_height'));rh=num(t.get('roof:height'),min(4,max(.8,r['d']*100*.26)))
 if r['owner']=='太和殿' and not stone:
  # Official hall-body height overrides the conflicting crowd-sourced 41m tag.
  # Keep the connected OSM terrace at 9m; normalize every structural tier above
  # that fixed anchor together, avoiding an individually floating scaled hall.
  if r['id']==638449346:minimum=9
  elif r['id']==638449353:minimum=24
  ratio=26.92/(41-9)
  if height>9:height=9+(height-9)*ratio
  if minimum>9:minimum=9+(minimum-9)*ratio
  rh*=ratio
 return height/100,max(.011,minimum/100+.011),rh/100


def build_part(B,r,hi):
 t=r['tags'];w,d=r['w'],r['d'];x,y=r['center'];shape=t.get('roof:shape');stone=t.get('building:material')=='stone' or t.get('roof:material')=='stone';wall=t.get('building')=='wall'
 hero=r['hero'];height,bottom,rh=part_elevations(r);top=height+.011
 if shape and not stone:roofbase=max(bottom,top-rh)
 elif not shape and not stone and 'building:part' not in t:shape='gabled' if w>2*d else 'hipped';rh=min(.07,max(.016,d*.32));roofbase=top
 else:roofbase=top
 mat='Limestone' if stone else 'Vermilion'
 if stone and shape=='skillion':
  # Source stone ramps retain their mapped outline and slope. On the two central
  # imperial flights, stairs flank a carved inclined stone rather than crossing it.
  angle=math.radians(num(t.get('roof:direction'),180));ds=(math.sin(angle),math.cos(angle));dsums=[a*ds[0]+b*ds[1] for a,b in r['boundary']];mi,ma=min(dsums),max(dsums);base=max(.011,top-rh)
  # Intersect each stair tread with its measured ramp boundary.
  cross=(-ds[1],ds[0]);points=[(a*cross[0]+b*cross[1],a*ds[0]+b*ds[1]) for a,b in r['boundary']];steps=22 if hi else 10
  imperial=r['id'] in [638449442,638467897];middle=(min(p[0]for p in points)+max(p[0]for p in points))/2;panel_width=min(.034,r['d']*.36)
  for j in range(steps):
   al=mi+(ma-mi)*j/steps;bl=mi+(ma-mi)*(j+1)/steps;sm=(al+bl)/2;ints=[]
   for aa,bb in zip(points,points[1:]+points[:1]):
    if (aa[1]<=sm<bb[1]) or (bb[1]<=sm<aa[1]):ints.append(aa[0]+(bb[0]-aa[0])*(sm-aa[1])/(bb[1]-aa[1]))
   if len(ints)<2:continue
   lo,high=min(ints),max(ints);cc=(lo+high)/2;level=base+rh*(1-j/steps);px=cross[0]*cc+ds[0]*sm;py=cross[1]*cc+ds[1]*sm
   for cl,ch in ([(lo,middle-panel_width/2),(middle+panel_width/2,high)] if imperial else [(lo,high)]):
    if ch<=cl:continue
    center=(cl+ch)/2;px=cross[0]*center+ds[0]*sm;py=cross[1]*center+ds[1]*sm
    B.box('Limestone',(px,py,(base+level)/2),ch-cl,bl-al,max(.001,level-base),cross)
  if imperial:
   def on_slab(across,along,raise_z=0):return (cross[0]*across+ds[0]*along,cross[1]*across+ds[1]*along,base+rh*(1-(along-mi)/(ma-mi))+.0008+raise_z)
   B.face('Limestone',[on_slab(middle-panel_width/2,ma),on_slab(middle+panel_width/2,ma),on_slab(middle+panel_width/2,mi),on_slab(middle-panel_width/2,mi)])
   for sign in [-1,1]:B.tube('Limestone',[on_slab(middle+sign*(panel_width/2-.0015),mi),on_slab(middle+sign*(panel_width/2-.0015),ma)],.0012,6 if hi else 4)
   if hi:
    # Low-relief cloud and curling dragon compositions are artistic relief,
    # explicitly not a digitization of the historic carved stone surface.
    for k in range(9):
     center=mi+(ma-mi)*(.07+.105*k);extent=(ma-mi)*.042
     body=[on_slab(middle+math.sin(j/18*math.tau*1.4)*panel_width*.19,center+(j/18-.5)*extent*1.7,.0009) for j in range(19)]
     B.tube('Limestone',body,.0011,6)
     for sign in [-1,1]:
      for row in [-1,1]:
       path=[]
       for j in range(13):
        a=j/12*math.tau*1.2;rr=.0035*(1-j/18)
        path.append(on_slab(middle+sign*panel_width*.29+math.cos(a)*rr,center+row*extent*.42+math.sin(a)*rr,.0006))
       B.tube('Limestone',path,.00065,5)
     for j in range(3,17,3):
      q=body[j];side=-1 if j%2 else 1;B.tube('Limestone',[q,(q[0]+cross[0]*side*.0035,q[1]+cross[1]*side*.0035,q[2]+.0006)],.0006,5)
  return
 if roofbase>bottom+.001:
  # Structural core is inset behind its column gallery.
  if not stone and hero and not shape and w>.15 and d>.1:
   inner=dict(r);inner['boundary']=[(x+(a-x)*.76,y+(b-y)*.76) for a,b in r['boundary']];inner['triangles']=[[(x+(a-x)*.76,y+(b-y)*.76) for a,b in tr] for tr in r['triangles']]
   solid(B,inner,bottom,roofbase,mat,hi);facade(B,r,bottom if r['id'] in [638449346,638449353] else max(bottom,roofbase-.12),roofbase,hi)
  else:
   solid(B,r,bottom,roofbase,mat,hi)
   if not stone and not wall and w>.095 and d>.04 and (hi or hero):facade(B,r,max(bottom,roofbase-.075),roofbase,hi and hero)
 if shape and not stone:build_roof(B,r,roofbase,rh,shape,hi)
 # Thin wall coping: dark brick plinth and tile edge, with no invented large roof.
 if wall and not stone:
  for a,b in zip(r['boundary'],r['boundary'][1:]+r['boundary'][:1]):
   if math.dist(a,b)>.03:B.tube('Limestone',[(a[0],a[1],.026),(b[0],b[1],.026)],.002,4)


def bridge_mesh(B,bridge,hi):
 line=bridge['line'];w=bridge['width'];lengths=[0]
 for a,b in zip(line,line[1:]):lengths.append(lengths[-1]+math.dist(a,b))
 length=lengths[-1]
 if length<.012:return
 count=max(5,math.ceil(length/(.019 if hi else .028)))
 def point(t,side):
  d=t*length;i=next((i for i in range(len(line)-1) if lengths[i+1]>=d),len(line)-2);a,b=line[i],line[i+1];f=(d-lengths[i])/max(.00001,lengths[i+1]-lengths[i]);dx=b[0]-a[0];dy=b[1]-a[1];n=math.hypot(dx,dy)
  return (a[0]+dx*f-dy/n*side*w/2,a[1]+dy*f+dx/n*side*w/2,.011+(.017 if bridge['humpback'] else .004)*math.sin(math.pi*t))
 left=[point(k/count,-1) for k in range(count+1)];right=[point(k/count,1) for k in range(count+1)]
 for a,b,c,d in zip(left,left[1:],right[1:],right):
  B.face('Limestone',[a,b,c,d])
  for p,q in [(a,b),(c,d)]:B.face('Limestone',[(p[0],p[1],p[2]-.005),(q[0],q[1],q[2]-.005),q,p])
 for edge in [left,right]:
  for p in edge:
   x,y,z=p;B.lathe('Limestone',x,y,[(z,.0023),(z+.009,.0017),(z+.010,.0025),(z+.013,.0006)],6 if hi else 4)
  B.tube('Limestone',[(x,y,z+.0097) for x,y,z in edge],.0015,6 if hi else 4)
  for p,q in zip(edge,edge[1:]):
   B.face('Limestone',[(p[0],p[1],p[2]+.0015),(q[0],q[1],q[2]+.0015),(q[0],q[1],q[2]+.0083),(p[0],p[1],p[2]+.0083)])


def tree_mesh(B,t,hi):
 x,y,r,h=t;seed=int((x+40)*1e5+y*1e4);rng=random.Random(seed);crown=r*.68;bend=(rng.random()-.5)*.014
 trunk=[(x,y,.011),(x+bend*.3,y,.011+h*.35),(x+bend,y+.006,.011+h*.65),(x+bend*.8,y+.004,.011+h*.82)]
 B.tube('Timber_Shadow',trunk,.004,7 if hi else 5)
 clusters=[]
 # Eight asymmetric main branches fork into overlapping leafy volumes. Leaves
 # fill branch interiors as well as ends; there is no star of isolated ray tips.
 for j in range(8):
  angle=j*2.399963+rng.uniform(-.28,.28);level=.43+rng.random()*.20
  start=(x+bend*level,y,.011+h*level);mr=crown*(.28+rng.random()*.10)
  mid=(x+math.cos(angle)*mr,y+math.sin(angle)*mr,.011+h*(level+.13))
  B.tube('Timber_Shadow',[start,mid],.0018,6 if hi else 4)
  for k in range(2):
   theta=angle+(-1 if k==0 else 1)*(.24+rng.random()*.32);rr=crown*(.55+rng.random()*.24)
   end=(x+math.cos(theta)*rr,y+math.sin(theta)*rr,.011+h*(.64+rng.random()*.22))
   elbow=tuple(mid[a]*.45+end[a]*.55 for a in range(3));B.tube('Timber_Shadow',[mid,elbow,end],.0011,5 if hi else 4)
   clusters.append((end,elbow,crown*(.20+rng.random()*.065)))
 # Overlapping upper/interior clusters bridge the forks into one mature canopy.
 for k in range(4):
  angle=k*2.399963+.7;rr=crown*(.12+rng.random()*.28)
  end=(x+math.cos(angle)*rr,y+math.sin(angle)*rr,.011+h*(.79+rng.random()*.09))
  clusters.append((end,trunk[-2],crown*.25))
 for index,(center,branch,spread) in enumerate(clusters):
  samples=range(18) if hi else [0,3,6,9,12,15]
  for k in samples:
   cr=random.Random(seed+index*727+k*37);dx=max(-1.15,min(1.15,cr.gauss(0,.58)))*spread;dy=max(-1.15,min(1.15,cr.gauss(0,.58)))*spread
   px=center[0]+dx;py=center[1]+dy;distance=math.hypot(px-x,py-y);limit=crown-.009
   if distance>limit:px=x+(px-x)*limit/distance;py=y+(py-y)*limit/distance
   pz=max(.011+h*.53,min(.011+h*.95,center[2]+cr.gauss(0,.48)*spread*.9))
   size=(.031+cr.random()*.009)*(1 if hi else 1.12);yaw=cr.random()*math.tau;tilt=.30+cr.random()*1.15
   u=Vector((math.cos(yaw),math.sin(yaw),0));v=Vector((-math.sin(yaw)*math.cos(tilt),math.cos(yaw)*math.cos(tilt),math.sin(tilt)));c=Vector((px,py,pz))
   points=[tuple(c+u*dx*size/2+v*dy*size*.57)for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
   B.face('Foliage_Leaves',points,False,[(0,0),(1,0),(1,1),(0,1)])
   if hi and k%6==0:B.tube('Timber_Shadow',[branch,(px,py,pz)],.00045,4)

manifest={'version':1,'id':'forbidden-city','coordinateSystem':'local east/north in 100 metre units; glTF Y up','origin':[116.415,39.915],'replacementBounds':data['bounds'],'uvUnits':'metres','groundZ':0.008,'structureBaseZ':0.011,'attribution':'© OpenStreetMap contributors, ODbL 1.0','accuracy':'OSM footprints with unverified crowd-sourced elevations; Taihe hall-body tiers are normalized to the Palace Museum official 26.92m body reference. Connected OSM terraces still use 9m rather than official 8.13m. Roof detailing, ornaments, timber, railings, vegetation and textures are artist-authored reconstruction, not measured heritage survey. The superseded OSM Taihe 41m tag is not a true measured height.','zones':[]}
all_high=[]
for zone,bounds in data['zones'].items():
 record={'id':zone,'bounds':bounds,'medium':zone+'-medium.glb','high':zone+'-high.glb','lods':{}}
 for lod in ['medium','high']:
  hi=lod=='high';B=Batch();surface=data['surfaces'][zone]
  for tri in surface['ground']:B.paving('Courtyard_Stone',[(x,y,.008) for x,y in tri])
  for field in surface['pavingFields']:
   for tri in field['triangles']:B.paving(field['material'],[(x,y,.008)for x,y in tri])
  for tri in surface['green']:B.face('Garden_Green',[(x,y,.012) for x,y in tri])
  for tri in surface['water']:B.face('Water_Jade',[(x,y,.004) for x,y in tri])
  for tri in surface['bankTops']:B.face('Courtyard_Stone',[(x,y,.014) for x,y in tri])
  for line in surface['bankLines']:
   for a,b in zip(line,line[1:]):
    B.face('Courtyard_Stone',[(a[0],a[1],.004),(b[0],b[1],.004),(b[0],b[1],.014),(a[0],a[1],.014)])
  for r in data['records']:
   if r['zone']==zone:build_part(B,r,hi)
  for segment in data.get('terraces',[]):
   if segment['zone']==zone:railing(B,segment['a'],segment['b'],segment['z']+.001,hi)
  for bridge in data.get('bridges',[]):
   if bridge['zone']==zone:bridge_mesh(B,bridge,hi)
  for t in surface['trees']:tree_mesh(B,t,hi)
  obs=B.create(zone,lod);bpy.ops.object.select_all(action='DESELECT')
  for o in obs:o.select_set(True)
  out=OUT/(zone+'-'+lod+'.glb')
  bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
  tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs);verts=sum(len(o.data.vertices) for o in obs)
  record['lods'][lod]={'triangles':tris,'vertices':verts,'drawCalls':len(obs),'bytes':out.stat().st_size};print(zone,lod,record['lods'][lod],flush=True)
  if hi:all_high.extend(obs)
  else:
   for o in obs:bpy.data.objects.remove(o,do_unlink=True)
 manifest['zones'].append(record)
# Micro roof overlays: all tile rolls, including hero halls, are near-view only.
# They are optional additions over the medium/high solid roof, never replacements.
micro_groups={}
for r in data['records']:
 t=r['tags'];stone=t.get('building:material')=='stone' or t.get('roof:material')=='stone'
 if stone or (not t.get('roof:shape') and 'building:part' in t) or t.get('roof:shape')=='flat':continue
 x,y=r['center'];ix=math.floor(x-data['bounds'][0]);iy=math.floor(y-data['bounds'][1]);micro_groups.setdefault((ix,iy),[]).append(r)
manifest['microTiles']=[]
micro_queue=[('roof-tiles-'+str(ix)+'-'+str(iy),records)for (ix,iy),records in sorted(micro_groups.items())]
while micro_queue:
 id,records=micro_queue.pop(0)
 B=Batch();B.tiles_only=True
 for r in records:
  t=r['tags'];wall=t.get('building')=='wall';shape=t.get('roof:shape');height,bottom,rh=part_elevations(r);top=height+.011
  if shape:roofbase=max(bottom,top-rh)
  else:shape='gabled' if r['w']>2*r['d'] else 'hipped';rh=min(.07,max(.016,r['d']*.32));roofbase=top
  build_roof(B,r,roofbase,rh,shape,True)
 obs=B.create(id,'micro')
 if not obs:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 out=OUT/(id+'.glb');bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
 if out.stat().st_size>16_000_000 and len(records)>1:
  # Keep every complete roof roll: subdivide spatial delivery, never decimate it.
  axis=max(range(2),key=lambda a:max(r['center'][a]for r in records)-min(r['center'][a]for r in records));ordered=sorted(records,key=lambda r:r['center'][axis]);middle=len(ordered)//2
  micro_queue[0:0]=[(id+'a',ordered[:middle]),(id+'b',ordered[middle:])]
  for o in obs:bpy.data.objects.remove(o,do_unlink=True)
  out.unlink();print('MICRO_SPLIT',id,len(records),flush=True);continue
 pts=[p for r in records for p in r['boundary']];bounds=[min(p[0]for p in pts),min(p[1]for p in pts),max(p[0]for p in pts),max(p[1]for p in pts)]
 triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs)
 spacings=sorted({.5 if r['hero'] else .4 for r in records})
 manifest['microTiles'].append({'id':id,'bounds':bounds,'url':out.name,'triangles':triangles,'bytes':out.stat().st_size,'tileSpacingMetres':0.4,'tileSpacingRangeMetres':spacings,'includesHero':any(r['hero']for r in records),'drawCalls':len(obs)})
 print('MICRO',id,triangles,out.stat().st_size,flush=True)
manifest['microDetailNotes']='All roof rolls, including 0.5m hero and 0.4m ancillary tiles, are optional close-view overlays in nominal 100m cells, recursively split below 16MB. Medium/high body LODs keep continuous roof surfaces, main/hip ridges and eave ornaments but no tile rolls, avoiding subpixel moire. Load micro only above ~300 projected pixels per 100m.'
manifest['heightCorrections']=[{'id':'taihe','sourceUrls':['https://www.dpm.org.cn/explore/building/236465.html','https://www.dpm.org.cn/Uploads/pdf/1602/T00092_00.pdf'],'verifiedDate':'2026-09-13','officialHallBodyMetres':26.92,'officialTerraceMetres':8.13,'officialTotalToRidgeMetres':35.05,'officialTotalIncludingFinialMetres':37.44,'osmPriorRoofDatumMetres':41,'retainedConnectedTerraceMetres':9,'normalizedNominalRoofDatumMetres':35.92,'remainingTerraceDifferenceMetres':.87,'bodyScaleAboveTerrace':26.92/32,'frontBays':11,'depthBays':5,'notes':'Wood core and both roof tiers are normalized together above a fixed 9m terrace. Lower gallery begins on that terrace; upper gallery begins above lower roof. Adjacent shared three-tier terraces are not independently rescaled. 35.92m is the normalized nominal roof datum, not a claim of measured finished height; authored ridge caps/finials extend above it and remain approximate. Global 1.1m presentation base offset is separate.'}]
manifest['foliage']={'material':'Foliage_Leaves','texture':'foliage.png','uvUnits':'0..1','mediumCardsPerTree':120,'highCardsPerTree':360}
manifest['surfaceMaterials']={'Terrace_Paving':{'texture':'marble.png','repeat':.25,'stonePanelMetres':[1.8,1.2],'jointMetres':.02},'Courtyard_Axis':{'texture':'courtyard-stone.png','repeat':.18},'Courtyard_Cool':{'texture':'courtyard-stone.png','repeat':.20},'Courtyard_Warm':{'texture':'courtyard-stone.png','repeat':.20},'uvNotes':'All paving UVs are in metres, rotated to the palace axis (~1.37 degrees). Terrace Paving has separate exact-height geometric panels; Limestone retains vertical masonry and white balustrades.'}
manifest['structuralRevision']='Separated axial paving fields and inset-joint terrace panels; continuously sampled semicylindrical roof rolls with arc-length UV and closed end faces; overlapping forked branch leaf volumes with unchanged planting positions.'
manifest['landscape']=data['landscape']
manifest['sourceRecordCount']=len(data['records']);manifest['totalHighTriangles']=sum(z['lods']['high']['triangles'] for z in manifest['zones'])
(OUT/'manifest.json.tmp').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));os.replace(OUT/'manifest.json.tmp',OUT/'manifest.json')
# Native Blender authoring file shares generated image maps, packed for portability.
# GLBs deliberately remain texture-free: the web renderer shares four image maps.
for matname,imagefile,scale,bump_distance in [('Courtyard_Stone','courtyard-stone.png',.25,.00035),('Courtyard_Axis','courtyard-stone.png',.18,.00025),('Courtyard_Cool','courtyard-stone.png',.20,.00025),('Courtyard_Warm','courtyard-stone.png',.20,.00025),('Terrace_Paving','marble.png',.25,.00015),('Limestone','marble.png',.25,.00018),('Roof_Glazed_Ochre','glazed-ochre.png',1,.00012)]:
 path=OUT/imagefile
 if not path.exists():continue
 m=MATERIALS[matname];nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);tex.image.pack();uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=scale;links.new(uv.outputs['UV'],mapping.inputs[0]);links.new(mapping.outputs['Vector'],tex.inputs['Vector'])
 if matname in ['Terrace_Paving','Courtyard_Axis','Courtyard_Cool','Courtyard_Warm']:
  tint={'Terrace_Paving':(.68,.70,.68,1),'Courtyard_Axis':(1.25,1.26,1.24,1),'Courtyard_Cool':(1.02,1.04,1.08,1),'Courtyard_Warm':(1.10,1.04,.96,1)}[matname]
  mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint;links.new(tex.outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color'])
 else:links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=bump_distance;links.new(tex.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
leaf_path=OUT/'foliage.png'
if leaf_path.exists():
 m=MATERIALS['Foliage_Leaves'];nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(leaf_path),check_existing=True);tex.image.pack();links.new(tex.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False
# Native authoring file includes every high-quality chunk at its true georeferenced position.
bpy.context.scene['Asset fidelity']=manifest['accuracy'];bpy.context.scene['Data attribution']=manifest['attribution']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'故宫精细建筑.blend'))
print('PALACE_LOD_BUILD_DONE',flush=True)
