"""OSM stair axes/counts with SRTM-derived elevations, not surveyed stair heights."""
import math
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
OFFICIAL='https://gygl.beijing.gov.cn/mlgy/mlgy_gyjg01/201912/t20191211_1048483.html'
IDS={78058972,227116618,227116615,584742930,584742931}
def prepare(elements,sx,sy,height):
 stairs=[]
 for e in elements:
  if e.get('type')!='way' or e['id']not in IDS:continue
  xy=[((v['lon']-116.415)*sx,(v['lat']-39.915)*sy)for v in e['geometry']];line=LineString(xy)
  a,b=height(*xy[0]),height(*xy[-1])
  if a>b:xy.reverse();line=LineString(xy);a,b=b,a
  rawcount=e.get('tags',{}).get('step_count');n=72 if e['id']==227116615 else int(rawcount)if rawcount else max(3,round((b-a)*100/.15))
  width=5.0 if e['id']in[78058972,227116618,227116615]else 2.2
  stairs.append({'osmId':e['id'],'axis':xy,'count':n,'countSource':OFFICIAL if e['id']==227116615 else'OSM step_count'if rawcount else'estimated from terrain rise at about 15cm per step','osmStepCount':int(rawcount)if rawcount else None,'widthMetresEstimated':width,'bottomOffset':a,'topOffset':b,'lengthMetres':line.length*100,'riseMetresEstimated':(b-a)*100,'surface':'stone'if e['id']!=227116615 else'brick','sourceConflict':'Official park description: 72 brick steps; cached OSM: 70, metal. Official count/material used.'if e['id']==227116615 else None,'_line':line,'_poly':line.buffer(width/200,cap_style=2,join_style=2)})
 return stairs

def grade(x,y,base,stairs):
 p=Point(x,y)
 for s in stairs:
  distance=p.distance(s['_poly'])
  if distance>.012:continue
  along=s['_line'].project(p)/s['_line'].length
  h=s['bottomOffset']+(s['topOffset']-s['bottomOffset'])*along
  # Eased blend outside the stair foundation, preserving unrelated building pads.
  t=min(1,distance/.012);t=t*t*(3-2*t)
  return h*(1-t)+base*t
 return base

def mesh(stairs):
 groups={'steps_treads':[],'steps_risers':[],'steps_edges':[],'steps_rails':[]};specs=[]
 def face(key,pts):groups[key].append(pts)
 def beam(key,a,b,r,sides=6):
  # Cylindrical rod in a stable local frame, positions use 100m map units.
  u=[b[k]-a[k]for k in range(3)];length=math.sqrt(sum(x*x for x in u));u=[x/length for x in u]
  v=[-u[1],u[0],0]if abs(u[2])<.99 else[1,0,0];norm=math.sqrt(sum(x*x for x in v));v=[x/norm for x in v];w=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
  rings=[[[c[k]+r*(math.cos(j*math.tau/sides)*v[k]+math.sin(j*math.tau/sides)*w[k])for k in range(3)]for j in range(sides)]for c in[a,b]]
  for j in range(sides):face(key,[rings[0][j],rings[0][(j+1)%sides],rings[1][(j+1)%sides],rings[1][j]])
  face(key,list(reversed(rings[0])));face(key,rings[1])
 for s in stairs:
  line=s['_line'];n=s['count'];w=s['widthMetresEstimated']/200;dh=(s['topOffset']-s['bottomOffset'])/n;levels=[]
  def point(distance,side=0,z=None):
   p=line.interpolate(distance);pa=line.interpolate(max(0,distance-.0001));pb=line.interpolate(min(line.length,distance+.0001));dx,dy=pb.x-pa.x,pb.y-pa.y;L=math.hypot(dx,dy);return[p.x-dy/L*side,p.y+dx/L*side,z if z is not None else 0]
  for i in range(n):
   d0=line.length*i/n;d1=line.length*(i+1)/n;z=.0127+s['bottomOffset']+(i+1)*dh;prev=z-dh
   a,b,c,d=point(d0,-w,z),point(d1,-w,z),point(d1,w,z),point(d0,w,z)
   face('steps_treads',[a,b,c,d]);face('steps_risers',[[a[0],a[1],prev],a,d,[d[0],d[1],prev]])
   # Closed side skirt follows each tread and extends below graded terrain.
   for sign in[-1,1]:
    p,q=point(d0,sign*w,z),point(d1,sign*w,z);vertices=[p,q,[q[0],q[1],z-.006],[p[0],p[1],prev-.006]];face('steps_edges',vertices if sign>0 else list(reversed(vertices)))
   # Shallow tread joints avoid a perfectly uniform slab without dense texture.
   slabs=max(2,round(s['widthMetresEstimated']/.72))
   for j in range(1,slabs):
    side=-w+2*w*j/slabs;beam('steps_risers',point(d0,side,z+.000015),point(d1,side,z+.000015),.000025,4)
   levels.append(z)
  for sign in[-1,1]:
   divisions=math.ceil(line.length/.018)
   for j in range(divisions+1):
    dist=line.length*j/divisions;z=.0127+s['bottomOffset']+min(n,max(1,math.ceil(j/divisions*n)))*dh
    beam('steps_rails',point(dist,sign*(w-.002),z),point(dist,sign*(w-.002),z+.009),.00026)
   for j in range(divisions):
    for railheight in[.0048,.009]:
     d0=line.length*j/divisions;d1=line.length*(j+1)/divisions;z0=.0127+s['bottomOffset']+j/divisions*(s['topOffset']-s['bottomOffset'])+railheight;z1=.0127+s['bottomOffset']+(j+1)/divisions*(s['topOffset']-s['bottomOffset'])+railheight
     beam('steps_rails',point(d0,sign*(w-.002),z0),point(d1,sign*(w-.002),z1),.00028)
  specs.append({**{k:v for k,v in s.items()if not k.startswith('_')},'treadTopHeights':levels})
 return groups,specs
