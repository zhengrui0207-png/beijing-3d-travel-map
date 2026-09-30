"""Photo-informed ancillary halls on the actual OSM footprints.
Seven identified Tiantan structures; ornament and untagged height remain inferred.
Photo: https://www.tiantanpark.cn/scenic_spot_list_g7yU_96/detail/1182.html
"""
import bpy, math, importlib.util, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
_spec=importlib.util.spec_from_file_location('temple_primitives',ROOT/'scripts/build_tiantan_detail.py')
P=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=P;_spec.loader.exec_module(P)
IDS={43921111,43921133,43921137,43921140,43921141,371497104,371497115}

def project(B,r,angle):
 co,si=math.cos(angle),math.sin(angle);cx,cy=r['center']
 for verts,faces,uvs in B.groups.values():
  for i,(x,y,z)in enumerate(verts):verts[i]=(cx*100+x*co-y*si,cy*100+x*si+y*co,z)
 return B

def dimensions(r):
 ring=r['rings'][0];edges=[(math.dist(a,b),a,b)for a,b in zip(ring,ring[1:]+ring[:1])]
 _,a,b=max(edges);angle=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(angle),math.sin(angle)
 xs=[x*co+y*si for x,y in ring];ys=[-x*si+y*co for x,y in ring]
 return (max(xs)-min(xs))*100,(max(ys)-min(ys))*100,angle

def geometry(r,detail=False):
 B=P.Builder(detail);L,D,angle=dimensions(r);h=r['height']*100;floor=1.1;plinth=.8;walltop=h*.62;roofbase=walltop+.4;peak=h+floor
 if r['osmId']==43921141:
  # Three separate glazed gates link the northern hall to the main courtyard.
  if not detail:
   w=L/3*.90;d=D*.85
   for center in [-L/3,0,L/3]:
    for sign in [-1,1]:B.box('red',(center+sign*w*.39,0,floor+1.6),(w*.22,d*.65,3.2))
    B.box('red',(center,0,floor+3.1),(w,d*.65,.45))
    for j in range(8):
     def ring(t):
      a=w/2-t*d*.35;b=max(.01,d/2*(1-t));z=floor+3.45+1.25*t**1.5
      return[(center-a,-b,z),(center+a,-b,z),(center+a,b,z),(center-a,b,z)]
     a,b=ring(j/8),ring((j+1)/8)
     for k in range(4):B.face('roof',[a[k],a[(k+1)%4],b[(k+1)%4],b[k]])
    B.beam('tile',(center-w*.22,0,floor+4.75),(center+w*.22,0,floor+4.75),.1,6)
  return project(B,r,angle)
 # Local x is long axis; roofs stay inside the mapped outer eave footprint.
 halfx=L/2;halfy=D/2;bodyx=halfx-.75;bodyy=halfy-1.15
 def profile(t):return roofbase+(peak-roofbase)*t**1.6+.10*math.exp(-t*22)
 if not detail:
  B.box('stone',(0,0,floor+plinth/2),(L-.2,D-.2,plinth))
  # Two broad stairs. Gate openings are actual voids between piers.
  for side in [-1,1]:
   for j in range(5):B.box('stone',(0,side*(halfy+.18+j*.28),floor+plinth*(5-j)/10),(min(6,L*.35),.29,plinth*(5-j)/5))
  if r['osmId']==43921137:
   for sign in [-1,1]:B.box('red',(sign*(bodyx-1.1),0,(floor+plinth+walltop)/2),(2.2,bodyy*2,walltop-floor-plinth))
   for x in [-L*.16,L*.16]:B.box('red',(x,0,(floor+plinth+walltop)/2),(1.0,bodyy*2,walltop-floor-plinth))
  else:B.box('redDark',(0,0,(floor+plinth+walltop)/2),(bodyx*2,bodyy*2,walltop-floor-plinth))
  rings=12
  for j in range(rings):
   t=j/rings;tt=(j+1)/rings
   def corners(t):
    a=halfx-t*halfy;b=max(.003,halfy*(1-t));return[(-a,-b,profile(t)),(a,-b,profile(t)),(a,b,profile(t)),(-a,b,profile(t))]
   a,b=corners(t),corners(tt)
   for k in range(4):B.face('roof',[a[k],a[(k+1)%4],b[(k+1)%4],b[k]])
  # Profiled eaves and ridge with upturned terminal tips.
  for sign in [-1,1]:
   B.box('roofEdge',(0,sign*halfy,roofbase),(L,.16,.20))
   B.box('jade',(0,sign*(halfy-.18),roofbase-.25),(L-.2,.22,.15))
  B.beam('tile',(-halfx+halfy,0,peak+.13),(halfx-halfy,0,peak+.13),.16,8)
  for sign in [-1,1]:
   x=sign*(halfx-halfy);B.beam('tile',(x,0,peak+.13),(x+sign*.4,0,peak+.65),.17,6)
 else:
  # Tile rolls follow every curved roof plane from the eave to the ridge.
  for side in range(4):
   span=L if side%2==0 else D;n=max(8,round(span/.38))
   for i in range(n):
    f=(i+.5)/n
    if side==0:p=(-halfx+L*f,-halfy)
    elif side==1:p=(halfx,-halfy+D*f)
    elif side==2:p=(halfx-L*f,halfy)
    else:p=(-halfx,halfy-D*f)
    end=(max(-halfx+halfy,min(halfx-halfy,p[0])),0)
    for j in range(10):
     def point(t):return (p[0]+(end[0]-p[0])*t,p[1]*(1-t),profile(t)+.035)
     B.beam('tile',point(j/10),point((j+1)/10),.045,5)
 # Column bays on both long elevations, repeated doors behind the colonnade.
 bays=9 if r['osmId']in [43921111,43921133]else 5
 for sign in [-1,1]:
  y=sign*(halfy-.68)
  if not detail:
   for i in range(bays+1):
    x=-bodyx+2*bodyx*i/bays;B.cylinder('red',.20,floor+plinth,walltop,10,center=(x,y))
   # Texture repeats per painted panel, not as one stretched strip.
   z0,z1=walltop-.65,walltop+.15
   pts=[(-bodyx,y,z0),(bodyx,y,z0),(bodyx,y,z1),(-bodyx,y,z1)]
   if sign>0:pts.reverse()
   B.face('frieze',pts,[(0,0),(bays,0),(bays,1),(0,1)])
  for i in range(bays):
   x=-bodyx+2*bodyx*(i+.5)/bays;w=2*bodyx/bays*.70
   if r['osmId']==43921137:continue
   z0,z1=floor+plinth+.1,walltop-.75
   if not detail:
    B.box('red',(x,sign*(bodyy+.015),(z0+z1)/2),(w,.055,z1-z0))
    B.box('shade',(x,sign*(bodyy+.05),(z0+z1)/2+.3),(w*.82,.025,max(.25,z1-z0-.9)))
   else:
    for j in range(7):B.box('woodGold',(x-w*.41+j*w*.82/6,sign*(bodyy+.08),(z0+z1)/2+.3),(.035,.055,max(.25,z1-z0-.9)))
    for j in range(5):B.box('woodGold',(x,sign*(bodyy+.09),z0+.6+j*max(.3,z1-z0-.95)/4),(w*.82,.05,.045))
 # Transform the entire building from its local axes into projected map coordinates.
 return project(B,r,angle)

