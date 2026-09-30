"""Remove imagery-inferred sheds that overlap the newly reconstructed ceremonial court."""
import json,math,runpy
from pathlib import Path
from shapely.geometry import Polygon
R=Path(__file__).resolve().parents[1];p=json.loads((R/'data/circular-mound-plan.json').read_text());court=Polygon(p['court']);f=R/'data/urban/overture-fill-records.json';blob=json.loads(f.read_text());removed=[];kept=[]
for r in blob['records']:
 (removed if Polygon(r['rings'][0],r['rings'][1:]).intersects(court)else kept).append(r)
if not removed:print('No additional inferred buildings to exclude');raise SystemExit
out=R/'data/urban/exclusions-circular-mound.json';out.write_text(json.dumps({'reason':'Imagery-inferred footprints overlap documented open ceremonial court; replacement follows mapped enclosure','records':removed},ensure_ascii=False))
blob['records']=kept;blob['stats']['accepted']-=len(removed);blob['stats']['estimatedHeight']-=sum(not r.get('heightTagged',False)for r in removed);blob['stats']['protectedLandmark']+=len(removed)
for r in removed:blob['stats']['inferredGable'if r['roofShape']=='inferred-gabled'else'flatUnspecified']-=1
f.write_text(json.dumps(blob,ensure_ascii=False,separators=(',',':')))
D=runpy.run_path(str(R/'scripts/prepare_infill_detail.py'));keys={f'{math.floor(r["center"][0]/10)}_{math.floor(r["center"][1]/10)}'for r in removed};idxpath=R/'data/urban/infill-detail/index.json';idx=json.loads(idxpath.read_text())
for key in keys:
 t=next(t for t in idx['tiles']if t['id']=='infill-'+key);data={'id':t['id'],'bounds':t['bounds'],'height':0,'buildings':0,'layers':{}}
 for r in kept:
  if f'{math.floor(r["center"][0]/10)}_{math.floor(r["center"][1]/10)}'!=key:continue
  layers=D['detail'](r)
  if not layers:continue
  data['height']=max(data['height'],r['height']+.006);data['buildings']+=1
  for kind,faces in layers.items():data['layers'].setdefault(kind,[]).extend(faces)
 Path(t['input']).write_text(json.dumps(data,separators=(',',':')));t['height']=data['height'];t['buildings']=data['buildings']
for r in removed:
 idx['stats'][r['roofShape']]-=1
 for kind,faces in D['detail'](r).items():idx['stats'][kind+'Triangles']-=sum(len(f)-2 for f in faces)
idxpath.write_text(json.dumps(idx,indent=2));print('Excluded',len(removed),'inferred buildings; tiles',keys)
