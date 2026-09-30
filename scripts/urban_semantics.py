"""Conservative OSM part semantics. Geometry association is done by the caller.
Do not inherit a parent's height/min_height: those describe a different volume.
"""
import re,math
SEMANTIC_KEYS=('historic','heritage','building:material','building:colour','material','building')
def inherited_tags(tags,parent=None):
 out=dict(tags)
 if 'building:part' in tags and parent:
  for key in SEMANTIC_KEYS:
   if key not in out and key in parent:out[key]=parent[key]
 return out

def metres(value,default):
 try:
  m=re.fullmatch(r'\s*([+-]?[\d.]+)\s*(m|metres|meters|ft|feet|\')?\s*',str(value),re.I)
  if not m:return default
  v=float(m[1]);v*=.3048 if m[2] in ['ft','feet',"'"] else 1
  return v if math.isfinite(v) else default
 except(ValueError,TypeError):return default

def minimum_height(tags,total):
 if 'min_height'in tags:return max(0,metres(tags['min_height'],0)),'min_height'
 if 'building:min_level'in tags:return max(0,metres(tags['building:min_level'],0)*3.2),'min_levelEstimated'
 return 0,'ground'

def is_heritage(tags):
 return bool(tags.get('historic') or tags.get('heritage')) or tags.get('building') in ['gate','temple','shrine','pagoda'] or tags.get('name') in ['东配殿','西配殿','祈年门','皇乾殿','具服殿'] and tags.get('roof:material')=='roof_tiles'

def wall_finish(tags,heritage):
 # An explicit material is retained; unobserved colours are only visual defaults.
 material=tags.get('building:material',tags.get('material',''))
 color=tags.get('building:colour','')
 solid=heritage or tags.get('building')=='wall' or material in ['stone','marble','granite'] and tags.get('historic') in ['monument','memorial']
 if not color and solid:color='#a6a39a' if material in ['stone','marble','granite'] else '#a62c22' if material=='wood' else '#875044'
 return {'material':material,'color':color,'solid':solid,'colorSource':'osm' if 'building:colour'in tags else 'illustrative' if color else 'default'}
