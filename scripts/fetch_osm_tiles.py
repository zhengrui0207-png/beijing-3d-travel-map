"""Read-only cached fallback through the official OSM map API."""
import pathlib,requests,json,xml.etree.ElementTree as ET,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
cache=ROOT/'data/tiles';cache.mkdir(exist_ok=True)
session=requests.Session();session.headers['User-Agent']='Xiaomeng-Beijing-Atlas/1.0 local-map-art'
nodes={};ways={};relations={};used=[]
def fetch(w,s,e,n,tag):
    path=cache/f'{tag}.osm'
    if not path.exists():
        url=f'https://www.openstreetmap.org/api/0.6/map?bbox={w:.6f},{s:.6f},{e:.6f},{n:.6f}'
        print('Tile',tag,'fetch',flush=True)
        r=session.get(url,timeout=90)
        if r.status_code==400 and 'too many nodes' in r.text.lower():
            mx=(w+e)/2;my=(s+n)/2
            for i,b in enumerate([(w,s,mx,my),(mx,s,e,my),(w,my,mx,n),(mx,my,e,n)]):fetch(*b,tag+str(i))
            return
        r.raise_for_status();path.write_bytes(r.content)
    root=ET.parse(path).getroot();used.append(tag)
    for el in root:
        if el.tag=='node':nodes[int(el.attrib['id'])]={'lat':float(el.attrib['lat']),'lon':float(el.attrib['lon'])}
        elif el.tag=='way':ways[int(el.attrib['id'])]=el
        elif el.tag=='relation':relations[int(el.attrib['id'])]=el
    print('Tile',tag,'OK',len(nodes),'nodes',flush=True)
for j in range(4):
    for i in range(4):fetch(116.345+i*.035,39.865+j*.025,116.345+(i+1)*.035,39.865+(j+1)*.025,f'{j}-{i}')
def tags(e):return {t.attrib['k']:t.attrib['v'] for t in e.findall('tag')}
def keep(t):return any(k in t for k in ['highway','building','building:part','water','waterway']) or t.get('natural') in ['water','wood'] or t.get('leisure') in ['park','garden','pitch'] or t.get('landuse') in ['grass','forest','recreation_ground']
def geom(w):return [nodes[int(nd.attrib['ref'])] for nd in w.findall('nd') if int(nd.attrib['ref']) in nodes]
elements=[]
for id,e in ways.items():
    t=tags(e)
    if keep(t):elements.append({'type':'way','id':id,'tags':t,'geometry':geom(e)})
for id,e in relations.items():
    t=tags(e)
    if not keep(t):continue
    ms=[]
    for m in e.findall('member'):
        if m.attrib['type']=='way' and int(m.attrib['ref']) in ways:
            ms.append({'type':'way','ref':int(m.attrib['ref']),'role':m.attrib.get('role',''),'geometry':geom(ways[int(m.attrib['ref'])])})
    if ms:elements.append({'type':'relation','id':id,'tags':t,'members':ms})
source={'endpoint':'https://www.openstreetmap.org/api/0.6/map','bbox':[39.865,116.345,39.965,116.485],'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attribution':'© OpenStreetMap contributors','license':'ODbL 1.0','url':'https://www.openstreetmap.org/copyright','tiles':used}
(ROOT/'data/source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
(ROOT/'data/osm_beijing.json').write_text(json.dumps({'osm3s':source,'elements':elements},ensure_ascii=False))
print('READY',len(elements),'elements',flush=True)
