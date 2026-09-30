"""Use the same cached OSM footprint selection as the base city.
Separate observable tags from estimated heights and decorative architectural detail.
"""
import pathlib,json,math,collections
from shapely.geometry import Polygon,box,LineString
from shapely.ops import split
from shapely import constrained_delaunay_triangles
from urban_semantics import inherited_tags,minimum_height,is_heritage,wall_finish
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Reuse the original parser/selection rules without executing its asset writes.
namespace={'__file__':str(ROOT/'scripts/prepare_geometry.py')}
source=(ROOT/'scripts/prepare_geometry.py').read_text()
exec(source[:source.index('water=unary_union(waters)')],namespace)
polygon=namespace['polygon'];num=namespace['num'];polys=namespace['polys'];SX=namespace['SX'];SY=namespace['SY']
from shapely.ops import unary_union
from shapely.strtree import STRtree
buildings=namespace['buildings'];parts=[g for e,g in buildings if 'building:part' in e.get('tags',{})];tree=STRtree(parts)
parent_entries=[(e,g)for e,g in buildings if 'building:part'not in e.get('tags',{})]
parent_tree=STRtree([g for e,g in parent_entries])
existing=json.loads((ROOT/'public/assets/metadata.json').read_text())
overrides=json.loads((ROOT/'data/urban/architectural-overrides.json').read_text())
from shapely.geometry import Point
custom=[]
for l in existing['landmarks']:
    if l['id'] in ['tiananmen','cctv','tiantan','guomao']:
        custom.append(Point(l['x'],l['y']).buffer({'tiananmen':.75,'cctv':1.55,'tiantan':.34,'guomao':.48}[l['id']]))
records=[];stats=collections.Counter()
def underside(g,z):
    out=[]
    for t in tris(g):
        a,b,c=t
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0:t=t[::-1]
        out.append([[round(x,5),round(y,5),z]for x,y in t])
    return out
def tris(g):
    return [[list(c)[:2] for c in list(t.exterior.coords)[:3]]for p in polys(g)for t in constrained_delaunay_triangles(p).geoms]
