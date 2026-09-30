"""Yuexin hall: OSM plan + official park architectural description, not survey.
Five bays, front/back galleries, grey-tile Xieshan roof, four-leaf centre doors.
"""
import json,math

def create(P,C,scene,field,root):
 import bpy
 r=next(r for r in json.loads((root/'data/urban/records.json').read_text())['records']if r['osmId']==478118173)
 pad=next(p for p in field['pads']if p['id']==r['id']);B=P.Builder(True);L,D,ang=C.dimensions(r)
 while ang>math.pi/2:ang-=math.pi
 while ang<-math.pi/2:ang+=math.pi
 hx,hy=L/2,D/2;floor=1.1;deck=floor+1.05;walltop=6.0;rb=6.3;peak=9.0
 bx,by=hx-.8,hy-1.6
 colors={'stone':(.55,.54,.49),'brick':(.22,.23,.21),'mortar':(.29,.30,.28),'red':(.28,.022,.012),'grey':(.095,.12,.125),'tile':(.14,.16,.16),'shade':(.009,.018,.019),'jade':(.023,.12,.075),'blue':(.017,.045,.09),'gold':(.48,.30,.055),'frieze':(.04,.09,.085),'plaque':(.012,.018,.018)}
 mats={k:P.mat('Yuexin '+k,c,.75 if k in ['grey','tile']else .85,texture=root/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else root/'public/assets/beihai-temples/yuexin-plaque.png'if k=='plaque'else root/'public/assets/palace/marble.png'if k=='stone'else None)for k,c in colors.items()}
 # Continuous raised base; front moon terrace extends beyond the eave footprint.
 front=-hy-4.0
 B.box('stone',(0,(front+hy-.25)/2,(deck+floor-2.2)/2),(L+.8,hy-.25-front,deck-floor+2.2))
 B.box('stone',(0,(front+hy-.25)/2,deck-.1),(L+1,hy-.25-front+.2,.2))
 # Paving courses over the terrace, avoiding duplicate coplanar surfaces.
 for j in range(5):B.box('mortar',(0,front+.7+j*.72,deck+.009),(L+.75,.016,.012))
 # Seven treads, documented by the park. Step width/run/rise inferred.
 for j in range(7):
  z=floor+1.05*(7-j)/7;y=front-.16-j*.30
  B.box('stone',(0,y,(floor+z)/2),(3.8,.315,z-floor))
 def railing(a,b,count,z):
  for j in range(count+1):
   f=j/count;x=a[0]+(b[0]-a[0])*f;y=a[1]+(b[1]-a[1])*f
   B.box('stone',(x,y,z+.54),(.22,.22,1.08));B.cylinder('stone',.15,z+1.07,z+1.27,8,.065,(x,y))
  for j in range(count):
   p=tuple(a[k]+(b[k]-a[k])*j/count for k in range(2));q=tuple(a[k]+(b[k]-a[k])*(j+1)/count for k in range(2))
   for zz in [.24,.84]:B.beam('stone',(*p,z+zz),(*q,z+zz),.07,6)
   for f in [.23,.50,.77]:
    x=p[0]+(q[0]-p[0])*f;y=p[1]+(q[1]-p[1])*f;B.box('stone',(x,y,z+.55),(.09,.09,.59))
 railing((-hx-.2,front+.1),(-2.0,front+.1),8,deck);railing((2.0,front+.1),(hx+.2,front+.1),8,deck)
 for sign in [-1,1]:
  railing((sign*(hx+.2),front+.1),(sign*(hx+.2),-hy+.6),5,deck)
  B.beam('stone',(sign*2,front-2.0,floor+1.1),(sign*2,front+.1,deck+1.1),.10,8)
 # Sides solid grey brick, long faces have recessed windows above knee walls.
 B.box('brick',(0,0,(deck+walltop)/2),(2*bx,2*by,walltop-deck))
 for sign in [-1,1]:
  y=sign*(hy-.58)
  for i in range(6):
   x=-bx+2*bx*i/5
   B.cylinder('red',.16,deck,walltop,16,center=(x,y));B.cylinder('stone',.22,deck,deck+.2,12,center=(x,y))
   B.box('blue',(x,y,walltop-.38),(.68,.7,.18));B.box('jade',(x,y,walltop-.16),(.90,.92,.14))
  for i in range(5):
   x=-bx+2*bx*(i+.5)/5;w=2*bx/5*.84;yy=sign*(by+.025);z0=deck+.85;z1=walltop-.62
   # Window muntins, with four full-height central door leaves.
   if i==2:z0=deck+.08
   B.box('shade',(x,yy,(z0+z1)/2),(w,.045,z1-z0))
   leaves=4 if i==2 else 3
   for k in range(leaves+1):B.box('red',(x-w/2+k*w/leaves,yy+sign*.04,(z0+z1)/2),(.065,.08,z1-z0+.1))
   for z in [z0,z1,z0+(z1-z0)*.35]:B.box('red',(x,yy+sign*.05,z),(w,.09,.075))
   for k in range(leaves):
    for zz in [z0+(z1-z0)*.57,z0+(z1-z0)*.80]:B.box('gold',(x-w/2+(k+.5)*w/leaves,yy+sign*.052,zz),(w/leaves-.065,.027,.016))
  for z in [deck+.23,deck+.48,deck+.72]:B.box('mortar',(0,sign*(by+.008),z),(2*bx,.016,.009))
  pts=[(-bx,y,walltop-.55),(bx,y,walltop-.55),(bx,y,walltop+.03),(-bx,y,walltop+.03)]
  if sign>0:pts.reverse()
  B.face('frieze',pts,[(0,0),(5,0),(5,1),(0,1)])
 # Xieshan: lower hipped skirt joins an upper gable without a tent/hip apex.
 join=.40;ridge=hx-hy*.54
 def section(t):return (hx-(hx-ridge)*min(t/join,1),hy*(1-t),rb+(peak-rb)*t**1.5)
 for sign in [-1,1]:
  for j in range(20):
   t,u=j/20,(j+1)/20;ax,ay,az=section(t);bx2,by2,bz=section(u)
   n=max(12,round(2*hx/.24))
   for i in range(n):
    f,g=-1+2*i/n,-1+2*(i+1)/n
    def pt(a,b,z,q,v):return(q*a,sign*b,z+.18*abs(q)**12*max(0,1-v/join)**3)
    pts=[pt(ax,ay,az,f,t),pt(ax,ay,az,g,t),pt(bx2,by2,bz,g,u),pt(bx2,by2,bz,f,u)];B.face('grey',pts if sign<0 else pts[::-1])
    q=(f+g)/2;p=pt(ax,ay,az+.027,q,t);q2=pt(bx2,by2,bz+.027,q,u);B.beam('tile',p,q2,.055,7)
  for i in range(n):
   x=-hx+2*hx*(i+.5)/n;B.beam('tile',(x,sign*hy,rb+.02),(x,sign*(hy+.06),rb-.10),.095,8)
  for j in range(8):
   t,u=join*j/8,join*(j+1)/8;ax,ay,az=section(t);bx2,by2,bz=section(u)
   pts=[(sign*ax,-ay,az+.18*(1-t/join)**3),(sign*ax,ay,az+.18*(1-t/join)**3),(sign*bx2,by2,bz+.18*(1-u/join)**3),(sign*bx2,-by2,bz+.18*(1-u/join)**3)];B.face('grey',pts if sign>0 else pts[::-1])
   for i in range(30):
    f=-1+2*(i+.5)/30;B.beam('tile',(sign*ax,f*ay,az+.04),(sign*bx2,f*by2,bz+.04),.055,6)
  _,yy,zz=section(join)
  x=sign*ridge;pts=[(x,-yy,zz),(x,yy,zz),(x,0,peak)];B.face('brick',pts if sign>0 else pts[::-1])
  for side in [-1,1]:
   for j in range(14):
    t=j/14;u=(j+1)/14
    B.beam('tile',(sign*ridge,side*yy*(1-t),zz+(peak-zz)*t**1.3+.07),(sign*ridge,side*yy*(1-u),zz+(peak-zz)*u**1.3+.07),.115,8)
 B.box('grey',(0,0,peak+.13),(2*ridge,.32,.26))
 for sign in [-1,1]:
  for j in range(6):B.beam('tile',(sign*(ridge+.04*j),0,peak+.14+.08*j),(sign*(ridge+.04*(j+1)),0,peak+.22+.08*j),.10,8)
 # Contemporary title text, generated here; no photo pixels or calligraphy copy.
 py=-(hy-.51);B.face('plaque',[(-1.25,py,walltop-.88),(1.25,py,walltop-.88),(1.25,py,walltop-.30),(-1.25,py,walltop-.30)],[(0,0),(1,0),(1,1),(0,1)])
 C.project(B,r,ang);objs=[]
 for key,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new('悦心殿 '+key);me.from_pydata([(x/100,y/100,z/100+pad['height'])for x,y,z in vs],[],fs);me.update();uv=me.uv_layers.new(name='Hall materials')
  for poly,coords in zip(me.polygons,uvs):
   for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
  me.materials.append(mats[key]);o=bpy.data.objects.new('悦心殿 '+key,me);scene.collection.objects.link(o)
  o['layer']='buildings_urban_courtyard';o['osmId']=str(r['osmId']);o['groundHeight']=.011+pad['height'];o['islandLift']=True;o['templeReplacement']=True;objs.append(o)
 entry={'id':r['osmId'],'name':'悦心殿','rings':r['rings'],'bounds':r['bounds'],'heightMetresEstimated':round(max(z for vs,fs,uvs in B.groups.values() for x,y,z in vs)-floor,3),'groundHeight':.011+pad['height'],'roofForm':'xieshan','role':'context-hall','bays':5,'frontSteps':7,'source':'https://gygl.beijing.gov.cn/whgy/whgy_wsgc/201912/t20191206_885733.html','fidelity':'Official description: five bays, grey barrel-tile Xieshan roof, front/back galleries, four centre door leaves, seven front steps. OSM footprint. Height, platform extent, stone carvings, ornament, windows, tile sizes inferred. Rear corridors not reconstructed.'}
 return objs,[entry]