def create(scene,records,detail=False):
 mats={
 'stone':P.mat('courtyard marble',(.7,.68,.62),.94,texture=ROOT/'public/assets/palace/marble.png'),
 'roof':P.mat('courtyard roof',(.016,.032,.065),.58),'tile':P.mat('courtyard tile',(.025,.045,.089),.53),
 'roofEdge':P.mat('courtyard eave',(.012,.027,.063),.62),'red':P.mat('courtyard pillars',(.33,.024,.018),.75),
 'redDark':P.mat('courtyard doors',(.20,.023,.016),.84),'jade':P.mat('courtyard bracket',(.035,.17,.13),.76),
 'woodGold':P.mat('courtyard lattice',(.34,.20,.054),.77),'shade':P.mat('courtyard recess',(.018,.015,.018),.94),
 'frieze':P.mat('courtyard frieze',(.03,.1,.2),.8,texture=ROOT/'public/assets/tiantan-detail/frieze.png')}
 objs=[]
 for r in records:
  if r['osmId']not in IDS:continue
  B=geometry(r,detail)
  for key,(vs,fs,uvs)in B.groups.items():
   me=bpy.data.meshes.new('Courtyard '+key);me.from_pydata([(x/100,y/100,z/100)for x,y,z in vs],[],fs);me.update()
   uv=me.uv_layers.new(name='Architecture')
   for poly,uvcoords in zip(me.polygons,uvs):
    for li,coord in zip(poly.loop_indices,uvcoords):uv.data[li].uv=coord
   me.materials.append(mats[key]);o=bpy.data.objects.new(f"Courtyard {r['osmId']} {key}",me);scene.collection.objects.link(o)
   o['layer']='buildings_urban_courtyard';o['osmId']=str(r['osmId']);o['groundHeight']=.011;objs.append(o)
 return objs
