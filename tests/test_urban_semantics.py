import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from urban_semantics import inherited_tags,minimum_height,is_heritage,wall_finish
class Semantics(unittest.TestCase):
 def test_roof_remains_elevated(self):
  self.assertEqual(minimum_height({'min_height':'29'},35),(29,'min_height'))
 def test_explicit_minimum_overrides_levels(self):
  self.assertEqual(minimum_height({'min_height':'6 m','building:min_level':'8'},30),(6,'min_height'))
 def test_feet_and_level_fallback_are_distinguished(self):
  self.assertAlmostEqual(minimum_height({'min_height':'10 ft'},30)[0],3.048)
  self.assertEqual(minimum_height({'building:min_level':'4'},30),(12.8,'min_levelEstimated'))
 def test_inheritance_does_not_copy_a_parents_height_or_override_child_material(self):
  child={'building:part':'yes','height':'35','min_height':'29','building:material':'wood'}
  parent={'height':'40','min_height':'12','historic':'city_gate','building:material':'stone','building:colour':'firebrick'}
  r=inherited_tags(child,parent);self.assertEqual(r['height'],'35');self.assertEqual(r['min_height'],'29');self.assertEqual(r['building:material'],'wood');self.assertTrue(is_heritage(r));self.assertTrue(wall_finish(r,True)['solid'])
 def test_ordinary_building_is_not_inherited(self):
  r=inherited_tags({'building':'apartments'},{'historic':'monument'});self.assertFalse(is_heritage(r));self.assertFalse(wall_finish(r,False)['solid'])
 def test_monument_uses_solid_stone_without_office_windows(self):
  tags={'historic':'monument','material':'stone'};self.assertTrue(wall_finish(tags,is_heritage(tags))['solid']);self.assertEqual(wall_finish(tags,True)['color'],'#a6a39a')
if __name__=='__main__':unittest.main()
