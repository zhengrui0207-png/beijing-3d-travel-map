"""Mapped enclosure and documented terrace dimensions; no survey precision implied."""
from pathlib import Path
import json,math,xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];nodes={};ways={};ids={29182811,237696577,237696580,43922680,43922681,43922687,43922688}
for f in (R/'data/tiles').glob('*.osm'):
 for e in ET.parse(f).getroot():
  if e.tag=='node':nodes[e.get('id')]=(float(e.get('lon')),float(e.get('lat')))
  elif e.tag=='way' and int(e.get('id'))in ids:ways[int(e.get('id'))]=[n.get('ref')for n in e.findall('nd')]
sx=111320*math.cos(math.radians(39.915))/100
def xy(n):x,y=nodes[n];return[(x-116.415)*sx,(y-39.915)*1113.2]
def pts(id):return[xy(n)for n in ways[id]]
a=np.array(pts(237696580)[:-1]);x,y=a.T;cx,cy,k=np.linalg.lstsq(np.c_[2*x,2*y,np.ones(len(x))],x*x+y*y,rcond=None)[0];center=[cx,cy]
rows=json.loads((R/'data/urban/records.json').read_text())['records'];gates=[];masks=[];source=[]
for id in [43922668,43922669,43922697,727026433,727026437,727026439,43922670,727026438]:
 r=next(a for a in rows if a['osmId']==id);q=list(Polygon(r['rings'][0]).minimum_rotated_rectangle.exterior.coords)[:4];edges=[(math.dist(a,b),a,b)for a,b in zip(q,q[1:]+q[:1])];L,a,b=max(edges);angle=math.atan2(b[1]-a[1],b[0]-a[0]);gates.append({'osmId':id,'center':r['center'],'length':L*100,'angle':angle,'kind':'inner'if id>=727000000 else'outer','mask':r['rings'][0],'existing':id in [43922670,727026438]})
 if id not in [43922670,727026438]:masks.append(r['rings'][0]);source.append(id)
for id in [237696578,237696579]:
 r=next(a for a in rows if a['osmId']==id);masks.append(r['rings'][0]);source.append(id)
# Smooth the mapped inner enclosure, then cut all four gate apertures.
raw=np.array(pts(237696577)[:-1]);smooth=[]
for i,p1 in enumerate(raw):
 p0,p2,p3=raw[(i-1)%len(raw)],raw[(i+1)%len(raw)],raw[(i+2)%len(raw)]
 for k in range(6):
  t=k/6;smooth.append((.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)).tolist())
smooth.append(smooth[0]);holes=unary_union([Polygon(g['mask']).buffer(.012)for g in gates if g['kind']=='inner']);cut=LineString(smooth).difference(holes)
inner=[list(q.coords)for q in getattr(cut,'geoms',[cut])];outer=[pts(i)for i in [43922680,43922681,43922687,43922688]]
court=pts(29182811);bounds=Polygon(court).bounds
plan={'center':center,'bounds':bounds,'court':court,'innerWall':inner,'outerWall':outer,'gates':gates,'maskPolygons':masks,'sourceOsmIds':source,'tiers':[{'radius':27.455,'height':1.67,'pavers':list(range(171,244,9)),'panelsPerQuarter':45},{'radius':19.655,'height':1.63,'pavers':list(range(90,163,9)),'panelsPerQuarter':27},{'radius':11.825,'height':1.87,'pavers':list(range(9,82,9)),'panelsPerQuarter':18}],'stairs':{'count':9,'width':5.4,'run':3.6},'source':'https://gygl.beijing.gov.cn/mlgy/mlgy_gyjg01/201912/t20191211_1048232.html','note':'Official tier diameters/heights and 9-step flights. Preserved mapped wall/gate alignments. Carving, balustrade profiles and paving variation are interpretive; not scanned. Total height5.17m follows park authority (the cultural heritage paper contains a5.71m total inconsistent with its own tier heights).'}
(R/'data/circular-mound-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));print('centre',center,'gates',len(gates),'inner arcs',len(inner),'pavers',[sum(t['pavers'])for t in plan['tiers']])
