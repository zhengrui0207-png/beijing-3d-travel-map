from pathlib import Path
import json,math,xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Polygon
R=Path(__file__).resolve().parents[1];nodes={};ways={};ids={43921113,727026692,727026693,727026694}
for f in (R/'data/tiles').glob('*.osm'):
 for e in ET.parse(f).getroot():
  if e.tag=='node':nodes[e.get('id')]=(float(e.get('lon')),float(e.get('lat')))
  elif e.tag=='way'and int(e.get('id'))in ids:ways[int(e.get('id'))]=[n.get('ref')for n in e.findall('nd')]
SX=111320*math.cos(math.radians(39.915))/100;SY=111320/100
def xy(id):x,y=nodes[id];return[(x-116.415)*SX,(y-39.915)*SY]
wall=[xy(n)for n in ways[43921113]];arr=np.array(wall);x,y=arr.T;fit=np.linalg.lstsq(np.c_[2*x,2*y,np.ones(len(x))],x*x+y*y,rcond=None)[0];cx,cy,c=fit;radius=(c+cx*cx+cy*cy)**.5
# Smooth between geographic vertices, keeping every mapped wall point and both gate junctions.
sm=[]
for i in range(len(wall)-1):
 p0=arr[max(0,i-1)];p1=arr[i];p2=arr[i+1];p3=arr[min(len(arr)-1,i+2)]
 for k in range(12):
  t=k/12;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);sm.append(v.tolist())
sm.append(wall[-1]);rows=json.loads((R/'data/urban/records.json').read_text())['records'];parts=[]
for id in [43921117,43921122,43921123]:
 r=next(r for r in rows if r['osmId']==id);poly=Polygon(r['rings'][0]);q=list(poly.minimum_rotated_rectangle.exterior.coords)[:4];edges=[(math.dist(a,b),a,b)for a,b in zip(q,q[1:]+q[:1])];L,a,b=max(edges);angle=math.atan2(b[1]-a[1],b[0]-a[0]);D=min(e[0]for e in edges);parts.append({'osmId':id,'name':r['name'],'center':r['center'],'length':L*100,'depth':D*100,'angle':angle,'mask':r['rings'][0]})
p={'center':[cx,cy],'sourceWall':wall,'wall':sm,'wallOsmId':43921113,'mappedDiameterMetres':radius*200,'documentedDiameterMetres':61.5,'wallHeightMetres':3.72,'wallThicknessMetres':.9,'parts':parts,'stairs':{str(id):[xy(n)for n in ways[id]]for id in [727026692,727026693,727026694]},'note':'Preserve smoothed OSM wall alignment; mapped diameter differs from published61.5m. Detailed gate/annex heights and decorative forms inferred, not surveyed.'};(R/'data/echo-court-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));print('wall diameter',p['mappedDiameterMetres'],'centre',p['center'],'parts',[(a['osmId'],a['length'],a['depth'])for a in parts])
# Stone paving joint lines clipped to the mapped enclosure, in local metres.
from shapely.geometry import LineString
court=Polygon([((x-cx)*100,(y-cy)*100)for x,y in sm]);lines=[]
def clipped(a,b):
 hit=court.intersection(LineString([a,b]))
 for line in getattr(hit,'geoms',[hit]):
  if line.geom_type=='LineString'and line.length>.035:lines.append(list(line.coords))
x0,y0,x1,y1=court.bounds;row=0;yy=math.floor(y0/.72)*.72
while yy<y1:
 clipped((x0,yy),(x1,yy));xx=math.floor(x0/1.4)*1.4+(row%2)*.7
 while xx<x1:clipped((xx,yy),(xx,yy+.72));xx+=1.4
 yy+=.72;row+=1
p['pavingJoints']=lines;(R/'data/echo-court-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));print('paving joints',len(lines))
