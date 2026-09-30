"""Conservative non-overlapping infill from Overture/East Asian building footprints.
Geographic footprints are observed inputs; all heights and optional gables are estimates.
"""
from pathlib import Path
import json,math,collections
from shapely.geometry import shape,Polygon,box,Point,LineString
from shapely.geometry.polygon import orient
from shapely.ops import transform,unary_union,split
from shapely import make_valid,constrained_delaunay_triangles
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1]
SX=111320*math.cos(math.radians(39.915))/100;SY=1113.2
project=lambda x,y:((x-116.415)*SX,(y-39.915)*SY)
clip=box(*project(116.345,39.865),*project(116.485,39.965))
def polygons(g):
 if g.geom_type=='Polygon':return [g]
 return [p for s in getattr(g,'geoms',[])for p in polygons(s)]
base=json.loads((ROOT/'data/urban/records.json').read_text())['records']
old=[Polygon(r['rings'][0],r['rings'][1:]).buffer(.003)for r in base];oldtree=STRtree(old)
raw=json.loads((ROOT/'data/urban/overture-beijing.geojson').read_text())['features']
# Reuse the cached, georeferenced OSM water and road interpretation.
ns={'__file__':str(ROOT/'scripts/prepare_geometry.py')};src=(ROOT/'scripts/prepare_geometry.py').read_text();exec(src[:src.index('water=unary_union(waters)')],ns)
water=unary_union(ns['waters']);roads=[g.buffer(.018 if e['tags'].get('highway')in ['motorway','trunk','primary','secondary','tertiary']else .008)for e,g in ns['roads']];roadtree=STRtree(roads)
manifest=json.loads((ROOT/'public/assets/route-landmarks/manifest.json').read_text())
protected=[box(*s['bounds']).buffer(.015)for s in manifest['assets']]
protected+=[box(*project(116.3864,39.912),*project(116.3955,39.9212)),Point(*project(116.39747,39.90872)).buffer(.80),box(-28.1,-13.9,-25.5,-12.0)]
# The original Tiananmen OSM anchor uses the corrected metadata location.
meta=json.loads((ROOT/'public/assets/metadata.json').read_text())
protected += [Point(l['x'],l['y']).buffer(.80) for l in meta['landmarks']if l['id']=='tiananmen']
protect=unary_union(protected)
rows=[];accepted=[];counts=collections.Counter();seen=set()
for f in raw:
 if any(s.get('dataset')=='OpenStreetMap' for s in f['properties'].get('sources',[])):counts['existingSourceSkipped']+=1;continue
 if f['id']in seen:counts['duplicateId']+=1;continue
 seen.add(f['id']);g=make_valid(transform(project,shape(f['geometry']))).intersection(clip)
 if g.is_empty or g.area<.0012:counts['small']+=1;continue
 if g.intersects(protect):counts['protectedLandmark']+=1;continue
 if g.intersects(water) and g.intersection(water).area/g.area>.05:counts['waterOverlap']+=1;continue
 hit=oldtree.query(g,predicate='intersects')
 if len(hit):
  occupied=unary_union([old[int(i)]for i in hit]);fraction=g.intersection(occupied).area/g.area
  if fraction>.15:counts['existingGeometryOverlap']+=1;continue
  g=g.difference(occupied);counts['edgeClipped']+=1
 hit=roadtree.query(g,predicate='intersects')
 if len(hit):
  occupied=unary_union([roads[int(i)]for i in hit]);fraction=g.intersection(occupied).area/g.area
  if fraction>.2:counts['roadOverlap']+=1;continue
  g=g.difference(occupied);counts['roadEdgeClipped']+=1
 for part,p in enumerate(polygons(g.simplify(.0015,preserve_topology=True))):
  if p.area<.0012:continue
  p=orient(p,1);rect=list(p.minimum_rotated_rectangle.exterior.coords)[:4];a,b,c,d=rect
  if math.dist(a,b)<math.dist(b,c):a,b,c,d=b,c,d,a
  length=math.dist(a,b);width=math.dist(b,c)
  if width<.018:counts['sliver']+=1;continue
  center=p.centroid;lon=center.x/SX+116.415;lat=center.y/SY+39.915
  historic=116.36<lon<116.438 and 39.87<lat<39.948
  h=(4.8 if p.area<.025 else 6.4 if historic else 9.6)/100
  if f['properties'].get('height'):
   h=max(.025,min(float(f['properties']['height'])/100,5.5));heightSource='source'
  else:heightSource='estimated'
  gable=historic and p.area<.06 and width<.15 and p.area/(width*length)>.93 and not p.interiors
  axis=((b[0]-a[0])/length,(b[1]-a[1])/length);normal=(-axis[1],axis[0]);cx=sum(x for x,y in rect)/4;cy=sum(y for x,y in rect)/4
  top=.011+h;rise=min(.018,width*.30)if gable else 0;eaves=top-rise
  def roofz(x,y):return top-rise*min(1,abs((x-cx)*normal[0]+(y-cy)*normal[1])/(width/2))
  segments=[p]
  if gable:
   line=LineString([(cx-axis[0]*100,cy-axis[1]*100),(cx+axis[0]*100,cy+axis[1]*100)])
   segments=polygons(split(p,line))
  roof=[]
  for seg in segments:
   for t in constrained_delaunay_triangles(seg).geoms:roof.append([[round(x,5),round(y,5),round(roofz(x,y),5)]for x,y in list(t.exterior.coords)[:3]])
  rings=[list(r.coords)[:-1]for r in [p.exterior,*p.interiors]];walls=[]
  for ring in rings:
   for a,b in zip(ring,ring[1:]+ring[:1]):
    points=[a,b];va=(a[0]-cx)*normal[0]+(a[1]-cy)*normal[1];vb=(b[0]-cx)*normal[0]+(b[1]-cy)*normal[1]
    if gable and va*vb<0:
     t=va/(va-vb);points.insert(1,(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    for aa,bb in zip(points,points[1:]):walls.append([[round(aa[0],5),round(aa[1],5),.011],[round(bb[0],5),round(bb[1],5),.011],[round(bb[0],5),round(bb[1],5),round(roofz(*bb),5)],[round(aa[0],5),round(aa[1],5),round(roofz(*aa),5)]])
  rows.append({'id':f['id']+f'/{part}','center':[center.x,center.y],'bounds':list(p.bounds),'rings':rings,'height':h,'heightSource':heightSource,'roofShape':'inferred-gabled'if gable else'unspecified-flat','source':f['properties']['sources'][0]['dataset'],'roof':roof,'walls':walls})
  accepted.append(p);counts['accepted']+=1;counts[heightSource+'Height']+=1;counts['inferredGable'if gable else'flatUnspecified']+=1
# Remove only decorative trees that overlap the newly added real footprints.
plant=json.loads((ROOT/'public/assets/cartographic/landscape.json').read_text());tree=STRtree(accepted);kept=[]
for row in plant['trees']:
 x,y=row[:2]
 if len(tree.query(Point(x,y).buffer(.035),predicate='intersects')):counts['decorativeTreesRemoved']+=1
 else:kept.append(row)
plant['trees']=kept
(ROOT/'public/assets/urban-fill/landscape.json').write_text(json.dumps(plant,separators=(',',':')))
result={'source':'Overture Maps 2026-09-23.1 / Qian Shi et al., East Asian buildings (2023), DOI 10.5281/zenodo.8174931; heights and gable forms inferred where absent','stats':dict(counts),'records':rows}
(ROOT/'data/urban/overture-fill-records.json').write_text(json.dumps(result,separators=(',',':')))
(ROOT/'output/overture-fill/filter-audit.json').write_text(json.dumps({'stats':dict(counts),'source':result['source'],'rawFeatures':len(raw),'bbox':[116.345,39.865,116.485,39.965]},indent=2))
print(json.dumps(counts),flush=True)
