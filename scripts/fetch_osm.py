import json, pathlib, requests, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
(ROOT / 'data').mkdir(parents=True, exist_ok=True)
BBOX = '39.865,116.345,39.965,116.485'
query = f'''[out:json][timeout:180][bbox:{BBOX}];
(
way[highway][highway!~"proposed|construction|steps"];
way[building]; relation[building];
way["building:part"];
way[natural=water]; relation[natural=water];
way[waterway][waterway!~"drain|ditch"];
way[leisure~"park|garden|pitch"];
relation[leisure~"park|garden"];
way[landuse~"grass|forest|recreation_ground"];
way[natural=wood];
);out geom;'''
target=ROOT/'data/osm_beijing.json'
if target.exists():
    data=json.loads(target.read_text())
else:
    for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://overpass.private.coffee/api/interpreter']:
        try:
            print('Fetching', endpoint, flush=True)
            r=requests.post(endpoint,data={'data':query},headers={'User-Agent':'Xiaomeng-Beijing-Atlas/1.0 (one-off local art project)'},timeout=220)
            r.raise_for_status(); data=r.json()
            if not data.get('elements'): raise ValueError('No map elements')
            target.write_text(json.dumps(data,ensure_ascii=False))
            (ROOT/'data/query.overpass').write_text(query)
            (ROOT/'data/source.json').write_text(json.dumps({'endpoint':endpoint,'bbox':[39.865,116.345,39.965,116.485],'timestamp':data.get('osm3s',{}),'attribution':'© OpenStreetMap contributors','license':'ODbL 1.0','url':'https://www.openstreetmap.org/copyright'},ensure_ascii=False,indent=2))
            break
        except Exception as e:
            print(type(e).__name__,str(e),flush=True)
    else: raise RuntimeError('All map endpoints failed')
from collections import Counter
print('Elements',len(data['elements']), 'Bytes',target.stat().st_size)
print(Counter('building' if 'building' in e.get('tags',{}) else 'road' if 'highway' in e.get('tags',{}) else 'other' for e in data['elements']))