for e,g in buildings:
    rawtags=e['tags'];parent=None
    if 'building:part'in rawtags:
        candidates=[parent_entries[int(i)]for i in parent_tree.query(g,predicate='intersects')]
        candidates=[(pe,pg)for pe,pg in candidates if pg.area>=g.area*.98 and pg.intersection(g).area>=g.area*.98]
        if candidates:parent=min(candidates,key=lambda pair:pair[1].area)[0]
    tags=inherited_tags(rawtags,parent['tags']if parent else None);cent=g.centroid
    if any(mask.contains(cent)for mask in custom):continue
    if 'building:part'not in tags:
        nearby=[parts[int(i)]for i in tree.query(g,predicate='intersects')]
        if nearby and unary_union(nearby).intersection(g).area>g.area*.65:continue
    lon=cent.x/SX+116.415;lat=cent.y/SY+39.915
    if 116.3864<lon<116.3955 and 39.9120<lat<39.9212:stats['retainedPalace']+=1;continue
    kind=tags.get('building','yes');default=7 if 116.365<lon<116.435 and 39.9<lat<39.95 else 15
    if kind in ['apartments','residential','dormitory']:default=18
    if kind in ['commercial','office','hotel']:default=32
    if kind in ['industrial','warehouse','school','retail']:default=12
    if kind in ['garage','garages','shed','roof']:default=3.5
    heritage=is_heritage(tags)
    if heritage:default=8
    h=num(tags['height'],default)if 'height'in tags else num(tags['building:levels'],default/3)*3.2 if 'building:levels'in tags else default
    h=max(2,min(h,550))/100;provenance='height'if 'height'in tags else 'levels'if 'building:levels'in tags else 'estimated'
    shape=tags.get('roof:shape','flat');roofsource='osm'if 'roof:shape'in tags else 'unspecified'
    override=overrides['buildings'].get(str(e['id']),{})
    if override:
        h=override['height']/100;provenance='photoEstimated';shape=override['roofShape'];roofsource='photoInferred';heritage=override['heritage']
    min_m,min_source=minimum_height(rawtags,h*100)
    if min_m>=h*100:
        stats['invalidVerticalExtent']+=1;min_m=0;min_source='conflictFallback'
    base=.011+min_m/100;finish=wall_finish(tags,heritage)
    for j,p in enumerate(polys(g.simplify(.005,preserve_topology=True))):
        if p.area<.0001:continue
        from shapely.geometry.polygon import orient
        p=orient(p,sign=1);rings=[list(r.coords)[:-1]for r in [p.exterior,*p.interiors]]
        rect=list(p.minimum_rotated_rectangle.exterior.coords)[:4];a,b,c,d=rect
        if math.dist(a,b)<math.dist(b,c):a,b,c,d=b,c,d,a
        length=math.dist(a,b);width=math.dist(b,c)
        if min(length,width)<1e-6 or not all(math.isfinite(v) for q in rect for v in q):continue
        axis=((b[0]-a[0])/length,(b[1]-a[1])/length);normal=(-axis[1],axis[0]);cx,cy=map(lambda values:sum(values)/4,zip(*rect))
        # Only honor pitch shapes on convex near-rectangular footprints; retain
        # irregular/holey footprints instead of roofing over open courtyards.
        support=shape in ['gabled','hipped','pyramidal','hipped-and-gabled','skillion']and p.area/(length*width)>.88 and not p.interiors
        rise=min((h-min_m/100)*.35,max(.012,min(.12,width*.38)))if support else 0
        if support and 'roof:height'in tags:rise=min(h-min_m/100,max(.005,num(tags['roof:height'],rise*100)/100))
        top=h+.011;eaves=top-rise;segments=[p]
        if support:
            lines=[LineString([(cx-axis[0]*100,cy-axis[1]*100),(cx+axis[0]*100,cy+axis[1]*100)])]
            if shape=='pyramidal':
                lines+=[LineString([a,c]),LineString([b,d])]
            elif shape in ['hipped','hipped-and-gabled']:
                # Split at the actual hip ridges, not the rectangle diagonals.
                for corner in rect:
                    u=(corner[0]-cx)*axis[0]+(corner[1]-cy)*axis[1]
                    end=(1 if u>0 else -1)*(length-width)/2
                    rx,ry=cx+axis[0]*end,cy+axis[1]*end
                    dx,dy=rx-corner[0],ry-corner[1]
                    lines.append(LineString([(corner[0]-dx*100,corner[1]-dy*100),(rx+dx*100,ry+dy*100)]))
            for line in lines:
                segments=[z for q in segments for z in polys(split(q,line))]
        def roofz(x,y):
            if not support:return top
            u=(x-cx)*axis[0]+(y-cy)*axis[1];v=(x-cx)*normal[0]+(y-cy)*normal[1]
            if shape=='skillion':f=(v+width/2)/width
            elif shape=='gabled':f=1-abs(v)/(width/2)
            else:f=min(1-abs(v)/(width/2),(length/2-abs(u))/(width/2 if shape!='pyramidal'else length/2))
            return eaves+rise*max(0,min(1,f))
        roof=[[[round(x,5),round(y,5),round(roofz(x,y),5)]for x,y in t]for q in segments for t in tris(q)]
        # Roof end walls follow the slope; this preserves the footprint exactly.
        walls=[]
        for ring in rings:
            for a,b in zip(ring,ring[1:]+ring[:1]):
                points=[a,b]
                va=(a[0]-cx)*normal[0]+(a[1]-cy)*normal[1];vb=(b[0]-cx)*normal[0]+(b[1]-cy)*normal[1]
                if support and shape=='gabled' and va*vb<0:
                    t=va/(va-vb);points.insert(1,(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
                for aa,bb in zip(points,points[1:]):
                    walls.append([[*aa,base],[*bb,base],[*bb,roofz(*bb)],[*aa,roofz(*aa)]])
        records.append({'id':f"{e['type']}/{e['id']}/{j}",'osmId':e['id'],'kind':kind,'heritage':heritage,'name':tags.get('name',''),'height':h,'minHeight':min_m/100,'minHeightSource':min_source,'parentOsmId':parent['id']if parent else None,'wallFinish':finish,'heightSource':provenance,'roofShape':shape if support else 'flat','roofSource':roofsource,'roofColor':override.get('roofColor',tags.get('roof:colour','gray')),'center':[cx,cy],'bounds':list(p.bounds),'roof':roof,'bottom':underside(p,base)if min_m>0 else [],'walls':walls,'eaves':eaves,'top':top,'rings':rings})
        stats['elevatedParts']+=int(min_m>0);stats['inheritedParts']+=int(parent is not None);stats['solidWalls']+=int(finish['solid']);stats['buildings']+=1;stats[provenance]+=1;stats['pitchedRoofs'if support else 'flatRoofs']+=1
out={'records':records,'stats':dict(stats),'units':'100 metres','source':'Cached OSM 2026-09-08. Unknown heights estimated. Untagged roof shapes remain flat; window/ledge details are illustrative.'}
out['source']+=' Explicit min_height is honoured; building parts inherit semantic/material tags from the smallest containing building footprint (98% coverage), never its height. Two conflicting minimum-level records retain ground-based fallback and are flagged. Three Tiantan ancillary forms use explicitly recorded photo-informed estimates in architectural-overrides.json.'
out['courtyardPaving']=[]
for e in namespace['elements']:
    if e['type']=='relation' and e['id']==313234:
        g=polygon(e)
        out['courtyardPaving'].append({'osmId':e['id'],'bounds':list(g.bounds),'triangles':tris(g),'source':'OSM pedestrian multipolygon, building holes retained'})
(ROOT/'data/urban/records.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
(ROOT/'output/urban/geometry-audit.json').write_text(json.dumps({'stats':dict(stats),'source':out['source']},ensure_ascii=False,indent=2))
print(dict(stats),flush=True)
