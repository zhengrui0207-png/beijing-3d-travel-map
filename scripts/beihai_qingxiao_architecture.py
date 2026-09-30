"""Qingxiao pavilion: two storeys / seven bays / upper gallery from Xicheng archive.
Roof and footprint from OSM; unmeasured proportions and ornament inferred.
No claim to reproduce an inspected photograph or historical painting.
"""
import json,math

def create(P,C,scene,field,root):
 import bpy
 r=next(r for r in json.loads((root/'data/urban/records.json').read_text())['records']if r['osmId']==262853255)
 pad=next(p for p in field['pads']if p['id']==r['id']);B=P.Builder(True);L,D,ang=C.dimensions(r)
 while ang>math.pi/2:ang-=math.pi
 while ang<-math.pi/2:ang+=math.pi
 hx,hy=L/2,D/2;floor=1.1;base=1.55;upper=5.25;eave=9.1;peak=12.2
 bx,by=hx-1.25,hy-1.45;bay=2*bx/7
 colors={'stone':(.43,.435,.40),'brick':(.22,.235,.22),'red':(.28,.032,.019),'roof':(.09,.115,.12),'tile':(.145,.16,.155),'blue':(.016,.058,.095),'jade':(.025,.14,.07),'gold':(.45,.27,.045),'shade':(.009,.017,.02),'frieze':(.03,.075,.09),'plaque':(.018,.018,.014)}
 mats={k:P.mat('Qingxiao '+k,v,.76 if k in ['roof','tile']else .85,texture=root/'public/assets/palace/marble.png'if k=='stone'else root/'public/assets/tiantan-detail/frieze.png'if k=='frieze'else root/'public/assets/beihai-temples/qingxiao-plaque.png'if k=='plaque'else None)for k,v in colors.items()}
 B.box('stone',(0,0,(base+floor-.7)/2),(L-.3,D-.3,base-floor+.7))
 B.box('stone',(0,0,base-.10),(L-.1,D-.1,.20))
 # Four broad entrance treads are estimated; no historical stair-count claim.
 for j in range(4):B.box('stone',(0,-hy-.15-j*.28,floor+(base-floor)*(4-j)/8),(3.3,.29,(base-floor)*(4-j)/4))
 # Enclosed cores remain behind both colonnades. Upper floor has an open gallery.
 for z0,z1 in [(base,4.2),(upper,eave-.3)]:
  B.box('brick',(0,0,(z0+z1)/2),(2*bx,2*by,z1-z0))
  for sign in [-1,1]:
   fronty=sign*(by+.02)
   for i in range(7):
    x=-bx+(i+.5)*bay;w=bay*.80;bottom=z0+.52 if i!=3 or z0==upper else z0+.04;top=z1-.45
    B.box('shade',(x,fronty,(bottom+top)/2),(w,.055,top-bottom))
    for u in range(5):B.box('red',(x-w/2+u*w/4,fronty+sign*.04,(bottom+top)/2),(.055,.08,top-bottom+.08))
    for z in [bottom,top,bottom+.35*(top-bottom)]:B.box('red',(x,fronty+sign*.05,z),(w+.05,.085,.07))
    # Narrow lattice above solid sill, rather than printed office-window squares.
    for u in range(9):B.box('gold',(x-w*.46+u*w*.92/8,fronty+sign*.054,(bottom+top)/2+.20),(.016,.025,max(.2,top-bottom-.60)))
    for u in range(4):B.box('gold',(x,fronty+sign*.054,bottom+.60+u*(top-bottom-.64)/4),(w*.94,.026,.017))
   coly=sign*(hy-.50)
   for i in range(8):
    x=-bx+bay*i;B.cylinder('red',.14,z0,z1+.22,14,center=(x,coly));B.cylinder('stone',.19,z0,z0+.15,12,center=(x,coly))
    for j in range(3):B.box('jade'if j%2 else'blue',(x,coly,z1-.35+j*.16),(.38+j*.15,.44+j*.16,.12))
   pts=[(-bx,coly,z1-.48),(bx,coly,z1-.48),(bx,coly,z1+.08),(-bx,coly,z1+.08)]
   if sign>0:pts.reverse()
   B.face('frieze',pts,[(0,0),(7,0),(7,1),(0,1)])
 B.box('brick',(0,0,(4.2+upper-.1)/2),(2*bx,2*by,upper-.1-4.2))
 # The flat balcony is above the waist eaves, with a genuine walkable-width gap.
 B.box('red',(0,0,upper-.10),(L-1.0,D-1.0,.20))
 for sign in [-1,1]:
  yy=sign*(hy-.56)
  for i in range(8):
   x=-bx+i*bay;B.box('red',(x,yy,upper+.46),(.12,.14,.92));B.cylinder('gold',.09,upper+.9,upper+1.0,8,.06,(x,yy))
  for z in [.18,.83]:B.beam('red',(-bx,yy,upper+z),(bx,yy,upper+z),.065,8)
  for i in range(7):
   x=-bx+(i+.5)*bay
   for j in range(5):B.box('red',(x-bay*.39+j*bay*.195,yy,upper+.5),(.045,.075,.6))
   B.box('jade',(x,yy-.002*sign,upper+.49),(bay*.86,.06,.055))
 # End galleries have the same guardrail and two slender roof supports.
 for sign in [-1,1]:
  x=sign*(hx-.52)
  for y in [-by,0,by]:
   B.cylinder('red',.14,upper,eave-.08,14,center=(x,y));B.box('red',(x,y,upper+.48),(.14,.14,.96))
  for z in [.2,.83]:B.beam('red',(x,-by,upper+z),(x,by,upper+z),.065,8)
  for j in range(18):B.box('red',(x,-by+2*by*(j+.5)/18,upper+.5),(.075,.045,.6))
 # Curved waist roof is an annulus, not a second solid pyramid through the floor.
 def rectpoint(side,f,xx,yy,z):
  if side==0:return(-xx+2*xx*f,-yy,z)
  if side==1:return(xx,-yy+2*yy*f,z)
  if side==2:return(xx-2*xx*f,yy,z)
  return(-xx,yy-2*yy*f,z)
 for side in range(4):
  n=max(16,round((L if side%2==0 else D)/.23))
  def lower(f,t):return rectpoint(side,f,hx-.08-(hx-bx-.02)*t,hy-.08-(hy-by-.02)*t,4.48+.63*t**1.5+.11*abs(2*f-1)**10*(1-t)**3)
  for i in range(n):
   for j in range(6):
    f,g=i/n,(i+1)/n;t,u=j/6,(j+1)/6
    B.face('roof',[lower(f,t),lower(g,t),lower(g,u),lower(f,u)])
    a,b=lower((f+g)/2,t),lower((f+g)/2,u);B.beam('tile',(*a[:2],a[2]+.025),(*b[:2],b[2]+.025),.048,6)
 # Hipped upper roof: four slopes, curved tile rolls and upturned corner hips.
 ridge=hx-hy
 for side in range(4):
  n=max(16,round((L if side%2==0 else D)/.24))
  def roof(f,t):
   x,y,_=rectpoint(side,f,hx,hy,0);endx=max(-ridge,min(ridge,x))
   return(x+(endx-x)*t,y*(1-t),eave+(peak-eave)*t**1.65+.18*abs(2*f-1)**12*(1-t)**3)
  for i in range(n):
   for j in range(16):
    f,g=i/n,(i+1)/n;t,u=j/16,(j+1)/16
    B.face('roof',[roof(f,t),roof(g,t),roof(g,u),roof(f,u)])
    a,b=roof((f+g)/2,t),roof((f+g)/2,u);B.beam('tile',(*a[:2],a[2]+.035),(*b[:2],b[2]+.035),.055,6)
   p=roof((i+.5)/n,0);B.beam('tile',p,(p[0],p[1],p[2]-.12),.093,8)
  for j in range(20):
   a,b=roof(0,j/20),roof(0,(j+1)/20);B.beam('tile',(*a[:2],a[2]+.09),(*b[:2],b[2]+.09),.105,8)
 B.box('roof',(0,0,peak+.18),(2*ridge,.30,.32))
 for sign in [-1,1]:
  for j in range(8):B.beam('tile',(sign*(ridge+.035*j),0,peak+.22+j*.07),(sign*(ridge+.035*(j+1)),0,peak+.29+j*.07),.12,8)
 # Modern typographic placeholder identifies the building; it is not a facsimile.
 py=-(hy-.43);B.face('plaque',[(-1.1,py,eave-.95),(1.1,py,eave-.95),(1.1,py,eave-.35),(-1.1,py,eave-.35)],[(0,0),(1,0),(1,1),(0,1)])
 height=max(z for vs,fs,uvs in B.groups.values()for x,y,z in vs)-floor
 C.project(B,r,ang);objs=[]
 for key,(vs,fs,uvs)in B.groups.items():
  me=bpy.data.meshes.new('庆霄楼 '+key);me.from_pydata([(x/100,y/100,z/100+pad['height'])for x,y,z in vs],[],fs);me.update();uv=me.uv_layers.new(name='Building materials')
  for poly,coords in zip(me.polygons,uvs):
   for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
  me.materials.append(mats[key]);o=bpy.data.objects.new('庆霄楼 '+key,me);scene.collection.objects.link(o)
  o['layer']='buildings_urban_courtyard';o['osmId']=str(r['osmId']);o['groundHeight']=.011+pad['height'];o['islandLift']=True;o['templeReplacement']=True;objs.append(o)
 entry={'id':r['osmId'],'name':'庆霄楼','rings':r['rings'],'bounds':r['bounds'],'heightMetresEstimated':round(height,3),'groundHeight':.011+pad['height'],'roofForm':'hipped-with-waist-eaves','role':'context-hall','bays':7,'storeys':2,'source':'https://www.bjxch.gov.cn/f/130226//27888.pdf','fidelity':'Two storeys, seven bays and upper gallery documented in Xicheng archive. Footprint and hipped roof tag from OSM. Height, waist eaves, balcony, colours, lattice and ornament approximated. Historical photo reference located but could not be visually inspected. Not a survey or a historical facsimile.'}
 return objs,[entry]
