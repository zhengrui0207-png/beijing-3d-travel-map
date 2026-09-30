"""Asset coverage inventory only, deliberately not a claim of visual fidelity."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=json.loads((R/'public/assets/tourism.json').read_text());m=json.loads((R/'public/assets/route-landmarks/manifest.json').read_text());routes={p for t in d['tours']for p in t['stops']};rows=[]
for p in d['places']:
 models=[s for s in m['assets']if s['id']==p['id']or s.get('parentPlace')==p['id']];palace=p['id']=='forbidden'and (R/'public/assets/palace/manifest.json').exists()
 rows.append({'id':p['id'],'name':p['name'],'inThemeRoute':p['id']in routes,'dedicatedModels':[s['id']for s in models],'palacePipeline':palace,'status':'dedicated_assets_present_fidelity_unproven'if models or palace else'generic_city_geometry_only_needs_review'})
a={'places':len(rows),'themeRoutePlaces':len(routes),'genericOnly':[r['id']for r in rows if r['status'].startswith('generic')],'rows':rows,'note':'Presence of GLB/LOD entries is not evidence of authentic geometry or sufficient close-up fidelity. Full completion requires visual inspection of every relevant landmark and urban region, performance and interaction checks.'};out=R/'.dream-loop/city-depth/landmark-coverage.json';out.write_text(json.dumps(a,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in a.items()if k!='rows'},ensure_ascii=False))
