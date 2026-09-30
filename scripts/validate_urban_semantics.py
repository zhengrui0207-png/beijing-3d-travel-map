from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1];new=json.loads((ROOT/'data/urban/records.json').read_text());old=json.loads((ROOT/'output/urban-semantics/records-before.json').read_text());before={r['id']:r for r in old['records']};after={r['id']:r for r in new['records']};assert before.keys()==after.keys()
for id,r in after.items():
 assert r['rings']==before[id]['rings'],id
 base=.011+r['minHeight'];assert base<r['top']
 for face in r['walls']:
  assert all(abs(p[2]-base)<1e-9 for p in face[:2]),id
  assert all(base-1e-6<=p[2]<=r['top']+1e-6 for p in face),id
 assert all(base-1e-5<=p[2]<=r['top']+1e-5 and all(math.isfinite(v)for v in p) for tri in r['roof']for p in tri),id
 if r['minHeight']>0:assert r['bottom'],id
 for a,b,c in r['bottom']:assert (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0,id
roof=after['way/637950096/0'];assert roof['parentOsmId']==25097188 and roof['minHeight']==.29 and roof['wallFinish']['solid'];assert abs(min(p[2]for face in roof['walls']for p in face)-.301)<1e-8
assert after['way/637950071/0']['wallFinish']['material']=='wood'
conflicts=[id for id,r in after.items()if r['minHeightSource']=='conflictFallback'];assert set(conflicts)=={'way/519416291/0','way/519416292/0'}
report={'buildings':len(after),'footprintsUnchanged':True,'elevatedParts':sum(r['minHeight']>0 for r in after.values()),'inheritedParts':sum(r['parentOsmId']is not None for r in after.values()),'solidWalls':sum(r['wallFinish']['solid']for r in after.values()),'conflictingRecordsPreserved':conflicts,'duanmenRoofBaseMetres':30.1,'note':'29m above 1.1m common scene datum; height coordinates include that datum. All source footprints preserved.'}
(ROOT/'output/urban-semantics/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
