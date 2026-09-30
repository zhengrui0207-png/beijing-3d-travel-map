"""Footprint-aligned facade coordinates; layouts are illustrative, source storeys retained."""
import math

def profile(row):
 kind=row['kind'];material=row.get('wallFinish',{}).get('material','')
 if material in ['glass','mirror']:return 'glass'
 if kind in ['apartments','residential','dormitory']:return 'residential'
 if kind in ['office','commercial','hotel','retail','mall','company']:return 'commercial'
 if kind in ['school','university','hospital','kindergarten','college','government','public']:return 'civic'
 if kind in ['house','bungalow','guardhouse','service','toilets','shed','garage','garages']:return 'lowrise'
 return 'generic'

def facade_layout(row,tags):
 style=profile(row);usable=max(.001,row['eaves']-.011-row.get('minHeight',0));tagged=False
 try:
  levels=float(tags.get('building:levels','nan'));minimum=float(tags.get('building:min_level',0))
  if math.isfinite(levels)and levels>minimum and levels<=180:
   # For elevated parts without min_level, infer occupied share without moving geometry.
   if row.get('minHeight',0)>0 and 'building:min_level'not in tags:minimum=levels*row['minHeight']/row['height']
   floors=max(1,round(levels-minimum));tagged=True
  else:raise ValueError()
 except(ValueError,TypeError):floors=max(1,round(usable/({'commercial':.038,'civic':.036}.get(style,.032))))
 return {'style':style,'floors':floors,'floorSource':'osm-levels'if tagged else 'height-inferred','floorHeight':usable/floors,'bayWidth':{'residential':.036,'commercial':.041,'civic':.033,'lowrise':.030,'glass':.016}.get(style,.034)}

def face_uv(face,row,layout):
 a,b=face[:2];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
 if length<1e-8:return [(0,0)]*len(face)
 bays=max(1,round(length/layout['bayWidth']));base=.011+row.get('minHeight',0)
 return [(((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(length*length)*bays,(p[2]-base)/layout['floorHeight'])for p in face]
