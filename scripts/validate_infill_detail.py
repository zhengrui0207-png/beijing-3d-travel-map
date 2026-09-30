"""Check outline-safe parapets with a concave courtyard and shallow gable ridge."""
import sys,math,json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
sys.path.insert(0,str(Path(__file__).parent))
from prepare_infill_detail import detail
outer=[[0,0],[1,0],[1,.4],[.6,.4],[.6,1],[0,1]];hole=[[.1,.1],[.1,.3],[.3,.3],[.3,.1]]
p=Polygon(outer,[hole]);r={'roofShape':'unspecified-flat','rings':[outer,hole],'roof':[[[0,0,.1],[1,0,.1],[0,1,.1]]]}
g=detail(r)['parapet'];tops=[Polygon([(x,y)for x,y,z in f])for f in g if len(f)==3];surface=unary_union(tops);expected=p.difference(p.buffer(-.002,join_style=2))
assert surface.symmetric_difference(expected).area<1e-12
assert surface.intersection(Polygon(hole)).area<1e-12
assert all(abs(f[0][2]-.1045)<1e-10 for f in g if len(f)==3)
# Two triangles sharing the ridge must create exactly one ridge beam.
r={'roofShape':'inferred-gabled','walls':[],'roof':[[[0,0,.06],[1,0,.06],[.5,.2,.03]],[[1,0,.06],[0,0,.06],[.5,-.2,.03]]]}
g=detail(r);assert len(g['ridge'])==6
print(json.dumps({'concaveCourtyardParapet':'pass','ridgeDeduplication':'pass','estimatedParapetHeightMetres':.45}))
