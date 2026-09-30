"""Two tower terraces constrained by OSM paved loops; geometry is inferred.
The platform boundaries are not survey polygons. A shrine arch podium is modeled
from its OSM footprint and the published two-storey/arched-base description.
"""
import math
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles

def prepare(elements,pads,sx,sy):
 byid={e['id']:e for e in elements if e.get('type')=='way'};levels={p['id']:p['height']for p in pads};terraces=[]
 for ident,padid,label in [(584742928,'561193504','白塔上层平台'),(584742932,'1021040719','白塔下层平台')]:
  ring=[((v['lon']-116.415)*sx,(v['lat']-39.915)*sy)for v in byid[ident]['geometry']]
  poly=Polygon(ring).buffer(.009,join_style=2)
  terraces.append({'osmId':ident,'name':label,'ring':list(poly.exterior.coords),'heightOffset':levels[padid],'boundarySource':'inferred from OSM paved footway centreline, expanded 0.9m','_poly':poly})
 return terraces

def grade(x,y,base,terraces):
 p=Point(x,y)
 for t in terraces:
  if t['_poly'].covers(p):return t['heightOffset']
 return base

def triangles(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return list(constrained_delaunay_triangles(g).geoms)
 return [t for p in getattr(g,'geoms',[])for t in triangles(p)]

def mesh(terraces,stairs,ground,records):
 groups={'platform_stone':[],'platform_joints':[],'platform_walls':[]};stairmask=unary_union([s['_poly']for s in stairs]);covered=Polygon()
 def face(key,pts):groups[key].append(pts)
 def slab(poly,z):
  # Separate shallow joints and stone slabs, both following the same height field.

  x0,y0,x1,y1=poly.bounds;dx,dy=.012,.006
  for j in range(math.floor(y0/dy),math.ceil(y1/dy)):
   for i in range(math.floor(x0/dx)-1,math.ceil(x1/dx)+1):
    ox=(j%2)*dx*.5
    base=poly.intersection(box(i*dx+ox,j*dy,(i+1)*dx+ox,(j+1)*dy))
    for t in triangles(base):face('platform_joints',[[x,y,z(x,y)]for x,y in list(t.exterior.coords)[:3]])
    tile=poly.intersection(box(i*dx+ox+.00006,j*dy+.00006,(i+1)*dx+ox-.00006,(j+1)*dy-.00006))
    for t in triangles(tile):face('platform_stone',[[x,y,z(x,y)+.00007]for x,y in list(t.exterior.coords)[:3]])
 for index,t in enumerate(terraces):
  top=.0125+t['heightOffset'];poly=t['_poly'];slab(poly.difference(covered).difference(stairmask),lambda x,y:top);covered=covered.union(poly)
  edge=poly.boundary.difference(stairmask.buffer(.001))
  lines=[edge]if edge.geom_type=='LineString'else list(edge.geoms)
  for line in lines:
   pts=list(line.coords)
   for a,b in zip(pts,pts[1:]):
    n=max(1,math.ceil(math.dist(a,b)/.012))
    for i in range(n):
     p=[a[k]+(b[k]-a[k])*i/n for k in range(2)];q=[a[k]+(b[k]-a[k])*(i+1)/n for k in range(2)]
     low=(.0105+terraces[1]['heightOffset'])if index==0 else min(.0105+ground(*p),.0105+ground(*q),top-.007)
     wall=[[*p,low],[*q,low],[*q,top],[*p,top]];face('platform_walls',wall if poly.exterior.is_ccw else list(reversed(wall)))
 # The shrine stands on an arched podium in front of the upper terrace.
 # Its boundary follows the mapped shrine footprint, with inferred 0.5m margin.
 low=.0125+terraces[1]['heightOffset'];top=.011+terraces[0]['heightOffset']
 cx,cy=-27.3014,10.3500;hx,hy=.049,.031;radius=.010;spring=max(.002,top-low-.012)
 def pt(x,y,z):return[cx+x,cy+y,z]
 for sign in[-1,1]:
  x=sign*hx;face('platform_walls',[pt(x,-hy,low),pt(x,hy,low),pt(x,hy,top),pt(x,-hy,top)])
  y=sign*hy
  for a,b in[(-hx,-radius),(radius,hx)]:face('platform_walls',[pt(a,y,low),pt(b,y,low),pt(b,y,top),pt(a,y,top)])
  for i in range(24):
   x0=-radius+2*radius*i/24;x1=-radius+2*radius*(i+1)/24
   z0=low+spring+math.sqrt(max(0,radius*radius-x0*x0));z1=low+spring+math.sqrt(max(0,radius*radius-x1*x1))
   face('platform_walls',[pt(x0,y,z0),pt(x1,y,z1),pt(x1,y,top),pt(x0,y,top)])
 for i in range(24):
  a=math.pi*i/24;b=math.pi*(i+1)/24;x0,x1=radius*math.cos(a),radius*math.cos(b);z0,z1=low+spring+radius*math.sin(a),low+spring+radius*math.sin(b)
  face('platform_walls',[pt(x0,-hy,z0),pt(x0,hy,z0),pt(x1,hy,z1),pt(x1,-hy,z1)])
 for x in[-radius,radius]:face('platform_walls',[pt(x,-hy,low),pt(x,hy,low),pt(x,hy,low+spring),pt(x,-hy,low+spring)])
 face('platform_stone',[pt(-hx,-hy,top),pt(hx,-hy,top),pt(hx,hy,top),pt(-hx,hy,top)])
 # Inner temple court is constrained by the inner faces of the four surrounding halls.
 court=Polygon([(-27.41313,9.74228),(-27.27686,9.74228),(-27.22588,9.80473),(-27.22537,9.93698),(-27.40826,9.93397),(-27.41270,9.91394)])
 buildings=unary_union([Polygon(r['rings'][0],r['rings'][1:])for r in records if r.get('osmId')in[478118169,478118170,478118171,478118172]])
 court=court.difference(buildings)
 slab(court,lambda x,y:.0125+ground(x,y))
 return groups,{'ring':list(court.exterior.coords),'source':'inferred paved courtyard extent between mapped hall faces; grade follows coarse terrain','areaSquareMetres':court.area*10000},court
