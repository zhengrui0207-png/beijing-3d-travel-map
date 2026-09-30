import unittest,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from urban_facades import facade_layout,face_uv,profile
class Facades(unittest.TestCase):
 def row(self,**kw):return dict({'kind':'apartments','height':.18,'minHeight':0,'eaves':.191},**kw)
 def test_actual_storeys_override_generic_spacing(self):
  r=self.row();s=facade_layout(r,{'building:levels':'5'});self.assertEqual(s['floors'],5);self.assertEqual(s['floorSource'],'osm-levels');self.assertAlmostEqual(s['floorHeight'],.036)
 def test_corners_have_whole_bays_even_on_rotated_walls(self):
  r=self.row();s=facade_layout(r,{'building:levels':'6'});f=[(1,2,.011),(1.17,2.17,.011),(1.17,2.17,.191),(1,2,.191)];uv=face_uv(f,r,s);self.assertAlmostEqual(uv[1][0],7);self.assertAlmostEqual(uv[2][1],6);self.assertEqual(uv[0],(0,0))
 def test_elevated_parts_begin_at_their_base(self):
  r=self.row(minHeight=.064);s=facade_layout(r,{'building:levels':'6','building:min_level':'2'});self.assertEqual(s['floors'],4);uv=face_uv([(0,0,.075),(.2,0,.075),(.2,0,.191),(0,0,.191)],r,s);self.assertAlmostEqual(uv[0][1],0);self.assertAlmostEqual(uv[2][1],4)
 def test_unknown_types_are_not_reclassified_as_offices(self):
  self.assertEqual(profile(self.row(kind='yes')),'generic');self.assertEqual(profile(self.row(kind='school')),'civic');self.assertEqual(profile(self.row(kind='office')),'commercial')
 def test_malformed_levels_are_explicitly_inferred(self):
  for levels in ['bad','nan','-2','0','999']:
   s=facade_layout(self.row(),{'building:levels':levels});self.assertEqual(s['floorSource'],'height-inferred');self.assertTrue(math.isfinite(s['floorHeight']))
if __name__=='__main__':unittest.main()
